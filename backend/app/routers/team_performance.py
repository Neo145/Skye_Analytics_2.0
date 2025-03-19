from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

# Import your database connection
from app.database import get_db
# Import helper functions and models
from app.models.team import TeamPerformance, WinPercentage, WinningStreak, RecentPerformance, HomeAwayPerformance, OpponentPerformance

router = APIRouter(
    prefix="/api/teams",
    tags=["Team Performance"]
)

# Helper functions
def calculate_win_percentage(wins, total_matches):
    if total_matches == 0:
        return 0.0
    return round((wins / total_matches) * 100, 2)

def get_all_matches(db: Session):
    """Fetch all matches data from the database"""
    # Using match_info table for match details
    query = """
    SELECT 
        filename, match_date, team1, team2, winner, venue, city, season
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

def get_team_home_venues(team: str):
    """Get home venues for a team"""
    # This is a simplified mapping - in a real app, you'd have this in your database
    team_venues = {
        "Mumbai Indians": ["Mumbai", "Wankhede Stadium"],
        "Chennai Super Kings": ["Chennai", "M.A. Chidambaram Stadium"],
        "Royal Challengers Bangalore": ["Bangalore", "M. Chinnaswamy Stadium"],
        "Kolkata Knight Riders": ["Kolkata", "Eden Gardens"],
        "Delhi Capitals": ["Delhi", "Arun Jaitley Stadium", "Feroz Shah Kotla"],
        "Sunrisers Hyderabad": ["Hyderabad", "Rajiv Gandhi International Stadium"],
        "Punjab Kings": ["Mohali", "Punjab Cricket Association Stadium"],
        "Rajasthan Royals": ["Jaipur", "Sawai Mansingh Stadium"],
        "Gujarat Titans": ["Ahmedabad", "Narendra Modi Stadium"],
        "Lucknow Super Giants": ["Lucknow", "BRSABV Ekana Cricket Stadium"]
    }
    
    # Return default empty list if team not found
    return team_venues.get(team, [])

@router.get("/", response_model=List[str])
def get_teams(db: Session = Depends(get_db)):
    """Get all team names"""
    return get_team_names(db)

@router.get("/{team}/win-percentage", response_model=WinPercentage)
def get_team_win_percentage(team: str, season: Optional[int] = None, db: Session = Depends(get_db)):
    """Get win percentage for a specific team, optionally filtered by season"""
    matches_df = get_all_matches(db)
    
    # Filter for the specific team
    team_matches = matches_df[(matches_df['team1'] == team) | (matches_df['team2'] == team)]
    
    if season:
        team_matches = team_matches[team_matches['season'] == season]
    
    if team_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found for team: {team}")
    
    # Calculate in Python
    total_matches = len(team_matches)
    total_wins = len(team_matches[team_matches['winner'] == team])
    win_percentage = calculate_win_percentage(total_wins, total_matches)
    
    return {
        "team": team,
        "total_matches": total_matches,
        "wins": total_wins,
        "win_percentage": win_percentage,
        "season": season if season else "all"
    }

@router.get("/{team}/winning-streak", response_model=WinningStreak)
def get_team_winning_streak(team: str, db: Session = Depends(get_db)):
    """Calculate current and longest winning streak for a team"""
    matches_df = get_all_matches(db)
    
    # Filter for matches involving the team
    team_matches = matches_df[(matches_df['team1'] == team) | (matches_df['team2'] == team)]
    
    if team_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found for team: {team}")
    
    # Sort matches by date
    team_matches['match_date'] = pd.to_datetime(team_matches['match_date'], errors='coerce')
    team_matches = team_matches.sort_values('match_date')
    
    # Create a new column indicating if the team won
    team_matches['team_won'] = team_matches['winner'] == team
    
    # Calculate longest winning streak
    max_win_streak = 0
    current_win_streak = 0
    
    results = team_matches['team_won'].tolist()
    
    for result in results:
        if result:  # Team won
            current_win_streak += 1
            max_win_streak = max(max_win_streak, current_win_streak)
        else:  # Team lost or tied
            current_win_streak = 0
    
    # Calculate current streak
    current_streak = 0
    current_streak_type = None
    
    # Reverse to get most recent matches first
    reversed_results = results[::-1]
    
    if reversed_results:
        current_streak_type = "win" if reversed_results[0] else "loss"
        current_streak = 1
        
        for i in range(1, len(reversed_results)):
            if (current_streak_type == "win" and reversed_results[i]) or \
               (current_streak_type == "loss" and not reversed_results[i]):
                current_streak += 1
            else:
                break
    
    return {
        "team": team,
        "current_streak": {
            "type": current_streak_type if current_streak_type else "none",
            "count": current_streak
        },
        "longest_winning_streak": max_win_streak
    }

@router.get("/{team}/recent-performance", response_model=RecentPerformance)
def get_team_recent_performance(team: str, matches: int = 5, db: Session = Depends(get_db)):
    """Get performance in last N matches"""
    matches_df = get_all_matches(db)
    
    # Filter for matches involving the team
    team_matches = matches_df[(matches_df['team1'] == team) | (matches_df['team2'] == team)]
    
    if team_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found for team: {team}")
    
    # Sort matches by date descending
    team_matches['match_date'] = pd.to_datetime(team_matches['match_date'], errors='coerce')
    team_matches = team_matches.sort_values('match_date', ascending=False)
    
    # Take only the last N matches
    recent_matches = team_matches.head(matches)
    
    results = []
    for _, match in recent_matches.iterrows():
        opponent = match['team2'] if match['team1'] == team else match['team1']
        match_result = "win" if match['winner'] == team else "loss"
        
        results.append({
            "match_id": match['filename'],
            "date": match['match_date'].strftime("%Y-%m-%d") if not pd.isna(match['match_date']) else None,
            "opponent": opponent,
            "result": match_result,
            "venue": match['venue']
        })
    
    # Calculate summary
    wins = sum(1 for match in results if match['result'] == "win")
    
    return {
        "team": team,
        "last_matches": matches,
        "wins": wins,
        "losses": matches - wins,
        "win_percentage": calculate_win_percentage(wins, len(results)),
        "matches": results
    }

@router.get("/{team}/home-away-performance", response_model=HomeAwayPerformance)
def get_team_home_away_performance(team: str, db: Session = Depends(get_db)):
    """Calculate home and away performance ratios"""
    matches_df = get_all_matches(db)
    
    # Filter for matches involving the team
    team_matches = matches_df[(matches_df['team1'] == team) | (matches_df['team2'] == team)]
    
    if team_matches.empty:
        raise HTTPException(status_code=404, detail=f"No matches found for team: {team}")
    
    # Get home venues for the team
    home_venues = get_team_home_venues(team)
    
    # Categorize matches as home or away
    # A match is a home match if it's played in one of the team's home venues
    home_matches = team_matches[
        team_matches['venue'].str.contains('|'.join(home_venues), case=False, na=False) |
        team_matches['city'].str.contains('|'.join(home_venues), case=False, na=False)
    ]
    away_matches = team_matches[~team_matches.index.isin(home_matches.index)]
    
    # Calculate home performance
    home_wins = len(home_matches[home_matches['winner'] == team])
    home_total = len(home_matches)
    home_win_percentage = calculate_win_percentage(home_wins, home_total)
    
    # Calculate away performance
    away_wins = len(away_matches[away_matches['winner'] == team])
    away_total = len(away_matches)
    away_win_percentage = calculate_win_percentage(away_wins, away_total)
    
    return {
        "team": team,
        "home_performance": {
            "matches": home_total,
            "wins": home_wins,
            "win_percentage": home_win_percentage
        },
        "away_performance": {
            "matches": away_total,
            "wins": away_wins,
            "win_percentage": away_win_percentage
        }
    }

@router.get("/{team}/opponent-performance/{opponent}", response_model=OpponentPerformance)
def get_team_opponent_performance(team: str, opponent: str, db: Session = Depends(get_db)):
    """Calculate performance against a specific opponent"""
    matches_df = get_all_matches(db)
    
    # Filter for matches between these two teams
    team_vs_opponent = matches_df[
        ((matches_df['team1'] == team) & (matches_df['team2'] == opponent)) |
        ((matches_df['team1'] == opponent) & (matches_df['team2'] == team))
    ]
    
    if team_vs_opponent.empty:
        raise HTTPException(status_code=404, detail=f"No matches found between {team} and {opponent}")
    
    # Calculate wins against this opponent
    total_matches = len(team_vs_opponent)
    wins = len(team_vs_opponent[team_vs_opponent['winner'] == team])
    win_percentage = calculate_win_percentage(wins, total_matches)
    
    # Get history of all matches
    match_history = []
    for _, match in team_vs_opponent.iterrows():
        match_history.append({
            "match_id": match['filename'],
            "date": match['match_date'].strftime("%Y-%m-%d") if not pd.isna(match['match_date']) else None,
            "winner": match['winner'],
            "venue": match['venue'],
            "season": match['season']
        })
    
    return {
        "team": team,
        "opponent": opponent,
        "total_matches": total_matches,
        "wins": wins,
        "losses": total_matches - wins,
        "win_percentage": win_percentage,
        "match_history": match_history
    }

@router.get("/performance-comparison", response_model=List[TeamPerformance])
def get_teams_performance_comparison(db: Session = Depends(get_db)):
    """Compare performance metrics for all teams"""
    teams = get_team_names(db)
    matches_df = get_all_matches(db)
    
    comparison = []
    for team in teams:
        # Filter for matches involving the team
        team_matches = matches_df[(matches_df['team1'] == team) | (matches_df['team2'] == team)]
        
        if team_matches.empty:
            continue
        
        # Calculate wins
        wins = len(team_matches[team_matches['winner'] == team])
        total_matches = len(team_matches)
        win_percentage = calculate_win_percentage(wins, total_matches)
        
        # Sort by date and get last 5 matches
        team_matches['match_date'] = pd.to_datetime(team_matches['match_date'], errors='coerce')
        recent_matches = team_matches.sort_values('match_date', ascending=False).head(5)
        recent_wins = len(recent_matches[recent_matches['winner'] == team])
        recent_win_percentage = calculate_win_percentage(recent_wins, len(recent_matches))
        
        comparison.append({
            "team": team,
            "total_matches": total_matches,
            "wins": wins,
            "win_percentage": win_percentage,
            "recent_form": {
                "matches": len(recent_matches),
                "wins": recent_wins,
                "win_percentage": recent_win_percentage
            }
        })
    
    # Sort by overall win percentage
    comparison.sort(key=lambda x: x["win_percentage"], reverse=True)
    
    return comparison