from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class PaperBase(BaseModel):
    id: str
    title: str
    summary: str
    authors: str
    published_date: date
    category: str
    pdf_url: str

class PaperCreate(PaperBase):
    pass

class Paper(PaperBase):
    is_favorite: bool
    is_pinned: bool = False
    ai_summary: Optional[str] = None

    class Config:
        orm_mode = True

class PaperSearch(BaseModel):
    date: date
    category: str
