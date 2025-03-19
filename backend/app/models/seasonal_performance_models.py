from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SeasonData(BaseModel):
    season: int
    matches_played: int
    wins: int
    losses: int
    win_percentage: float
    playoff_qualification: str

class TeamPerformance(BaseModel):
    team: str
    seasonal_data: List[SeasonData]

class SeasonalPerformanceResponse(BaseModel):
    season_count: int
    teams: List[str]
    seasonal_performance: List[TeamPerformance]

class ConsistencyMetric(BaseModel):
    team: str
    seasons_participated: int
    avg_win_percentage: float
    max_win_percentage: float
    min_win_percentage: float
    std_dev_win_percentage: float
    cv_win_percentage: float
    most_consistent_season: int
    seasons_above_50_percent: int

class SeasonalConsistencyResponse(BaseModel):
    metrics_description: Dict[str, str]
    consistency_metrics: List[ConsistencyMetric]

class TrendMetric(BaseModel):
    team: str
    overall_trend: str
    trend_strength: float
    recent_trend: str
    best_season: int
    worst_season: int
    first_season: int
    last_season: int
    first_to_last_change: float

class SeasonalTrendResponse(BaseModel):
    metrics_description: Dict[str, str]
    trend_metrics: List[TrendMetric]

class MatchData(BaseModel):
    date: str
    opponent: str
    venue: str
    result: str

class FirstLastData(BaseModel):
    season: int
    first_match: MatchData
    last_match: MatchData
    first_match_win: bool
    last_match_win: bool

class TeamFirstLastData(BaseModel):
    team: str
    first_last_data: List[FirstLastData]
    first_match_win_percentage: float
    last_match_win_percentage: float

class FirstLastMatchResponse(BaseModel):
    first_last_match_data: List[TeamFirstLastData]

class SeasonListResponse(BaseModel):
    seasons: List[int]