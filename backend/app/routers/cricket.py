from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional, Dict, Any, Union
from app.main import get_db_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

# ---------- MATCH STATISTICS ENDPOINTS ---------- #

@router.get("/match-statistics", response_model=Dict[str, Any],
           summary="Get match statistics by season or for all seasons",
           description="""
           Retrieve comprehensive match statistics for IPL seasons.
           
           Parameters:
           - season: Optional filter for a specific season (e.g., "2023", "2007/08")
           - include_totals: Whether to include aggregated totals across all seasons
           
           Returns detailed statistics including batting first/second win percentages,
           tie matches, super overs, and more.
           """)
async def get_match_statistics(
    season: Optional[str] = Query(None, description="Filter by season (e.g., '2023', '2007/08')"),
    include_totals: bool = Query(True, description="Include aggregated totals in response")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Base query
        query = """
        SELECT 
            s.season_name,
            s.season_year,
            COUNT(*) as total_matches,
            SUM(CASE WHEN i1.batting_team_id = m.winner_id THEN 1 ELSE 0 END) as first_batting_wins,
            SUM(CASE WHEN i2.batting_team_id = m.winner_id THEN 1 ELSE 0 END) as second_batting_wins,
            SUM(CASE WHEN m.result = 'tie' THEN 1 ELSE 0 END) as tie_matches,
            SUM(CASE WHEN m.is_super_over = TRUE THEN 1 ELSE 0 END) as super_over_matches,
            COUNT(DISTINCT m.venue_id) as venues_used
        FROM 
            matches m
            JOIN seasons s ON m.season_id = s.season_id
            LEFT JOIN innings i1 ON m.match_id = i1.match_id AND i1.inning_number = 1
            LEFT JOIN innings i2 ON m.match_id = i2.match_id AND i2.inning_number = 2
        """
        
        # Add season filter if provided
        params = []
        if season:
            query += " WHERE s.season_name = %s"
            params.append(season)
        
        # Group by season
        query += " GROUP BY s.season_name, s.season_year ORDER BY s.season_year DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Process results
        stats_by_season = []
        for row in results:
            season_stats = dict(row)
            
            # Calculate percentages
            total = season_stats['total_matches']
            if total > 0:
                first_wins = season_stats['first_batting_wins'] or 0
                second_wins = season_stats['second_batting_wins'] or 0
                season_stats['first_batting_win_percentage'] = round((first_wins / total) * 100, 2)
                season_stats['second_batting_win_percentage'] = round((second_wins / total) * 100, 2)
            else:
                season_stats['first_batting_win_percentage'] = 0
                season_stats['second_batting_win_percentage'] = 0
                
            stats_by_season.append(season_stats)
        
        # If requested and we have multiple seasons, add totals
        if include_totals and len(stats_by_season) > 1:
            totals = {
                "season_name": "All Seasons",
                "season_year": None,
                "total_matches": sum(s['total_matches'] for s in stats_by_season),
                "first_batting_wins": sum(s['first_batting_wins'] or 0 for s in stats_by_season),
                "second_batting_wins": sum(s['second_batting_wins'] or 0 for s in stats_by_season),
                "tie_matches": sum(s['tie_matches'] or 0 for s in stats_by_season),
                "super_over_matches": sum(s['super_over_matches'] or 0 for s in stats_by_season),
                "venues_used": max(s['venues_used'] or 0 for s in stats_by_season)
            }
            
            # Calculate overall percentages
            if totals['total_matches'] > 0:
                totals['first_batting_win_percentage'] = round((totals['first_batting_wins'] / totals['total_matches']) * 100, 2)
                totals['second_batting_win_percentage'] = round((totals['second_batting_wins'] / totals['total_matches']) * 100, 2)
            else:
                totals['first_batting_win_percentage'] = 0
                totals['second_batting_win_percentage'] = 0
                
            stats_by_season.append(totals)
        
        cursor.close()
        conn.close()
        
        return {
            "match_statistics": stats_by_season,
            "total_seasons": len(results),
            "filters_applied": {"season": season} if season else {}
        }
    
    except Exception as e:
        logger.error(f"Error retrieving match statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving match statistics: {str(e)}")


# ---------- TOSS ANALYSIS ENDPOINTS ---------- #

@router.get("/toss-analysis", response_model=Dict[str, Any],
          summary="Get toss analysis statistics",
          description="""
          Analyze toss decisions and outcomes.
          
          Parameters:
          - season: Optional season filter (e.g., "2023", "2007/08")
          - team: Optional team name filter (exact match required)
          - include_totals: Whether to include aggregated totals
          
          Returns comprehensive statistics on toss wins, decisions to bat/field,
          and success rates based on those decisions.
          """)
async def get_toss_analysis(
    season: Optional[str] = Query(None, description="Filter by season (e.g., '2023', '2007/08')"),
    team: Optional[str] = Query(None, description="Filter by team name (exact match)"),
    include_totals: bool = Query(True, description="Include aggregated totals in response")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Base query
        query = """
        SELECT 
            s.season_name,
            s.season_year,
            t.team_name,
            SUM(ts.toss_wins) as toss_wins,
            SUM(ts.chose_bat) as chose_bat,
            SUM(ts.chose_field) as chose_field,
            SUM(ts.won_after_batting) as won_after_batting,
            SUM(ts.won_after_fielding) as won_after_fielding
        FROM 
            toss_stats ts
            JOIN teams t ON ts.team_id = t.team_id
            JOIN seasons s ON ts.season_id = s.season_id
        """
        
        # Add filters if provided
        conditions = []
        params = []
        
        if season:
            conditions.append("s.season_name = %s")
            params.append(season)
        
        if team:
            conditions.append("t.team_name = %s")
            params.append(team)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Group by team and season
        query += " GROUP BY s.season_name, s.season_year, t.team_name ORDER BY s.season_year DESC, t.team_name"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        toss_analysis = []
        for row in results:
            toss_data = dict(row)
            
            # Calculate percentages
            if toss_data['toss_wins'] > 0:
                chose_bat = toss_data['chose_bat'] or 0
                chose_field = toss_data['chose_field'] or 0
                toss_data['chose_bat_percentage'] = round((chose_bat / toss_data['toss_wins']) * 100, 2)
                toss_data['chose_field_percentage'] = round((chose_field / toss_data['toss_wins']) * 100, 2)
            else:
                toss_data['chose_bat_percentage'] = 0
                toss_data['chose_field_percentage'] = 0
                
            if toss_data['chose_bat'] and toss_data['chose_bat'] > 0:
                won_batting = toss_data['won_after_batting'] or 0
                toss_data['won_after_batting_percentage'] = round((won_batting / toss_data['chose_bat']) * 100, 2)
            else:
                toss_data['won_after_batting_percentage'] = 0
                
            if toss_data['chose_field'] and toss_data['chose_field'] > 0:
                won_fielding = toss_data['won_after_fielding'] or 0
                toss_data['won_after_fielding_percentage'] = round((won_fielding / toss_data['chose_field']) * 100, 2)
            else:
                toss_data['won_after_fielding_percentage'] = 0
                
            toss_analysis.append(toss_data)
        
        # Calculate totals if multiple teams/seasons are present
        if include_totals and len(toss_analysis) > 1:
            if team:
                # If filtering for a single team, aggregate across seasons
                totals = {
                    "season_name": "All Seasons",
                    "season_year": None,
                    "team_name": team,
                    "toss_wins": sum(t['toss_wins'] or 0 for t in toss_analysis),
                    "chose_bat": sum(t['chose_bat'] or 0 for t in toss_analysis),
                    "chose_field": sum(t['chose_field'] or 0 for t in toss_analysis),
                    "won_after_batting": sum(t['won_after_batting'] or 0 for t in toss_analysis),
                    "won_after_fielding": sum(t['won_after_fielding'] or 0 for t in toss_analysis),
                }
            else:
                # If no team filter, aggregate across all teams and seasons
                totals = {
                    "season_name": "All",
                    "season_year": None,
                    "team_name": "All Teams",
                    "toss_wins": sum(t['toss_wins'] or 0 for t in toss_analysis),
                    "chose_bat": sum(t['chose_bat'] or 0 for t in toss_analysis),
                    "chose_field": sum(t['chose_field'] or 0 for t in toss_analysis),
                    "won_after_batting": sum(t['won_after_batting'] or 0 for t in toss_analysis),
                    "won_after_fielding": sum(t['won_after_fielding'] or 0 for t in toss_analysis),
                }
                
            # Calculate percentages for totals
            if totals['toss_wins'] > 0:
                totals['chose_bat_percentage'] = round((totals['chose_bat'] / totals['toss_wins']) * 100, 2)
                totals['chose_field_percentage'] = round((totals['chose_field'] / totals['toss_wins']) * 100, 2)
            else:
                totals['chose_bat_percentage'] = 0
                totals['chose_field_percentage'] = 0
                
            if totals['chose_bat'] > 0:
                totals['won_after_batting_percentage'] = round((totals['won_after_batting'] / totals['chose_bat']) * 100, 2)
            else:
                totals['won_after_batting_percentage'] = 0
                
            if totals['chose_field'] > 0:
                totals['won_after_fielding_percentage'] = round((totals['won_after_fielding'] / totals['chose_field']) * 100, 2)
            else:
                totals['won_after_fielding_percentage'] = 0
                
            toss_analysis.append(totals)
        
        cursor.close()
        conn.close()
        
        return {
            "toss_analysis": toss_analysis,
            "total_records": len(results),
            "filters_applied": {
                "season": season if season else None,
                "team": team if team else None
            }
        }
    
    except Exception as e:
        logger.error(f"Error retrieving toss analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving toss analysis: {str(e)}")


# ---------- TEAM ANALYSIS ENDPOINTS ---------- #

@router.get("/team-stats", response_model=Dict[str, Any],
          summary="Get team performance statistics",
          description="""
          Retrieve comprehensive team performance statistics.
          
          Parameters:
          - team_name: Optional filter by specific team name (exact match)
          - season: Optional filter by season (e.g., "2023", "2007/08")
          - include_totals: Whether to include aggregated totals across seasons
          
          Returns detailed team performance metrics including overall win percentage,
          home/away win rates, and batting/bowling first success rates.
          """)
async def get_team_stats(
    team_name: Optional[str] = Query(None, description="Filter by team name (exact match)"),
    season: Optional[str] = Query(None, description="Filter by season (e.g., '2023', '2007/08')"),
    include_totals: bool = Query(True, description="Include aggregated totals in response")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Base query
        query = """
        SELECT 
            t.team_name,
            s.season_name,
            s.season_year,
            tss.matches_played,
            tss.matches_won,
            tss.home_matches_played,
            tss.home_matches_won,
            tss.away_matches_played,
            tss.away_matches_won,
            tss.batting_first_played,
            tss.batting_first_won,
            tss.bowling_first_played,
            tss.bowling_first_won
        FROM 
            team_season_stats tss
            JOIN teams t ON tss.team_id = t.team_id
            JOIN seasons s ON tss.season_id = s.season_id
        """
        
        # Add filters if provided
        conditions = []
        params = []
        
        if team_name:
            conditions.append("t.team_name = %s")
            params.append(team_name)
        
        if season:
            conditions.append("s.season_name = %s")
            params.append(season)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Order by
        query += " ORDER BY s.season_year DESC, t.team_name"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        team_stats = []
        for row in results:
            stats = dict(row)
            
            # Calculate win percentages
            if stats['matches_played'] and stats['matches_played'] > 0:
                stats['overall_win_percentage'] = round((stats['matches_won'] / stats['matches_played']) * 100, 2)
            else:
                stats['overall_win_percentage'] = 0
                
            if stats['home_matches_played'] and stats['home_matches_played'] > 0:
                stats['home_win_percentage'] = round((stats['home_matches_won'] / stats['home_matches_played']) * 100, 2)
            else:
                stats['home_win_percentage'] = 0
                
            if stats['away_matches_played'] and stats['away_matches_played'] > 0:
                stats['away_win_percentage'] = round((stats['away_matches_won'] / stats['away_matches_played']) * 100, 2)
            else:
                stats['away_win_percentage'] = 0
                
            if stats['batting_first_played'] and stats['batting_first_played'] > 0:
                stats['batting_first_win_percentage'] = round((stats['batting_first_won'] / stats['batting_first_played']) * 100, 2)
            else:
                stats['batting_first_win_percentage'] = 0
                
            if stats['bowling_first_played'] and stats['bowling_first_played'] > 0:
                stats['bowling_first_win_percentage'] = round((stats['bowling_first_won'] / stats['bowling_first_played']) * 100, 2)
            else:
                stats['bowling_first_win_percentage'] = 0
                
            team_stats.append(stats)
        
        # Calculate totals if requested and multiple records exist
        if include_totals and len(team_stats) > 1:
            if team_name:
                # If filtering by team, aggregate across seasons
                team_totals = {
                    "team_name": team_name,
                    "season_name": "All Seasons",
                    "season_year": None,
                    "matches_played": sum(s['matches_played'] or 0 for s in team_stats),
                    "matches_won": sum(s['matches_won'] or 0 for s in team_stats),
                    "home_matches_played": sum(s['home_matches_played'] or 0 for s in team_stats),
                    "home_matches_won": sum(s['home_matches_won'] or 0 for s in team_stats),
                    "away_matches_played": sum(s['away_matches_played'] or 0 for s in team_stats),
                    "away_matches_won": sum(s['away_matches_won'] or 0 for s in team_stats),
                    "batting_first_played": sum(s['batting_first_played'] or 0 for s in team_stats),
                    "batting_first_won": sum(s['batting_first_won'] or 0 for s in team_stats),
                    "bowling_first_played": sum(s['bowling_first_played'] or 0 for s in team_stats),
                    "bowling_first_won": sum(s['bowling_first_won'] or 0 for s in team_stats),
                }
                
                # Calculate percentages
                if team_totals['matches_played'] > 0:
                    team_totals['overall_win_percentage'] = round((team_totals['matches_won'] / team_totals['matches_played']) * 100, 2)
                else:
                    team_totals['overall_win_percentage'] = 0
                    
                if team_totals['home_matches_played'] > 0:
                    team_totals['home_win_percentage'] = round((team_totals['home_matches_won'] / team_totals['home_matches_played']) * 100, 2)
                else:
                    team_totals['home_win_percentage'] = 0
                    
                if team_totals['away_matches_played'] > 0:
                    team_totals['away_win_percentage'] = round((team_totals['away_matches_won'] / team_totals['away_matches_played']) * 100, 2)
                else:
                    team_totals['away_win_percentage'] = 0
                    
                if team_totals['batting_first_played'] > 0:
                    team_totals['batting_first_win_percentage'] = round((team_totals['batting_first_won'] / team_totals['batting_first_played']) * 100, 2)
                else:
                    team_totals['batting_first_win_percentage'] = 0
                    
                if team_totals['bowling_first_played'] > 0:
                    team_totals['bowling_first_win_percentage'] = round((team_totals['bowling_first_won'] / team_totals['bowling_first_played']) * 100, 2)
                else:
                    team_totals['bowling_first_win_percentage'] = 0
                    
                team_stats.append(team_totals)
        
        cursor.close()
        conn.close()
        
        return {
            "team_statistics": team_stats,
            "total_records": len(results),
            "filters_applied": {
                "team_name": team_name if team_name else None,
                "season": season if season else None
            }
        }
    
    except Exception as e:
        logger.error(f"Error retrieving team statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving team statistics: {str(e)}")


# ---------- VENUE ANALYSIS ENDPOINTS ---------- #

@router.get("/venue-stats", response_model=Dict[str, Any],
         summary="Get venue statistics",
         description="""
         Analyze performance statistics for venues.
         
         Parameters:
         - venue_name: Optional filter by venue name (exact match)
         - season: Optional filter by season (e.g., "2023", "2007/08")
         - include_totals: Whether to include aggregated totals
         
         Returns detailed venue performance data including win rates when
         batting first/second and toss decision trends.
         """)
async def get_venue_stats(
    venue_name: Optional[str] = Query(None, description="Filter by venue name (exact match)"),
    season: Optional[str] = Query(None, description="Filter by season (e.g., '2023', '2007/08')"),
    include_totals: bool = Query(True, description="Include aggregated totals in response")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Base query for venues
        query = """
        SELECT 
            v.venue_name,
            v.city,
            s.season_name,
            s.season_year,
            COUNT(DISTINCT m.match_id) as total_matches,
            SUM(CASE WHEN i1.batting_team_id = m.winner_id THEN 1 ELSE 0 END) as first_batting_wins,
            SUM(CASE WHEN i2.batting_team_id = m.winner_id THEN 1 ELSE 0 END) as second_batting_wins,
            SUM(CASE WHEN m.toss_decision = 'field' THEN 1 ELSE 0 END) as field_decisions,
            SUM(CASE WHEN m.toss_decision = 'bat' THEN 1 ELSE 0 END) as bat_decisions
        FROM 
            venues v
            JOIN matches m ON v.venue_id = m.venue_id
            JOIN innings i1 ON m.match_id = i1.match_id AND i1.inning_number = 1
            JOIN innings i2 ON m.match_id = i2.match_id AND i2.inning_number = 2
            JOIN seasons s ON m.season_id = s.season_id
        """
        
        # Add filters if provided
        conditions = []
        params = []
        
        if venue_name:
            conditions.append("v.venue_name = %s")
            params.append(venue_name)
        
        if season:
            conditions.append("s.season_name = %s")
            params.append(season)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Group by venue and season
        query += " GROUP BY v.venue_name, v.city, s.season_name, s.season_year ORDER BY v.venue_name, s.season_year DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        venue_stats = []
        for row in results:
            stats = dict(row)
            
            # Calculate percentages
            if stats['total_matches'] and stats['total_matches'] > 0:
                first_wins = stats['first_batting_wins'] or 0
                second_wins = stats['second_batting_wins'] or 0
                stats['first_batting_win_percentage'] = round((first_wins / stats['total_matches']) * 100, 2)
                stats['second_batting_win_percentage'] = round((second_wins / stats['total_matches']) * 100, 2)
            else:
                stats['first_batting_win_percentage'] = 0
                stats['second_batting_win_percentage'] = 0
                
            total_toss_decisions = (stats['field_decisions'] or 0) + (stats['bat_decisions'] or 0)
            if total_toss_decisions > 0:
                stats['field_decision_percentage'] = round((stats['field_decisions'] / total_toss_decisions) * 100, 2)
                stats['bat_decision_percentage'] = round((stats['bat_decisions'] / total_toss_decisions) * 100, 2)
            else:
                stats['field_decision_percentage'] = 0
                stats['bat_decision_percentage'] = 0
                
            venue_stats.append(stats)
        
        # If requested and multiple records exist, include totals
        if include_totals and len(venue_stats) > 1:
            if venue_name:
                # If filtering by venue, aggregate across seasons
                venue_totals = {
                    "venue_name": venue_name,
                    "city": venue_stats[0]['city'] if venue_stats else None,
                    "season_name": "All Seasons",
                    "season_year": None,
                    "total_matches": sum(v['total_matches'] or 0 for v in venue_stats),
                    "first_batting_wins": sum(v['first_batting_wins'] or 0 for v in venue_stats),
                    "second_batting_wins": sum(v['second_batting_wins'] or 0 for v in venue_stats),
                    "field_decisions": sum(v['field_decisions'] or 0 for v in venue_stats),
                    "bat_decisions": sum(v['bat_decisions'] or 0 for v in venue_stats)
                }
                
                # Calculate percentages
                if venue_totals['total_matches'] > 0:
                    venue_totals['first_batting_win_percentage'] = round((venue_totals['first_batting_wins'] / venue_totals['total_matches']) * 100, 2)
                    venue_totals['second_batting_win_percentage'] = round((venue_totals['second_batting_wins'] / venue_totals['total_matches']) * 100, 2)
                else:
                    venue_totals['first_batting_win_percentage'] = 0
                    venue_totals['second_batting_win_percentage'] = 0
                    
                total_toss_decisions = venue_totals['field_decisions'] + venue_totals['bat_decisions']
                if total_toss_decisions > 0:
                    venue_totals['field_decision_percentage'] = round((venue_totals['field_decisions'] / total_toss_decisions) * 100, 2)
                    venue_totals['bat_decision_percentage'] = round((venue_totals['bat_decisions'] / total_toss_decisions) * 100, 2)
                else:
                    venue_totals['field_decision_percentage'] = 0
                    venue_totals['bat_decision_percentage'] = 0
                    
                venue_stats.append(venue_totals)
        
        cursor.close()
        conn.close()
        
        return {
            "venue_statistics": venue_stats,
            "total_records": len(results),
            "filters_applied": {
                "venue_name": venue_name if venue_name else None,
                "season": season if season else None
            }
        }
    
    except Exception as e:
        logger.error(f"Error retrieving venue statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving venue statistics: {str(e)}")


 # ---------- HEAD-TO-HEAD ANALYSIS ENDPOINTS ---------- #

@router.get("/head-to-head/{team1}/{team2}", response_model=Dict[str, Any],
           summary="Get head-to-head statistics between two teams",
           description="""
           Analyze the performance between two teams across all seasons or a specific season.
           
           Path Parameters:
           - team1: Name of the first team (e.g., "Chennai Super Kings")
           - team2: Name of the second team (e.g., "Mumbai Indians")
           
           Query Parameters:
           - season: Optional filter by season (e.g., "2023", "2007/08")
           - include_totals: Whether to include aggregated totals
           
           Returns detailed head-to-head statistics including matches played,
           win records, and win percentages.
           """)
async def get_head_to_head(
    team1: str = Path(..., description="First team name"),
    team2: str = Path(..., description="Second team name"),
    season: Optional[str] = Query(None, description="Filter by season (e.g., '2023', '2007/08')"),
    include_totals: bool = Query(True, description="Include aggregated totals in response")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get team IDs
        cursor.execute("SELECT team_id FROM teams WHERE team_name = %s", (team1,))
        team1_result = cursor.fetchone()
        
        if not team1_result:
            raise HTTPException(status_code=404, detail=f"Team '{team1}' not found")
        
        cursor.execute("SELECT team_id FROM teams WHERE team_name = %s", (team2,))
        team2_result = cursor.fetchone()
        
        if not team2_result:
            raise HTTPException(status_code=404, detail=f"Team '{team2}' not found")
        
        team1_id = team1_result["team_id"]
        team2_id = team2_result["team_id"]
        
        # Determine the correct order for team1_id and team2_id
        if team1_id > team2_id:
            team1_id, team2_id = team2_id, team1_id
            team1, team2 = team2, team1
            flip_results = True
        else:
            flip_results = False
        
        # Base query
        query = """
        SELECT 
            h.team1_id,
            h.team2_id,
            s.season_name,
            s.season_year,
            h.matches_played,
            h.team1_wins,
            h.team2_wins,
            h.no_results,
            t1.team_name as team1_name,
            t2.team_name as team2_name
        FROM 
            head_to_head h
            JOIN teams t1 ON h.team1_id = t1.team_id
            JOIN teams t2 ON h.team2_id = t2.team_id
            JOIN seasons s ON h.season_id = s.season_id
        WHERE 
            h.team1_id = %s AND h.team2_id = %s
        """
        
        params = [team1_id, team2_id]
        
        # Add season filter if provided
        if season:
            query += " AND s.season_name = %s"
            params.append(season)
        
        # Order by season
        query += " ORDER BY s.season_year DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        h2h_stats = []
        for row in results:
            stats = dict(row)
            
            # Flip the results if needed
            if flip_results:
                stats['team1_wins'], stats['team2_wins'] = stats['team2_wins'], stats['team1_wins']
                stats['team1_name'], stats['team2_name'] = stats['team2_name'], stats['team1_name']
            
            # Calculate win percentages
            total_results = stats['matches_played'] - (stats['no_results'] or 0)
            if total_results > 0:
                stats['team1_win_percentage'] = round((stats['team1_wins'] / total_results) * 100, 2)
                stats['team2_win_percentage'] = round((stats['team2_wins'] / total_results) * 100, 2)
            else:
                stats['team1_win_percentage'] = 0
                stats['team2_win_percentage'] = 0
                
            h2h_stats.append(stats)
        
        # Add a total row if multiple seasons and requested
        if include_totals and len(h2h_stats) > 1:
            total_stats = {
                "season_name": "All Seasons",
                "season_year": None,
                "team1_name": team1,
                "team2_name": team2,
                "matches_played": sum(s['matches_played'] or 0 for s in h2h_stats),
                "team1_wins": sum(s['team1_wins'] or 0 for s in h2h_stats),
                "team2_wins": sum(s['team2_wins'] or 0 for s in h2h_stats),
                "no_results": sum(s['no_results'] or 0 for s in h2h_stats)
            }
            
            # Calculate overall percentages
            total_results = total_stats['matches_played'] - total_stats['no_results']
            if total_results > 0:
                total_stats['team1_win_percentage'] = round((total_stats['team1_wins'] / total_results) * 100, 2)
                total_stats['team2_win_percentage'] = round((total_stats['team2_wins'] / total_results) * 100, 2)
            else:
                total_stats['team1_win_percentage'] = 0
                total_stats['team2_win_percentage'] = 0
                
            h2h_stats.append(total_stats)
        
        cursor.close()
        conn.close()
        
        return {
            "head_to_head_statistics": h2h_stats,
            "total_records": len(results),
            "filters_applied": {
                "team1": team1,
                "team2": team2,
                "season": season if season else None
            }
        }
    
    except Exception as e:
        logger.error(f"Error retrieving head-to-head statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving head-to-head statistics: {str(e)}")

# ---------- PLAYER STATISTICS ENDPOINTS ---------- #

@router.get("/player-stats/{player_name}", response_model=Dict[str, Any],
           summary="Get player statistics",
           description="""
           Retrieve comprehensive statistics for a specific player.
           
           Path Parameters:
           - player_name: Name of the player (e.g., "Virat Kohli")
           
           Query Parameters:
           - season: Optional filter by season (e.g., "2023", "2007/08")
           - include_totals: Whether to include career totals across seasons
           
           Returns detailed batting and bowling statistics including
           runs scored, strike rates, bowling figures, and more.
           """)
async def get_player_stats(
    player_name: str = Path(..., description="Name of the player"),
    season: Optional[str] = Query(None, description="Filter by season (e.g., '2023', '2007/08')"),
    include_totals: bool = Query(True, description="Include career totals in response")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if player exists
        cursor.execute("SELECT player_id,player_name FROM players WHERE player_name = %s", (player_name,))
        player_result = cursor.fetchone()
        
        if not player_result:
            # If exact match not found, try partial match
            cursor.execute("SELECT player_id, player_name FROM players WHERE player_name ILIKE %s LIMIT 1", (f"%{player_name}%",))
            player_result = cursor.fetchone()
            
            if not player_result:
                raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found. Please check the name and try again.")
            
            # Use the found player name
            player_name = player_result["player_name"]
        
        player_id = player_result["player_id"]
        
        # Query for batting statistics
        batting_query = """
        SELECT 
            p.player_name,
            t.team_name,
            s.season_name,
            s.season_year,
            COUNT(DISTINCT d.match_id) as matches_played,
            COUNT(DISTINCT CASE WHEN d.batsman_id = p.player_id THEN d.inning_id END) as innings_batted,
            SUM(CASE WHEN d.batsman_id = p.player_id THEN d.batsman_runs ELSE 0 END) as runs_scored,
            COUNT(CASE WHEN d.batsman_id = p.player_id THEN 1 ELSE NULL END) as balls_faced,
            SUM(CASE WHEN d.batsman_id = p.player_id AND d.batsman_runs = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN d.batsman_id = p.player_id AND d.batsman_runs = 6 THEN 1 ELSE 0 END) as sixes,
            MAX(CASE WHEN d.batsman_id = p.player_id THEN 
                (SELECT SUM(d2.batsman_runs) 
                 FROM deliveries d2 
                 WHERE d2.batsman_id = p.player_id AND d2.inning_id = d.inning_id) 
            ELSE 0 END) as highest_score
        FROM 
            players p
            JOIN deliveries d ON p.player_id = d.batsman_id
            JOIN innings i ON d.inning_id = i.inning_id
            JOIN matches m ON i.match_id = m.match_id
            JOIN seasons s ON m.season_id = s.season_id
            JOIN teams t ON i.batting_team_id = t.team_id
        WHERE 
            p.player_id = %s
        """
        
        # Query for bowling statistics
        bowling_query = """
        SELECT 
            p.player_name,
            t.team_name,
            s.season_name,
            s.season_year,
            COUNT(DISTINCT d.match_id) as matches_played,
            COUNT(DISTINCT CASE WHEN d.bowler_id = p.player_id THEN d.inning_id END) as innings_bowled,
            COUNT(CASE WHEN d.bowler_id = p.player_id THEN 1 ELSE NULL END) as balls_bowled,
            SUM(CASE WHEN d.bowler_id = p.player_id THEN d.total_runs ELSE 0 END) as runs_conceded,
            SUM(CASE WHEN d.bowler_id = p.player_id AND d.is_wicket = TRUE AND 
                     d.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') 
                THEN 1 ELSE 0 END) as wickets,
            COUNT(DISTINCT CASE WHEN d.bowler_id = p.player_id AND 
                                (SELECT SUM(CASE WHEN d2.is_wicket = TRUE AND 
                                                  d2.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') 
                                            THEN 1 ELSE 0 END) 
                                FROM deliveries d2 
                                WHERE d2.bowler_id = p.player_id AND 
                                      d2.inning_id = d.inning_id AND 
                                      d2.match_id = d.match_id) >= 3 
                          THEN d.inning_id END) as three_plus_wickets,
            COUNT(DISTINCT CASE WHEN d.bowler_id = p.player_id AND 
                                (SELECT SUM(CASE WHEN d2.is_wicket = TRUE AND 
                                                  d2.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') 
                                            THEN 1 ELSE 0 END) 
                                FROM deliveries d2 
                                WHERE d2.bowler_id = p.player_id AND 
                                      d2.inning_id = d.inning_id AND 
                                      d2.match_id = d.match_id) >= 5 
                          THEN d.inning_id END) as five_plus_wickets
        FROM 
            players p
            JOIN deliveries d ON p.player_id = d.bowler_id
            JOIN innings i ON d.inning_id = i.inning_id
            JOIN matches m ON i.match_id = m.match_id
            JOIN seasons s ON m.season_id = s.season_id
            JOIN teams t ON i.bowling_team_id = t.team_id
        WHERE 
            p.player_id = %s
        """
        
        # Add season filter if provided
        params = [player_id]
        params_bowling = [player_id]
        if season:
            batting_query += " AND s.season_name = %s"
            bowling_query += " AND s.season_name = %s"
            params.append(season)
            params_bowling.append(season)
        
        # Group by season and team
        batting_query += " GROUP BY p.player_name, t.team_name, s.season_name, s.season_year ORDER BY s.season_year DESC, t.team_name"
        bowling_query += " GROUP BY p.player_name, t.team_name, s.season_name, s.season_year ORDER BY s.season_year DESC, t.team_name"
        
        # Execute queries
        cursor.execute(batting_query, params)
        batting_results = cursor.fetchall()
        
        cursor.execute(bowling_query, params_bowling)
        bowling_results = cursor.fetchall()
        
        # Process batting statistics
        batting_stats = []
        for row in batting_results:
            stats = dict(row)
            
            # Calculate additional metrics
            if stats['balls_faced'] and stats['balls_faced'] > 0:
                stats['strike_rate'] = round((stats['runs_scored'] / stats['balls_faced']) * 100, 2)
            else:
                stats['strike_rate'] = 0
            
            # Calculate batting average (We don't have not_outs directly)
            if stats['innings_batted'] and stats['innings_batted'] > 0:
                stats['batting_average'] = round(stats['runs_scored'] / stats['innings_batted'], 2)
            else:
                stats['batting_average'] = 0
                
            # Calculate boundaries percentage
            if stats['balls_faced'] and stats['balls_faced'] > 0:
                boundaries = (stats['fours'] or 0) + (stats['sixes'] or 0)
                stats['boundary_percentage'] = round((boundaries / stats['balls_faced']) * 100, 2)
            else:
                stats['boundary_percentage'] = 0
                
            batting_stats.append(stats)
        
        # Process bowling statistics
        bowling_stats = []
        for row in bowling_results:
            stats = dict(row)
            
            # Calculate additional metrics
            if stats['balls_bowled'] and stats['balls_bowled'] > 0:
                overs = stats['balls_bowled'] // 6 + (stats['balls_bowled'] % 6) / 10
                stats['overs'] = round(overs, 1)
                stats['economy'] = round(stats['runs_conceded'] / overs, 2)
            else:
                stats['overs'] = 0
                stats['economy'] = 0
                
            if stats['wickets'] and stats['wickets'] > 0:
                stats['bowling_average'] = round(stats['runs_conceded'] / stats['wickets'], 2)
                stats['bowling_strike_rate'] = round(stats['balls_bowled'] / stats['wickets'], 2)
            else:
                stats['bowling_average'] = 0
                stats['bowling_strike_rate'] = 0
                
            bowling_stats.append(stats)
        
        # Calculate career totals if requested
        if include_totals and (len(batting_stats) > 1 or len(bowling_stats) > 1):
            # Batting career totals
            if batting_stats:
                batting_totals = {
                    "player_name": player_name,
                    "team_name": "All Teams",
                    "season_name": "Career",
                    "season_year": None,
                    "matches_played": max(sum(b['matches_played'] or 0 for b in batting_stats) // len(set(b['team_name'] for b in batting_stats)), 
                                      len(set(f"{b['season_name']}_{b['team_name']}" for b in batting_stats))),
                    "innings_batted": sum(b['innings_batted'] or 0 for b in batting_stats),
                    "runs_scored": sum(b['runs_scored'] or 0 for b in batting_stats),
                    "balls_faced": sum(b['balls_faced'] or 0 for b in batting_stats),
                    "fours": sum(b['fours'] or 0 for b in batting_stats),
                    "sixes": sum(b['sixes'] or 0 for b in batting_stats),
                    "highest_score": max(b['highest_score'] or 0 for b in batting_stats)
                }
                
                # Calculate derived stats
                if batting_totals['balls_faced'] > 0:
                    batting_totals['strike_rate'] = round((batting_totals['runs_scored'] / batting_totals['balls_faced']) * 100, 2)
                else:
                    batting_totals['strike_rate'] = 0
                    
                if batting_totals['innings_batted'] > 0:
                    batting_totals['batting_average'] = round(batting_totals['runs_scored'] / batting_totals['innings_batted'], 2)
                else:
                    batting_totals['batting_average'] = 0
                    
                if batting_totals['balls_faced'] > 0:
                    boundaries = batting_totals['fours'] + batting_totals['sixes']
                    batting_totals['boundary_percentage'] = round((boundaries / batting_totals['balls_faced']) * 100, 2)
                else:
                    batting_totals['boundary_percentage'] = 0
                    
                batting_stats.append(batting_totals)
                
            # Bowling career totals
            if bowling_stats:
                bowling_totals = {
                    "player_name": player_name,
                    "team_name": "All Teams",
                    "season_name": "Career",
                    "season_year": None,
                    "matches_played": max(sum(b['matches_played'] or 0 for b in bowling_stats) // len(set(b['team_name'] for b in bowling_stats)), 
                                      len(set(f"{b['season_name']}_{b['team_name']}" for b in bowling_stats))),
                    "innings_bowled": sum(b['innings_bowled'] or 0 for b in bowling_stats),
                    "balls_bowled": sum(b['balls_bowled'] or 0 for b in bowling_stats),
                    "runs_conceded": sum(b['runs_conceded'] or 0 for b in bowling_stats),
                    "wickets": sum(b['wickets'] or 0 for b in bowling_stats),
                    "three_plus_wickets": sum(b['three_plus_wickets'] or 0 for b in bowling_stats),
                    "five_plus_wickets": sum(b['five_plus_wickets'] or 0 for b in bowling_stats)
                }
                
                # Calculate derived stats
                if bowling_totals['balls_bowled'] > 0:
                    overs = bowling_totals['balls_bowled'] // 6 + (bowling_totals['balls_bowled'] % 6) / 10
                    bowling_totals['overs'] = round(overs, 1)
                    bowling_totals['economy'] = round(bowling_totals['runs_conceded'] / overs, 2)
                else:
                    bowling_totals['overs'] = 0
                    bowling_totals['economy'] = 0
                    
                if bowling_totals['wickets'] > 0:
                    bowling_totals['bowling_average'] = round(bowling_totals['runs_conceded'] / bowling_totals['wickets'], 2)
                    bowling_totals['bowling_strike_rate'] = round(bowling_totals['balls_bowled'] / bowling_totals['wickets'], 2)
                else:
                    bowling_totals['bowling_average'] = 0
                    bowling_totals['bowling_strike_rate'] = 0
                    
                bowling_stats.append(bowling_totals)
        
        cursor.close()
        conn.close()
        
        return {
            "player_name": player_name,
            "batting_statistics": batting_stats,
            "bowling_statistics": bowling_stats,
            "total_seasons_played": len(set(b['season_name'] for b in batting_stats if b['season_name'] != "Career")) if batting_stats else 
                                   len(set(b['season_name'] for b in bowling_stats if b['season_name'] != "Career")),
            "filters_applied": {
                "season": season if season else None
            }
        }
    
    except Exception as e:
        logger.error(f"Error retrieving player statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving player statistics: {str(e)}")


# ---------- TEAMS LIST ENDPOINT ---------- #

@router.get("/teams", response_model=Dict[str, Any],
          summary="Get list of all teams",
          description="Returns a list of all teams in the IPL from 2008 to present.")
async def get_teams():
    """
    Get list of all teams
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT t.team_id, t.team_name, t.team_short_name, 
               COUNT(DISTINCT m.match_id) as matches_played,
               COUNT(DISTINCT s.season_id) as seasons_played,
               MIN(s.season_year) as first_season,
               MAX(s.season_year) as last_season
        FROM teams t
        LEFT JOIN matches m ON t.team_id = m.team1_id OR t.team_id = m.team2_id
        LEFT JOIN seasons s ON m.season_id = s.season_id
        GROUP BY t.team_id, t.team_name, t.team_short_name
        ORDER BY t.team_name
        """)
        results = cursor.fetchall()
        
        teams = [dict(row) for row in results]
        
        cursor.close()
        conn.close()
        
        return {
            "teams": teams,
            "total_teams": len(teams),
            "current_teams": len([t for t in teams if t.get('last_season') and t['last_season'] >= 2023])
        }
    
    except Exception as e:
        logger.error(f"Error retrieving teams: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving teams: {str(e)}")


# ---------- SEASONS LIST ENDPOINT ---------- #

@router.get("/seasons", response_model=Dict[str, Any],
          summary="Get list of all seasons",
          description="Returns a list of all IPL seasons from 2008 to present with basic stats.")
async def get_seasons():
    """
    Get list of all seasons
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT s.season_id, s.season_name, s.season_year, 
               COUNT(DISTINCT m.match_id) as matches_played,
               COUNT(DISTINCT m.venue_id) as venues_used,
               COUNT(DISTINCT t1.team_id) as teams_participated
        FROM seasons s
        LEFT JOIN matches m ON s.season_id = m.season_id
        LEFT JOIN teams t1 ON m.team1_id = t1.team_id
        GROUP BY s.season_id, s.season_name, s.season_year
        ORDER BY s.season_year DESC
        """)
        results = cursor.fetchall()
        
        seasons = [dict(row) for row in results]
        
        cursor.close()
        conn.close()
        
        return {
            "seasons": seasons,
            "total_seasons": len(seasons),
            "total_matches": sum(s['matches_played'] for s in seasons)
        }
    
    except Exception as e:
        logger.error(f"Error retrieving seasons: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving seasons: {str(e)}")


# ---------- VENUES LIST ENDPOINT ---------- #

@router.get("/venues", response_model=Dict[str, Any],
          summary="Get list of all venues",
          description="Returns a list of all venues used in the IPL from 2008 to present with basic stats.")
async def get_venues():
    """
    Get list of all venues
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT v.venue_id, v.venue_name, v.city, 
               COUNT(DISTINCT m.match_id) as matches_hosted,
               COUNT(DISTINCT s.season_id) as seasons_used,
               MIN(s.season_year) as first_season,
               MAX(s.season_year) as last_season
        FROM venues v
        LEFT JOIN matches m ON v.venue_id = m.venue_id
        LEFT JOIN seasons s ON m.season_id = s.season_id
        GROUP BY v.venue_id, v.venue_name, v.city
        ORDER BY matches_hosted DESC
        """)
        results = cursor.fetchall()
        
        venues = [dict(row) for row in results]
        
        cursor.close()
        conn.close()
        
        return {
            "venues": venues,
            "total_venues": len(venues),
            "total_cities": len(set(v['city'] for v in venues if v['city']))
        }
    
    except Exception as e:
        logger.error(f"Error retrieving venues: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving venues: {str(e)}")


# ---------- PLAYERS SEARCH ENDPOINT ---------- #

@router.get("/players/search", response_model=Dict[str, Any],
           summary="Search for players by name",
           description="""
           Search for players by name (partial match).
           
           Parameters:
           - query: Search string (partial player name)
           - limit: Maximum number of results to return (default: 10)
           
           Returns a list of matching players with their IDs.
           """)
async def search_players(
    query: str = Query(..., min_length=2, description="Search string (partial player name)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return")
):
    """
    Search for players by name
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        search_query = f"%{query}%"
        cursor.execute("""
        SELECT 
            p.player_id, 
            p.player_name,
            COUNT(DISTINCT m.match_id) as matches_played,
            CASE WHEN COUNT(DISTINCT CASE WHEN d.batsman_id = p.player_id THEN d.match_id END) > 0 THEN true ELSE false END as is_batsman,
            CASE WHEN COUNT(DISTINCT CASE WHEN d.bowler_id = p.player_id THEN d.match_id END) > 0 THEN true ELSE false END as is_bowler
        FROM 
            players p
            LEFT JOIN deliveries d ON p.player_id = d.batsman_id OR p.player_id = d.bowler_id
            LEFT JOIN innings i ON d.inning_id = i.inning_id
            LEFT JOIN matches m ON i.match_id = m.match_id
        WHERE 
            p.player_name ILIKE %s
        GROUP BY 
            p.player_id, p.player_name
        ORDER BY 
            matches_played DESC, p.player_name
        LIMIT %s
        """, (search_query, limit))
        
        results = cursor.fetchall()
        
        players = [dict(row) for row in results]
        
        cursor.close()
        conn.close()
        
        return {
            "players": players,
            "total_found": len(players),
            "search_query": query
        }
    
    except Exception as e:
        logger.error(f"Error searching players: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching players: {str(e)}")


# ---------- MATCH DETAILS ENDPOINT ---------- #

@router.get("/match/{match_id}", response_model=Dict[str, Any],
         summary="Get detailed information for a specific match",
         description="""
         Retrieve comprehensive details for a specific match including 
         team information, player performances, and ball-by-ball data.
         
         Path Parameters:
         - match_id: ID of the match to retrieve
         
         Returns full match details including scorecard and player performances.
         """)
async def get_match_details(
    match_id: int = Path(..., description="ID of the match to retrieve")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get basic match info
        cursor.execute("""
        SELECT 
            m.match_id, m.match_date, s.season_name, v.venue_name, v.city,
            t1.team_name as team1_name, t2.team_name as team2_name,
            tw.team_name as toss_winner_name, m.toss_decision,
            w.team_name as winner_name, m.result, m.result_margin,
            p.player_name as player_of_match
        FROM 
            matches m
            JOIN seasons s ON m.season_id = s.season_id
            JOIN venues v ON m.venue_id = v.venue_id
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            LEFT JOIN teams tw ON m.toss_winner_id = tw.team_id
            LEFT JOIN teams w ON m.winner_id = w.team_id
            LEFT JOIN players p ON m.player_of_match_id = p.player_id
        WHERE 
            m.match_id = %s
        """, (match_id,))
        
        match_info = cursor.fetchone()
        
        if not match_info:
            raise HTTPException(status_code=404, detail=f"Match with ID {match_id} not found")
        
        match_info = dict(match_info)
        
        # Get innings data
        cursor.execute("""
        SELECT 
            i.inning_id, i.inning_number, 
            t1.team_name as batting_team, t2.team_name as bowling_team,
            i.total_runs, i.total_wickets, i.total_overs, i.extras
        FROM 
            innings i
            JOIN teams t1 ON i.batting_team_id = t1.team_id
            JOIN teams t2 ON i.bowling_team_id = t2.team_id
        WHERE 
            i.match_id = %s
        ORDER BY 
            i.inning_number
        """, (match_id,))
        
        innings_data = [dict(row) for row in cursor.fetchall()]
        
        # Get batting performances for each innings
        batting_performances = []
        bowling_performances = []
        
        for inning in innings_data:
            inning_id = inning['inning_id']
            
            # Batting performances
            cursor.execute("""
            WITH player_balls AS (
                SELECT 
                    d.batsman_id,
                    SUM(d.batsman_runs) as runs,
                    COUNT(*) as balls,
                    SUM(CASE WHEN d.batsman_runs = 4 THEN 1 ELSE 0 END) as fours,
                    SUM(CASE WHEN d.batsman_runs = 6 THEN 1 ELSE 0 END) as sixes,
                    MAX(CASE WHEN d.is_wicket AND 
                             d.player_dismissed_id = d.batsman_id 
                             THEN d.dismissal_kind ELSE NULL END) as dismissal_kind,
                    MAX(CASE WHEN d.is_wicket AND 
                             d.player_dismissed_id = d.batsman_id AND
                             d.fielder_id IS NOT NULL
                             THEN p_f.player_name ELSE NULL END) as fielder_name,
                    MAX(CASE WHEN d.is_wicket AND 
                             d.player_dismissed_id = d.batsman_id
                             THEN p_b.player_name ELSE NULL END) as bowler_name
                FROM 
                    deliveries d
                    LEFT JOIN players p_f ON d.fielder_id = p_f.player_id
                    LEFT JOIN players p_b ON d.bowler_id = p_b.player_id
                WHERE 
                    d.inning_id = %s
                GROUP BY 
                    d.batsman_id
            )
            SELECT 
                p.player_name,
                pb.runs,
                pb.balls,
                pb.fours,
                pb.sixes,
                CASE WHEN pb.dismissal_kind IS NULL THEN 'not out' ELSE pb.dismissal_kind END as dismissal,
                pb.fielder_name,
                pb.bowler_name,
                CASE WHEN pb.balls > 0 THEN ROUND((pb.runs::float / pb.balls) * 100, 2) ELSE 0 END as strike_rate
            FROM 
                player_balls pb
                JOIN players p ON pb.batsman_id = p.player_id
            ORDER BY 
                pb.runs DESC, pb.balls
            """, (inning_id,))
            
            inning_batting = [dict(row) for row in cursor.fetchall()]
            for batsman in inning_batting:
                batsman['inning_number'] = inning['inning_number']
                batsman['batting_team'] = inning['batting_team']
            
            batting_performances.extend(inning_batting)
            
            # Bowling performances
            cursor.execute("""
            WITH bowler_stats AS (
                SELECT 
                    d.bowler_id,
                    COUNT(*) as balls,
                    SUM(d.total_runs) as runs,
                    SUM(CASE WHEN d.is_wicket AND 
                              d.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field')
                              THEN 1 ELSE 0 END) as wickets,
                    SUM(CASE WHEN d.extras_type = 'wides' THEN 1 ELSE 0 END) as wides,
                    SUM(CASE WHEN d.extras_type = 'noballs' THEN 1 ELSE 0 END) as noballs
                FROM 
                    deliveries d
                WHERE 
                    d.inning_id = %s
                GROUP BY 
                    d.bowler_id
            )
            SELECT 
                p.player_name,
                bs.balls,
                FLOOR(bs.balls / 6) || '.' || (bs.balls %% 6) as overs,
                bs.runs,
                bs.wickets,
                bs.wides,
                bs.noballs,
                CASE WHEN FLOOR(bs.balls / 6) > 0 THEN 
                    ROUND((bs.runs::float / (FLOOR(bs.balls / 6) + (bs.balls %% 6)/10)), 2)
                ELSE 0 END as economy
            FROM 
                bowler_stats bs
                JOIN players p ON bs.bowler_id = p.player_id
            ORDER BY 
                bs.wickets DESC, bs.runs
            """, (inning_id,))
            
            inning_bowling = [dict(row) for row in cursor.fetchall()]
            for bowler in inning_bowling:
                bowler['inning_number'] = inning['inning_number']
                bowler['bowling_team'] = inning['bowling_team']
            
            bowling_performances.extend(inning_bowling)
        
        cursor.close()
        conn.close()
        
        return {
            "match_info": match_info,
            "innings": innings_data,
            "batting_performances": batting_performances,
            "bowling_performances": bowling_performances
        }
    
    except Exception as e:
        logger.error(f"Error retrieving match details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving tournament summary: {str(e)}")


# ---------- PLAYER STATISTICS ENDPOINTS ---------- #

@router.get("/player-stats/{player_name}", response_model=Dict[str, Any],
           summary="Get player statistics",
           description="""
           Retrieve comprehensive statistics for a specific player.
           
           Path Parameters:
           - player_name: Name of the player (e.g., "Virat Kohli")
           
           Query Parameters:
           - season: Optional filter by season (e.g., "2023", "2007/08")
           - include_totals: Whether to include career totals across seasons
           
           Returns detailed batting and bowling statistics including
           runs scored, strike rates, bowling figures, and more.
           """)
async def get_player_stats(
    player_name: str = Path(..., description="Name of the player"),
    season: Optional[str] = Query(None, description="Filter by season (e.g., '2023', '2007/08')"),
    include_totals: bool = Query(True, description="Include career totals in response")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if player exists
        cursor.execute("SELECT player_id FROM players WHERE player_name = %s", (player_name,))
        player_result = cursor.fetchone()
        
        if not player_result:
            # If exact match not found, try partial match
            cursor.execute("SELECT player_id, player_name FROM players WHERE player_name ILIKE %s LIMIT 1", (f"%{player_name}%",))
            player_result = cursor.fetchone()
            
            if not player_result:
                raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found. Please check the name and try again.")
            
            # Use the found player name
            player_name = player_result["player_name"]
        
        player_id = player_result["player_id"]
        
        # Query for batting statistics
        batting_query = """
        SELECT 
            p.player_name,
            t.team_name,
            s.season_name,
            s.season_year,
            COUNT(DISTINCT d.match_id) as matches_played,
            COUNT(DISTINCT CASE WHEN d.batsman_id = p.player_id THEN d.inning_id END) as innings_batted,
            SUM(CASE WHEN d.batsman_id = p.player_id THEN d.batsman_runs ELSE 0 END) as runs_scored,
            COUNT(CASE WHEN d.batsman_id = p.player_id THEN 1 ELSE NULL END) as balls_faced,
            SUM(CASE WHEN d.batsman_id = p.player_id AND d.batsman_runs = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN d.batsman_id = p.player_id AND d.batsman_runs = 6 THEN 1 ELSE 0 END) as sixes,
            MAX(CASE WHEN d.batsman_id = p.player_id THEN 
                (SELECT SUM(d2.batsman_runs) 
                 FROM deliveries d2 
                 WHERE d2.batsman_id = p.player_id AND d2.inning_id = d.inning_id) 
            ELSE 0 END) as highest_score
        FROM 
            players p
            JOIN deliveries d ON p.player_id = d.batsman_id
            JOIN innings i ON d.inning_id = i.inning_id
            JOIN matches m ON i.match_id = m.match_id
            JOIN seasons s ON m.season_id = s.season_id
            JOIN teams t ON i.batting_team_id = t.team_id
        WHERE 
            p.player_id = %s
        """
        
        # Query for bowling statistics
        bowling_query = """
        SELECT 
            p.player_name,
            t.team_name,
            s.season_name,
            s.season_year,
            COUNT(DISTINCT d.match_id) as matches_played,
            COUNT(DISTINCT CASE WHEN d.bowler_id = p.player_id THEN d.inning_id END) as innings_bowled,
            COUNT(CASE WHEN d.bowler_id = p.player_id THEN 1 ELSE NULL END) as balls_bowled,
            SUM(CASE WHEN d.bowler_id = p.player_id THEN d.total_runs ELSE 0 END) as runs_conceded,
            SUM(CASE WHEN d.bowler_id = p.player_id AND d.is_wicket = TRUE AND 
                     d.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') 
                THEN 1 ELSE 0 END) as wickets,
            COUNT(DISTINCT CASE WHEN d.bowler_id = p.player_id AND 
                                (SELECT SUM(CASE WHEN d2.is_wicket = TRUE AND 
                                                  d2.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') 
                                            THEN 1 ELSE 0 END) 
                                FROM deliveries d2 
                                WHERE d2.bowler_id = p.player_id AND 
                                      d2.inning_id = d.inning_id AND 
                                      d2.match_id = d.match_id) >= 3 
                          THEN d.inning_id END) as three_plus_wickets,
            COUNT(DISTINCT CASE WHEN d.bowler_id = p.player_id AND 
                                (SELECT SUM(CASE WHEN d2.is_wicket = TRUE AND 
                                                  d2.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') 
                                            THEN 1 ELSE 0 END) 
                                FROM deliveries d2 
                                WHERE d2.bowler_id = p.player_id AND 
                                      d2.inning_id = d.inning_id AND 
                                      d2.match_id = d.match_id) >= 5 
                          THEN d.inning_id END) as five_plus_wickets
        FROM 
            players p
            JOIN deliveries d ON p.player_id = d.bowler_id
            JOIN innings i ON d.inning_id = i.inning_id
            JOIN matches m ON i.match_id = m.match_id
            JOIN seasons s ON m.season_id = s.season_id
            JOIN teams t ON i.bowling_team_id = t.team_id
        WHERE 
            p.player_id = %s
        """
        
        # Add season filter if provided
        params = [player_id]
        params_bowling = [player_id]
        if season:
            batting_query += " AND s.season_name = %s"
            bowling_query += " AND s.season_name = %s"
            params.append(season)
            params_bowling.append(season)
        
        # Group by season and team
        batting_query += " GROUP BY p.player_name, t.team_name, s.season_name, s.season_year ORDER BY s.season_year DESC, t.team_name"
        bowling_query += " GROUP BY p.player_name, t.team_name, s.season_name, s.season_year ORDER BY s.season_year DESC, t.team_name"
        
        # Execute queries
        cursor.execute(batting_query, params)
        batting_results = cursor.fetchall()
        
        cursor.execute(bowling_query, params_bowling)
        bowling_results = cursor.fetchall()
        
        # Process batting statistics
        batting_stats = []
        for row in batting_results:
            stats = dict(row)
            
            # Calculate additional metrics
            if stats['balls_faced'] and stats['balls_faced'] > 0:
                stats['strike_rate'] = round((stats['runs_scored'] / stats['balls_faced']) * 100, 2)
            else:
                stats['strike_rate'] = 0
            
            # Calculate batting average (We don't have not_outs directly)
            if stats['innings_batted'] and stats['innings_batted'] > 0:
                stats['batting_average'] = round(stats['runs_scored'] / stats['innings_batted'], 2)
            else:
                stats['batting_average'] = 0
                
            # Calculate boundaries percentage
            if stats['balls_faced'] and stats['balls_faced'] > 0:
                boundaries = (stats['fours'] or 0) + (stats['sixes'] or 0)
                stats['boundary_percentage'] = round((boundaries / stats['balls_faced']) * 100, 2)
            else:
                stats['boundary_percentage'] = 0
                
            batting_stats.append(stats)
        
        # Process bowling statistics
        bowling_stats = []
        for row in bowling_results:
            stats = dict(row)
            
            # Calculate additional metrics
            if stats['balls_bowled'] and stats['balls_bowled'] > 0:
                overs = stats['balls_bowled'] // 6 + (stats['balls_bowled'] % 6) / 10
                stats['overs'] = round(overs, 1)
                stats['economy'] = round(stats['runs_conceded'] / overs, 2)
            else:
                stats['overs'] = 0
                stats['economy'] = 0
                
            if stats['wickets'] and stats['wickets'] > 0:
                stats['bowling_average'] = round(stats['runs_conceded'] / stats['wickets'], 2)
                stats['bowling_strike_rate'] = round(stats['balls_bowled'] / stats['wickets'], 2)
            else:
                stats['bowling_average'] = 0
                stats['bowling_strike_rate'] = 0
                
            bowling_stats.append(stats)
        
        # Calculate career totals if requested
        if include_totals and (len(batting_stats) > 1 or len(bowling_stats) > 1):
            # Batting career totals
            if batting_stats:
                batting_totals = {
                    "player_name": player_name,
                    "team_name": "All Teams",
                    "season_name": "Career",
                    "season_year": None,
                    "matches_played": max(sum(b['matches_played'] or 0 for b in batting_stats) // len(set(b['team_name'] for b in batting_stats)), 
                                      len(set(f"{b['season_name']}_{b['team_name']}" for b in batting_stats))),
                    "innings_batted": sum(b['innings_batted'] or 0 for b in batting_stats),
                    "runs_scored": sum(b['runs_scored'] or 0 for b in batting_stats),
                    "balls_faced": sum(b['balls_faced'] or 0 for b in batting_stats),
                    "fours": sum(b['fours'] or 0 for b in batting_stats),
                    "sixes": sum(b['sixes'] or 0 for b in batting_stats),
                    "highest_score": max(b['highest_score'] or 0 for b in batting_stats)
                }
                
                # Calculate derived stats
                if batting_totals['balls_faced'] > 0:
                    batting_totals['strike_rate'] = round((batting_totals['runs_scored'] / batting_totals['balls_faced']) * 100, 2)
                else:
                    batting_totals['strike_rate'] = 0
                    
                if batting_totals['innings_batted'] > 0:
                    batting_totals['batting_average'] = round(batting_totals['runs_scored'] / batting_totals['innings_batted'], 2)
                else:
                    batting_totals['batting_average'] = 0
                    
                if batting_totals['balls_faced'] > 0:
                    boundaries = batting_totals['fours'] + batting_totals['sixes']
                    batting_totals['boundary_percentage'] = round((boundaries / batting_totals['balls_faced']) * 100, 2)
                else:
                    batting_totals['boundary_percentage'] = 0
                    
                batting_stats.append(batting_totals)
                
            # Bowling career totals
            if bowling_stats:
                bowling_totals = {
                    "player_name": player_name,
                    "team_name": "All Teams",
                    "season_name": "Career",
                    "season_year": None,
                    "matches_played": max(sum(b['matches_played'] or 0 for b in bowling_stats) // len(set(b['team_name'] for b in bowling_stats)), 
                                      len(set(f"{b['season_name']}_{b['team_name']}" for b in bowling_stats))),
                    "innings_bowled": sum(b['innings_bowled'] or 0 for b in bowling_stats),
                    "balls_bowled": sum(b['balls_bowled'] or 0 for b in bowling_stats),
                    "runs_conceded": sum(b['runs_conceded'] or 0 for b in bowling_stats),
                    "wickets": sum(b['wickets'] or 0 for b in bowling_stats),
                    "three_plus_wickets": sum(b['three_plus_wickets'] or 0 for b in bowling_stats),
                    "five_plus_wickets": sum(b['five_plus_wickets'] or 0 for b in bowling_stats)
                }
                
                # Calculate derived stats
                if bowling_totals['balls_bowled'] > 0:
                    overs = bowling_totals['balls_bowled'] // 6 + (bowling_totals['balls_bowled'] % 6) / 10
                    bowling_totals['overs'] = round(overs, 1)
                    bowling_totals['economy'] = round(bowling_totals['runs_conceded'] / overs, 2)
                else:
                    bowling_totals['overs'] = 0
                    bowling_totals['economy'] = 0
                    
                if bowling_totals['wickets'] > 0:
                    bowling_totals['bowling_average'] = round(bowling_totals['runs_conceded'] / bowling_totals['wickets'], 2)
                    bowling_totals['bowling_strike_rate'] = round(bowling_totals['balls_bowled'] / bowling_totals['wickets'], 2)
                else:
                    bowling_totals['bowling_average'] = 0
                    bowling_totals['bowling_strike_rate'] = 0
                    
                bowling_stats.append(bowling_totals)
        
        cursor.close()
        conn.close()
        
        return {
            "player_name": player_name,
            "batting_statistics": batting_stats,
            "bowling_statistics": bowling_stats,
            "total_seasons_played": len(set(b['season_name'] for b in batting_stats if b['season_name'] != "Career")) if batting_stats else 
                                   len(set(b['season_name'] for b in bowling_stats if b['season_name'] != "Career")),
            "filters_applied": {
                "season": season if season else None
            }
        }
    
    except Exception as e:
        logger.error(f"Error retrieving player statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving player statistics: {str(e)}")


# ---------- TEAMS LIST ENDPOINT ---------- #

@router.get("/teams", response_model=Dict[str, Any],
          summary="Get list of all teams",
          description="Returns a list of all teams in the IPL from 2008 to present.")
async def get_teams():
    """
    Get list of all teams
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT t.team_id, t.team_name, t.team_short_name, 
               COUNT(DISTINCT m.match_id) as matches_played,
               COUNT(DISTINCT s.season_id) as seasons_played,
               MIN(s.season_year) as first_season,
               MAX(s.season_year) as last_season
        FROM teams t
        LEFT JOIN matches m ON t.team_id = m.team1_id OR t.team_id = m.team2_id
        LEFT JOIN seasons s ON m.season_id = s.season_id
        GROUP BY t.team_id, t.team_name, t.team_short_name
        ORDER BY t.team_name
        """)
        results = cursor.fetchall()
        
        teams = [dict(row) for row in results]
        
        cursor.close()
        conn.close()
        
        return {
            "teams": teams,
            "total_teams": len(teams),
            "current_teams": len([t for t in teams if t.get('last_season') and t['last_season'] >= 2023])
        }
    
    except Exception as e:
        logger.error(f"Error retrieving teams: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving teams: {str(e)}")


# ---------- SEASONS LIST ENDPOINT ---------- #

@router.get("/seasons", response_model=Dict[str, Any],
          summary="Get list of all seasons",
          description="Returns a list of all IPL seasons from 2008 to present with basic stats.")
async def get_seasons():
    """
    Get list of all seasons
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT s.season_id, s.season_name, s.season_year, 
               COUNT(DISTINCT m.match_id) as matches_played,
               COUNT(DISTINCT m.venue_id) as venues_used,
               COUNT(DISTINCT t1.team_id) as teams_participated
        FROM seasons s
        LEFT JOIN matches m ON s.season_id = m.season_id
        LEFT JOIN teams t1 ON m.team1_id = t1.team_id
        GROUP BY s.season_id, s.season_name, s.season_year
        ORDER BY s.season_year DESC
        """)
        results = cursor.fetchall()
        
        seasons = [dict(row) for row in results]
        
        cursor.close()
        conn.close()
        
        return {
            "seasons": seasons,
            "total_seasons": len(seasons),
            "total_matches": sum(s['matches_played'] for s in seasons)
        }
    
    except Exception as e:
        logger.error(f"Error retrieving seasons: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving seasons: {str(e)}")


# ---------- VENUES LIST ENDPOINT ---------- #

@router.get("/venues", response_model=Dict[str, Any],
          summary="Get list of all venues",
          description="Returns a list of all venues used in the IPL from 2008 to present with basic stats.")
async def get_venues():
    """
    Get list of all venues
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT v.venue_id, v.venue_name, v.city, 
               COUNT(DISTINCT m.match_id) as matches_hosted,
               COUNT(DISTINCT s.season_id) as seasons_used,
               MIN(s.season_year) as first_season,
               MAX(s.season_year) as last_season
        FROM venues v
        LEFT JOIN matches m ON v.venue_id = m.venue_id
        LEFT JOIN seasons s ON m.season_id = s.season_id
        GROUP BY v.venue_id, v.venue_name, v.city
        ORDER BY matches_hosted DESC
        """)
        results = cursor.fetchall()
        
        venues = [dict(row) for row in results]
        
        cursor.close()
        conn.close()
        
        return {
            "venues": venues,
            "total_venues": len(venues),
            "total_cities": len(set(v['city'] for v in venues if v['city']))
        }
    
    except Exception as e:
        logger.error(f"Error retrieving venues: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving venues: {str(e)}")


# ---------- PLAYERS SEARCH ENDPOINT ---------- #

@router.get("/players/search", response_model=Dict[str, Any],
           summary="Search for players by name",
           description="""
           Search for players by name (partial match).
           
           Parameters:
           - query: Search string (partial player name)
           - limit: Maximum number of results to return (default: 10)
           
           Returns a list of matching players with their IDs.
           """)
async def search_players(
    query: str = Query(..., min_length=2, description="Search string (partial player name)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return")
):
    """
    Search for players by name
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        search_query = f"%{query}%"
        cursor.execute("""
        SELECT 
            p.player_id, 
            p.player_name,
            COUNT(DISTINCT m.match_id) as matches_played,
            CASE WHEN COUNT(DISTINCT CASE WHEN d.batsman_id = p.player_id THEN d.match_id END) > 0 THEN true ELSE false END as is_batsman,
            CASE WHEN COUNT(DISTINCT CASE WHEN d.bowler_id = p.player_id THEN d.match_id END) > 0 THEN true ELSE false END as is_bowler
        FROM 
            players p
            LEFT JOIN deliveries d ON p.player_id = d.batsman_id OR p.player_id = d.bowler_id
            LEFT JOIN innings i ON d.inning_id = i.inning_id
            LEFT JOIN matches m ON i.match_id = m.match_id
        WHERE 
            p.player_name ILIKE %s
        GROUP BY 
            p.player_id, p.player_name
        ORDER BY 
            matches_played DESC, p.player_name
        LIMIT %s
        """, (search_query, limit))
        
        results = cursor.fetchall()
        
        players = [dict(row) for row in results]
        
        cursor.close()
        conn.close()
        
        return {
            "players": players,
            "total_found": len(players),
            "search_query": query
        }
    
    except Exception as e:
        logger.error(f"Error searching players: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching players: {str(e)}")


# ---------- MATCH DETAILS ENDPOINT ---------- #

@router.get("/match/{match_id}", response_model=Dict[str, Any],
         summary="Get detailed information for a specific match",
         description="""
         Retrieve comprehensive details for a specific match including 
         team information, player performances, and ball-by-ball data.
         
         Path Parameters:
         - match_id: ID of the match to retrieve
         
         Returns full match details including scorecard and player performances.
         """)
async def get_match_details(
    match_id: int = Path(..., description="ID of the match to retrieve")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get basic match info
        cursor.execute("""
        SELECT 
            m.match_id, m.match_date, s.season_name, v.venue_name, v.city,
            t1.team_name as team1_name, t2.team_name as team2_name,
            tw.team_name as toss_winner_name, m.toss_decision,
            w.team_name as winner_name, m.result, m.result_margin,
            p.player_name as player_of_match
        FROM 
            matches m
            JOIN seasons s ON m.season_id = s.season_id
            JOIN venues v ON m.venue_id = v.venue_id
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            LEFT JOIN teams tw ON m.toss_winner_id = tw.team_id
            LEFT JOIN teams w ON m.winner_id = w.team_id
            LEFT JOIN players p ON m.player_of_match_id = p.player_id
        WHERE 
            m.match_id = %s
        """, (match_id,))
        
        match_info = cursor.fetchone()
        
        if not match_info:
            raise HTTPException(status_code=404, detail=f"Match with ID {match_id} not found")
        
        match_info = dict(match_info)
        
        # Get innings data
        cursor.execute("""
        SELECT 
            i.inning_id, i.inning_number, 
            t1.team_name as batting_team, t2.team_name as bowling_team,
            i.total_runs, i.total_wickets, i.total_overs, i.extras
        FROM 
            innings i
            JOIN teams t1 ON i.batting_team_id = t1.team_id
            JOIN teams t2 ON i.bowling_team_id = t2.team_id
        WHERE 
            i.match_id = %s
        ORDER BY 
            i.inning_number
        """, (match_id,))
        
        innings_data = [dict(row) for row in cursor.fetchall()]
        
        # Get batting performances for each innings
        batting_performances = []
        bowling_performances = []
        
        for inning in innings_data:
            inning_id = inning['inning_id']
            
            # Batting performances
            cursor.execute("""
            WITH player_balls AS (
                SELECT 
                    d.batsman_id,
                    SUM(d.batsman_runs) as runs,
                    COUNT(*) as balls,
                    SUM(CASE WHEN d.batsman_runs = 4 THEN 1 ELSE 0 END) as fours,
                    SUM(CASE WHEN d.batsman_runs = 6 THEN 1 ELSE 0 END) as sixes,
                    MAX(CASE WHEN d.is_wicket AND 
                             d.player_dismissed_id = d.batsman_id 
                             THEN d.dismissal_kind ELSE NULL END) as dismissal_kind,
                    MAX(CASE WHEN d.is_wicket AND 
                             d.player_dismissed_id = d.batsman_id AND
                             d.fielder_id IS NOT NULL
                             THEN p_f.player_name ELSE NULL END) as fielder_name,
                    MAX(CASE WHEN d.is_wicket AND 
                             d.player_dismissed_id = d.batsman_id
                             THEN p_b.player_name ELSE NULL END) as bowler_name
                FROM 
                    deliveries d
                    LEFT JOIN players p_f ON d.fielder_id = p_f.player_id
                    LEFT JOIN players p_b ON d.bowler_id = p_b.player_id
                WHERE 
                    d.inning_id = %s
                GROUP BY 
                    d.batsman_id
            )
            SELECT 
                p.player_name,
                pb.runs,
                pb.balls,
                pb.fours,
                pb.sixes,
                CASE WHEN pb.dismissal_kind IS NULL THEN 'not out' ELSE pb.dismissal_kind END as dismissal,
                pb.fielder_name,
                pb.bowler_name,
                CASE WHEN pb.balls > 0 THEN ROUND((pb.runs::float / pb.balls) * 100, 2) ELSE 0 END as strike_rate
            FROM 
                player_balls pb
                JOIN players p ON pb.batsman_id = p.player_id
            ORDER BY 
                pb.runs DESC, pb.balls
            """, (inning_id,))
            
            inning_batting = [dict(row) for row in cursor.fetchall()]
            for batsman in inning_batting:
                batsman['inning_number'] = inning['inning_number']
                batsman['batting_team'] = inning['batting_team']
            
            batting_performances.extend(inning_batting)
            
            # Bowling performances
            cursor.execute("""
            WITH bowler_stats AS (
                SELECT 
                    d.bowler_id,
                    COUNT(*) as balls,
                    SUM(d.total_runs) as runs,
                    SUM(CASE WHEN d.is_wicket AND 
                              d.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field')
                              THEN 1 ELSE 0 END) as wickets,
                    SUM(CASE WHEN d.extras_type = 'wides' THEN 1 ELSE 0 END) as wides,
                    SUM(CASE WHEN d.extras_type = 'noballs' THEN 1 ELSE 0 END) as noballs
                FROM 
                    deliveries d
                WHERE 
                    d.inning_id = %s
                GROUP BY 
                    d.bowler_id
            )
            SELECT 
                p.player_name,
                bs.balls,
                FLOOR(bs.balls / 6) || '.' || (bs.balls %% 6) as overs,
                bs.runs,
                bs.wickets,
                bs.wides,
                bs.noballs,
                CASE WHEN FLOOR(bs.balls / 6) > 0 THEN 
                    ROUND((bs.runs::float / (FLOOR(bs.balls / 6) + (bs.balls %% 6)/10)), 2)
                ELSE 0 END as economy
            FROM 
                bowler_stats bs
                JOIN players p ON bs.bowler_id = p.player_id
            ORDER BY 
                bs.wickets DESC, bs.runs
            """, (inning_id,))
            
            inning_bowling = [dict(row) for row in cursor.fetchall()]
            for bowler in inning_bowling:
                bowler['inning_number'] = inning['inning_number']
                bowler['bowling_team'] = inning['bowling_team']
            
            bowling_performances.extend(inning_bowling)
        
        cursor.close()
        conn.close()
        
        return {
            "match_info": match_info,
            "innings": innings_data,
            "batting_performances": batting_performances,
            "bowling_performances": bowling_performances
        }
    
    except Exception as e:
        logger.error(f"Error retrieving match details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving match details: {str(e)}")

# ---------- TOURNAMENT SUMMARY ENDPOINT ---------- #

@router.get("/tournament-summary/{season}", response_model=Dict[str, Any],
         summary="Get tournament summary for a specific season",
         description="""
         Get a comprehensive summary of an IPL tournament season.
         
         Path Parameters:
         - season: Season name (e.g., "2023", "2007/08")
         
         Returns detailed statistics including top performers,
         match summaries, and tournament-wide metrics.
         """)
async def get_tournament_summary(
    season: str = Path(..., description="Season name (e.g., '2023', '2007/08')")
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if season exists
        cursor.execute("SELECT season_id, season_year FROM seasons WHERE season_name = %s", (season,))
        season_result = cursor.fetchone()
        
        if not season_result:
            raise HTTPException(status_code=404, detail=f"Season '{season}' not found")
        
        season_id = season_result["season_id"]
        season_year = season_result["season_year"]
        
        # Get tournament summary
        cursor.execute("""
        SELECT 
            COUNT(DISTINCT m.match_id) as total_matches,
            COUNT(DISTINCT v.venue_id) as venues_used,
            COUNT(DISTINCT t.team_id) as teams_participated,
            SUM(CASE WHEN i1.batting_team_id = m.winner_id THEN 1 ELSE 0 END) as batting_first_wins,
            SUM(CASE WHEN i2.batting_team_id = m.winner_id THEN 1 ELSE 0 END) as batting_second_wins,
            SUM(CASE WHEN m.result = 'tie' THEN 1 ELSE 0 END) as tie_matches,
            SUM(CASE WHEN m.is_super_over = TRUE THEN 1 ELSE 0 END) as super_over_matches,
            MIN(m.match_date) as start_date,
            MAX(m.match_date) as end_date
        FROM 
            matches m
            JOIN venues v ON m.venue_id = v.venue_id
            JOIN teams t ON m.team1_id = t.team_id OR m.team2_id = t.team_id
            LEFT JOIN innings i1 ON m.match_id = i1.match_id AND i1.inning_number = 1
            LEFT JOIN innings i2 ON m.match_id = i2.match_id AND i2.inning_number = 2
        WHERE 
            m.season_id = %s
        """, (season_id,))
        
        summary = dict(cursor.fetchone())
        
        # Get top teams
        cursor.execute("""
        SELECT 
            t.team_name,
            ts.matches_played,
            ts.matches_won,
            ROUND((ts.matches_won::float / ts.matches_played) * 100, 2) as win_percentage,
            ts.batting_first_won,
            ts.bowling_first_won
        FROM 
            team_season_stats ts
            JOIN teams t ON ts.team_id = t.team_id
        WHERE 
            ts.season_id = %s
        ORDER BY 
            ts.matches_won DESC, win_percentage DESC
        LIMIT 4
        """, (season_id,))
        
        top_teams = [dict(row) for row in cursor.fetchall()]
        
        # Get top batsmen
        cursor.execute("""
        SELECT 
            p.player_name,
            t.team_name,
            SUM(CASE WHEN d.batsman_id = p.player_id THEN d.batsman_runs ELSE 0 END) as runs,
            COUNT(CASE WHEN d.batsman_id = p.player_id THEN 1 ELSE NULL END) as balls_faced,
            SUM(CASE WHEN d.batsman_id = p.player_id AND d.batsman_runs = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN d.batsman_id = p.player_id AND d.batsman_runs = 6 THEN 1 ELSE 0 END) as sixes,
            ROUND(SUM(CASE WHEN d.batsman_id = p.player_id THEN d.batsman_runs ELSE 0 END)::float / 
                 COUNT(CASE WHEN d.batsman_id = p.player_id THEN 1 ELSE NULL END) * 100, 2) as strike_rate
        FROM 
            players p
            JOIN deliveries d ON p.player_id = d.batsman_id
            JOIN innings i ON d.inning_id = i.inning_id
            JOIN matches m ON i.match_id = m.match_id
            JOIN teams t ON i.batting_team_id = t.team_id
        WHERE 
            m.season_id = %s
        GROUP BY 
            p.player_id, p.player_name, t.team_name
        HAVING 
            SUM(CASE WHEN d.batsman_id = p.player_id THEN d.batsman_runs ELSE 0 END) >= 100
        ORDER BY 
            runs DESC
        LIMIT 10
        """, (season_id,))
        
        top_batsmen = [dict(row) for row in cursor.fetchall()]
        
        # Get top bowlers
        cursor.execute("""
        SELECT 
            p.player_name,
            t.team_name,
            COUNT(CASE WHEN d.bowler_id = p.player_id THEN 1 ELSE NULL END) as balls_bowled,
            FLOOR(COUNT(CASE WHEN d.bowler_id = p.player_id THEN 1 ELSE NULL END) / 6) as overs_bowled,
            SUM(CASE WHEN d.bowler_id = p.player_id THEN d.total_runs ELSE 0 END) as runs_conceded,
            SUM(CASE WHEN d.bowler_id = p.player_id AND d.is_wicket = TRUE AND 
                     d.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') 
                THEN 1 ELSE 0 END) as wickets,
            ROUND(SUM(CASE WHEN d.bowler_id = p.player_id THEN d.total_runs ELSE 0 END)::float / 
                 (COUNT(CASE WHEN d.bowler_id = p.player_id THEN 1 ELSE NULL END) / 6), 2) as economy
        FROM 
            players p
            JOIN deliveries d ON p.player_id = d.bowler_id
            JOIN innings i ON d.inning_id = i.inning_id
            JOIN matches m ON i.match_id = m.match_id
            JOIN teams t ON i.bowling_team_id = t.team_id
        WHERE 
            m.season_id = %s
        GROUP BY 
            p.player_id, p.player_name, t.team_name
        HAVING 
            SUM(CASE WHEN d.bowler_id = p.player_id AND d.is_wicket = TRUE AND 
                     d.dismissal_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') 
                THEN 1 ELSE 0 END) >= 5
        ORDER BY 
            wickets DESC, economy
        LIMIT 10
        """, (season_id,))
        
        top_bowlers = [dict(row) for row in cursor.fetchall()]
        
        # Get venue stats
        cursor.execute("""
        SELECT 
            v.venue_name,
            v.city,
            COUNT(DISTINCT m.match_id) as matches_hosted,
            ROUND(AVG(CASE WHEN i.inning_number = 1 THEN i.total_runs ELSE NULL END), 2) as avg_first_innings_score,
            ROUND(AVG(CASE WHEN i.inning_number = 2 THEN i.total_runs ELSE NULL END), 2) as avg_second_innings_score,
            SUM(CASE WHEN i1.batting_team_id = m.winner_id THEN 1 ELSE 0 END) as batting_first_wins,
            SUM(CASE WHEN i2.batting_team_id = m.winner_id THEN 1 ELSE 0 END) as batting_second_wins
        FROM 
            venues v
            JOIN matches m ON v.venue_id = m.venue_id
            JOIN innings i ON m.match_id = i.match_id
            LEFT JOIN innings i1 ON m.match_id = i1.match_id AND i1.inning_number = 1
            LEFT JOIN innings i2 ON m.match_id = i2.match_id AND i2.inning_number = 2
        WHERE 
            m.season_id = %s
        GROUP BY 
            v.venue_id, v.venue_name, v.city
        HAVING 
            COUNT(DISTINCT m.match_id) >= 2
        ORDER BY 
            matches_hosted DESC
        """, (season_id,))
        
        venue_stats = [dict(row) for row in cursor.fetchall()]
        
        # Get playoff matches if any
        cursor.execute("""
        SELECT 
            m.match_id,
            m.match_date,
            t1.team_name as team1,
            t2.team_name as team2,
            CASE WHEN m.winner_id IS NOT NULL THEN 
                (SELECT team_name FROM teams WHERE team_id = m.winner_id) 
                ELSE 'No result' 
            END as winner,
            m.result,
            m.result_margin,
            m.match_type
        FROM 
            matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
        WHERE 
            m.season_id = %s AND 
            m.match_type NOT IN ('League')
        ORDER BY 
            m.match_date
        """, (season_id,))
        
        playoff_matches = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        # Calculate batting first vs batting second win percentages
        total_completed = summary.get('batting_first_wins', 0) + summary.get('batting_second_wins', 0)
        if total_completed > 0:
            summary['batting_first_win_percentage'] = round((summary.get('batting_first_wins', 0) / total_completed) * 100, 2)
            summary['batting_second_win_percentage'] = round((summary.get('batting_second_wins', 0) / total_completed) * 100, 2)
        else:
            summary['batting_first_win_percentage'] = 0
            summary['batting_second_win_percentage'] = 0
        
        tournament_duration = None
        if summary.get('start_date') and summary.get('end_date'):
            start = datetime.strptime(str(summary['start_date']), '%Y-%m-%d')
            end = datetime.strptime(str(summary['end_date']), '%Y-%m-%d')
            tournament_duration = (end - start).days + 1
            summary['tournament_duration'] = tournament_duration
        
        return {
            "season": season,
            "year": season_year,
            "summary": summary,
            "top_teams": top_teams,
            "top_batsmen": top_batsmen,
            "top_bowlers": top_bowlers,
            "venue_stats": venue_stats,
            "playoff_matches": playoff_matches
        }
    
    except Exception as e:
        logger.error(f"Error retrieving tournament summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving tournament summary: {str(e)}")