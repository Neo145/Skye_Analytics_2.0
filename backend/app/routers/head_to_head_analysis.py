from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

# Import your database connection
from app.database import get_db
# Import models
from app.models.head_to_head import (
    HeadToHeadSummary, VenueAnalysis, VictoryMargins, 
    HeadToHeadTrends, RecentHeadToHead
)

router = APIRouter(
    prefix="/api/head-to-head",
    tags=["Head-to-Head Analysis"]
)

# Helper functions
def calculate_win_percentage(wins, total_matches):
    if total_matches == 0:
        return 0.0
    return round((wins / total_matches) * 100, 2)

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

def get_team_names(db: Session):
    """Get list of all team names"""
    query = """
    SELECT DISTINCT team 
    FROM vw_team_performance
    """
    result = pd.read_sql(query, db.bind)
    return result['team'].tolist()

@router.get("/teams")
def get_h2h_team_list(db: Session = Depends(get_db)):
    """Get list of all teams for head-to-head selection"""
    return get_team_names(db)

@router.get("/summary/{team1}/{team2}", response_model=HeadToHeadSummary)
def get_head_to_head_summary(team1: str, team2: str, db: Session = Depends(get_db)):
    """Get comprehensive head-to-head summary between two teams"""
    # Get all matches
    matches_df = get_all_matches(db)
    
    # Filter for matches between these two teams
    h2h_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) | 
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if h2h_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Calculate basic stats
    total_matches = len(h2h_matches)
    team1_wins = len(h2h_matches[h2h_matches['winner'] == team1])
    team2_wins = len(h2h_matches[h2h_matches['winner'] == team2])
    no_results = total_matches - team1_wins - team2_wins
    
    # Sort matches by date for recent performance
    h2h_matches['match_date'] = pd.to_datetime(h2h_matches['match_date'], errors='coerce')
    h2h_matches = h2h_matches.sort_values('match_date')
    
    # Get recent performance (last 5 matches)
    recent_matches = h2h_matches.tail(5)
    recent_team1_wins = len(recent_matches[recent_matches['winner'] == team1])
    recent_team2_wins = len(recent_matches[recent_matches['winner'] == team2])
    
    # Get head-to-head matches with margin details
    match_history = []
    for _, match in h2h_matches.iterrows():
        match_record = {
            "match_id": match['filename'],
            "season": match['season'] if not pd.isna(match['season']) else None,
            "date": match['match_date'].strftime("%Y-%m-%d") if not pd.isna(match['match_date']) else None,
            "venue": match['venue'],
            "winner": match['winner'],
            "margin": match['margin'] if not pd.isna(match['margin']) else "No result"
        }
        match_history.append(match_record)
    
    # Create the response
    return {
        "team1": team1,
        "team2": team2,
        "total_matches": total_matches,
        "team1_wins": team1_wins,
        "team2_wins": team2_wins,
        "no_results": no_results,
        "team1_win_percentage": calculate_win_percentage(team1_wins, total_matches),
        "team2_win_percentage": calculate_win_percentage(team2_wins, total_matches),
        "recent_performance": {
            "matches": len(recent_matches),
            "team1_wins": recent_team1_wins,
            "team2_wins": recent_team2_wins
        },
        "match_history": match_history
    }

@router.get("/venue-analysis/{team1}/{team2}", response_model=VenueAnalysis)
def get_head_to_head_venue_analysis(team1: str, team2: str, db: Session = Depends(get_db)):
    """Analyze head-to-head performance at different venues between two teams"""
    # Get all matches
    matches_df = get_all_matches(db)
    
    # Filter for matches between these two teams
    h2h_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) | 
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if h2h_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Group by venue and calculate stats
    venue_performance = []
    
    # Group by venue
    venues = h2h_matches['venue'].unique()
    
    for venue in venues:
        venue_matches = h2h_matches[h2h_matches['venue'] == venue]
        total_venue_matches = len(venue_matches)
        team1_venue_wins = len(venue_matches[venue_matches['winner'] == team1])
        team2_venue_wins = len(venue_matches[venue_matches['winner'] == team2])
        
        venue_performance.append({
            "venue": venue,
            "total_matches": total_venue_matches,
            "team1_wins": team1_venue_wins,
            "team2_wins": team2_venue_wins,
            "team1_win_percentage": calculate_win_percentage(team1_venue_wins, total_venue_matches),
            "team2_win_percentage": calculate_win_percentage(team2_venue_wins, total_venue_matches)
        })
    
    # Sort by total matches played at venue (descending)
    venue_performance.sort(key=lambda x: x["total_matches"], reverse=True)
    
    return {
        "team1": team1,
        "team2": team2,
        "venue_analysis": venue_performance
    }

