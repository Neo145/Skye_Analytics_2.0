from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from app.database import get_db
from app.models.seasonal_performance import (
    SeasonalPerformanceResponse,
    SeasonalConsistencyResponse,
    SeasonalTrendResponse,
    FirstLastMatchResponse,
    SeasonListResponse
)

router = APIRouter(
    prefix="/api/seasonal-performance",
    tags=["Seasonal Performance"],
    responses={404: {"description": "Not found"}},
)

def get_match_data(db: Session):
    """
    Fetch match data from the database for seasonal analysis
    """
    query = """
    SELECT 
        m.*,
        t1.name as team1_name,
        t2.name as team2_name,
        CASE WHEN m.winner_id = m.team1_id THEN t1.name 
             WHEN m.winner_id = m.team2_id THEN t2.name
             ELSE NULL END as winner_name
    FROM ipl_matches m
    LEFT JOIN ipl_teams t1 ON m.team1_id = t1.id
    LEFT JOIN ipl_teams t2 ON m.team2_id = t2.id
    ORDER BY m.match_date
    """
    
    try:
        data = pd.read_sql(query, db.connection())
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching match data: {str(e)}")

def get_seasons_list(db: Session):
    """
    Get list of all IPL seasons
    """
    try:
        query = """
        SELECT 
            DISTINCT EXTRACT(YEAR FROM match_date) as season
        FROM 
            ipl_matches
        ORDER BY 
            season
        """
        seasons = pd.read_sql(query, db.connection())
        return seasons['season'].astype(int).tolist()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching seasons: {str(e)}")

def get_teams_list(db: Session):
    """
    Get list of all IPL teams
    """
    try:
        query = """
        SELECT id, name, short_name
        FROM ipl_teams
        ORDER BY name
        """
        teams = pd.read_sql(query, db.connection())
        return teams.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching teams: {str(e)}")

def calculate_seasonal_performance(matches_df, team_name=None):
    """
    Calculate team performance for each season
    """
    # Filter by team if specified
    if team_name:
        team_matches = matches_df[
            (matches_df['team1_name'] == team_name) | 
            (matches_df['team2_name'] == team_name)
        ].copy()
    else:
        team_matches = matches_df.copy()
    
    # Extract year from match_date
    team_matches['season'] = pd.DatetimeIndex(team_matches['match_date']).year
    
    # Initialize results
    results = []
    
    # Get unique teams
    if team_name:
        teams = [team_name]
    else:
        teams = list(set(team_matches['team1_name'].tolist() + team_matches['team2_name'].tolist()))
    
    # Calculate seasonal performance for each team
    for team in teams:
        # Get matches where team participated
        team_data = team_matches[
            (team_matches['team1_name'] == team) | 
            (team_matches['team2_name'] == team)
        ].copy()
        
        # Group by season
        seasonal_data = []
        for season, season_matches in team_data.groupby('season'):
            # Calculate wins
            wins = season_matches[season_matches['winner_name'] == team].shape[0]
            
            # Calculate total matches
            total_matches = season_matches.shape[0]
            
            # Win percentage
            win_percentage = (wins / total_matches * 100) if total_matches > 0 else 0
            
            # Playoff qualification (simplified logic - assuming top 4 teams qualify)
            # In a real implementation, this would be more complex based on league structure
            playoff_qualification = "Yes" if wins / total_matches >= 0.6 else "No"
            
            seasonal_data.append({
                "season": int(season),
                "matches_played": total_matches,
                "wins": wins,
                "losses": total_matches - wins,
                "win_percentage": round(win_percentage, 2),
                "playoff_qualification": playoff_qualification
            })
        
        if seasonal_data:
            results.append({
                "team": team,
                "seasonal_data": sorted(seasonal_data, key=lambda x: x["season"])
            })
    
    return results

