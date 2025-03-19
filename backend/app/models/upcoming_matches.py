# app/models/upcoming_matches.py
from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.database import Base

class UpcomingMatch(Base):
    __tablename__ = "ipl_upcoming_matches"
    
    id = Column(String, primary_key=True, index=True)
    match_date = Column(DateTime, nullable=True)
    team1 = Column(String, nullable=True)
    team2 = Column(String, nullable=True)
    series = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<UpcomingMatch(id={self.id}, team1={self.team1}, team2={self.team2})>"