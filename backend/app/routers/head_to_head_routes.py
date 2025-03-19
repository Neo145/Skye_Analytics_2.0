from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import numpy as np

# Import database connection
from app.database import get_db

# Import models
from app.models.head_to_head import (
    HeadToHeadMatchup, 
    HeadToHeadVenueSummary, 
    HeadToHeadSeasonalTrend, 
    DetailedMatchResult,
    HeadToHeadDetailedHistory,
    MarginAnalysis,
    RecentTrendAnalysis
)

router = APIRouter(
    prefix="/api/head-to-head",
    tags=["Head-to-Head Analysis"]
)

# Inline helper functions
def get_team_names(db: Session):
    """Get list of all team names"""
    query = """
    SELECT DISTINCT team 
    FROM vw_team_performance
    """
    result = pd.read_sql(query, db.bind)
    return result['team'].tolist()

def get_all_matches(db: Session):
    """Fetch all matches data from the database"""
    query = """
    SELECT 
        filename, match_date, team1, team2, winner, venue, city, season, margin
    FROM 
        match_info
    ORDER BY
        match_date
    """
    return pd.read_sql(query, db.bind)

def calculate_win_percentage(wins, total_matches):
    if total_matches == 0:
        return 0.0
    return round((wins / total_matches) * 100, 2)

def parse_margin(margin_str: str) -> float:
    """
    Parse margin string to numeric value
    Handles formats like '5 runs', '7 wickets', etc.
    """
    try:
        parts = margin_str.lower().split()
        if len(parts) >= 2:
            numeric_part = float(parts[0])
            return numeric_part
        return 0.0
    except (ValueError, AttributeError):
        return 0.0

@router.get("/matchup/{team1}/{team2}", response_model=HeadToHeadMatchup)
def get_head_to_head_matchup(team1: str, team2: str, db: Session = Depends(get_db)):
    """
    Get comprehensive head-to-head matchup statistics between two teams
    """
    matches_df = get_all_matches(db)
    
    # Filter matches between the two teams
    head_to_head_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if head_to_head_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Calculate wins
    team1_wins = len(head_to_head_matches[head_to_head_matches['winner'] == team1])
    team2_wins = len(head_to_head_matches[head_to_head_matches['winner'] == team2])
    total_matches = len(head_to_head_matches)
    
    return {
        "team1": team1,
        "team2": team2,
        "total_matches": total_matches,
        "team1_wins": team1_wins,
        "team2_wins": team2_wins,
        "draws": 0,  # Assuming no draws in IPL
        "team1_win_percentage": calculate_win_percentage(team1_wins, total_matches),
        "team2_win_percentage": calculate_win_percentage(team2_wins, total_matches)
    }

@router.get("/venue-summary/{team1}/{team2}", response_model=List[HeadToHeadVenueSummary])
def get_head_to_head_venue_summary(team1: str, team2: str, db: Session = Depends(get_db)):
    """
    Analyze head-to-head performance across different venues
    """
    matches_df = get_all_matches(db)
    
    # Filter matches between the two teams
    head_to_head_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if head_to_head_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Group by venue
    venue_summaries = []
    venue_groups = head_to_head_matches.groupby('venue')
    
    for venue, venue_matches in venue_groups:
        total_matches = len(venue_matches)
        team1_wins = len(venue_matches[venue_matches['winner'] == team1])
        team2_wins = len(venue_matches[venue_matches['winner'] == team2])
        
        venue_summaries.append({
            "venue": venue,
            "total_matches": total_matches,
            "team1_wins": team1_wins,
            "team2_wins": team2_wins,
            "team1_win_percentage": calculate_win_percentage(team1_wins, total_matches),
            "team2_win_percentage": calculate_win_percentage(team2_wins, total_matches)
        })
    
    return venue_summaries

