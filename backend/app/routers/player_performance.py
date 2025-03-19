from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

# Import database connection
from app.database import get_db
# Import models
from app.models.player_performance import (
    PlayerPerformanceResponse, PlayerBasicInfo, BattingPerformanceSummary,
    BowlingPerformanceSummary, InningsHighlight, BowlingHighlight,
    TeamwisePerformance, SeasonalPerformance, VenuePerformance, MatchSituationPerformance
)

router = APIRouter(
    prefix="/api/player-performance",
    tags=["Player Performance"]
)

# Helper functions
def calculate_strike_rate(runs, balls):
    if balls == 0:
        return 0.0
    return round((runs / balls) * 100, 2)

def calculate_economy_rate(runs, overs):
    if overs == 0:
        return 0.0
    return round(runs / overs, 2)

def calculate_bowling_strike_rate(balls, wickets):
    if wickets == 0:
        return 0.0
    return round(balls / wickets, 2)

def calculate_batting_average(runs, innings, not_outs):
    if (innings - not_outs) == 0:
        return 0.0
    return round(runs / (innings - not_outs), 2)

def calculate_bowling_average(runs, wickets):
    if wickets == 0:
        return 0.0
    return round(runs / wickets, 2)

def convert_overs_to_balls(overs):
    """Convert overs to balls (e.g., 4.3 overs = 4*6 + 3 = 27 balls)"""
    if pd.isna(overs):
        return 0
    
    whole_overs = int(overs)
    partial_overs = overs - whole_overs
    return whole_overs * 6 + int(partial_overs * 10)  # Convert decimal to balls

def get_player_batting_data(player_name: str, db: Session):
    """Get batting data for a specific player"""
    # Using innings_data table which has ball-by-ball data
    query = """
    SELECT 
        i.filename, i.innings_type, i.team, i.over_ball, i.batsman, 
        i.bowler, i.non_striker, i.runs_batsman, i.runs_total, 
        i.extras_type, i.extras_runs, i.wicket_details,
        m.match_date, m.venue, m.team1, m.team2, m.winner, m.season
    FROM 
        innings_data i
    JOIN 
        match_info m ON i.filename = m.filename
    WHERE 
        i.batsman = :player_name
    ORDER BY 
        m.match_date, i.over_ball
    """
    params = {"player_name": player_name}
    
    return pd.read_sql(query, db.bind, params=params)

def get_player_bowling_data(player_name: str, db: Session):
    """Get bowling data for a specific player"""
    # Using innings_data table which has ball-by-ball data
    query = """
    SELECT 
        i.filename, i.innings_type, i.team, i.over_ball, i.batsman, 
        i.bowler, i.non_striker, i.runs_batsman, i.runs_total, 
        i.extras_type, i.extras_runs, i.wicket_details,
        m.match_date, m.venue, m.team1, m.team2, m.winner, m.season
    FROM 
        innings_data i
    JOIN 
        match_info m ON i.filename = m.filename
    WHERE 
        i.bowler = :player_name
    ORDER BY 
        m.match_date, i.over_ball
    """
    params = {"player_name": player_name}
    
    return pd.read_sql(query, db.bind, params=params)

def get_player_info(player_name: str, db: Session):
    """Get basic player information"""
    # Try to get from ipl_players table
    query = """
    SELECT 
        name, country, playing_role, batting_style, bowling_style
    FROM 
        ipl_players
    WHERE 
        name = :player_name
    LIMIT 1
    """
    params = {"player_name": player_name}
    
    result = pd.read_sql(query, db.bind, params=params)
    
    if not result.empty:
        return {
            "player_name": player_name,
            "country": result['country'].iloc[0] if 'country' in result.columns else None,
            "playing_role": result['playing_role'].iloc[0] if 'playing_role' in result.columns else None,
            "batting_style": result['batting_style'].iloc[0] if 'batting_style' in result.columns else None,
            "bowling_style": result['bowling_style'].iloc[0] if 'bowling_style' in result.columns else None
        }
    
    # If not found, return basic info
    return {
        "player_name": player_name,
        "country": None,
        "playing_role": None,
        "batting_style": None,
        "bowling_style": None
    }

def get_player_list(db: Session):
    """Get list of all player names"""
    # Try different tables to get player names
    
    # First try ipl_players table
    query1 = """
    SELECT DISTINCT name
    FROM ipl_players
    ORDER BY name
    """
    
    result1 = pd.read_sql(query1, db.bind)
    
    if not result1.empty:
        return result1['name'].tolist()
    
    # If no results, try innings_data table
    query2 = """
    SELECT DISTINCT batsman as player_name
    FROM innings_data
    ORDER BY batsman
    """
    
    result2 = pd.read_sql(query2, db.bind)
    
    if not result2.empty:
        return result2['player_name'].tolist()
    
    # If still no results, try player view
    query3 = """
    SELECT DISTINCT player_name
    FROM vw_player_batting_performance
    ORDER BY player_name
    """
    
    result3 = pd.read_sql(query3, db.bind)
    
    if not result3.empty:
        return result3['player_name'].tolist()
    
    return []

@router.get("/players", response_model=List[str])
def get_all_players(db: Session = Depends(get_db)):
    """Get list of all players"""
    return get_player_list(db)