def analyze_consistency(seasonal_data):
    """
    Analyze consistency in team performance across seasons
    """
    consistency_metrics = []
    
    for team_data in seasonal_data:
        team = team_data["team"]
        seasons = team_data["seasonal_data"]
        
        if len(seasons) <= 1:
            continue
            
        # Calculate consistency metrics
        win_percentages = [season["win_percentage"] for season in seasons]
        
        consistency_metrics.append({
            "team": team,
            "seasons_participated": len(seasons),
            "avg_win_percentage": round(np.mean(win_percentages), 2),
            "max_win_percentage": round(max(win_percentages), 2),
            "min_win_percentage": round(min(win_percentages), 2),
            "std_dev_win_percentage": round(np.std(win_percentages), 2),
            "cv_win_percentage": round(np.std(win_percentages) / np.mean(win_percentages) * 100, 2) if np.mean(win_percentages) > 0 else 0,
            "most_consistent_season": seasons[np.argmin(np.abs(np.array(win_percentages) - np.mean(win_percentages)))]["season"],
            "seasons_above_50_percent": sum(1 for wp in win_percentages if wp >= 50)
        })
    
    # Sort by consistency (lower coefficient of variation means more consistent)
    consistency_metrics.sort(key=lambda x: x["cv_win_percentage"])
    
    return consistency_metrics

def analyze_trends(seasonal_data):
    """
    Analyze improvement or decline trends in team performance
    """
    trend_metrics = []
    
    for team_data in seasonal_data:
        team = team_data["team"]
        seasons = team_data["seasonal_data"]
        
        if len(seasons) <= 2:
            continue
            
        # Sort by season
        seasons.sort(key=lambda x: x["season"])
        
        # Calculate trend metrics
        win_percentages = [season["win_percentage"] for season in seasons]
        seasons_list = [season["season"] for season in seasons]
        
        # Linear regression to find trend
        x = np.array(range(len(seasons_list)))
        y = np.array(win_percentages)
        
        # Calculate slope using numpy polyfit
        slope, intercept = np.polyfit(x, y, 1)
        
        # Calculate trend direction and strength
        trend_direction = "Improving" if slope > 0 else "Declining"
        trend_strength = abs(slope)
        
        # Calculate recent trend (last 3 seasons or all if less than 3)
        recent_seasons = min(3, len(seasons))
        recent_win_percentages = win_percentages[-recent_seasons:]
        recent_slope, recent_intercept = np.polyfit(range(recent_seasons), recent_win_percentages, 1)
        recent_trend = "Improving" if recent_slope > 0 else "Declining"
        
        # Best and worst seasons
        best_season = seasons[np.argmax(win_percentages)]["season"]
        worst_season = seasons[np.argmin(win_percentages)]["season"]
        
        trend_metrics.append({
            "team": team,
            "overall_trend": trend_direction,
            "trend_strength": round(trend_strength, 2),
            "recent_trend": recent_trend,
            "best_season": best_season,
            "worst_season": worst_season,
            "first_season": seasons[0]["season"],
            "last_season": seasons[-1]["season"],
            "first_to_last_change": round(win_percentages[-1] - win_percentages[0], 2)
        })
    
    # Sort by trend strength
    trend_metrics.sort(key=lambda x: x["trend_strength"], reverse=True)
    
    return trend_metrics