@router.get("/seasonal-trend/{team1}/{team2}", response_model=List[HeadToHeadSeasonalTrend])
def get_head_to_head_seasonal_trend(team1: str, team2: str, db: Session = Depends(get_db)):
    """
    Analyze head-to-head performance across different seasons
    """
    matches_df = get_all_matches(db)
    
    # Filter matches between the two teams
    head_to_head_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if head_to_head_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Group by season
    seasonal_trends = []
    season_groups = head_to_head_matches.groupby('season')
    
    for season, season_matches in season_groups:
        total_matches = len(season_matches)
        team1_wins = len(season_matches[season_matches['winner'] == team1])
        team2_wins = len(season_matches[season_matches['winner'] == team2])
        
        seasonal_trends.append({
            "season": season,
            "total_matches": total_matches,
            "team1_wins": team1_wins,
            "team2_wins": team2_wins,
            "team1_win_percentage": calculate_win_percentage(team1_wins, total_matches),
            "team2_win_percentage": calculate_win_percentage(team2_wins, total_matches)
        })
    
    return seasonal_trends

@router.get("/match-history/{team1}/{team2}", response_model=HeadToHeadDetailedHistory)
def get_head_to_head_detailed_history(team1: str, team2: str, db: Session = Depends(get_db)):
    """
    Get detailed match history between two teams
    """
    matches_df = get_all_matches(db)
    
    # Filter matches between the two teams
    head_to_head_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if head_to_head_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Sort matches by date
    head_to_head_matches['match_date'] = pd.to_datetime(head_to_head_matches['match_date'], errors='coerce')
    head_to_head_matches = head_to_head_matches.sort_values('match_date', ascending=False)
    
    # Convert to list of detailed match results
    match_results = []
    for _, match in head_to_head_matches.iterrows():
        match_results.append({
            "match_id": match['filename'],
            "date": match['match_date'].strftime("%Y-%m-%d") if not pd.isna(match['match_date']) else "",
            "venue": match['venue'],
            "winner": match['winner'],
            "margin": match['margin'],
            "season": match['season']
        })
    
    return {
        "team1": team1,
        "team2": team2,
        "total_matches": len(match_results),
        "matches": match_results
    }

@router.get("/margin-analysis/{team1}/{team2}", response_model=MarginAnalysis)
def get_head_to_head_margin_analysis(team1: str, team2: str, db: Session = Depends(get_db)):
    """
    Analyze victory margins between two teams
    """
    matches_df = get_all_matches(db)
    
    # Filter matches between the two teams
    head_to_head_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if head_to_head_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Compute margin analysis
    team1_margin_wins = head_to_head_matches[head_to_head_matches['winner'] == team1]
    team2_margin_wins = head_to_head_matches[head_to_head_matches['winner'] == team2]
    
    # Parse and compute margins
    team1_parsed_margins = team1_margin_wins['margin'].apply(parse_margin)
    team2_parsed_margins = team2_margin_wins['margin'].apply(parse_margin)
    
    return {
        "team1_total_margin_wins": len(team1_margin_wins),
        "team2_total_margin_wins": len(team2_margin_wins),
        "average_margin_team1": team1_parsed_margins.mean() if not team1_parsed_margins.empty else None,
        "average_margin_team2": team2_parsed_margins.mean() if not team2_parsed_margins.empty else None,
        "max_margin_team1": team1_parsed_margins.max() if not team1_parsed_margins.empty else None,
        "max_margin_team2": team2_parsed_margins.max() if not team2_parsed_margins.empty else None
    }

@router.get("/recent-trend/{team1}/{team2}", response_model=RecentTrendAnalysis)
def get_head_to_head_recent_trend(team1: str, team2: str, last_n_matches: int = 10, db: Session = Depends(get_db)):
    """
    Analyze recent performance trend between two teams
    """
    matches_df = get_all_matches(db)
    
    # Filter matches between the two teams
    head_to_head_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) |
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if head_to_head_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Sort matches by date in descending order and take last N matches
    head_to_head_matches['match_date'] = pd.to_datetime(head_to_head_matches['match_date'], errors='coerce')
    recent_matches = head_to_head_matches.sort_values('match_date', ascending=False).head(last_n_matches)
    
    # Calculate recent wins
    team1_recent_wins = len(recent_matches[recent_matches['winner'] == team1])
    team2_recent_wins = len(recent_matches[recent_matches['winner'] == team2])
    
    return {
        "team1": team1,
        "team2": team2,
        "last_n_matches": last_n_matches,
        "team1_recent_wins": team1_recent_wins,
        "team2_recent_wins": team2_recent_wins,
        "team1_recent_win_percentage": calculate_win_percentage(team1_recent_wins, last_n_matches),
        "team2_recent_win_percentage": calculate_win_percentage(team2_recent_wins, last_n_matches)
    }