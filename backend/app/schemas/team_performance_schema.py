from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TeamPerformanceResponse(BaseModel):
    team: str
    total_matches: int
    wins: int
    win_percentage: float
    last_10_performance: float
    max_winning_streak: int
    home_wins: int
    away_wins: int
    home_win_ratio: float
    away_win_ratio: float

class HeadToHeadResponse(BaseModel):
    team1: str
    team2: str
    total_matches: int
    team1_wins: int
    team2_wins: int
    avg_margin_team1: Optional[float]
    avg_margin_team2: Optional[float]
    season_breakdown: List[Dict[str, Any]]
    recent_matches: List[Dict[str, Any]]

class TeamPerformanceTrendsResponse(BaseModel):
    team: str
    seasonal_trends: List[Dict[str, Any]]
    avg_win_percentage: Optional[float]
    best_season_win_percentage: Optional[float]
    worst_season_win_percentage: Optional[float]

class OpponentPerformanceResponse(BaseModel):
    team: str
    opponent_performance: List[Dict[str, Any]]

class VenuePerformanceResponse(BaseModel):
    team: str
    venue_performance: List[Dict[str, Any]]

class MatchConditionsPerformanceResponse(BaseModel):
    team: str
    match_conditions_performance: List[Dict[str, Any]]