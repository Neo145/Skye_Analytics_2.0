from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.utils.db_utils import execute_raw_sql, query_to_dataframe

router = APIRouter(
    prefix="/api/matches",
    tags=["Matches"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
def get_match_stats(
    season: Optional[int] = None,
    venue: Optional[str] = None,
    team: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get match statistics with optional filters."""
    try:
        # Build dynamic filters
        filters = []
        params = {}
        
        if season:
            filters.append("m.season = :season")
            params["season"] = season
            
        if venue:
            filters.append("m.venue = :venue")
            params["venue"] = venue
            
        if team:
            filters.append("(m.team1 = :team OR m.team2 = :team)")
            params["team"] = team
            
        filter_clause = " AND ".join(filters)
        if filter_clause:
            filter_clause = "WHERE " + filter_clause
            
        # Overall match statistics
        overall_stats_query = f"""
        SELECT 
            COUNT(*) as total_matches,
            COUNT(DISTINCT venue) as venues_used,
            COUNT(DISTINCT CONCAT(team1, '-', team2)) as team_combinations,
            SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END) as bat_first_count,
            SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END) as field_first_count,
            ROUND(SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as bat_first_percentage,
            ROUND(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as field_first_percentage,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'bat' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'bat' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_batting_first,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'field' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'field' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_fielding_first,
            SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END) as toss_winner_won_match,
            ROUND(SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as toss_winner_win_percentage
        FROM match_info m
        {filter_clause}
        """
        
        # Season-wise match statistics
        season_stats_query = f"""
        SELECT 
            m.season,
            COUNT(*) as total_matches,
            COUNT(DISTINCT venue) as venues_used,
            SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END) as bat_first_count,
            SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END) as field_first_count,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'bat' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'bat' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_batting_first,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'field' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'field' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_fielding_first,
            ROUND(SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as toss_winner_win_percentage
        FROM match_info m
        {filter_clause}
        GROUP BY m.season
        ORDER BY m.season
        """
        
        # Team-wise match statistics
        team_stats_query = f"""
        WITH team_matches AS (
            SELECT 
                team_name,
                m.season,
                m.venue,
                m.toss_winner,
                m.toss_decision,
                m.winner,
                CASE 
                    WHEN m.winner = team_name THEN 1
                    ELSE 0
                END as is_win
            FROM (
                SELECT team1 as team_name, * FROM match_info
                UNION ALL
                SELECT team2 as team_name, * FROM match_info
            ) m
            {filter_clause.replace('m.', '')}
        )
        SELECT 
            team_name,
            COUNT(*) as matches_played,
            SUM(is_win) as matches_won,
            ROUND(SUM(is_win)::numeric / COUNT(*) * 100, 2) as win_percentage,
            COUNT(DISTINCT season) as seasons_played,
            COUNT(DISTINCT venue) as venues_played
        FROM team_matches
        GROUP BY team_name
        ORDER BY win_percentage DESC
        """
        
        # Venue-wise match statistics
        venue_stats_query = f"""
        SELECT 
            m.venue,
            m.city,
            COUNT(*) as matches_hosted,
            COUNT(DISTINCT m.season) as seasons,
            SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END) as bat_first_count,
            SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END) as field_first_count,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'bat' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'bat' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_batting_first,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'field' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'field' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_fielding_first,
            ROUND(SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'bat' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'bat' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END)::numeric / NULLIF(SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END), 0) * 100, 2) as batting_first_win_percentage,
            ROUND(SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'field' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'field' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END)::numeric / NULLIF(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END), 0) * 100, 2) as fielding_first_win_percentage
        FROM match_info m
        {filter_clause}
        GROUP BY m.venue, m.city
        ORDER BY matches_hosted DESC
        """
        
        overall_stats = execute_raw_sql(db, overall_stats_query, params)
        season_stats = execute_raw_sql(db, season_stats_query, params)
        team_stats = execute_raw_sql(db, team_stats_query, params)
        venue_stats = execute_raw_sql(db, venue_stats_query, params)
        
        return {
            "overall_stats": overall_stats[0] if overall_stats else None,
            "season_stats": season_stats,
            "team_stats": team_stats,
            "venue_stats": venue_stats,
            "filters_applied": {
                "season": season,
                "venue": venue,
                "team": team
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching match statistics: {str(e)}")

@router.get("/{filename}")
def get_match_details(
    filename: str,
    db: Session = Depends(get_db)
):
    """Get detailed information for a specific match."""
    try:
        # Match info
        match_query = """
        SELECT *
        FROM match_info
        WHERE filename = :filename
        """
        
        match_info = execute_raw_sql(db, match_query, {"filename": filename})
        
        if not match_info:
            raise HTTPException(status_code=404, detail=f"Match not found: {filename}")
            
        # First innings
        first_innings_query = """
        SELECT *
        FROM innings_data
        WHERE filename = :filename AND innings_type = '1st'
        ORDER BY over_ball
        """
        
        # Second innings
        second_innings_query = """
        SELECT *
        FROM innings_data
        WHERE filename = :filename AND innings_type = '2nd'
        ORDER BY over_ball
        """
        
        # Innings summary
        innings_summary_query = """
        WITH innings_data_summary AS (
            SELECT 
                innings_type,
                team,
                SUM(runs_total) as total_runs,
                COUNT(DISTINCT CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN batsman END) as wickets,
                MAX(over_ball) as overs_played,
                COUNT(*) as balls_played,
                SUM(CASE WHEN runs_batsman = 4 THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN runs_batsman = 6 THEN 1 ELSE 0 END) as sixes,
                SUM(CASE WHEN extras_type IS NOT NULL AND extras_type != '' THEN extras_runs ELSE 0 END) as extras
            FROM innings_data
            WHERE filename = :filename
            GROUP BY innings_type, team
        ),
        batsman_summary AS (
            SELECT 
                innings_type,
                team,
                batsman,
                SUM(runs_batsman) as runs,
                COUNT(*) as balls_faced,
                SUM(CASE WHEN runs_batsman = 4 THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN runs_batsman = 6 THEN 1 ELSE 0 END) as sixes,
                ROUND(SUM(runs_batsman)::numeric / COUNT(*) * 100, 2) as strike_rate
            FROM innings_data
            WHERE filename = :filename
            GROUP BY innings_type, team, batsman
        ),
        bowler_summary AS (
            SELECT 
                innings_type,
                team,
                bowler,
                COUNT(*) as balls_bowled,
                SUM(runs_total) as runs_conceded,
                COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) as wickets,
                ROUND(COUNT(*)::numeric / 6, 1) as overs,
                ROUND(SUM(runs_total)::numeric / (COUNT(*) / 6.0), 2) as economy
            FROM innings_data
            WHERE filename = :filename
            GROUP BY innings_type, team, bowler
        )
        
        SELECT 
            ids.innings_type,
            ids.team,
            ids.total_runs,
            ids.wickets,
            FLOOR(ids.overs_played)::int || '.' || (ids.balls_played % 6) as overs,
            ids.balls_played,
            ids.fours,
            ids.sixes,
            ids.extras,
            json_agg(
                json_build_object(
                    'batsman', bs.batsman,
                    'runs', bs.runs,
                    'balls_faced', bs.balls_faced,
                    'fours', bs.fours,
                    'sixes', bs.sixes,
                    'strike_rate', bs.strike_rate
                )
            ) as batting_scorecard,
            (
                SELECT json_agg(
                    json_build_object(
                        'bowler', bws.bowler,
                        'overs', bws.overs,
                        'runs_conceded', bws.runs_conceded,
                        'wickets', bws.wickets,
                        'economy', bws.economy
                    )
                )
                FROM bowler_summary bws
                WHERE bws.innings_type = ids.innings_type AND bws.team != ids.team
            ) as bowling_scorecard
        FROM innings_data_summary ids
        JOIN batsman_summary bs ON ids.innings_type = bs.innings_type AND ids.team = bs.team
        GROUP BY ids.innings_type, ids.team, ids.total_runs, ids.wickets, ids.overs_played, ids.balls_played, ids.fours, ids.sixes, ids.extras
        ORDER BY ids.innings_type
        """
        
        first_innings = execute_raw_sql(db, first_innings_query, {"filename": filename})
        second_innings = execute_raw_sql(db, second_innings_query, {"filename": filename})
        innings_summary = execute_raw_sql(db, innings_summary_query, {"filename": filename})
        
        # Extract match metadata
        match_data = match_info[0] if match_info else {}
        
        return {
            "match_info": match_data,
            "innings_summary": innings_summary,
            "first_innings": first_innings,
            "second_innings": second_innings,
            "match_id": filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching match details: {str(e)}")

@router.get("/seasons/{season}")
def get_season_matches(
    season: int,
    db: Session = Depends(get_db)
):
    """Get all matches for a specific season."""
    try:
        # Check if season exists
        check_query = """
        SELECT COUNT(*) 
        FROM match_info 
        WHERE season = :season
        """
        
        count = db.execute(text(check_query), {"season": season}).scalar()
        
        if count == 0:
            raise HTTPException(status_code=404, detail=f"No matches found for season: {season}")
            
        # Season matches
        matches_query = """
        SELECT 
            filename,
            match_date,
            venue,
            city,
            team1,
            team2,
            toss_winner,
            toss_decision,
            winner,
            margin,
            player_of_match
        FROM match_info
        WHERE season = :season
        ORDER BY match_date
        """
        
        # Season stats
        stats_query = """
        SELECT 
            COUNT(*) as total_matches,
            COUNT(DISTINCT venue) as venues_used,
            COUNT(DISTINCT team1) + COUNT(DISTINCT team2) - COUNT(DISTINCT CASE WHEN team1 = team2 THEN team1 END) as teams_participated,
            SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END) as bat_first_count,
            SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END) as field_first_count,
            ROUND(SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as bat_first_percentage,
            ROUND(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as field_first_percentage,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'bat' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'bat' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_batting_first,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'field' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'field' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_fielding_first,
            SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END) as toss_winner_won_match,
            ROUND(SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as toss_winner_win_percentage
        FROM match_info
        WHERE season = :season
        """
        
        # Team stats for the season
        team_stats_query = """
        WITH team_matches AS (
            SELECT 
                team_name,
                m.toss_winner,
                m.toss_decision,
                m.winner,
                CASE 
                    WHEN m.winner = team_name THEN 1
                    ELSE 0
                END as is_win
            FROM (
                SELECT team1 as team_name, * FROM match_info
                UNION ALL
                SELECT team2 as team_name, * FROM match_info
            ) m
            WHERE m.season = :season
        )
        SELECT 
            team_name,
            COUNT(*) as matches_played,
            SUM(is_win) as matches_won,
            ROUND(SUM(is_win)::numeric / COUNT(*) * 100, 2) as win_percentage
        FROM team_matches
        GROUP BY team_name
        ORDER BY matches_won DESC, win_percentage DESC
        """
        
        matches = execute_raw_sql(db, matches_query, {"season": season})
        stats = execute_raw_sql(db, stats_query, {"season": season})
        team_stats = execute_raw_sql(db, team_stats_query, {"season": season})
        
        return {
            "season": season,
            "matches": matches,
            "stats": stats[0] if stats else None,
            "team_stats": team_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching season matches: {str(e)}")