@router.get("/victory-margins/{team1}/{team2}", response_model=VictoryMargins)
def get_head_to_head_margins(team1: str, team2: str, db: Session = Depends(get_db)):
    """Analyze victory margins in head-to-head matches between two teams"""
    # Get all matches
    matches_df = get_all_matches(db)
    
    # Filter for matches between these two teams
    h2h_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) | 
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if h2h_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Process margins
    team1_margins = []
    team2_margins = []
    
    for _, match in h2h_matches.iterrows():
        if match['winner'] == team1 and not pd.isna(match['margin']):
            team1_margins.append({
                "match_id": match['filename'],
                "season": match['season'] if not pd.isna(match['season']) else None,
                "date": match['match_date'].strftime("%Y-%m-%d") if not pd.isna(match['match_date']) else None,
                "venue": match['venue'],
                "margin": match['margin']
            })
        elif match['winner'] == team2 and not pd.isna(match['margin']):
            team2_margins.append({
                "match_id": match['filename'],
                "season": match['season'] if not pd.isna(match['season']) else None,
                "date": match['match_date'].strftime("%Y-%m-%d") if not pd.isna(match['match_date']) else None,
                "venue": match['venue'],
                "margin": match['margin']
            })
    
    # Process margins to classify them
    def categorize_margins(margins_list):
        runs_victories = [m for m in margins_list if "run" in m["margin"].lower()]
        wickets_victories = [m for m in margins_list if "wicket" in m["margin"].lower()]
        super_over_victories = [m for m in margins_list if "super over" in m["margin"].lower()]
        other_victories = [m for m in margins_list if "run" not in m["margin"].lower() 
                          and "wicket" not in m["margin"].lower() 
                          and "super over" not in m["margin"].lower()]
        
        return {
            "by_runs": runs_victories,
            "by_wickets": wickets_victories,
            "super_over": super_over_victories,
            "other": other_victories
        }
    
    team1_categorized = categorize_margins(team1_margins)
    team2_categorized = categorize_margins(team2_margins)
    
    return {
        "team1": team1,
        "team2": team2,
        "team1_margins": {
            "total_victories": len(team1_margins),
            "by_runs_count": len(team1_categorized["by_runs"]),
            "by_wickets_count": len(team1_categorized["by_wickets"]),
            "super_over_count": len(team1_categorized["super_over"]),
            "other_count": len(team1_categorized["other"]),
            "detailed_margins": team1_categorized
        },
        "team2_margins": {
            "total_victories": len(team2_margins),
            "by_runs_count": len(team2_categorized["by_runs"]),
            "by_wickets_count": len(team2_categorized["by_wickets"]),
            "super_over_count": len(team2_categorized["super_over"]),
            "other_count": len(team2_categorized["other"]),
            "detailed_margins": team2_categorized
        }
    }