def analyze_first_last_matches(matches_df, team_name=None):
    """
    Analyze first and last match performance for each season
    """
    # Filter by team if specified
    if team_name:
        team_matches = matches_df[
            (matches_df['team1_name'] == team_name) | 
            (matches_df['team2_name'] == team_name)
        ].copy()
    else:
        team_matches = matches_df.copy()
    
    # Extract year from match_date
    team_matches['season'] = pd.DatetimeIndex(team_matches['match_date']).year
    
    # Initialize results
    results = []
    
    # Get unique teams
    if team_name:
        teams = [team_name]
    else:
        teams = list(set(team_matches['team1_name'].tolist() + team_matches['team2_name'].tolist()))
    
    for team in teams:
        # Get matches where team participated
        team_data = team_matches[
            (team_matches['team1_name'] == team) | 
            (team_matches['team2_name'] == team)
        ].copy()
        
        # Sort by date
        team_data = team_data.sort_values('match_date')
        
        # Group by season
        first_last_data = []
        for season, season_matches in team_data.groupby('season'):
            # Get first and last match of the season
            first_match = season_matches.iloc[0]
            last_match = season_matches.iloc[-1]
            
            # Determine if team won first match
            first_match_result = "Won" if first_match['winner_name'] == team else "Lost"
            if first_match['winner_name'] is None:
                first_match_result = "No Result"
                
            # Determine if team won last match
            last_match_result = "Won" if last_match['winner_name'] == team else "Lost"
            if last_match['winner_name'] is None:
                last_match_result = "No Result"
            
            # Determine opponent in first match
            first_match_opponent = first_match['team2_name'] if first_match['team1_name'] == team else first_match['team1_name']
            
            # Determine opponent in last match
            last_match_opponent = last_match['team2_name'] if last_match['team1_name'] == team else last_match['team1_name']
            
            first_last_data.append({
                "season": int(season),
                "first_match": {
                    "date": first_match['match_date'].strftime("%Y-%m-%d"),
                    "opponent": first_match_opponent,
                    "venue": first_match['venue'],
                    "result": first_match_result
                },
                "last_match": {
                    "date": last_match['match_date'].strftime("%Y-%m-%d"),
                    "opponent": last_match_opponent,
                    "venue": last_match['venue'],
                    "result": last_match_result
                },
                "first_match_win": first_match_result == "Won",
                "last_match_win": last_match_result == "Won"
            })
        
        if first_last_data:
            # Calculate some statistics
            first_match_wins = sum(1 for m in first_last_data if m["first_match_win"])
            last_match_wins = sum(1 for m in first_last_data if m["last_match_win"])
            
            results.append({
                "team": team,
                "first_last_data": sorted(first_last_data, key=lambda x: x["season"]),
                "first_match_win_percentage": round((first_match_wins / len(first_last_data) * 100), 2),
                "last_match_win_percentage": round((last_match_wins / len(first_last_data) * 100), 2)
            })
    
    return results

@router.get("/seasons", response_model=SeasonListResponse)
def get_seasons(db: Session = Depends(get_db)):
    """
    Get list of all IPL seasons for filtering
    """
    seasons = get_seasons_list(db)
    return {"seasons": seasons}

@router.get("/teams", response_model=List[Dict[str, Any]])
def get_teams(db: Session = Depends(get_db)):
    """
    Get list of all IPL teams for filtering
    """
    teams = get_teams_list(db)
    return teams

@router.get("/performance", response_model=SeasonalPerformanceResponse)
def get_seasonal_performance(
    team: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get team performance across different IPL seasons
    """
    matches_df = get_match_data(db)
    seasonal_data = calculate_seasonal_performance(matches_df, team)
    
    return {
        "season_count": len(set(matches_df['season'])),
        "teams": [data["team"] for data in seasonal_data],
        "seasonal_performance": seasonal_data
    }

@router.get("/consistency", response_model=SeasonalConsistencyResponse)
def get_consistency_analysis(
    team: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Analyze consistency in team performance across seasons
    """
    matches_df = get_match_data(db)
    seasonal_data = calculate_seasonal_performance(matches_df, team)
    consistency_metrics = analyze_consistency(seasonal_data)
    
    return {
        "metrics_description": {
            "cv_win_percentage": "Coefficient of variation of win percentage (lower means more consistent)",
            "std_dev_win_percentage": "Standard deviation of win percentage across seasons",
            "seasons_above_50_percent": "Number of seasons with win percentage above 50%"
        },
        "consistency_metrics": consistency_metrics
    }

@router.get("/trends", response_model=SeasonalTrendResponse)
def get_trend_analysis(
    team: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Analyze improvement or decline trends in team performance
    """
    matches_df = get_match_data(db)
    seasonal_data = calculate_seasonal_performance(matches_df, team)
    trend_metrics = analyze_trends(seasonal_data)
    
    return {
        "metrics_description": {
            "overall_trend": "Overall trend direction (Improving or Declining)",
            "trend_strength": "Strength of the trend (higher means stronger trend)",
            "recent_trend": "Trend direction in the last 3 seasons",
            "first_to_last_change": "Change in win percentage from first to last season"
        },
        "trend_metrics": trend_metrics
    }

@router.get("/first-last-matches", response_model=FirstLastMatchResponse)
def get_first_last_match_analysis(
    team: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Analyze first and last match performance for each season
    """
    matches_df = get_match_data(db)
    first_last_data = analyze_first_last_matches(matches_df, team)
    
    return {
        "first_last_match_data": first_last_data
    }