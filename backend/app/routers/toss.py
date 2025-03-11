from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.utils.db_utils import execute_raw_sql, query_to_dataframe

router = APIRouter(
    prefix="/api/toss",
    tags=["Toss Analysis"],
    responses={404: {"description": "Not found"}},
)

@router.get("/analysis")
def get_toss_analysis(
    season: Optional[int] = None,
    team: Optional[str] = None,
    venue: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get comprehensive toss analysis with optional filters."""
    try:
        # Build dynamic filters
        filters = []
        params = {}
        
        if season:
            filters.append("m.season = :season")
            params["season"] = season
            
        if team:
            filters.append("(m.team1 = :team OR m.team2 = :team)")
            params["team"] = team
            
        if venue:
            filters.append("m.venue = :venue")
            params["venue"] = venue
            
        filter_clause = " AND ".join(filters)
        if filter_clause:
            filter_clause = "WHERE " + filter_clause
            
        # Overall toss statistics
        overall_query = f"""
        SELECT 
            COUNT(*) as total_matches,
            SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END) as chose_bat,
            SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END) as chose_field,
            ROUND(SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as chose_bat_percentage,
            ROUND(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as chose_field_percentage,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'bat' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'bat' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_after_batting,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'field' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'field' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_after_fielding,
            ROUND(SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'bat' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'bat' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END)::numeric / NULLIF(SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END), 0) * 100, 2) as won_after_batting_percentage,
            ROUND(SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'field' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'field' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END)::numeric / NULLIF(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END), 0) * 100, 2) as won_after_fielding_percentage,
            SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END) as toss_winner_won_match,
            ROUND(SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as toss_winner_win_percentage
        FROM match_info m
        {filter_clause}
        """
        
        # Season-wise toss statistics
        season_query = f"""
        SELECT 
            m.season,
            COUNT(*) as total_matches,
            SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END) as chose_bat,
            SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END) as chose_field,
            ROUND(SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as chose_bat_percentage,
            ROUND(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as chose_field_percentage,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'bat' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'bat' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_after_batting,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'field' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'field' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_after_fielding,
            ROUND(SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'bat' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'bat' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END)::numeric / NULLIF(SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END), 0) * 100, 2) as won_after_batting_percentage,
            ROUND(SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'field' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'field' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END)::numeric / NULLIF(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END), 0) * 100, 2) as won_after_fielding_percentage,
            SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END) as toss_winner_won_match,
            ROUND(SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as toss_winner_win_percentage
        FROM match_info m
        {filter_clause}
        GROUP BY m.season
        ORDER BY m.season
        """
        
        # Team-wise toss statistics
        team_query = f"""
        WITH team_toss AS (
            SELECT 
                team_name,
                COUNT(*) as matches_played,
                SUM(CASE WHEN toss_winner = team_name THEN 1 ELSE 0 END) as toss_wins,
                SUM(CASE WHEN toss_winner = team_name AND toss_decision = 'bat' THEN 1 ELSE 0 END) as chose_bat,
                SUM(CASE WHEN toss_winner = team_name AND toss_decision = 'field' THEN 1 ELSE 0 END) as chose_field,
                SUM(CASE WHEN toss_winner = team_name AND winner = team_name THEN 1 ELSE 0 END) as won_after_winning_toss,
                SUM(CASE WHEN toss_winner != team_name AND winner = team_name THEN 1 ELSE 0 END) as won_after_losing_toss
            FROM (
                SELECT team1 as team_name, * FROM match_info m
                UNION ALL
                SELECT team2 as team_name, * FROM match_info m
            ) t
            {filter_clause.replace('m.', 't.')}
            GROUP BY team_name
        )
        SELECT 
            team_name,
            matches_played,
            toss_wins,
            ROUND(toss_wins::numeric / matches_played * 100, 2) as toss_win_percentage,
            chose_bat,
            chose_field,
            ROUND(chose_bat::numeric / NULLIF(toss_wins, 0) * 100, 2) as chose_bat_percentage,
            ROUND(chose_field::numeric / NULLIF(toss_wins, 0) * 100, 2) as chose_field_percentage,
            won_after_winning_toss,
            ROUND(won_after_winning_toss::numeric / NULLIF(toss_wins, 0) * 100, 2) as win_rate_after_winning_toss,
            won_after_losing_toss,
            ROUND(won_after_losing_toss::numeric / NULLIF(matches_played - toss_wins, 0) * 100, 2) as win_rate_after_losing_toss
        FROM team_toss
        ORDER BY toss_win_percentage DESC
        """
        
        # Venue-wise toss statistics
        venue_query = f"""
        SELECT 
            venue,
            COUNT(*) as total_matches,
            SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END) as chose_bat,
            SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END) as chose_field,
            ROUND(SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as chose_bat_percentage,
            ROUND(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as chose_field_percentage,
            ROUND(SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as toss_winner_win_percentage
        FROM match_info m
        {filter_clause}
        GROUP BY venue
        HAVING COUNT(*) >= 5
        ORDER BY total_matches DESC
        """
        
        overall_stats = execute_raw_sql(db, overall_query, params)
        season_stats = execute_raw_sql(db, season_query, params)
        team_stats = execute_raw_sql(db, team_query, params)
        venue_stats = execute_raw_sql(db, venue_query, params)
        
        return {
            "overall_stats": overall_stats[0] if overall_stats else None,
            "season_stats": season_stats,
            "team_stats": team_stats,
            "venue_stats": venue_stats,
            "filters_applied": {
                "season": season,
                "team": team,
                "venue": venue
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching toss analysis: {str(e)}")

@router.get("/teams/{team_name}")
def get_team_toss_stats(
    team_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get detailed toss statistics for a specific team."""
    try:
        # Check if team exists
        check_query = """
        SELECT COUNT(*) 
        FROM (
            SELECT team1 as team FROM match_info
            UNION
            SELECT team2 as team FROM match_info
        ) as teams
        WHERE team = :team_name
        """
        
        count = db.execute(text(check_query), {"team_name": team_name}).scalar()
        
        if count == 0:
            raise HTTPException(status_code=404, detail=f"Team not found: {team_name}")
            
        # Season filter
        season_filter = "AND season = :season" if season else ""
        params = {"team_name": team_name}
        
        if season:
            params["season"] = season
            
        # Overall team toss stats
        overall_query = """
        WITH team_matches AS (
            SELECT 
                *
            FROM match_info
            WHERE (team1 = :team_name OR team2 = :team_name)
            """ + season_filter + """
        )
        SELECT 
            COUNT(*) as total_matches,
            SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END) as toss_wins,
            ROUND(SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as toss_win_percentage,
            SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'bat' THEN 1 ELSE 0 END) as chose_bat,
            SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'field' THEN 1 ELSE 0 END) as chose_field,
            ROUND(SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'bat' THEN 1 ELSE 0 END)::numeric / 
                NULLIF(SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END), 0) * 100, 2) as chose_bat_percentage,
            ROUND(SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'field' THEN 1 ELSE 0 END)::numeric / 
                NULLIF(SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END), 0) * 100, 2) as chose_field_percentage,
            SUM(CASE WHEN toss_winner = :team_name AND winner = :team_name THEN 1 ELSE 0 END) as won_after_winning_toss,
            ROUND(SUM(CASE WHEN toss_winner = :team_name AND winner = :team_name THEN 1 ELSE 0 END)::numeric / 
                NULLIF(SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END), 0) * 100, 2) as win_rate_after_winning_toss,
            SUM(CASE WHEN toss_winner != :team_name AND winner = :team_name THEN 1 ELSE 0 END) as won_after_losing_toss,
            ROUND(SUM(CASE WHEN toss_winner != :team_name AND winner = :team_name THEN 1 ELSE 0 END)::numeric / 
                NULLIF(SUM(CASE WHEN toss_winner != :team_name THEN 1 ELSE 0 END), 0) * 100, 2) as win_rate_after_losing_toss,
            SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'bat' AND winner = :team_name THEN 1 ELSE 0 END) as won_after_batting,
            ROUND(SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'bat' AND winner = :team_name THEN 1 ELSE 0 END)::numeric / 
                NULLIF(SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'bat' THEN 1 ELSE 0 END), 0) * 100, 2) as win_rate_after_batting,
            SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'field' AND winner = :team_name THEN 1 ELSE 0 END) as won_after_fielding,
            ROUND(SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'field' AND winner = :team_name THEN 1 ELSE 0 END)::numeric / 
                NULLIF(SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'field' THEN 1 ELSE 0 END), 0) * 100, 2) as win_rate_after_fielding
        FROM team_matches
        """
        
        # Season-wise team toss stats
        season_query = """
        WITH team_matches AS (
            SELECT 
                *
            FROM match_info
            WHERE (team1 = :team_name OR team2 = :team_name)
            """ + season_filter + """
        )
        SELECT 
            season,
            COUNT(*) as total_matches,
            SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END) as toss_wins,
            ROUND(SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as toss_win_percentage,
            SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'bat' THEN 1 ELSE 0 END) as chose_bat,
            SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'field' THEN 1 ELSE 0 END) as chose_field,
            SUM(CASE WHEN toss_winner = :team_name AND winner = :team_name THEN 1 ELSE 0 END) as won_after_winning_toss,
            SUM(CASE WHEN toss_winner != :team_name AND winner = :team_name THEN 1 ELSE 0 END) as won_after_losing_toss
        FROM team_matches
        GROUP BY season
        ORDER BY season
        """
        
        # Venue-wise team toss stats
        venue_query = """
        WITH team_matches AS (
            SELECT 
                *
            FROM match_info
            WHERE (team1 = :team_name OR team2 = :team_name)
            """ + season_filter + """
        )
        SELECT 
            venue,
            COUNT(*) as total_matches,
            SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END) as toss_wins,
            ROUND(SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as toss_win_percentage,
            SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'bat' THEN 1 ELSE 0 END) as chose_bat,
            SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'field' THEN 1 ELSE 0 END) as chose_field,
            SUM(CASE WHEN toss_winner = :team_name AND winner = :team_name THEN 1 ELSE 0 END) as won_after_winning_toss,
            SUM(CASE WHEN toss_winner != :team_name AND winner = :team_name THEN 1 ELSE 0 END) as won_after_losing_toss
        FROM team_matches
        GROUP BY venue
        HAVING COUNT(*) >= 3
        ORDER BY total_matches DESC
        """
        
        # Opponent-wise team toss stats
        opponent_query = """
        WITH team_matches AS (
            SELECT 
                *,
                CASE 
                    WHEN team1 = :team_name THEN team2
                    ELSE team1
                END as opponent
            FROM match_info
            WHERE (team1 = :team_name OR team2 = :team_name)
            """ + season_filter + """
        )
        SELECT 
            opponent,
            COUNT(*) as total_matches,
            SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END) as toss_wins,
            ROUND(SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as toss_win_percentage,
            SUM(CASE WHEN toss_winner = :team_name AND winner = :team_name THEN 1 ELSE 0 END) as won_after_winning_toss,
            SUM(CASE WHEN toss_winner != :team_name AND winner = :team_name THEN 1 ELSE 0 END) as won_after_losing_toss
        FROM team_matches
        GROUP BY opponent
        HAVING COUNT(*) >= 3
        ORDER BY total_matches DESC
        """
        
        overall_stats = execute_raw_sql(db, overall_query, params)
        season_stats = execute_raw_sql(db, season_query, params)
        venue_stats = execute_raw_sql(db, venue_query, params)
        opponent_stats = execute_raw_sql(db, opponent_query, params)
        
        return {
            "team_name": team_name,
            "overall_stats": overall_stats[0] if overall_stats else None,
            "season_stats": season_stats,
            "venue_stats": venue_stats,
            "opponent_stats": opponent_stats,
            "filters_applied": {
                "season": season
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team toss stats: {str(e)}")

@router.get("/trends")
def get_toss_trends(
    db: Session = Depends(get_db)
):
    """Get toss decision and outcome trends over the years."""
    try:
        # Toss decision trends by season
        decision_trends_query = """
        SELECT 
            season,
            COUNT(*) as total_matches,
            SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END) as chose_bat,
            SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END) as chose_field,
            ROUND(SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as chose_bat_percentage,
            ROUND(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as chose_field_percentage
        FROM match_info
        GROUP BY season
        ORDER BY season
        """
        
        # Toss outcome trends by season
        outcome_trends_query = """
        SELECT 
            season,
            COUNT(*) as total_matches,
            SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END) as toss_winner_won_match,
            ROUND(SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as toss_winner_win_percentage,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'bat' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'bat' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_after_batting,
            ROUND(SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'bat' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'bat' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END)::numeric / NULLIF(SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END), 0) * 100, 2) as batting_first_win_percentage,
            SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'field' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'field' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END) as won_after_fielding,
            ROUND(SUM(CASE 
                WHEN 
                    (toss_winner = team1 AND toss_decision = 'field' AND winner = team1) OR
                    (toss_winner = team2 AND toss_decision = 'field' AND winner = team2) 
                THEN 1 
                ELSE 0 
            END)::numeric / NULLIF(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END), 0) * 100, 2) as fielding_first_win_percentage
        FROM match_info
        GROUP BY season
        ORDER BY season
        """
        
        decision_trends = execute_raw_sql(db, decision_trends_query)
        outcome_trends = execute_raw_sql(db, outcome_trends_query)
        
        return {
            "decision_trends": decision_trends,
            "outcome_trends": outcome_trends
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching toss trends: {str(e)}")