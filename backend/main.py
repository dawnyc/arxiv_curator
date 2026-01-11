from fastapi import FastAPI, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import models, schemas, services, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/papers", response_model=List[schemas.Paper])
def search_papers(
    category: Optional[str] = Query(None, description="Arxiv category, e.g., cs.AI"),
    search_date: Optional[date] = Query(None, description="Date to search"),
    paper_id: Optional[str] = Query(None, description="Specific paper ID"),
    keyword: Optional[str] = Query(None, description="Search keyword"),
    days_back: Optional[int] = Query(None, description="Number of days to search back"),
    db: Session = Depends(get_db)
):
    papers_data = []

    # Case 1: Search by ID
    if paper_id:
        single_paper = services.get_paper_by_id_from_arxiv(paper_id)
        if single_paper:
            papers_data = [single_paper]
    # Case 2: Search by Keyword + Date Range (or just Date Range)
    elif category and (keyword or days_back):
        papers_data = services.get_papers_from_arxiv(category, search_date=search_date, keyword=keyword, days_back=days_back)
    # Case 2: Search by Date/Category (Standard)
    elif category and search_date:
        papers_data = services.get_papers_from_arxiv(category, search_date=search_date)
    else:
        # Fallback or bad request if neither provided (though optional, logic requires one path)
        return []
    
    if not papers_data:
        return []

    # 2. Batch fetch existing papers from DB to avoid N+1 queries
    paper_ids = [p.id for p in papers_data]
    existing_papers = db.query(models.Paper).filter(models.Paper.id.in_(paper_ids)).all()
    existing_map = {p.id: p for p in existing_papers}
    
    results = []
    for p_data in papers_data:
        db_paper = existing_map.get(p_data.id)
        
        if not db_paper:
            # Create in DB if not exists
            db_paper = services.create_paper(db, p_data)
        else:
            # Update existing paper's category if it doesn't match the new full list
            if db_paper.category != p_data.category:
                db_paper.category = p_data.category
                db.commit()
                db.refresh(db_paper)
        
        results.append(db_paper)
    
    return results

@app.post("/api/papers/{paper_id}/analyze")
def analyze_paper(
    paper_id: str, 
    db: Session = Depends(get_db),
    x_openai_key: Optional[str] = Header(None, alias="X-OpenAI-Key"),
    model: str = Query(None, description="Model name (e.g., gpt-4o)"),
    base_url: str = Query(None, description="Custom base URL for API"),
    system_prompt: str = Query(None, description="Custom system prompt for AI")
):
    # Default to gpt-4o-mini if not provided
    model_name = model if model else "gpt-4o-mini"
    summary = services.generate_ai_summary(db, paper_id, x_openai_key, base_url, model_name, system_prompt)
        
    if not summary:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {"ai_summary": summary}

@app.post("/api/papers/{paper_id}/favorite")
def favorite_paper(paper_id: str, db: Session = Depends(get_db)):
    paper = services.toggle_favorite(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@app.post("/api/papers/{paper_id}/pin")
def pin_paper(paper_id: str, db: Session = Depends(get_db)):
    paper = services.toggle_pin(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

@app.post("/api/favorites/clear-unpinned")
def clear_unpinned(db: Session = Depends(get_db)):
    count = services.clear_unpinned_favorites(db)
    return {"cleared_count": count}

@app.post("/api/cache/clear")
def clear_cache(db: Session = Depends(get_db)):
    count = services.clear_cache(db)
    return {"cleared_count": count}

@app.get("/api/favorites", response_model=List[schemas.Paper])
def get_favorites(db: Session = Depends(get_db)):
    return db.query(models.Paper).filter(models.Paper.is_favorite == True).all()

# Serve frontend static files (if we put index.html in frontend folder)
# We will mount it at root, but make sure API routes are defined first
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