@router.get("/{player_name}", response_model=PlayerPerformanceResponse)
def get_player_performance(
    player_name: str, 
    include_batting: bool = True,
    include_bowling: bool = True,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get comprehensive performance data for a player"""
    # Get player basic info
    player_info = get_player_info(player_name, db)
    
    response = {
        "player_info": player_info,
        "batting_summary": None,
        "bowling_summary": None,
        "highest_scores": None,
        "best_bowling": None,
        "against_teams": None,
        "by_season": None,
        "by_venue": None,
        "by_match_situation": None
    }
    
    # Get batting data if requested
    if include_batting:
        batting_data = get_player_batting_data(player_name, db)
        
        # Filter by season if specified
        if season and not batting_data.empty:
            batting_data = batting_data[batting_data['season'] == season]
        
        if not batting_data.empty:
            # Process batting data
            batting_summary = process_batting_data(batting_data, player_name)
            response["batting_summary"] = batting_summary
            
            # Get highest scores
            response["highest_scores"] = get_highest_scores(batting_data, player_name)
            
            # Get performance against different teams
            response["against_teams"] = get_batting_against_teams(batting_data, player_name)
            
            # Get seasonal performance
            response["by_season"] = get_batting_by_season(batting_data, player_name)
            
            # Get venue performance
            response["by_venue"] = get_batting_by_venue(batting_data, player_name)
            
            # Get match situation performance
            response["by_match_situation"] = get_batting_match_situations(batting_data, player_name)
    
    # Get bowling data if requested
    if include_bowling:
        bowling_data = get_player_bowling_data(player_name, db)
        
        # Filter by season if specified
        if season and not bowling_data.empty:
            bowling_data = bowling_data[bowling_data['season'] == season]
        
        if not bowling_data.empty:
            # Process bowling data
            bowling_summary = process_bowling_data(bowling_data, player_name)
            response["bowling_summary"] = bowling_summary
            
            # Get best bowling performances
            response["best_bowling"] = get_best_bowling(bowling_data, player_name)
            
            # Update against teams with bowling stats
            teams_performance = response["against_teams"] or []
            bowling_against_teams = get_bowling_against_teams(bowling_data, player_name)
            
            # Merge bowling stats with existing batting stats against teams
            response["against_teams"] = merge_team_performances(teams_performance, bowling_against_teams)
            
            # Update seasonal performance with bowling stats
            seasons_performance = response["by_season"] or []
            bowling_by_season = get_bowling_by_season(bowling_data, player_name)
            
            # Merge bowling stats with existing batting stats by season
            response["by_season"] = merge_seasonal_performances(seasons_performance, bowling_by_season)
            
            # Update venue performance with bowling stats
            venues_performance = response["by_venue"] or []
            bowling_by_venue = get_bowling_by_venue(bowling_data, player_name)
            
            # Merge bowling stats with existing batting stats by venue
            response["by_venue"] = merge_venue_performances(venues_performance, bowling_by_venue)
            
            # Update match situation performance with bowling stats
            situations_performance = response["by_match_situation"] or []
            bowling_match_situations = get_bowling_match_situations(bowling_data, player_name)
            
            # Merge bowling stats with existing batting stats by match situation
            response["by_match_situation"] = merge_situation_performances(situations_performance, bowling_match_situations)
    
    # If no data found at all
    if (include_batting and include_bowling and 
        response["batting_summary"] is None and response["bowling_summary"] is None):
        raise HTTPException(status_code=404, detail=f"No performance data found for player: {player_name}")
    
    return response

@router.get("/{player_name}/batting", response_model=BattingPerformanceSummary)
def get_player_batting_summary(
    player_name: str, 
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get batting summary for a player"""
    batting_data = get_player_batting_data(player_name, db)
    
    # Filter by season if specified
    if season and not batting_data.empty:
        batting_data = batting_data[batting_data['season'] == season]
    
    if batting_data.empty:
        raise HTTPException(status_code=404, detail=f"No batting data found for player: {player_name}")
    
    return process_batting_data(batting_data, player_name)

@router.get("/{player_name}/bowling", response_model=BowlingPerformanceSummary)
def get_player_bowling_summary(
    player_name: str, 
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get bowling summary for a player"""
    bowling_data = get_player_bowling_data(player_name, db)
    
    # Filter by season if specified
    if season and not bowling_data.empty:
        bowling_data = bowling_data[bowling_data['season'] == season]
    
    if bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No bowling data found for player: {player_name}")
    
    return process_bowling_data(bowling_data, player_name)

@router.get("/{player_name}/highest-scores", response_model=List[InningsHighlight])
def get_player_highest_scores(
    player_name: str, 
    limit: int = 5,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get highest scores for a player"""
    batting_data = get_player_batting_data(player_name, db)
    
    # Filter by season if specified
    if season and not batting_data.empty:
        batting_data = batting_data[batting_data['season'] == season]
    
    if batting_data.empty:
        raise HTTPException(status_code=404, detail=f"No batting data found for player: {player_name}")
    
    return get_highest_scores(batting_data, player_name, limit)

@router.get("/{player_name}/best-bowling", response_model=List[BowlingHighlight])
def get_player_best_bowling(
    player_name: str, 
    limit: int = 5,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get best bowling performances for a player"""
    bowling_data = get_player_bowling_data(player_name, db)
    
    # Filter by season if specified
    if season and not bowling_data.empty:
        bowling_data = bowling_data[bowling_data['season'] == season]
    
    if bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No bowling data found for player: {player_name}")
    
    return get_best_bowling(bowling_data, player_name, limit)

@router.get("/{player_name}/against-teams", response_model=List[TeamwisePerformance])
def get_player_against_teams(
    player_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get player performance against different teams"""
    # Get batting data
    batting_data = get_player_batting_data(player_name, db)
    
    # Filter by season if specified
    if season and not batting_data.empty:
        batting_data = batting_data[batting_data['season'] == season]
    
    # Get bowling data
    bowling_data = get_player_bowling_data(player_name, db)
    
    # Filter by season if specified
    if season and not bowling_data.empty:
        bowling_data = bowling_data[bowling_data['season'] == season]
    
    if batting_data.empty and bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No performance data found for player: {player_name}")
    
    batting_against_teams = [] if batting_data.empty else get_batting_against_teams(batting_data, player_name)
    bowling_against_teams = [] if bowling_data.empty else get_bowling_against_teams(bowling_data, player_name)
    
    return merge_team_performances(batting_against_teams, bowling_against_teams)

@router.get("/{player_name}/by-season", response_model=List[SeasonalPerformance])
def get_player_by_season(
    player_name: str,
    db: Session = Depends(get_db)
):
    """Get player performance across seasons"""
    # Get batting data
    batting_data = get_player_batting_data(player_name, db)
    
    # Get bowling data
    bowling_data = get_player_bowling_data(player_name, db)
    
    if batting_data.empty and bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No performance data found for player: {player_name}")
    
    batting_by_season = [] if batting_data.empty else get_batting_by_season(batting_data, player_name)
    bowling_by_season = [] if bowling_data.empty else get_bowling_by_season(bowling_data, player_name)
    
    return merge_seasonal_performances(batting_by_season, bowling_by_season)

@router.get("/{player_name}/by-venue", response_model=List[VenuePerformance])
def get_player_by_venue(
    player_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get player performance across venues"""
    # Get batting data
    batting_data = get_player_batting_data(player_name, db)
    
    # Filter by season if specified
    if season and not batting_data.empty:
        batting_data = batting_data[batting_data['season'] == season]
    
    # Get bowling data
    bowling_data = get_player_bowling_data(player_name, db)
    
    # Filter by season if specified
    if season and not bowling_data.empty:
        bowling_data = bowling_data[bowling_data['season'] == season]
    
    if batting_data.empty and bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No performance data found for player: {player_name}")
    
    batting_by_venue = [] if batting_data.empty else get_batting_by_venue(batting_data, player_name)
    bowling_by_venue = [] if bowling_data.empty else get_bowling_by_venue(bowling_data, player_name)
    
    return merge_venue_performances(batting_by_venue, bowling_by_venue)

@router.get("/{player_name}/match-situations", response_model=List[MatchSituationPerformance])
def get_player_match_situations(
    player_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get player performance in different match situations"""
    # Get batting data
    batting_data = get_player_batting_data(player_name, db)
    
    # Filter by season if specified
    if season and not batting_data.empty:
        batting_data = batting_data[batting_data['season'] == season]
    
    # Get bowling data
    bowling_data = get_player_bowling_data(player_name, db)
    
    # Filter by season if specified
    if season and not bowling_data.empty:
        bowling_data = bowling_data[bowling_data['season'] == season]
    
    if batting_data.empty and bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No performance data found for player: {player_name}")
    
    batting_situations = [] if batting_data.empty else get_batting_match_situations(batting_data, player_name)
    bowling_situations = [] if bowling_data.empty else get_bowling_match_situations(bowling_data, player_name)
    
    return merge_situation_performances(batting_situations, bowling_situations)

# Helper functions for data processing

def process_batting_data(batting_data, player_name):
    """Process batting data and return summary"""
    # Group by match to get innings information
    innings_grouped = batting_data.groupby('filename')
    
    # Calculate innings-level stats
    innings_stats = []
    matches_played = len(innings_grouped)
    total_runs = 0
    total_balls = 0
    not_outs = 0
    centuries = 0
    half_centuries = 0
    highest_score = 0
    total_fours = 0
    total_sixes = 0
    
    for match_id, innings in innings_grouped:
        # Calculate runs scored in this innings
        runs = innings['runs_batsman'].sum()
        balls = len(innings)
        
        # Check if not out (no wicket_details for the batsman in this innings)
        is_not_out = True
        for _, ball in innings.iterrows():
            if not pd.isna(ball['wicket_details']) and player_name in str(ball['wicket_details']):
                is_not_out = False
                break
        
        if is_not_out:
            not_outs += 1
        
        # Count boundaries
        fours = len(innings[innings['runs_batsman'] == 4])
        sixes = len(innings[innings['runs_batsman'] == 6])
        
        # Update totals
        total_runs += runs
        total_balls += balls
        total_fours += fours
        total_sixes += sixes
        
        # Update highest score
        highest_score = max(highest_score, runs)
        
        # Check for century/half-century
        if runs >= 100:
            centuries += 1
        elif runs >= 50:
            half_centuries += 1
    
    # Calculate averages and rates
    batting_average = calculate_batting_average(total_runs, matches_played, not_outs)
    strike_rate = calculate_strike_rate(total_runs, total_balls)
    
    return {
        "matches_played": matches_played,
        "innings_batted": matches_played,  # Assuming 1 innings per match
        "runs_scored": total_runs,
        "balls_faced": total_balls,
        "highest_score": highest_score,
        "average": batting_average,
        "strike_rate": strike_rate,
        "centuries": centuries,
        "half_centuries": half_centuries,
        "fours": total_fours,
        "sixes": total_sixes,
        "not_outs": not_outs
    }

def process_bowling_data(bowling_data, player_name):
    """Process bowling data and return summary"""
    # Group by match to get innings information
    innings_grouped = bowling_data.groupby('filename')
    
    # Calculate innings-level stats
    matches_played = len(innings_grouped)
    total_wickets = 0
    total_runs = 0
    best_bowling_wickets = 0
    best_bowling_runs = float('inf')
    best_bowling_match = ""
    four_wickets = 0
    five_wickets = 0
    
    for match_id, innings in innings_grouped:
        # Calculate wickets taken in this innings
        wickets = 0
        for _, ball in innings.iterrows():
            if not pd.isna(ball['wicket_details']):
                wickets += 1
        
        # Calculate runs conceded
        runs = innings['runs_total'].sum()
        
        # Calculate overs bowled (assuming 6 balls per over)
        overs = len(innings) / 6
        
        # Update totals
        total_wickets += wickets
        total_runs += runs
        
        # Check for best bowling performance
        if wickets > best_bowling_wickets or (wickets == best_bowling_wickets and runs < best_bowling_runs):
            best_bowling_wickets = wickets
            best_bowling_runs = runs
            best_bowling_match = match_id
        
        # Check for 4/5 wicket hauls
        if wickets >= 5:
            five_wickets += 1
        elif wickets >= 4:
            four_wickets += 1
    
    # Calculate total overs bowled
    total_balls = len(bowling_data)
    total_overs = total_balls / 6
    
    # Calculate averages and rates
    bowling_average = calculate_bowling_average(total_runs, total_wickets)
    economy_rate = calculate_economy_rate(total_runs, total_overs)
    bowling_strike_rate = calculate_bowling_strike_rate(total_balls, total_wickets)
    
    # Format best bowling figures
    best_bowling = f"{best_bowling_wickets}/{best_bowling_runs}" if best_bowling_wickets > 0 else "0/0"
    
    return {
        "matches_played": matches_played,
        "innings_bowled": matches_played,  # Assuming 1 innings per match
        "overs_bowled": round(total_overs, 1),
        "runs_conceded": total_runs,
        "wickets": total_wickets,
        "best_bowling_figures": best_bowling,
        "average": bowling_average,
        "economy_rate": economy_rate,
        "strike_rate": bowling_strike_rate,
        "four_wickets": four_wickets,
        "five_wickets": five_wickets
    }

def get_highest_scores(batting_data, player_name, limit=5):
    """Get highest scores for a player"""
    if batting_data.empty:
        return []
    
    # Group by match
    match_groups = batting_data.groupby('filename')
    innings_highlights = []
    
    for match_id, innings in match_groups:
        first_ball = innings.iloc[0]
        opponent = first_ball['team2'] if first_ball['team'] == first_ball['team1'] else first_ball['team1']
        
        # Calculate runs and balls
        runs = innings['runs_batsman'].sum()
        balls = len(innings)
        
        # Calculate boundaries
        fours = len(innings[innings['runs_batsman'] == 4])
        sixes = len(innings[innings['runs_batsman'] == 6])
        
        # Check if not out
        is_not_out = True
        for _, ball in innings.iterrows():
            if not pd.isna(ball['wicket_details']) and player_name in str(ball['wicket_details']):
                is_not_out = False
                break
        
        # Calculate strike rate
        strike_rate = calculate_strike_rate(runs, balls)
        
        # Get result
        result = "Win" if first_ball['winner'] == first_ball['team'] else "Loss"
        
        innings_highlights.append({
            "match_id": match_id,
            "date": first_ball['match_date'] if not pd.isna(first_ball['match_date']) else None,
            "opponent": opponent,
            "score": runs,
            "balls_faced": balls,
            "strike_rate": strike_rate,
            "fours": fours,
            "sixes": sixes,
            "not_out": is_not_out,
            "result": result,
            "venue": first_ball['venue'] if not pd.isna(first_ball['venue']) else None,
            "season": int(first_ball['season']) if not pd.isna(first_ball['season']) else None
        })
    
    # Sort by runs scored (descending)
    innings_highlights.sort(key=lambda x: (x["score"], x["strike_rate"]), reverse=True)
    
    # Return top N innings
    return innings_highlights[:limit]

def get_best_bowling(bowling_data, player_name, limit=5):
    """Get best bowling performances for a player"""
    if bowling_data.empty:
        return []
    
    # Group by match
    match_groups = bowling_data.groupby('filename')
    bowling_highlights = []
    
    for match_id, innings in match_groups:
        first_ball = innings.iloc[0]
        opponent = first_ball['team2'] if first_ball['team'] == first_ball['team1'] else first_ball['team1']
        
        # Calculate wickets and runs
        wickets = 0
        for _, ball in innings.iterrows():
            if not pd.isna(ball['wicket_details']):
                wickets += 1
        
        runs = innings['runs_total'].sum()
        
        # Calculate overs bowled
        balls = len(innings)
        overs = balls // 6 + (balls % 6) / 10  # Format as 4.3 for 4 overs and 3 balls
        
        # Calculate economy
        economy = calculate_economy_rate(runs, overs)
        
        # Get result
        result = "Win" if first_ball['winner'] == first_ball['team'] else "Loss"
        
        # Bowling figures
        bowling_figures = f"{wickets}/{runs}"
        
        bowling_highlights.append({
            "match_id": match_id,
            "date": first_ball['match_date'] if not pd.isna(first_ball['match_date']) else None,
            "opponent": opponent,
            "overs": round(overs, 1),
            "wickets": wickets,
            "runs_conceded": runs,
            "economy": economy,
            "bowling_figures": bowling_figures,
            "result": result,
            "venue": first_ball['venue'] if not pd.isna(first_ball['venue']) else None,
            "season": int(first_ball['season']) if not pd.isna(first_ball['season']) else None
        })
    
    # Sort by wickets (descending) and then by runs (ascending)
    bowling_highlights.sort(key=lambda x: (-x["wickets"], x["runs_conceded"]))
    
    # Return top N performances
    return bowling_highlights[:limit]

def get_batting_against_teams(batting_data, player_name):
    """Analyze batting performance against different teams"""
    if batting_data.empty:
        return []
    
    # Find which teams the player played for
    player_teams = batting_data['team'].unique()
    
    # Determine opponents
    teamwise_performance = []
    
    for team in player_teams:
        # Filter matches where player played for this team
        team_matches = batting_data[batting_data['team'] == team]
        
        # Get unique opponents
        opponent_teams = []
        
        for _, row in team_matches.iterrows():
            opponent = row['team2'] if row['team'] == row['team1'] else row['team1']
            if opponent not in opponent_teams:
                opponent_teams.append(opponent)
        
        # Analyze performance against each opponent
        for opponent in opponent_teams:
            match_ids = []
            total_runs = 0
            total_balls = 0
            highest_score = 0
            
            for match_id, innings in team_matches.groupby('filename'):
                first_ball = innings.iloc[0]
                match_opponent = first_ball['team2'] if first_ball['team'] == first_ball['team1'] else first_ball['team1']
                
                if match_opponent == opponent:
                    match_ids.append(match_id)
                    runs = innings['runs_batsman'].sum()
                    balls = len(innings)
                    
                    total_runs += runs
                    total_balls += balls
                    highest_score = max(highest_score, runs)
            
            matches_played = len(match_ids)
            
            if matches_played > 0:
                # Calculate averages and rates
                average = round(total_runs / matches_played, 2)
                strike_rate = calculate_strike_rate(total_runs, total_balls)
                
                teamwise_performance.append({
                    "team": opponent,
                    "matches": matches_played,
                    "innings": matches_played,
                    "runs": total_runs,
                    "average": average,
                    "strike_rate": strike_rate,
                    "best_score": highest_score
                })
    
    # Sort by runs scored (descending)
    teamwise_performance.sort(key=lambda x: x["runs"], reverse=True)
    
    return teamwise_performance

def get_bowling_against_teams(bowling_data, player_name):
    """Analyze bowling performance against different teams"""
    if bowling_data.empty:
        return []
    
    # Find which teams the player played for
    player_teams = bowling_data['team'].unique()
    
    # Determine opponents
    teamwise_performance = []
    
    for team in player_teams:
        # Filter matches where player played for this team
        team_matches = bowling_data[bowling_data['team'] == team]
        
        # Get unique opponents
        opponent_teams = []
        
        for _, row in team_matches.iterrows():
            opponent = row['team2'] if row['team'] == row['team1'] else row['team1']
            if opponent not in opponent_teams:
                opponent_teams.append(opponent)
        
        # Analyze performance against each opponent
        for opponent in opponent_teams:
            match_ids = []
            total_wickets = 0
            total_runs = 0
            total_balls = 0
            best_bowling_wickets = 0
            best_bowling_runs = float('inf')
            
            for match_id, innings in team_matches.groupby('filename'):
                first_ball = innings.iloc[0]
                match_opponent = first_ball['team2'] if first_ball['team'] == first_ball['team1'] else first_ball['team1']
                
                if match_opponent == opponent:
                    match_ids.append(match_id)
                    
                    # Calculate wickets taken in this innings
                    wickets = 0
                    for _, ball in innings.iterrows():
                        if not pd.isna(ball['wicket_details']):
                            wickets += 1
                    
                    runs = innings['runs_total'].sum()
                    balls = len(innings)
                    
                    total_wickets += wickets
                    total_runs += runs
                    total_balls += balls
                    
                    # Check for best bowling performance
                    if wickets > best_bowling_wickets or (wickets == best_bowling_wickets and runs < best_bowling_runs):
                        best_bowling_wickets = wickets
                        best_bowling_runs = runs
            
            matches_played = len(match_ids)
            
            if matches_played > 0:
                # Calculate averages and rates
                total_overs = total_balls / 6
                economy = calculate_economy_rate(total_runs, total_overs)
                bowling_strike_rate = calculate_bowling_strike_rate(total_balls, total_wickets)
                
                # Format best bowling figures
                best_bowling = f"{best_bowling_wickets}/{best_bowling_runs}" if best_bowling_wickets > 0 else "0/0"
                
                teamwise_performance.append({
                    "team": opponent,
                    "matches": matches_played,
                    "innings": matches_played,
                    "wickets": total_wickets,
                    "economy": economy,
                    "bowling_strike_rate": bowling_strike_rate,
                    "best_bowling": best_bowling
                })
    
    # Sort by wickets taken (descending)
    teamwise_performance.sort(key=lambda x: x["wickets"], reverse=True)
    
    return teamwise_performance

def get_batting_by_season(batting_data, player_name):
    """Analyze batting performance by season"""
    if batting_data.empty:
        return []
    
    # Group by season
    seasonal_performance = []
    
    for season, season_data in batting_data.groupby('season'):
        if pd.isna(season):
            continue
            
        total_runs = 0
        total_balls = 0
        match_ids = []
        
        for match_id, innings in season_data.groupby('filename'):
            runs = innings['runs_batsman'].sum()
            balls = len(innings)
            
            total_runs += runs
            total_balls += balls
            
            if match_id not in match_ids:
                match_ids.append(match_id)
        
        matches_played = len(match_ids)
        
        if matches_played > 0:
            # Calculate averages and rates
            average = round(total_runs / matches_played, 2)
            strike_rate = calculate_strike_rate(total_runs, total_balls)
            
            seasonal_performance.append({
                "season": int(season),
                "matches": matches_played,
                "runs": total_runs,
                "average": average,
                "strike_rate": strike_rate
            })
    
    # Sort by season (ascending)
    seasonal_performance.sort(key=lambda x: x["season"])
    
    return seasonal_performance

def get_bowling_by_season(bowling_data, player_name):
    """Analyze bowling performance by season"""
    if bowling_data.empty:
        return []
    
    # Group by season
    seasonal_performance = []
    
    for season, season_data in bowling_data.groupby('season'):
        if pd.isna(season):
            continue
            
        total_wickets = 0
        total_runs = 0
        total_balls = 0
        match_ids = []
        
        for match_id, innings in season_data.groupby('filename'):
            # Calculate wickets taken in this innings
            wickets = 0
            for _, ball in innings.iterrows():
                if not pd.isna(ball['wicket_details']):
                    wickets += 1
            
            runs = innings['runs_total'].sum()
            balls = len(innings)
            
            total_wickets += wickets
            total_runs += runs
            total_balls += balls
            
            if match_id not in match_ids:
                match_ids.append(match_id)
        
        matches_played = len(match_ids)
        
        if matches_played > 0:
            # Calculate averages and rates
            total_overs = total_balls / 6
            economy = calculate_economy_rate(total_runs, total_overs)
            bowling_strike_rate = calculate_bowling_strike_rate(total_balls, total_wickets)
            
            seasonal_performance.append({
                "season": int(season),
                "matches": matches_played,
                "wickets": total_wickets,
                "economy": economy,
                "bowling_strike_rate": bowling_strike_rate
            })
    
    # Sort by season (ascending)
    seasonal_performance.sort(key=lambda x: x["season"])
    
    return seasonal_performance

def get_batting_by_venue(batting_data, player_name):
    """Analyze batting performance by venue"""
    if batting_data.empty:
        return []
    
    # Group by venue
    venue_performance = []
    
    for venue, venue_data in batting_data.groupby('venue'):
        if pd.isna(venue):
            continue
            
        total_runs = 0
        total_balls = 0
        match_ids = []
        
        for match_id, innings in venue_data.groupby('filename'):
            runs = innings['runs_batsman'].sum()
            balls = len(innings)
            
            total_runs += runs
            total_balls += balls
            
            if match_id not in match_ids:
                match_ids.append(match_id)
        
        matches_played = len(match_ids)
        
        if matches_played > 0:
            # Calculate averages and rates
            average = round(total_runs / matches_played, 2)
            strike_rate = calculate_strike_rate(total_runs, total_balls)
            
            venue_performance.append({
                "venue": venue,
                "matches": matches_played,
                "innings": matches_played,
                "runs": total_runs,
                "average": average,
                "strike_rate": strike_rate
            })
    
    # Sort by matches played (descending)
    venue_performance.sort(key=lambda x: x["matches"], reverse=True)
    
    return venue_performance

def get_bowling_by_venue(bowling_data, player_name):
    """Analyze bowling performance by venue"""
    if bowling_data.empty:
        return []
    
    # Group by venue
    venue_performance = []
    
    for venue, venue_data in bowling_data.groupby('venue'):
        if pd.isna(venue):
            continue
            
        total_wickets = 0
        total_runs = 0
        total_balls = 0
        match_ids = []
        
        for match_id, innings in venue_data.groupby('filename'):
            # Calculate wickets taken in this innings
            wickets = 0
            for _, ball in innings.iterrows():
                if not pd.isna(ball['wicket_details']):
                    wickets += 1
            
            runs = innings['runs_total'].sum()
            balls = len(innings)
            
            total_wickets += wickets
            total_runs += runs
            total_balls += balls
            
            if match_id not in match_ids:
                match_ids.append(match_id)
        
        matches_played = len(match_ids)
        
        if matches_played > 0:
            # Calculate averages and rates
            total_overs = total_balls / 6
            economy = calculate_economy_rate(total_runs, total_overs)
            bowling_strike_rate = calculate_bowling_strike_rate(total_balls, total_wickets)
            
            venue_performance.append({
                "venue": venue,
                "matches": matches_played,
                "innings": matches_played,
                "wickets": total_wickets,
                "economy": economy,
                "bowling_strike_rate": bowling_strike_rate
            })
    
    # Sort by matches played (descending)
    venue_performance.sort(key=lambda x: x["matches"], reverse=True)
    
    return venue_performance

def get_batting_match_situations(batting_data, player_name):
    """Analyze batting performance in different match situations"""
    if batting_data.empty:
        return []
    
    # Define match situations
    situations = [
        {"name": "PowerPlay (1-6)", "min_over": 0, "max_over": 6},
        {"name": "Middle Overs (7-15)", "min_over": 6, "max_over": 15},
        {"name": "Death Overs (16-20)", "min_over": 15, "max_over": 20}
    ]
    
    situation_performance = []
    
    for situation in situations:
        # Filter data for this situation
        situation_data = batting_data[
            (batting_data['over_ball'] >= situation["min_over"]) & 
            (batting_data['over_ball'] < situation["max_over"])
        ]
        
        if situation_data.empty:
            continue
        
        total_runs = situation_data['runs_batsman'].sum()
        total_balls = len(situation_data)
        
        # Calculate averages and rates
        strike_rate = calculate_strike_rate(total_runs, total_balls)
        
        situation_performance.append({
            "situation": situation["name"],
            "innings": len(situation_data.groupby('filename')),
            "runs": total_runs,
            "strike_rate": strike_rate
        })
    
    return situation_performance

def get_bowling_match_situations(bowling_data, player_name):
    """Analyze bowling performance in different match situations"""
    if bowling_data.empty:
        return []
    
    # Define match situations
    situations = [
        {"name": "PowerPlay (1-6)", "min_over": 0, "max_over": 6},
        {"name": "Middle Overs (7-15)", "min_over": 6, "max_over": 15},
        {"name": "Death Overs (16-20)", "min_over": 15, "max_over": 20}
    ]
    
    situation_performance = []
    
    for situation in situations:
        # Filter data for this situation
        situation_data = bowling_data[
            (bowling_data['over_ball'] >= situation["min_over"]) & 
            (bowling_data['over_ball'] < situation["max_over"])
        ]
        
        if situation_data.empty:
            continue
        
        total_runs = situation_data['runs_total'].sum()
        total_balls = len(situation_data)
        total_overs = total_balls / 6
        
        # Calculate wickets
        total_wickets = 0
        for _, ball in situation_data.iterrows():
            if not pd.isna(ball['wicket_details']):
                total_wickets += 1
        
        # Calculate economy and strike rate
        economy = calculate_economy_rate(total_runs, total_overs)
        bowling_strike_rate = calculate_bowling_strike_rate(total_balls, total_wickets)
        
        situation_performance.append({
            "situation": situation["name"],
            "innings": len(situation_data.groupby('filename')),
            "wickets": total_wickets,
            "economy": economy,
            "bowling_strike_rate": bowling_strike_rate
        })
    
    return situation_performance

def merge_team_performances(batting_performances, bowling_performances):
    """Merge batting and bowling performances against teams"""
    # Create a dictionary with team as key
    team_dict = {}
    
    # Add batting performances
    for perf in batting_performances:
        team = perf["team"]
        team_dict[team] = {
            "team": team,
            "matches": perf["matches"],
            "innings": perf["innings"],
            "runs": perf["runs"],
            "average": perf["average"],
            "strike_rate": perf["strike_rate"],
            "best_score": perf["best_score"]
        }
    
    # Add or update with bowling performances
    for perf in bowling_performances:
        team = perf["team"]
        if team in team_dict:
            # Update existing entry
            team_dict[team].update({
                "wickets": perf["wickets"],
                "economy": perf["economy"],
                "bowling_strike_rate": perf["bowling_strike_rate"],
                "best_bowling": perf["best_bowling"]
            })
        else:
            # Create new entry
            team_dict[team] = {
                "team": team,
                "matches": perf["matches"],
                "innings": perf["innings"],
                "wickets": perf["wickets"],
                "economy": perf["economy"],
                "bowling_strike_rate": perf["bowling_strike_rate"],
                "best_bowling": perf["best_bowling"]
            }
    
    # Convert back to list
    merged_performances = list(team_dict.values())
    
    # Sort by matches played (descending)
    merged_performances.sort(key=lambda x: x["matches"], reverse=True)
    
    return merged_performances

def merge_seasonal_performances(batting_performances, bowling_performances):
    """Merge batting and bowling performances by season"""
    # Create a dictionary with season as key
    season_dict = {}
    
    # Add batting performances
    for perf in batting_performances:
        season = perf["season"]
        season_dict[season] = {
            "season": season,
            "matches": perf["matches"],
            "runs": perf["runs"],
            "average": perf["average"],
            "strike_rate": perf["strike_rate"]
        }
    
    # Add or update with bowling performances
    for perf in bowling_performances:
        season = perf["season"]
        if season in season_dict:
            # Update existing entry
            season_dict[season].update({
                "wickets": perf["wickets"],
                "economy": perf["economy"],
                "bowling_strike_rate": perf["bowling_strike_rate"]
            })
        else:
            # Create new entry
            season_dict[season] = {
                "season": season,
                "matches": perf["matches"],
                "wickets": perf["wickets"],
                "economy": perf["economy"],
                "bowling_strike_rate": perf["bowling_strike_rate"]
            }
    
    # Convert back to list
    merged_performances = list(season_dict.values())
    
    # Sort by season (ascending)
    merged_performances.sort(key=lambda x: x["season"])
    
    return merged_performances

def merge_venue_performances(batting_performances, bowling_performances):
    """Merge batting and bowling performances by venue"""
    # Create a dictionary with venue as key
    venue_dict = {}
    
    # Add batting performances
    for perf in batting_performances:
        venue = perf["venue"]
        venue_dict[venue] = {
            "venue": venue,
            "matches": perf["matches"],
            "innings": perf["innings"],
            "runs": perf["runs"],
            "average": perf["average"],
            "strike_rate": perf["strike_rate"]
        }
    
    # Add or update with bowling performances
    for perf in bowling_performances:
        venue = perf["venue"]
        if venue in venue_dict:
            # Update existing entry
            venue_dict[venue].update({
                "wickets": perf["wickets"],
                "economy": perf["economy"],
                "bowling_strike_rate": perf["bowling_strike_rate"]
            })
        else:
            # Create new entry
            venue_dict[venue] = {
                "venue": venue,
                "matches": perf["matches"],
                "innings": perf["innings"],
                "wickets": perf["wickets"],
                "economy": perf["economy"],
                "bowling_strike_rate": perf["bowling_strike_rate"]
            }
    
    # Convert back to list
    merged_performances = list(venue_dict.values())
    
    # Sort by matches played (descending)
    merged_performances.sort(key=lambda x: x["matches"], reverse=True)
    
    return merged_performances

def merge_situation_performances(batting_situations, bowling_situations):
    """Merge batting and bowling performances by match situation"""
    # Create a dictionary with situation as key
    situation_dict = {}
    
    # Add batting performances
    for perf in batting_situations:
        situation = perf["situation"]
        situation_dict[situation] = {
            "situation": situation,
            "innings": perf["innings"],
            "runs": perf["runs"],
            "strike_rate": perf["strike_rate"]
        }
    
    # Add or update with bowling performances
    for perf in bowling_situations:
        situation = perf["situation"]
        if situation in situation_dict:
            # Update existing entry
            situation_dict[situation].update({
                "wickets": perf["wickets"],
                "economy": perf["economy"],
                "bowling_strike_rate": perf["bowling_strike_rate"]
            })
        else:
            # Create new entry
            situation_dict[situation] = {
                "situation": situation,
                "innings": perf["innings"],
                "wickets": perf["wickets"],
                "economy": perf["economy"],
                "bowling_strike_rate": perf["bowling_strike_rate"]
            }
    
    # Convert back to list
    merged_performances = list(situation_dict.values())
    
    return merged_performances

# API Endpoints
@router.get("/players", response_model=List[str])
def get_all_players(db: Session = Depends(get_db)):
    """Get list of all players"""
    return get_player_list(db)

@router.get("/{player_name}", response_model=PlayerPerformanceResponse)
def get_player_performance(
    player_name: str, 
    include_batting: bool = True,
    include_bowling: bool = True,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get comprehensive performance data for a player"""
    # Get player basic info
    player_info = get_player_info(player_name, db)
    
    response = {
        "player_info": player_info,
        "batting_summary": None,
        "bowling_summary": None,
        "highest_scores": None,
        "best_bowling": None,
        "against_teams": None,
        "by_season": None,
        "by_venue": None,
        "by_match_situation": None
    }
    
    # Get batting data if requested
    if include_batting:
        batting_data = get_player_batting_data(player_name, db)
        
        # Filter by season if specified
        if season and not batting_data.empty:
            batting_data = batting_data[batting_data['season'] == season]
        
        if not batting_data.empty:
            # Process batting data
            batting_summary = process_batting_data(batting_data, player_name)
            response["batting_summary"] = batting_summary
            
            # Get highest scores
            response["highest_scores"] = get_highest_scores(batting_data, player_name)
            
            # Get performance against different teams
            response["against_teams"] = get_batting_against_teams(batting_data, player_name)
            
            # Get seasonal performance
            response["by_season"] = get_batting_by_season(batting_data, player_name)
            
            # Get venue performance
            response["by_venue"] = get_batting_by_venue(batting_data, player_name)
            
            # Get match situation performance
            response["by_match_situation"] = get_batting_match_situations(batting_data, player_name)
    
    # Get bowling data if requested
    if include_bowling:
        bowling_data = get_player_bowling_data(player_name, db)
        
        # Filter by season if specified
        if season and not bowling_data.empty:
            bowling_data = bowling_data[bowling_data['season'] == season]
        
        if not bowling_data.empty:
            # Process bowling data
            bowling_summary = process_bowling_data(bowling_data, player_name)
            response["bowling_summary"] = bowling_summary
            
            # Get best bowling performances
            response["best_bowling"] = get_best_bowling(bowling_data, player_name)
            
            # Update against teams with bowling stats
            teams_performance = response["against_teams"] or []
            bowling_against_teams = get_bowling_against_teams(bowling_data, player_name)
            
            # Merge bowling stats with existing batting stats against teams
            response["against_teams"] = merge_team_performances(teams_performance, bowling_against_teams)
            
            # Update seasonal performance with bowling stats
            seasons_performance = response["by_season"] or []
            bowling_by_season = get_bowling_by_season(bowling_data, player_name)
            
            # Merge bowling stats with existing batting stats by season
            response["by_season"] = merge_seasonal_performances(seasons_performance, bowling_by_season)
            
            # Update venue performance with bowling stats
            venues_performance = response["by_venue"] or []
            bowling_by_venue = get_bowling_by_venue(bowling_data, player_name)
            
            # Merge bowling stats with existing batting stats by venue
            response["by_venue"] = merge_venue_performances(venues_performance, bowling_by_venue)
            
            # Update match situation performance with bowling stats
            situations_performance = response["by_match_situation"] or []
            bowling_match_situations = get_bowling_match_situations(bowling_data, player_name)
            
            # Merge bowling stats with existing batting stats by match situation
            response["by_match_situation"] = merge_situation_performances(situations_performance, bowling_match_situations)
    
    # If no data found at all
    if (include_batting and include_bowling and 
        response["batting_summary"] is None and response["bowling_summary"] is None):
        raise HTTPException(status_code=404, detail=f"No performance data found for player: {player_name}")
    
    return response

@router.get("/{player_name}/batting", response_model=BattingPerformanceSummary)
def get_player_batting_summary(
    player_name: str, 
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get batting summary for a player"""
    batting_data = get_player_batting_data(player_name, db)
    
    # Filter by season if specified
    if season and not batting_data.empty:
        batting_data = batting_data[batting_data['season'] == season]
    
    if batting_data.empty:
        raise HTTPException(status_code=404, detail=f"No batting data found for player: {player_name}")
    
    return process_batting_data(batting_data, player_name)

@router.get("/{player_name}/bowling", response_model=BowlingPerformanceSummary)
def get_player_bowling_summary(
    player_name: str, 
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get bowling summary for a player"""
    bowling_data = get_player_bowling_data(player_name, db)
    
    # Filter by season if specified
    if season and not bowling_data.empty:
        bowling_data = bowling_data[bowling_data['season'] == season]
    
    if bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No bowling data found for player: {player_name}")
    
    return process_bowling_data(bowling_data, player_name)

@router.get("/{player_name}/highest-scores", response_model=List[InningsHighlight])
def get_player_highest_scores(
    player_name: str, 
    limit: int = 5,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get highest scores for a player"""
    batting_data = get_player_batting_data(player_name, db)
    
    # Filter by season if specified
    if season and not batting_data.empty:
        batting_data = batting_data[batting_data['season'] == season]
    
    if batting_data.empty:
        raise HTTPException(status_code=404, detail=f"No batting data found for player: {player_name}")
    
    return get_highest_scores(batting_data, player_name, limit)

@router.get("/{player_name}/best-bowling", response_model=List[BowlingHighlight])
def get_player_best_bowling(
    player_name: str, 
    limit: int = 5,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get best bowling performances for a player"""
    bowling_data = get_player_bowling_data(player_name, db)
    
    # Filter by season if specified
    if season and not bowling_data.empty:
        bowling_data = bowling_data[bowling_data['season'] == season]
    
    if bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No bowling data found for player: {player_name}")
    
    return get_best_bowling(bowling_data, player_name, limit)

@router.get("/{player_name}/against-teams", response_model=List[TeamwisePerformance])
def get_player_against_teams(
    player_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get player performance against different teams"""
    # Get batting data
    batting_data = get_player_batting_data(player_name, db)
    
    # Filter by season if specified
    if season and not batting_data.empty:
        batting_data = batting_data[batting_data['season'] == season]
    
    # Get bowling data
    bowling_data = get_player_bowling_data(player_name, db)
    
    # Filter by season if specified
    if season and not bowling_data.empty:
        bowling_data = bowling_data[bowling_data['season'] == season]
    
    if batting_data.empty and bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No performance data found for player: {player_name}")
    
    batting_against_teams = [] if batting_data.empty else get_batting_against_teams(batting_data, player_name)
    bowling_against_teams = [] if bowling_data.empty else get_bowling_against_teams(bowling_data, player_name)
    
    return merge_team_performances(batting_against_teams, bowling_against_teams)

@router.get("/{player_name}/by-season", response_model=List[SeasonalPerformance])
def get_player_by_season(
    player_name: str,
    db: Session = Depends(get_db)
):
    """Get player performance across seasons"""
    # Get batting data
    batting_data = get_player_batting_data(player_name, db)
    
    # Get bowling data
    bowling_data = get_player_bowling_data(player_name, db)
    
    if batting_data.empty and bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No performance data found for player: {player_name}")
    
    batting_by_season = [] if batting_data.empty else get_batting_by_season(batting_data, player_name)
    bowling_by_season = [] if bowling_data.empty else get_bowling_by_season(bowling_data, player_name)
    
    return merge_seasonal_performances(batting_by_season, bowling_by_season)

@router.get("/{player_name}/by-venue", response_model=List[VenuePerformance])
def get_player_by_venue(
    player_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get player performance across venues"""
    # Get batting data
    batting_data = get_player_batting_data(player_name, db)
    
    # Filter by season if specified
    if season and not batting_data.empty:
        batting_data = batting_data[batting_data['season'] == season]
    
    # Get bowling data
    bowling_data = get_player_bowling_data(player_name, db)
    
    # Filter by season if specified
    if season and not bowling_data.empty:
        bowling_data = bowling_data[bowling_data['season'] == season]
    
    if batting_data.empty and bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No performance data found for player: {player_name}")
    
    batting_by_venue = [] if batting_data.empty else get_batting_by_venue(batting_data, player_name)
    bowling_by_venue = [] if bowling_data.empty else get_bowling_by_venue(bowling_data, player_name)
    
    return merge_venue_performances(batting_by_venue, bowling_by_venue)

@router.get("/{player_name}/match-situations", response_model=List[MatchSituationPerformance])
def get_player_match_situations(
    player_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get player performance in different match situations"""
    # Get batting data
    batting_data = get_player_batting_data(player_name, db)
    
    # Filter by season if specified
    if season and not batting_data.empty:
        batting_data = batting_data[batting_data['season'] == season]
    
    # Get bowling data
    bowling_data = get_player_bowling_data(player_name, db)
    
    # Filter by season if specified
    if season and not bowling_data.empty:
        bowling_data = bowling_data[bowling_data['season'] == season]
    
    if batting_data.empty and bowling_data.empty:
        raise HTTPException(status_code=404, detail=f"No performance data found for player: {player_name}")
    
    batting_situations = [] if batting_data.empty else get_batting_match_situations(batting_data, player_name)
    bowling_situations = [] if bowling_data.empty else get_bowling_match_situations(bowling_data, player_name)
    
    return merge_situation_performances(batting_situations, bowling_situations)