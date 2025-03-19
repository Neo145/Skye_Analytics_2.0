from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

class MatchDetails(BaseModel):
    match_id: str
    season: Optional[int] = None
    date: Optional[str] = None
    venue: Optional[str] = None
    winner: Optional[str] = None
    margin: Optional[str] = None

class RecentPerformance(BaseModel):
    matches: int
    team1_wins: int
    team2_wins: int

class HeadToHeadSummary(BaseModel):
    team1: str
    team2: str
    total_matches: int
    team1_wins: int
    team2_wins: int
    no_results: int
    team1_win_percentage: float
    team2_win_percentage: float
    recent_performance: RecentPerformance
    match_history: List[MatchDetails]

class VenuePerformance(BaseModel):
    venue: str
    total_matches: int
    team1_wins: int
    team2_wins: int
    team1_win_percentage: float
    team2_win_percentage: float

class VenueAnalysis(BaseModel):
    team1: str
    team2: str
    venue_analysis: List[VenuePerformance]

class MarginDetails(BaseModel):
    match_id: str
    season: Optional[int] = None
    date: Optional[str] = None
    venue: Optional[str] = None
    margin: str

class CategorizedMargins(BaseModel):
    by_runs: List[MarginDetails]
    by_wickets: List[MarginDetails]
    super_over: List[MarginDetails]
    other: List[MarginDetails]

class TeamMargins(BaseModel):
    total_victories: int
    by_runs_count: int
    by_wickets_count: int
    super_over_count: int
    other_count: int
    detailed_margins: CategorizedMargins

class VictoryMargins(BaseModel):
    team1: str
    team2: str
    team1_margins: TeamMargins
    team2_margins: TeamMargins

class SeasonalPerformance(BaseModel):
    season: int
    total_matches: int
    team1_wins: int
    team2_wins: int
    team1_win_percentage: float
    team2_win_percentage: float

class HeadToHeadTrends(BaseModel):
    team1: str
    team2: str
    seasonal_performance: List[SeasonalPerformance]
    team1_longest_streak: int
    team2_longest_streak: int
    team1_current_streak: int
    team2_current_streak: int
    timeline: List[MatchDetails]

class RecentHeadToHead(BaseModel):
    team1: str
    team2: str
    match_count: int
    team1_wins: int
    team2_wins: int
    matches: List[MatchDetails]