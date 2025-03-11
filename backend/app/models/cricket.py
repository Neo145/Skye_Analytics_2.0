from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class MatchInfo(Base):
    """Model for match_info table containing match-level metadata."""
    __tablename__ = "match_info"

    filename = Column(String, primary_key=True, index=True)
    data_version = Column(Float)
    created_date = Column(String)
    competition = Column(String)
    match_date = Column(String)
    venue = Column(String)
    city = Column(String)
    match_type = Column(String)
    toss_winner = Column(String)
    toss_decision = Column(String)
    winner = Column(String)
    margin = Column(String)
    player_of_match = Column(String)
    team1 = Column(String)
    team2 = Column(String)
    season = Column(Integer)

    # Relationship to innings_data
    innings = relationship("InningsData", back_populates="match")


class InningsData(Base):
    """Model for innings_data table containing ball-by-ball information."""
    __tablename__ = "innings_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, ForeignKey("match_info.filename"))
    innings_type = Column(String)
    team = Column(String)
    over_ball = Column(Float)
    batsman = Column(String)
    bowler = Column(String)
    non_striker = Column(String)
    runs_batsman = Column(Integer)
    runs_total = Column(Integer)
    extras_type = Column(String)
    extras_runs = Column(Integer)
    wicket_details = Column(String)

    # Relationship to match_info
    match = relationship("MatchInfo", back_populates="innings")