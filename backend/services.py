import arxiv
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
import models, schemas
import os
from openai import OpenAI

def get_papers_from_arxiv(category: str, search_date: date, limit: int = 1000):
    # Construct query with date range
    # Use lastUpdatedDate for filtering to get papers updated/published on that specific day
    date_str = search_date.strftime("%Y%m%d")
    query = f"cat:{category} AND lastUpdatedDate:[{date_str}0000 TO {date_str}2359]"
    
    client = arxiv.Client()
    
    search = arxiv.Search(
        query = query,
        max_results = limit,
        sort_by = arxiv.SortCriterion.LastUpdatedDate,
        sort_order = arxiv.SortOrder.Descending
    )

    results = []
    
    for r in client.results(search):
        # We don't need strict date filtering here because query handles it,
        # but arxiv date format might be slightly different (published vs submitted).
        # We accept all results returned by the query.
        authors = ", ".join([a.name for a in r.authors])
        
        # Capture all categories
        # r.categories is a list like ['cs.AI', 'cs.LG']
        categories = ", ".join(r.categories)
        
        paper = schemas.PaperCreate(
            id=r.entry_id.split('/')[-1],
            title=r.title,
            summary=r.summary,
            authors=authors,
            published_date=r.updated.date(), # Use updated date as the 'published_date' field for display
            category=categories, # Store all categories joined by comma
            pdf_url=r.pdf_url
        )
        results.append(paper)
            
    return results

def get_paper_by_id_from_arxiv(paper_id: str):
    """
    Fetch a single paper by its ID (e.g., '2310.12345')
    """
    client = arxiv.Client()
    search = arxiv.Search(id_list=[paper_id])
    
    try:
        r = next(client.results(search))
        authors = ", ".join([a.name for a in r.authors])
        categories = ", ".join(r.categories)
        
        paper = schemas.PaperCreate(
            id=r.entry_id.split('/')[-1],
            title=r.title,
            summary=r.summary,
            authors=authors,
            published_date=r.updated.date(),
            category=categories,
            pdf_url=r.pdf_url
        )
        return paper
    except StopIteration:
        return None
    except Exception as e:
        print(f"Error fetching paper {paper_id}: {e}")
        return None

def get_paper(db: Session, paper_id: str):
    return db.query(models.Paper).filter(models.Paper.id == paper_id).first()

def create_paper(db: Session, paper: schemas.PaperCreate):
    db_paper = models.Paper(
        id=paper.id,
        title=paper.title,
        summary=paper.summary,
        authors=paper.authors,
        published_date=paper.published_date,
        category=paper.category,
        pdf_url=paper.pdf_url
    )
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)
    return db_paper

def toggle_favorite(db: Session, paper_id: str):
    db_paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if db_paper:
        db_paper.is_favorite = not db_paper.is_favorite
        # If unfavoriting, also remove pin
        if not db_paper.is_favorite:
            db_paper.is_pinned = False
        db.commit()
        db.refresh(db_paper)
    return db_paper

def toggle_pin(db: Session, paper_id: str):
    db_paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if db_paper:
        db_paper.is_pinned = not db_paper.is_pinned
        # Ensure it is favorited if pinned
        if db_paper.is_pinned:
            db_paper.is_favorite = True
        db.commit()
        db.refresh(db_paper)
    return db_paper

def clear_unpinned_favorites(db: Session):
    # Unfavorite all papers that are favorites but NOT pinned
    papers_to_clear = db.query(models.Paper).filter(
        models.Paper.is_favorite == True,
        models.Paper.is_pinned == False
    ).all()
    
    for paper in papers_to_clear:
        paper.is_favorite = False
    
    db.commit()
    return len(papers_to_clear)

def clear_cache(db: Session):
    # Delete all papers that are NOT favorites and NOT pinned
    # This keeps user data but removes cached search results
    count = db.query(models.Paper).filter(
        models.Paper.is_favorite == False,
        models.Paper.is_pinned == False
    ).delete()
    
    db.commit()
    return count

def generate_ai_summary(db: Session, paper_id: str, api_key: str = None, base_url: str = None, model: str = "gpt-4o-mini", system_prompt: str = None):
    db_paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if not db_paper:
        return None
    
    if db_paper.ai_summary:
        return db_paper.ai_summary

    # Mock AI Summary for now (unless we want to enable real AI later)
    # The api_key is available here if we want to use it
    
    summary = ""
    
    if api_key:
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            # Use custom prompt if provided, otherwise default
            prompt_content = system_prompt if system_prompt else "You are a concise research assistant. Summarize the paper in Chinese using the following markdown format:\n\n**🎯 核心问题**: [1 sentence]\n**💡 方法创新**: [1-2 sentences]\n**🧪 关键结论**: [1-2 sentences]\n\nKeep it under 150 words total. Avoid fluff."
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt_content},
                    {"role": "user", "content": f"Title: {db_paper.title}\n\nAbstract: {db_paper.summary}"}
                ]
            )
            summary = response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            # Fallback or error message
            summary = f"AI Analysis failed: {str(e)}"
    else:
        # Fallback if no key provided
        summary = f"Please provide an OpenAI API Key to generate a summary. (Mock: {db_paper.title})"
    
    db_paper.ai_summary = summary
    db.commit()
    db.refresh(db_paper)
    return summary