@router.get("/trends/{team1}/{team2}", response_model=HeadToHeadTrends)
def get_head_to_head_trends(team1: str, team2: str, db: Session = Depends(get_db)):
    """Analyze head-to-head performance trends over time between two teams"""
    # Get all matches
    matches_df = get_all_matches(db)
    
    # Filter for matches between these two teams
    h2h_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) | 
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if h2h_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Convert date and ensure sorted by date
    h2h_matches['match_date'] = pd.to_datetime(h2h_matches['match_date'], errors='coerce')
    h2h_matches = h2h_matches.sort_values('match_date')
    
    # Group by season and analyze performance
    h2h_matches['season'] = h2h_matches['season'].fillna(0).astype(int)
    seasonal_performance = []
    
    # Group by season
    seasonal_groups = h2h_matches.groupby('season')
    
    for season, group in seasonal_groups:
        if season == 0:  # Skip if season is unknown
            continue
            
        total_season_matches = len(group)
        team1_season_wins = len(group[group['winner'] == team1])
        team2_season_wins = len(group[group['winner'] == team2])
        
        seasonal_performance.append({
            "season": int(season),
            "total_matches": total_season_matches,
            "team1_wins": team1_season_wins,
            "team2_wins": team2_season_wins,
            "team1_win_percentage": calculate_win_percentage(team1_season_wins, total_season_matches),
            "team2_win_percentage": calculate_win_percentage(team2_season_wins, total_season_matches)
        })
    
    # Calculate streaks and recent form
    team1_current_streak = 0
    team2_current_streak = 0
    team1_longest_streak = 0
    team2_longest_streak = 0
    
    # Calculate longest winning streak
    current_team1_streak = 0
    current_team2_streak = 0
    
    for _, match in h2h_matches.iterrows():
        if match['winner'] == team1:
            current_team1_streak += 1
            current_team2_streak = 0
            team1_longest_streak = max(team1_longest_streak, current_team1_streak)
        elif match['winner'] == team2:
            current_team2_streak += 1
            current_team1_streak = 0
            team2_longest_streak = max(team2_longest_streak, current_team2_streak)
    
    # Calculate current streak (most recent matches)
    recent_matches = h2h_matches.tail(10)  # Look at last 10 matches
    
    for _, match in recent_matches[::-1].iterrows():  # Reverse to start from most recent
        if team1_current_streak == 0 and team2_current_streak == 0:
            if match['winner'] == team1:
                team1_current_streak = 1
            elif match['winner'] == team2:
                team2_current_streak = 1
        else:
            break  # Already found the current streak
    
    # Create a timeline of head-to-head results
    timeline = []
    for _, match in h2h_matches.iterrows():
        timeline.append({
            "match_id": match['filename'],
            "season": int(match['season']) if not pd.isna(match['season']) else None,
            "date": match['match_date'].strftime("%Y-%m-%d") if not pd.isna(match['match_date']) else None,
            "venue": match['venue'],
            "winner": match['winner'],
            "margin": match['margin'] if not pd.isna(match['margin']) else "No result"
        })
    
    return {
        "team1": team1,
        "team2": team2,
        "seasonal_performance": seasonal_performance,
        "team1_longest_streak": team1_longest_streak,
        "team2_longest_streak": team2_longest_streak,
        "team1_current_streak": team1_current_streak,
        "team2_current_streak": team2_current_streak,
        "timeline": timeline
    }

@router.get("/recent/{team1}/{team2}", response_model=RecentHeadToHead)
def get_recent_head_to_head(team1: str, team2: str, limit: int = 5, db: Session = Depends(get_db)):
    """Get recent head-to-head matches between two teams"""
    # Get all matches
    matches_df = get_all_matches(db)
    
    # Filter for matches between these two teams
    h2h_matches = matches_df[
        ((matches_df['team1'] == team1) & (matches_df['team2'] == team2)) | 
        ((matches_df['team1'] == team2) & (matches_df['team2'] == team1))
    ]
    
    if h2h_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team1} and {team2}")
    
    # Sort by date in descending order
    h2h_matches['match_date'] = pd.to_datetime(h2h_matches['match_date'], errors='coerce')
    h2h_matches = h2h_matches.sort_values('match_date', ascending=False)
    
    # Get recent matches
    recent_matches = h2h_matches.head(limit)
    
    # Format the response
    matches = []
    for _, match in recent_matches.iterrows():
        matches.append({
            "match_id": match['filename'],
            "season": int(match['season']) if not pd.isna(match['season']) else None,
            "date": match['match_date'].strftime("%Y-%m-%d") if not pd.isna(match['match_date']) else None,
            "venue": match['venue'],
            "winner": match['winner'],
            "margin": match['margin'] if not pd.isna(match['margin']) else "No result"
        })
    
    # Calculate recent performance summary
    team1_wins = len(recent_matches[recent_matches['winner'] == team1])
    team2_wins = len(recent_matches[recent_matches['winner'] == team2])
    
    return {
        "team1": team1,
        "team2": team2,
        "match_count": len(recent_matches),
        "team1_wins": team1_wins,
        "team2_wins": team2_wins,
        "matches": matches
    }