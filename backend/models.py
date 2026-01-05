from sqlalchemy import Column, Integer, String, Boolean, Text, Date
from database import Base

class Paper(Base):
    __tablename__ = "papers"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    summary = Column(Text)
    authors = Column(String)
    published_date = Column(Date)
    category = Column(String)
    pdf_url = Column(String)
    is_favorite = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    ai_summary = Column(Text, nullable=True)