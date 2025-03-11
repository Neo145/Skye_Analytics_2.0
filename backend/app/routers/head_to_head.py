from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.utils.db_utils import execute_raw_sql, query_to_dataframe

router = APIRouter(
    prefix="/api/head-to-head",
    tags=["Head-to-Head Analysis"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
def get_all_head_to_head(
    db: Session = Depends(get_db)
):
    """Get all head-to-head records between teams."""
    try:
        query = """
        WITH team_matchups AS (
            SELECT 
                CASE 
                    WHEN team1 < team2 THEN team1 
                    ELSE team2 
                END as team_a,
                CASE 
                    WHEN team1 < team2 THEN team2 
                    ELSE team1 
                END as team_b,
                CASE 
                    WHEN team1 < team2 THEN 
                        CASE WHEN winner = team1 THEN 'team_a' 
                             WHEN winner = team2 THEN 'team_b' 
                             ELSE 'no_result' 
                        END
                    ELSE 
                        CASE WHEN winner = team1 THEN 'team_b' 
                             WHEN winner = team2 THEN 'team_a' 
                             ELSE 'no_result' 
                        END
                END as winner
            FROM match_info
        )
        
        SELECT 
            team_a,
            team_b,
            COUNT(*) as matches_played,
            SUM(CASE WHEN winner = 'team_a' THEN 1 ELSE 0 END) as team_a_wins,
            SUM(CASE WHEN winner = 'team_b' THEN 1 ELSE 0 END) as team_b_wins,
            SUM(CASE WHEN winner = 'no_result' THEN 1 ELSE 0 END) as no_results,
            ROUND(SUM(CASE WHEN winner = 'team_a' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as team_a_win_percentage,
            ROUND(SUM(CASE WHEN winner = 'team_b' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as team_b_win_percentage
        FROM team_matchups
        GROUP BY team_a, team_b
        HAVING COUNT(*) > 0
        ORDER BY matches_played DESC, team_a, team_b
        """
        
        h2h_records = execute_raw_sql(db, query)
        return {"head_to_head_records": h2h_records}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching head-to-head records: {str(e)}")

@router.get("/{team1}/{team2}")
def get_specific_head_to_head(
    team1: str,
    team2: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get detailed head-to-head analysis between two specific teams."""
    try:
        # Check if both teams exist
        check_query = """
        SELECT 
            SUM(CASE WHEN team = :team1 THEN 1 ELSE 0 END) as team1_exists,
            SUM(CASE WHEN team = :team2 THEN 1 ELSE 0 END) as team2_exists
        FROM (
            SELECT team1 as team FROM match_info
            UNION
            SELECT team2 as team FROM match_info
        ) as teams
        """
        
        check_result = execute_raw_sql(db, check_query, {"team1": team1, "team2": team2})
        
        if not check_result or check_result[0]["team1_exists"] == 0:
            raise HTTPException(status_code=404, detail=f"Team not found: {team1}")
            
        if check_result[0]["team2_exists"] == 0:
            raise HTTPException(status_code=404, detail=f"Team not found: {team2}")
            
        # Season filter
        season_filter = "AND season = :season" if season else ""
        params = {"team1": team1, "team2": team2}
        
        if season:
            params["season"] = season
            
        # Overall head-to-head stats
        overall_query = """
        SELECT 
            COUNT(*) as matches_played,
            SUM(CASE WHEN winner = :team1 THEN 1 ELSE 0 END) as team1_wins,
            SUM(CASE WHEN winner = :team2 THEN 1 ELSE 0 END) as team2_wins,
            SUM(CASE WHEN winner != :team1 AND winner != :team2 THEN 1 ELSE 0 END) as no_results,
            ROUND(SUM(CASE WHEN winner = :team1 THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as team1_win_percentage,
            ROUND(SUM(CASE WHEN winner = :team2 THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as team2_win_percentage,
            SUM(CASE WHEN toss_winner = :team1 THEN 1 ELSE 0 END) as team1_toss_wins,
            SUM(CASE WHEN toss_winner = :team2 THEN 1 ELSE 0 END) as team2_toss_wins,
            SUM(CASE WHEN toss_winner = :team1 AND winner = :team1 THEN 1 ELSE 0 END) as team1_won_after_winning_toss,
            SUM(CASE WHEN toss_winner = :team2 AND winner = :team2 THEN 1 ELSE 0 END) as team2_won_after_winning_toss
        FROM match_info
        WHERE (team1 = :team1 AND team2 = :team2) OR (team1 = :team2 AND team2 = :team1)
        """ + season_filter
        
        # Season-wise head-to-head stats
        season_query = """
        SELECT 
            season,
            COUNT(*) as matches_played,
            SUM(CASE WHEN winner = :team1 THEN 1 ELSE 0 END) as team1_wins,
            SUM(CASE WHEN winner = :team2 THEN 1 ELSE 0 END) as team2_wins,
            SUM(CASE WHEN winner != :team1 AND winner != :team2 THEN 1 ELSE 0 END) as no_results
        FROM match_info
        WHERE (team1 = :team1 AND team2 = :team2) OR (team1 = :team2 AND team2 = :team1)
        """ + season_filter + """
        GROUP BY season
        ORDER BY season
        """
        
        # Venue-wise head-to-head stats
        venue_query = """
        SELECT 
            venue,
            COUNT(*) as matches_played,
            SUM(CASE WHEN winner = :team1 THEN 1 ELSE 0 END) as team1_wins,
            SUM(CASE WHEN winner = :team2 THEN 1 ELSE 0 END) as team2_wins,
            SUM(CASE WHEN winner != :team1 AND winner != :team2 THEN 1 ELSE 0 END) as no_results
        FROM match_info
        WHERE (team1 = :team1 AND team2 = :team2) OR (team1 = :team2 AND team2 = :team1)
        """ + season_filter + """
        GROUP BY venue
        ORDER BY matches_played DESC
        """
        
        # Match list
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
        WHERE (team1 = :team1 AND team2 = :team2) OR (team1 = :team2 AND team2 = :team1)
        """ + season_filter + """
        ORDER BY match_date DESC
        """
        
        # Player performances in head-to-head matches
        batting_query = """
        WITH h2h_matches AS (
            SELECT filename
            FROM match_info
            WHERE (team1 = :team1 AND team2 = :team2) OR (team1 = :team2 AND team2 = :team1)
            """ + season_filter + """
        ),
        player_innings AS (
            SELECT 
                i.team,
                i.batsman,
                i.filename,
                SUM(i.runs_batsman) as runs,
                COUNT(*) as balls_faced
            FROM innings_data i
            JOIN h2h_matches h ON i.filename = h.filename
            GROUP BY i.team, i.batsman, i.filename
        )
        SELECT 
            team,
            batsman,
            COUNT(DISTINCT filename) as matches,
            SUM(runs) as total_runs,
            MAX(runs) as highest_score,
            ROUND(AVG(runs), 2) as avg_runs,
            SUM(balls_faced) as balls_faced,
            ROUND(SUM(runs)::numeric / SUM(balls_faced) * 100, 2) as strike_rate
        FROM player_innings
        GROUP BY team, batsman
        HAVING SUM(runs) >= 50
        ORDER BY total_runs DESC
        LIMIT 20
        """
        
        # Bowling performances in head-to-head matches
        bowling_query = """
        WITH h2h_matches AS (
            SELECT filename
            FROM match_info
            WHERE (team1 = :team1 AND team2 = :team2) OR (team1 = :team2 AND team2 = :team1)
            """ + season_filter + """
        ),
        wickets_by_bowler AS (
            SELECT 
                i.team,
                i.bowler,
                i.filename,
                COUNT(CASE WHEN i.wicket_details IS NOT NULL AND i.wicket_details != '' THEN 1 END) as wickets
            FROM innings_data i
            JOIN h2h_matches h ON i.filename = h.filename
            GROUP BY i.team, i.bowler, i.filename
        ),
        bowling_stats AS (
            SELECT 
                i.team,
                i.bowler,
                i.filename,
                COUNT(*) as balls_bowled,
                SUM(i.runs_total) as runs_conceded
            FROM innings_data i
            JOIN h2h_matches h ON i.filename = h.filename
            GROUP BY i.team, i.bowler, i.filename
        )
        SELECT 
            bs.team,
            bs.bowler,
            COUNT(DISTINCT bs.filename) as matches,
            SUM(COALESCE(wb.wickets, 0)) as total_wickets,
            MAX(COALESCE(wb.wickets, 0)) as best_bowling,
            SUM(bs.balls_bowled) as balls_bowled,
            SUM(bs.runs_conceded) as runs_conceded,
            ROUND(SUM(bs.runs_conceded)::numeric / (SUM(bs.balls_bowled) / 6.0), 2) as economy
        FROM bowling_stats bs
        LEFT JOIN wickets_by_bowler wb ON bs.team = wb.team AND bs.bowler = wb.bowler AND bs.filename = wb.filename
        GROUP BY bs.team, bs.bowler
        HAVING SUM(COALESCE(wb.wickets, 0)) > 0
        ORDER BY total_wickets DESC, economy
        LIMIT 20
        """
        
        overall_stats = execute_raw_sql(db, overall_query, params)
        season_stats = execute_raw_sql(db, season_query, params)
        venue_stats = execute_raw_sql(db, venue_query, params)
        matches = execute_raw_sql(db, matches_query, params)
        batting_performances = execute_raw_sql(db, batting_query, params)
        bowling_performances = execute_raw_sql(db, bowling_query, params)
        
        return {
            "team1": team1,
            "team2": team2,
            "overall_stats": overall_stats[0] if overall_stats else None,
            "season_stats": season_stats,
            "venue_stats": venue_stats,
            "matches": matches,
            "batting_performances": batting_performances,
            "bowling_performances": bowling_performances,
            "filters_applied": {
                "season": season
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching head-to-head stats: {str(e)}")

@router.get("/team/{team_name}/records")
def get_team_all_h2h_records(
    team_name: str,
    db: Session = Depends(get_db)
):
    """Get head-to-head records for a specific team against all opponents."""
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
            
        # Get head-to-head records against all opponents
        query = """
        WITH team_matches AS (
            SELECT 
                CASE 
                    WHEN team1 = :team_name THEN team2
                    ELSE team1
                END as opponent,
                CASE 
                    WHEN winner = :team_name THEN 1
                    WHEN winner IS NULL OR winner = '' THEN 0
                    ELSE -1
                END as result
            FROM match_info
            WHERE team1 = :team_name OR team2 = :team_name
        )
        
        SELECT 
            opponent,
            COUNT(*) as matches_played,
            SUM(CASE WHEN result = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN result = -1 THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN result = 0 THEN 1 ELSE 0 END) as no_results,
            ROUND(SUM(CASE WHEN result = 1 THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as win_percentage
        FROM team_matches
        GROUP BY opponent
        ORDER BY matches_played DESC, win_percentage DESC
        """
        
        h2h_records = execute_raw_sql(db, query, {"team_name": team_name})
        
        return {
            "team_name": team_name,
            "head_to_head_records": h2h_records
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team's head-to-head records: {str(e)}")

@router.get("/strongest-rivalries")
def get_strongest_rivalries(
    min_matches: int = Query(5, ge=3, description="Minimum number of matches played between teams"),
    db: Session = Depends(get_db)
):
    """Get the strongest rivalries based on number of matches and closeness of the contest."""
    try:
        query = """
        WITH team_matchups AS (
            SELECT 
                CASE 
                    WHEN team1 < team2 THEN team1 
                    ELSE team2 
                END as team_a,
                CASE 
                    WHEN team1 < team2 THEN team2 
                    ELSE team1 
                END as team_b,
                CASE 
                    WHEN team1 < team2 THEN 
                        CASE WHEN winner = team1 THEN 'team_a' 
                             WHEN winner = team2 THEN 'team_b' 
                             ELSE 'no_result' 
                        END
                    ELSE 
                        CASE WHEN winner = team1 THEN 'team_b' 
                             WHEN winner = team2 THEN 'team_a' 
                             ELSE 'no_result' 
                        END
                END as winner
            FROM match_info
        ),
        rivalry_stats AS (
            SELECT 
                team_a,
                team_b,
                COUNT(*) as matches_played,
                SUM(CASE WHEN winner = 'team_a' THEN 1 ELSE 0 END) as team_a_wins,
                SUM(CASE WHEN winner = 'team_b' THEN 1 ELSE 0 END) as team_b_wins,
                SUM(CASE WHEN winner = 'no_result' THEN 1 ELSE 0 END) as no_results,
                ROUND(SUM(CASE WHEN winner = 'team_a' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as team_a_win_percentage,
                ROUND(SUM(CASE WHEN winner = 'team_b' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as team_b_win_percentage,
                ABS(SUM(CASE WHEN winner = 'team_a' THEN 1 ELSE 0 END) - SUM(CASE WHEN winner = 'team_b' THEN 1 ELSE 0 END)) as win_difference,
                ROUND(ABS(
                    SUM(CASE WHEN winner = 'team_a' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100 - 
                    SUM(CASE WHEN winner = 'team_b' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100
                ), 2) as win_percentage_difference
            FROM team_matchups
            GROUP BY team_a, team_b
            HAVING COUNT(*) >= :min_matches
        )
        
        SELECT 
            team_a,
            team_b,
            matches_played,
            team_a_wins,
            team_b_wins,
            no_results,
            team_a_win_percentage,
            team_b_win_percentage,
            win_difference,
            win_percentage_difference,
            CASE 
                WHEN win_percentage_difference < 10 THEN 'Very Competitive'
                WHEN win_percentage_difference < 20 THEN 'Competitive'
                WHEN win_percentage_difference < 30 THEN 'Moderately Competitive'
                ELSE 'One-sided'
            END as rivalry_type,
            ROUND(
                (matches_played::numeric * 0.5) + 
                ((50 - win_percentage_difference) * 0.5) +
                (LEAST(team_a_wins, team_b_wins) * 0.2), 
                2
            ) as rivalry_score
        FROM rivalry_stats
        ORDER BY rivalry_score DESC, matches_played DESC
        LIMIT 20
        """
        
        rivalries = execute_raw_sql(db, query, {"min_matches": min_matches})
        
        return {
            "min_matches": min_matches,
            "rivalries": rivalries
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching strongest rivalries: {str(e)}")