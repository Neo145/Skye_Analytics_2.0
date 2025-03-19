from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd

# Import your database connection
from app.database import get_db

# Pydantic models for type hinting and validation
from pydantic import BaseModel

class HeadToHeadSummary(BaseModel):
    team1: str
    team2: str
    total_matches: int
    team1_wins: int
    team2_wins: int
    draws: int
    team1_win_percentage: float
    team2_win_percentage: float

class HeadToHeadMatchDetail(BaseModel):
    match_id: str
    date: Optional[str] = None
    venue: str
    winner: str
    margin: Optional[str] = None
    season: Optional[int] = None

class HeadToHeadVenuePerformance(BaseModel):
    team1: str
    team2: str
    venues: List[dict]

class HeadToHeadTrend(BaseModel):
    team1: str
    team2: str
    recent_matches: List[HeadToHeadMatchDetail]
    trend_analysis: dict

class HeadToHeadMarginAnalysis(BaseModel):
    team1: str
    team2: str
    average_margin_team1: Optional[float] = None
    average_margin_team2: Optional[float] = None
    most_dominant_victory_team1: Optional[HeadToHeadMatchDetail] = None
    most_dominant_victory_team2: Optional[HeadToHeadMatchDetail] = None

# Create the router
router = APIRouter(
    prefix="/api/head-to-head",
    tags=["Head-to-Head Analysis"]
)

def calculate_win_percentage(wins, total_matches):
    """Calculate win percentage"""
    if total_matches == 0:
        return 0.0
    return round((wins / total_matches) * 100, 2)

def get_all_matches(db: Session):
    """Fetch all matches data from the database"""
    try:
        query = """
        SELECT 
            filename, 
            match_date, 
            team1, 
            team2, 
            winner, 
            venue, 
            city, 
            season, 
            margin
        FROM 
            match_info
        ORDER BY
            match_date
        """
        return pd.read_sql(query, db.bind)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching matches: {str(e)}")

@router.get("/summary", response_model=HeadToHeadSummary)
def get_head_to_head_summary(
    team1: str, 
    team2: str, 
    db: Session = Depends(get_db)
):
    """Get comprehensive head-to-head summary between two teams"""
    matches_df = get_all_matches(db)
    
    # Filter matches between the two teams
    head_to_head_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if head_to_head_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Calculate wins for each team
    team1_wins = len(head_to_head_matches[head_to_head_matches['winner'] == team1])
    team2_wins = len(head_to_head_matches[head_to_head_matches['winner'] == team2])
    total_matches = len(head_to_head_matches)
    draws = total_matches - (team1_wins + team2_wins)
    
    return {
        "team1": team1,
        "team2": team2,
        "total_matches": total_matches,
        "team1_wins": team1_wins,
        "team2_wins": team2_wins,
        "draws": draws,
        "team1_win_percentage": calculate_win_percentage(team1_wins, total_matches),
        "team2_win_percentage": calculate_win_percentage(team2_wins, total_matches)
    }

@router.get("/match-details", response_model=List[HeadToHeadMatchDetail])
def get_head_to_head_match_details(
    team1: str, 
    team2: str, 
    limit: Optional[int] = 10, 
    db: Session = Depends(get_db)
):
    """Get detailed match history between two teams"""
    matches_df = get_all_matches(db)
    
    # Filter matches between the two teams
    head_to_head_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if head_to_head_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Sort by date descending and limit
    head_to_head_matches['match_date'] = pd.to_datetime(head_to_head_matches['match_date'], errors='coerce')
    head_to_head_matches = head_to_head_matches.sort_values('match_date', ascending=False).head(limit)
    
    match_details = []
    for _, match in head_to_head_matches.iterrows():
        match_details.append({
            "match_id": match['filename'],
            "date": match['match_date'].strftime("%Y-%m-%d") if not pd.isna(match['match_date']) else None,
            "venue": match['venue'],
            "winner": match['winner'],
            "margin": match['margin'],
            "season": match['season']
        })
    
    return match_details

