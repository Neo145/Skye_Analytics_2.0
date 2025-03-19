from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

class StreakInfo(BaseModel):
    type: str  # "win" or "loss"
    count: int

class MatchResult(BaseModel):
    match_id: str
    date: Optional[str] = None
    opponent: str
    result: str  # "win" or "loss"
    venue: Optional[str] = None

class MatchHistory(BaseModel):
    match_id: str
    date: Optional[str] = None
    winner: str
    venue: Optional[str] = None
    season: Optional[int] = None

class PerformanceMetrics(BaseModel):
    matches: int
    wins: int
    win_percentage: float

class RecentForm(BaseModel):
    matches: int
    wins: int
    win_percentage: float

class WinPercentage(BaseModel):
    team: str
    total_matches: int
    wins: int
    win_percentage: float
    season: Union[int, str]

class WinningStreak(BaseModel):
    team: str
    current_streak: StreakInfo
    longest_winning_streak: int

class RecentPerformance(BaseModel):
    team: str
    last_matches: int
    wins: int
    losses: int
    win_percentage: float
    matches: List[MatchResult]

class HomeAwayPerformance(BaseModel):
    team: str
    home_performance: PerformanceMetrics
    away_performance: PerformanceMetrics

class OpponentPerformance(BaseModel):
    team: str
    opponent: str
    total_matches: int
    wins: int
    losses: int
    win_percentage: float
    match_history: List[MatchHistory]

class TeamPerformance(BaseModel):
    team: str
    total_matches: int
    wins: int
    win_percentage: float
    recent_form: RecentForm