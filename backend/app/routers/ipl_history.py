# app/routers/ipl_history.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from typing import List, Optional, Dict, Any

router = APIRouter(
    prefix="/api/ipl-history",
    tags=["IPL History"],
    responses={404: {"description": "Not found"}}
)

@router.get("/overview")
def get_comprehensive_ipl_history(
    season: Optional[int] = None,
    category: Optional[str] = Query(None, 
        description="Specific category to retrieve: toss, venue, team, player, match, records"),
    db: Session = Depends(get_db)
):
    """
    Comprehensive IPL History Analytics Endpoint
    
    Provides a unified interface for retrieving IPL analytics across different categories.
    
    Parameters:
    - season: Optional season filter
    - category: Optional specific category to retrieve
    """
    try:
        # Prepare a comprehensive analytics dictionary
        ipl_history = {
            "metadata": {
                "total_seasons": 0,
                "total_matches": 0,
                "total_teams": 0,
                "date_range": {}
            },
            "seasons": [],
            "toss_analytics": {},
            "venue_analytics": {},
            "team_analytics": {},
            "player_analytics": {},
            "match_analytics": {},
            "record_books": {}
        }
        
        # Seasons Overview
        seasons_query = """
        SELECT 
            season,
            COUNT(*) as matches_played,
            MIN(date) as first_match,
            MAX(date) as last_match,
            COUNT(DISTINCT venue) as venues_used,
            COUNT(DISTINCT winner) as teams_participated
        FROM match_info
        GROUP BY season
        ORDER BY season
        """
        seasons_results = db.execute(text(seasons_query)).fetchall()
        
        ipl_history["metadata"]["total_seasons"] = len(seasons_results)
        ipl_history["seasons"] = [
            {
                "year": row[0],
                "matches_played": row[1],
                "first_match": row[2],
                "last_match": row[3],
                "venues_used": row[4],
                "teams_participated": row[5]
            } for row in seasons_results
        ]
        
        # If a specific season is provided, filter results
        if season:
            seasons_results = [row for row in seasons_results if row[0] == season]
        
        # Toss Analytics
        toss_query = """
        SELECT 
            season,
            toss_winner,
            COUNT(*) as total_tosses,
            ROUND(SUM(CASE WHEN toss_decision = 'bat' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) as bat_percentage,
            ROUND(SUM(CASE WHEN toss_decision = 'field' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) as field_percentage,
            ROUND(SUM(CASE WHEN winner = toss_winner THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) as toss_win_match_percentage
        FROM match_info
        GROUP BY season, toss_winner
        ORDER BY season, total_tosses DESC
        """
        toss_results = db.execute(text(toss_query)).fetchall()
        
        ipl_history["toss_analytics"] = [
            {
                "season": row[0],
                "toss_winner": row[1],
                "total_tosses": row[2],
                "bat_percentage": row[3],
                "field_percentage": row[4],
                "toss_win_match_percentage": row[5]
            } for row in toss_results
        ]
        
        # Venue Analytics
        venue_query = """
        SELECT 
            season,
            venue,
            COUNT(*) as matches_hosted,
            ROUND(AVG(CASE WHEN toss_decision = 'bat' THEN 1.0 ELSE 0 END) * 100, 2) as avg_bat_first_percentage,
            ROUND(AVG(CASE WHEN winner = team1 THEN 1.0 ELSE 0 END) * 100, 2) as team1_win_percentage
        FROM match_info
        GROUP BY season, venue
        ORDER BY season, matches_hosted DESC
        """
        venue_results = db.execute(text(venue_query)).fetchall()
        
        ipl_history["venue_analytics"] = [
            {
                "season": row[0],
                "venue": row[1],
                "matches_hosted": row[2],
                "avg_bat_first_percentage": row[3],
                "team1_win_percentage": row[4]
            } for row in venue_results
        ]
        
        # Team Analytics
        team_query = """
        SELECT 
            season,
            team1 as team,
            COUNT(*) as matches_played,
            SUM(CASE WHEN winner = team1 THEN 1 ELSE 0 END) as matches_won,
            ROUND(SUM(CASE WHEN winner = team1 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) as win_percentage
        FROM match_info
        GROUP BY season, team1
        UNION ALL
        SELECT 
            season,
            team2 as team,
            COUNT(*) as matches_played,
            SUM(CASE WHEN winner = team2 THEN 1 ELSE 0 END) as matches_won,
            ROUND(SUM(CASE WHEN winner = team2 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) as win_percentage
        FROM match_info
        GROUP BY season, team2
        ORDER BY season, win_percentage DESC
        """
        team_results = db.execute(text(team_query)).fetchall()
        
        ipl_history["team_analytics"] = [
            {
                "season": row[0],
                "team": row[1],
                "matches_played": row[2],
                "matches_won": row[3],
                "win_percentage": row[4]
            } for row in team_results
        ]
        
        # Player Analytics (Top performers)
        player_query = """
        WITH batting_stats AS (
            SELECT 
                m.season,
                i.batsman as player,
                SUM(i.runs_batsman) as total_runs,
                COUNT(DISTINCT i.filename) as matches,
                ROUND(AVG(i.runs_batsman), 2) as average
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            GROUP BY m.season, i.batsman
        ),
        bowling_stats AS (
            SELECT 
                m.season,
                i.bowler as player,
                COUNT(*) as wickets,
                SUM(i.runs_total) as runs_conceded,
                ROUND(SUM(i.runs_total)::numeric / (COUNT(*) / 6.0), 2) as economy_rate
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            WHERE i.wicket_details IS NOT NULL
            GROUP BY m.season, i.bowler
        )
        SELECT 
            b.season,
            b.player as top_batsman,
            b.total_runs,
            b.matches as batting_matches,
            w.player as top_bowler,
            w.wickets,
            w.runs_conceded,
            w.economy_rate
        FROM batting_stats b
        JOIN bowling_stats w ON b.season = w.season
        ORDER BY b.total_runs DESC, w.wickets DESC
        """
        player_results = db.execute(text(player_query)).fetchall()
        
        ipl_history["player_analytics"] = [
            {
                "season": row[0],
                "top_batsman": row[1],
                "total_runs": row[2],
                "batting_matches": row[3],
                "top_bowler": row[4],
                "wickets": row[5],
                "runs_conceded": row[6],
                "economy_rate": row[7]
            } for row in player_results
        ]
        
        # Match Analytics
        match_query = """
        SELECT 
            season,
            COUNT(*) as total_matches,
            SUM(CASE WHEN result = 'normal' THEN 1 ELSE 0 END) as normal_matches,
            SUM(CASE WHEN result = 'tie' THEN 1 ELSE 0 END) as tie_matches,
            SUM(CASE WHEN super_over = 'yes' THEN 1 ELSE 0 END) as super_over_matches,
            ROUND(AVG(result_margin), 2) as avg_margin
        FROM match_info
        GROUP BY season
        ORDER BY season
        """
        match_results = db.execute(text(match_query)).fetchall()
        
        ipl_history["match_analytics"] = [
            {
                "season": row[0],
                "total_matches": row[1],
                "normal_matches": row[2],
                "tie_matches": row[3],
                "super_over_matches": row[4],
                "avg_margin": row[5]
            } for row in match_results
        ]
        
        # Record Books (Most of something)
        record_query = """
        WITH player_records AS (
            SELECT 
                m.season,
                i.batsman as top_run_scorer,
                SUM(i.runs_batsman) as total_runs,
                i.bowler as top_wicket_taker,
                COUNT(*) as wickets
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            GROUP BY m.season, i.batsman, i.bowler
        )
        SELECT 
            season,
            top_run_scorer,
            total_runs,
            top_wicket_taker,
            wickets
        FROM player_records
        ORDER BY total_runs DESC, wickets DESC
        """
        record_results = db.execute(text(record_query)).fetchall()
        
        ipl_history["record_books"] = [
            {
                "season": row[0],
                "top_run_scorer": row[1],
                "total_runs": row[2],
                "top_wicket_taker": row[3],
                "wickets": row[4]
            } for row in record_results
        ]
        
        # Apply category filtering if specified
        if category:
            category = category.lower()
            if category in ipl_history:
                return {category: ipl_history[category]}
        
        return ipl_history
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving IPL history: {str(e)}")

# In main.py, add the router
# from app.routers import ipl_history
# app.include_router(ipl_history.router)