@router.get("/venue-performance", response_model=HeadToHeadVenuePerformance)
def get_head_to_head_venue_performance(team1: str, team2: str, db: Session = Depends(get_db)):
    """Analyze venue-wise performance for head-to-head matches"""
    matches_df = get_all_matches(db)
    
    # Filter matches between the two teams
    head_to_head_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if head_to_head_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Group by venue and calculate performance
    venue_performance = []
    venues = head_to_head_matches['venue'].unique()
    
    for venue in venues:
        venue_matches = head_to_head_matches[head_to_head_matches['venue'] == venue]
        
        team1_matches = venue_matches[venue_matches['team1'] == team1]
        team2_matches = venue_matches[venue_matches['team1'] == team2]
        
        venue_info = {
            "venue": venue,
            "total_matches": len(venue_matches),
            team1: {
                "matches": len(team1_matches),
                "wins": len(team1_matches[team1_matches['winner'] == team1]),
                "win_percentage": calculate_win_percentage(
                    len(team1_matches[team1_matches['winner'] == team1]), 
                    len(team1_matches)
                )
            },
            team2: {
                "matches": len(team2_matches),
                "wins": len(team2_matches[team2_matches['winner'] == team2]),
                "win_percentage": calculate_win_percentage(
                    len(team2_matches[team2_matches['winner'] == team2]), 
                    len(team2_matches)
                )
            }
        }
        
        venue_performance.append(venue_info)
    
    return {
        "team1": team1,
        "team2": team2,
        "venues": venue_performance
    }

@router.get("/trend-analysis", response_model=HeadToHeadTrend)
def get_head_to_head_trend_analysis(
    team1: str, 
    team2: str, 
    recent_matches: int = 10, 
    db: Session = Depends(get_db)
):
    """Analyze recent performance trend between two teams"""
    matches_df = get_all_matches(db)
    
    # Filter matches between the two teams
    head_to_head_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if head_to_head_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Sort by date descending and limit
    head_to_head_matches['match_date'] = pd.to_datetime(head_to_head_matches['match_date'], errors='coerce')
    recent_matches_df = head_to_head_matches.sort_values('match_date', ascending=False).head(recent_matches)
    
    # Prepare recent match details
    recent_match_details = []
    for _, match in recent_matches_df.iterrows():
        recent_match_details.append({
            "match_id": match['filename'],
            "date": match['match_date'].strftime("%Y-%m-%d") if not pd.isna(match['match_date']) else None,
            "venue": match['venue'],
            "winner": match['winner'],
            "season": match['season']
        })
    
    # Trend analysis
    trend_analysis = {
        "total_recent_matches": len(recent_matches_df),
        team1: {
            "wins": len(recent_matches_df[recent_matches_df['winner'] == team1]),
            "win_percentage": calculate_win_percentage(
                len(recent_matches_df[recent_matches_df['winner'] == team1]), 
                len(recent_matches_df)
            )
        },
        team2: {
            "wins": len(recent_matches_df[recent_matches_df['winner'] == team2]),
            "win_percentage": calculate_win_percentage(
                len(recent_matches_df[recent_matches_df['winner'] == team2]), 
                len(recent_matches_df)
            )
        }
    }
    
    return {
        "team1": team1,
        "team2": team2,
        "recent_matches": recent_match_details,
        "trend_analysis": trend_analysis
    }

@router.get("/margin-analysis", response_model=HeadToHeadMarginAnalysis)
def get_head_to_head_margin_analysis(team1: str, team2: str, db: Session = Depends(get_db)):
    """Analyze victory margins between two teams"""
    matches_df = get_all_matches(db)
    
    # Filter matches between the two teams
    head_to_head_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if head_to_head_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Parse and convert margins to numeric values (this is a simplified approach)
    def parse_margin(margin: str) -> float:
        try:
            # Remove text and keep only numeric part
            import re
            numeric_margin = re.findall(r'\d+', margin)[0]
            return float(numeric_margin)
        except:
            return 0.0
    
    # Calculate margins for each team
    team1_matches = head_to_head_matches[head_to_head_matches['winner'] == team1]
    team2_matches = head_to_head_matches[head_to_head_matches['winner'] == team2]
    
    # Calculate average margins
    team1_margins = team1_matches['margin'].apply(parse_margin)
    team2_margins = team2_matches['margin'].apply(parse_margin)
    
    # Find most dominant victories
    def get_most_dominant_victory(team_matches):
        if team_matches.empty:
            return None
        
        most_dominant = team_matches.loc[team_matches['margin'].apply(parse_margin).idxmax()]
        return {
            "match_id": most_dominant['filename'],
            "date": pd.to_datetime(most_dominant['match_date']).strftime("%Y-%m-%d"),
            "venue": most_dominant['venue'],
            "winner": most_dominant['winner'],
            "margin": most_dominant['margin'],
            "season": most_dominant['season']
        }
    
    return {
        "team1": team1,
        "team2": team2,
        "average_margin_team1": team1_margins.mean() if not team1_margins.empty else None,
        "average_margin_team2": team2_margins.mean() if not team2_margins.empty else None,
        "most_dominant_victory_team1": get_most_dominant_victory(team1_matches),
        "most_dominant_victory_team2": get_most_dominant_victory(team2_matches)
    }