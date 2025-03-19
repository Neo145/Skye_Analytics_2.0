from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class VenueBasic(BaseModel):
    """Basic venue information model"""
    name: str
    city: Optional[str] = None
    total_matches: int


class VenueDetailResponse(BaseModel):
    """Detailed venue information response model"""
    name: str
    city: Optional[str] = None
    total_matches: int
    avg_first_innings_score: float
    avg_second_innings_score: float
    highest_score: Dict[str, Any]
    lowest_score: Dict[str, Any]
    toss_win_match_win_percentage: float
    batting_first_win_percentage: float
    most_runs: Dict[str, Any]
    most_wickets: Dict[str, Any]
    matches_by_season: Dict[str, int]


class TeamVenuePerformance(BaseModel):
    """Team's performance at a specific venue"""
    team: str
    matches_played: int
    matches_won: int
    win_percentage: float
    avg_runs_scored: float
    highest_score: Dict[str, Any]
    avg_wickets_taken: float
    best_bowling: Dict[str, Any]


class VenueTeamPerformanceResponse(BaseModel):
    """Team performances at a specific venue"""
    venue_name: str
    city: Optional[str] = None
    total_matches: int
    team_performances: List[TeamVenuePerformance]


class VenuePitchCharacteristics(BaseModel):
    """Pitch characteristics of a venue"""
    venue_name: str
    city: Optional[str] = None
    batting_friendly_score: float  # 0-10 scale
    avg_run_rate: float
    avg_boundaries_per_match: Dict[str, float]  # fours, sixes
    avg_wickets_per_match: float
    spin_effectiveness: float  # 0-10 scale
    pace_effectiveness: float  # 0-10 scale
    avg_first_innings_score: float
    avg_second_innings_score: float
    historic_pitch_behavior: str  # Description


class VenueMatchList(BaseModel):
    """List of matches at a venue"""
    venue_name: str
    city: Optional[str] = None
    total_matches: int
    matches: List[Dict[str, Any]]


class VenueListResponse(BaseModel):
    """List of all venues"""
    count: int
    venues: List[VenueBasic]


class VenueSeasonTrends(BaseModel):
    """Season-by-season trends at a venue"""
    venue_name: str
    city: Optional[str] = None
    season_data: List[Dict[str, Any]]