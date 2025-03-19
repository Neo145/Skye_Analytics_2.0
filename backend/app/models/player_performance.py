from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union

class PlayerBasicInfo(BaseModel):
    player_name: str
    playing_role: Optional[str] = None
    batting_style: Optional[str] = None
    bowling_style: Optional[str] = None
    country: Optional[str] = None

class BattingPerformanceSummary(BaseModel):
    matches_played: int
    innings_batted: int
    runs_scored: int
    balls_faced: int
    highest_score: int
    average: float
    strike_rate: float
    centuries: int
    half_centuries: int
    fours: int
    sixes: int
    not_outs: int

class BowlingPerformanceSummary(BaseModel):
    matches_played: int
    innings_bowled: int
    overs_bowled: float
    runs_conceded: int
    wickets: int
    best_bowling_figures: str
    average: float
    economy_rate: float
    strike_rate: float
    four_wickets: int
    five_wickets: int

class InningsHighlight(BaseModel):
    match_id: str
    date: Optional[str] = None
    opponent: str
    score: int
    balls_faced: int
    strike_rate: float
    fours: int
    sixes: int
    not_out: bool
    result: str  # Win/Loss
    venue: Optional[str] = None
    season: Optional[int] = None

class BowlingHighlight(BaseModel):
    match_id: str
    date: Optional[str] = None
    opponent: str
    overs: float
    wickets: int
    runs_conceded: int
    economy: float
    bowling_figures: str
    result: str  # Win/Loss
    venue: Optional[str] = None
    season: Optional[int] = None

class TeamwisePerformance(BaseModel):
    team: str
    matches: int
    innings: int
    runs: Optional[int] = None
    average: Optional[float] = None
    strike_rate: Optional[float] = None
    wickets: Optional[int] = None
    economy: Optional[float] = None
    bowling_strike_rate: Optional[float] = None
    best_score: Optional[int] = None
    best_bowling: Optional[str] = None

class SeasonalPerformance(BaseModel):
    season: int
    matches: int
    runs: Optional[int] = None
    average: Optional[float] = None
    strike_rate: Optional[float] = None
    wickets: Optional[int] = None
    economy: Optional[float] = None
    bowling_strike_rate: Optional[float] = None
    
class VenuePerformance(BaseModel):
    venue: str
    matches: int
    innings: int
    runs: Optional[int] = None
    average: Optional[float] = None
    strike_rate: Optional[float] = None
    wickets: Optional[int] = None
    economy: Optional[float] = None
    bowling_strike_rate: Optional[float] = None

class MatchSituationPerformance(BaseModel):
    situation: str  # e.g., "PowerPlay", "Death Overs", "Chase", etc.
    innings: int
    runs: Optional[int] = None
    average: Optional[float] = None
    strike_rate: Optional[float] = None
    wickets: Optional[int] = None
    economy: Optional[float] = None
    bowling_strike_rate: Optional[float] = None

class PlayerPerformanceResponse(BaseModel):
    player_info: PlayerBasicInfo
    batting_summary: Optional[BattingPerformanceSummary] = None
    bowling_summary: Optional[BowlingPerformanceSummary] = None
    highest_scores: Optional[List[InningsHighlight]] = None
    best_bowling: Optional[List[BowlingHighlight]] = None
    against_teams: Optional[List[TeamwisePerformance]] = None
    by_season: Optional[List[SeasonalPerformance]] = None
    by_venue: Optional[List[VenuePerformance]] = None
    by_match_situation: Optional[List[MatchSituationPerformance]] = None