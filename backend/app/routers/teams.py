from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.utils.db_utils import execute_raw_sql, query_to_dataframe

router = APIRouter(
    prefix="/api/teams",
    tags=["Teams"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
def get_teams(db: Session = Depends(get_db)):
    """Get list of all teams with basic statistics."""
    try:
        query = """
        SELECT 
            team_name,
            COUNT(DISTINCT m.season) as seasons_played,
            COUNT(*) as matches_played,
            SUM(CASE WHEN m.winner = team_name THEN 1 ELSE 0 END) as matches_won,
            ROUND(SUM(CASE WHEN m.winner = team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as win_percentage
        FROM (
            SELECT team1 as team_name, * FROM match_info
            UNION ALL
            SELECT team2 as team_name, * FROM match_info
        ) as m
        GROUP BY team_name
        ORDER BY win_percentage DESC
        """
        
        teams_data = execute_raw_sql(db, query)
        return {"teams": teams_data}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching teams: {str(e)}")

@router.get("/{team_name}")
def get_team_stats(
    team_name: str, 
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a specific team."""
    try:
        # Basic team stats
        basic_stats_query = """
        SELECT 
            team_name,
            COUNT(DISTINCT m.season) as seasons_played,
            COUNT(*) as matches_played,
            SUM(CASE WHEN m.winner = team_name THEN 1 ELSE 0 END) as matches_won,
            ROUND(SUM(CASE WHEN m.winner = team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as win_percentage,
            MIN(m.season) as first_season,
            MAX(m.season) as last_season,
            COUNT(DISTINCT m.venue) as venues_played
        FROM (
            SELECT team1 as team_name, * FROM match_info
            UNION ALL
            SELECT team2 as team_name, * FROM match_info
        ) as m
        WHERE team_name = :team_name
        GROUP BY team_name
        """
        
        basic_stats = execute_raw_sql(db, basic_stats_query, {"team_name": team_name})
        
        if not basic_stats:
            raise HTTPException(status_code=404, detail=f"Team not found: {team_name}")
        
        # Season-wise performance
        season_stats_query = """
        SELECT 
            m.season,
            COUNT(*) as matches_played,
            SUM(CASE WHEN m.winner = team_name THEN 1 ELSE 0 END) as matches_won,
            ROUND(SUM(CASE WHEN m.winner = team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as win_percentage
        FROM (
            SELECT team1 as team_name, * FROM match_info
            UNION ALL
            SELECT team2 as team_name, * FROM match_info
        ) as m
        WHERE team_name = :team_name
        GROUP BY m.season
        ORDER BY m.season
        """
        
        season_stats = execute_raw_sql(db, season_stats_query, {"team_name": team_name})
        
        # Home vs Away performance
        venue_stats_query = """
        WITH team_home_venue AS (
            SELECT 
                :team_name as team_name,
                MODE() WITHIN GROUP (ORDER BY venue) as home_venue
            FROM match_info
            WHERE team1 = :team_name OR team2 = :team_name
        ),
        team_matches AS (
            SELECT 
                m.filename,
                m.team1,
                m.team2,
                m.winner,
                m.venue,
                thv.home_venue,
                CASE 
                    WHEN m.venue = thv.home_venue THEN 'Home' 
                    ELSE 'Away' 
                END as venue_type
            FROM match_info m
            CROSS JOIN team_home_venue thv
            WHERE m.team1 = :team_name OR m.team2 = :team_name
        )
        SELECT 
            venue_type,
            COUNT(*) as matches_played,
            SUM(CASE WHEN winner = :team_name THEN 1 ELSE 0 END) as matches_won,
            ROUND(SUM(CASE WHEN winner = :team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as win_percentage
        FROM team_matches
        GROUP BY venue_type
        ORDER BY venue_type
        """
        
        venue_stats = execute_raw_sql(db, venue_stats_query, {"team_name": team_name})
        
        # Opponent analysis
        opponent_stats_query = """
        WITH team_matches AS (
            SELECT 
                m.match_date,
                m.team_name,
                CASE 
                    WHEN m.team1 = m.team_name THEN m.team2
                    ELSE m.team1
                END as opponent,
                m.winner
            FROM (
                SELECT team1 as team_name, * FROM match_info
                UNION ALL
                SELECT team2 as team_name, * FROM match_info
            ) as m
            WHERE m.team_name = :team_name
        )
        SELECT 
            opponent,
            COUNT(*) as matches_played,
            SUM(CASE WHEN winner = :team_name THEN 1 ELSE 0 END) as matches_won,
            ROUND(SUM(CASE WHEN winner = :team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as win_percentage
        FROM team_matches
        GROUP BY opponent
        ORDER BY matches_played DESC
        """
        
        opponent_stats = execute_raw_sql(db, opponent_stats_query, {"team_name": team_name})
        
        # Toss performance
        toss_stats_query = """
        SELECT 
            COUNT(*) as total_matches,
            SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END) as toss_wins,
            ROUND(SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as toss_win_percentage,
            SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'bat' THEN 1 ELSE 0 END) as chose_bat,
            SUM(CASE WHEN toss_winner = :team_name AND toss_decision = 'field' THEN 1 ELSE 0 END) as chose_field,
            SUM(CASE WHEN toss_winner = :team_name AND winner = :team_name THEN 1 ELSE 0 END) as won_after_winning_toss,
            ROUND(SUM(CASE WHEN toss_winner = :team_name AND winner = :team_name THEN 1 ELSE 0 END)::numeric / 
                NULLIF(SUM(CASE WHEN toss_winner = :team_name THEN 1 ELSE 0 END), 0) * 100, 2) as win_rate_after_winning_toss
        FROM match_info
        WHERE team1 = :team_name OR team2 = :team_name
        """
        
        toss_stats = execute_raw_sql(db, toss_stats_query, {"team_name": team_name})
        
        return {
            "team_name": team_name,
            "basic_stats": basic_stats[0] if basic_stats else None,
            "season_stats": season_stats,
            "venue_stats": venue_stats,
            "opponent_stats": opponent_stats,
            "toss_stats": toss_stats[0] if toss_stats else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team stats: {str(e)}")

@router.get("/{team_name}/seasons/{season}")
def get_team_season_stats(
    team_name: str,
    season: int,
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a specific team in a specific season."""
    try:
        # Check if team played in the season
        check_query = """
        SELECT COUNT(*) 
        FROM match_info 
        WHERE (team1 = :team_name OR team2 = :team_name)
        AND season = :season
        """
        
        count = db.execute(text(check_query), {"team_name": team_name, "season": season}).scalar()
        
        if count == 0:
            raise HTTPException(status_code=404, detail=f"Team {team_name} did not play in the {season} season")
            
        # Season performance
        season_stats_query = """
        SELECT 
            m.season,
            COUNT(*) as matches_played,
            SUM(CASE WHEN m.winner = team_name THEN 1 ELSE 0 END) as matches_won,
            ROUND(SUM(CASE WHEN m.winner = team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as win_percentage,
            COUNT(DISTINCT m.venue) as venues_played,
            STRING_AGG(DISTINCT m.venue, ', ') as venue_list
        FROM (
            SELECT team1 as team_name, * FROM match_info
            UNION ALL
            SELECT team2 as team_name, * FROM match_info
        ) as m
        WHERE team_name = :team_name AND m.season = :season
        GROUP BY m.season
        """
        
        season_stats = execute_raw_sql(db, season_stats_query, {"team_name": team_name, "season": season})
        
        # Match results
        matches_query = """
        SELECT 
            m.match_date,
            m.venue,
            m.city,
            CASE 
                WHEN m.team1 = :team_name THEN m.team2
                ELSE m.team1
            END as opponent,
            m.toss_winner,
            m.toss_decision,
            m.winner,
            m.margin,
            m.player_of_match
        FROM match_info m
        WHERE (m.team1 = :team_name OR m.team2 = :team_name)
        AND m.season = :season
        ORDER BY m.match_date
        """
        
        matches = execute_raw_sql(db, matches_query, {"team_name": team_name, "season": season})
        
        # Get batting stats for the team in the season
        batting_stats_query = """
        WITH team_innings AS (
            SELECT 
                i.*,
                m.match_date,
                m.venue
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            WHERE i.team = :team_name
            AND m.season = :season
        )
        SELECT 
            batsman,
            COUNT(DISTINCT filename) as matches,
            COUNT(*) as balls_faced,
            SUM(runs_batsman) as runs,
            MAX(runs_batsman) as highest_score,
            ROUND(SUM(runs_batsman)::numeric / COUNT(*) * 100, 2) as strike_rate,
            SUM(CASE WHEN runs_batsman = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN runs_batsman = 6 THEN 1 ELSE 0 END) as sixes
        FROM team_innings
        GROUP BY batsman
        ORDER BY runs DESC
        """
        
        batting_stats = execute_raw_sql(db, batting_stats_query, {"team_name": team_name, "season": season})
        
        # Get bowling stats for the team in the season
        bowling_stats_query = """
        WITH team_bowling AS (
            SELECT 
                i.*,
                m.match_date,
                m.venue
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            WHERE i.team != :team_name
            AND (m.team1 = :team_name OR m.team2 = :team_name)
            AND m.season = :season
        ),
        wicket_data AS (
            SELECT 
                bowler,
                COUNT(*) as wickets
            FROM team_bowling
            WHERE wicket_details IS NOT NULL AND wicket_details != ''
            GROUP BY bowler
        )
        SELECT 
            tb.bowler,
            COUNT(DISTINCT tb.filename) as matches,
            COUNT(*) as balls_bowled,
            SUM(tb.runs_total) as runs_conceded,
            COALESCE(wd.wickets, 0) as wickets,
            ROUND(SUM(tb.runs_total)::numeric / (COUNT(*) / 6.0), 2) as economy
        FROM team_bowling tb
        LEFT JOIN wicket_data wd ON tb.bowler = wd.bowler
        GROUP BY tb.bowler, wd.wickets
        ORDER BY wickets DESC, economy
        """
        
        bowling_stats = execute_raw_sql(db, bowling_stats_query, {"team_name": team_name, "season": season})
        
        return {
            "team_name": team_name,
            "season": season,
            "season_stats": season_stats[0] if season_stats else None,
            "matches": matches,
            "batting_stats": batting_stats,
            "bowling_stats": bowling_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team season stats: {str(e)}")