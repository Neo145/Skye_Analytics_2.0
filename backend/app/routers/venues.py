from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.utils.db_utils import execute_raw_sql, query_to_dataframe

router = APIRouter(
    prefix="/api/venues",
    tags=["Venues"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
def get_venues(
    db: Session = Depends(get_db)
):
    """Get list of all venues with basic statistics."""
    try:
        query = """
        SELECT 
            venue,
            city,
            COUNT(*) as matches_hosted,
            COUNT(DISTINCT season) as seasons_used,
            MIN(season) as first_season,
            MAX(season) as last_season
        FROM match_info
        GROUP BY venue, city
        ORDER BY matches_hosted DESC
        """
        
        venues_data = execute_raw_sql(db, query)
        return {"venues": venues_data}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching venues: {str(e)}")

@router.get("/{venue_name}")
def get_venue_stats(
    venue_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a specific venue."""
    try:
        # Build filter for seasons
        season_filter = "AND m.season = :season" if season else ""
        params = {"venue_name": venue_name}
        
        if season:
            params["season"] = season
            
        # Check if venue exists
        check_query = """
        SELECT COUNT(*) 
        FROM match_info 
        WHERE venue = :venue_name
        """
        
        count = db.execute(text(check_query), {"venue_name": venue_name}).scalar()
        
        if count == 0:
            raise HTTPException(status_code=404, detail=f"Venue not found: {venue_name}")
            
        # Basic venue stats
        basic_stats_query = f"""
        SELECT 
            venue,
            city,
            COUNT(*) as matches_hosted,
            COUNT(DISTINCT season) as seasons_used,
            MIN(season) as first_season,
            MAX(season) as last_season,
            COUNT(DISTINCT team1) + COUNT(DISTINCT team2) as teams_played
        FROM match_info m
        WHERE venue = :venue_name
        {season_filter}
        GROUP BY venue, city
        """
        
        basic_stats = execute_raw_sql(db, basic_stats_query, params)
        
        # Match outcomes
        outcomes_query = f"""
        SELECT 
            COUNT(*) as total_matches,
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
            END)::numeric / NULLIF(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END), 0) * 100, 2) as fielding_first_win_percentage,
            SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END) as toss_winner_won_match,
            ROUND(SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as toss_winner_win_percentage
        FROM match_info m
        WHERE venue = :venue_name
        {season_filter}
        """
        
        outcomes = execute_raw_sql(db, outcomes_query, params)
        
        # Season-wise stats
        season_stats_query = f"""
        SELECT 
            season,
            COUNT(*) as total_matches,
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
        WHERE venue = :venue_name
        {season_filter}
        GROUP BY season
        ORDER BY season
        """
        
        season_stats = execute_raw_sql(db, season_stats_query, params)
        
        # Team performance at venue
        team_stats_query = f"""
        WITH team_matches AS (
            SELECT 
                team_name,
                m.season,
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
            WHERE m.venue = :venue_name
            {season_filter}
        )
        SELECT 
            team_name,
            COUNT(*) as matches_played,
            SUM(is_win) as matches_won,
            ROUND(SUM(is_win)::numeric / COUNT(*) * 100, 2) as win_percentage,
            COUNT(DISTINCT season) as seasons
        FROM team_matches
        GROUP BY team_name
        ORDER BY matches_played DESC, win_percentage DESC
        """
        
        team_stats = execute_raw_sql(db, team_stats_query, params)
        
        # Batting and bowling stats at venue
        batting_stats_query = f"""
        WITH venue_batting AS (
            SELECT 
                i.*,
                m.season,
                m.venue
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            WHERE m.venue = :venue_name
            {season_filter}
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
        FROM venue_batting
        GROUP BY batsman
        HAVING COUNT(*) >= 30
        ORDER BY runs DESC
        LIMIT 20
        """
        
        # Bowling stats at venue
        bowling_stats_query = f"""
        WITH venue_bowling AS (
            SELECT 
                i.*,
                m.season,
                m.venue
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            WHERE m.venue = :venue_name
            {season_filter}
        ),
        wickets_by_bowler AS (
            SELECT 
                bowler,
                COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) as wickets
            FROM venue_bowling
            GROUP BY bowler
        )
        SELECT 
            vb.bowler,
            COUNT(DISTINCT vb.filename) as matches,
            COUNT(*) as balls_bowled,
            ROUND(COUNT(*)::numeric / 6, 1) as overs,
            SUM(vb.runs_total) as runs_conceded,
            COALESCE(wb.wickets, 0) as wickets,
            ROUND(SUM(vb.runs_total)::numeric / (COUNT(*) / 6.0), 2) as economy
        FROM venue_bowling vb
        LEFT JOIN wickets_by_bowler wb ON vb.bowler = wb.bowler
        GROUP BY vb.bowler, wb.wickets
        HAVING COUNT(*) >= 30
        ORDER BY COALESCE(wb.wickets, 0) DESC, economy
        LIMIT 20
        """
        
        # Recent matches at venue
        recent_matches_query = f"""
        SELECT 
            filename,
            match_date,
            team1,
            team2,
            toss_winner,
            toss_decision,
            winner,
            margin,
            player_of_match
        FROM match_info m
        WHERE venue = :venue_name
        {season_filter}
        ORDER BY match_date DESC
        LIMIT 10
        """
        
        batting_stats = execute_raw_sql(db, batting_stats_query, params)
        bowling_stats = execute_raw_sql(db, bowling_stats_query, params)
        recent_matches = execute_raw_sql(db, recent_matches_query, params)
        
        return {
            "venue_name": venue_name,
            "basic_stats": basic_stats[0] if basic_stats else None,
            "match_outcomes": outcomes[0] if outcomes else None,
            "season_stats": season_stats,
            "team_stats": team_stats,
            "batting_stats": batting_stats,
            "bowling_stats": bowling_stats,
            "recent_matches": recent_matches,
            "filters_applied": {
                "season": season
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_venue_stats: {str(e)}")
        print(f"Venue: {venue_name}, Season: {season}")
        raise HTTPException(status_code=500, detail=f"Error fetching venue stats: {str(e)}")

@router.get("/comparisons")
def compare_venues(
    venues: str = Query(..., description="Comma-separated list of venue names to compare"),
    db: Session = Depends(get_db)
):
    """Compare statistics for multiple venues."""
    try:
        # Parse comma-separated venues
        venue_list = [venue.strip() for venue in venues.split(',')]
        
        if not venue_list:
            raise HTTPException(status_code=400, detail="At least one venue must be specified")
            
        # Format venue list for SQL IN clause
        venue_placeholders = ', '.join([f"'{venue}'" for venue in venue_list])
        venue_in_clause = f"({venue_placeholders})"
        
        # Basic venue comparison
        comparison_query = f"""
        SELECT 
            venue,
            city,
            COUNT(*) as matches_hosted,
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
            END)::numeric / NULLIF(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END), 0) * 100, 2) as fielding_first_win_percentage,
            ROUND(SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as bat_first_percentage,
            ROUND(SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as field_first_percentage,
            ROUND(SUM(CASE WHEN winner = toss_winner THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as toss_winner_win_percentage
        FROM match_info m
        WHERE venue IN {venue_in_clause}
        GROUP BY venue, city
        ORDER BY matches_hosted DESC
        """
        
        # Batting statistics comparison
        batting_comparison_query = f"""
        WITH venue_innings AS (
            SELECT 
                m.venue,
                i.innings_type,
                i.filename,
                SUM(i.runs_total) as total_runs,
                COUNT(*) as balls,
                SUM(CASE WHEN i.runs_batsman = 4 THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN i.runs_batsman = 6 THEN 1 ELSE 0 END) as sixes,
                COUNT(CASE WHEN i.wicket_details IS NOT NULL AND i.wicket_details != '' THEN 1 END) as wickets
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            WHERE m.venue IN {venue_in_clause}
            GROUP BY m.venue, i.innings_type, i.filename
        )
        SELECT 
            venue,
            ROUND(AVG(total_runs), 2) as avg_innings_score,
            ROUND(AVG(balls), 2) as avg_balls_per_innings,
            ROUND(AVG(wickets), 2) as avg_wickets_per_innings,
            ROUND(AVG(fours), 2) as avg_fours_per_innings,
            ROUND(AVG(sixes), 2) as avg_sixes_per_innings,
            ROUND(SUM(total_runs)::numeric / SUM(balls) * 6, 2) as run_rate,
            ROUND(SUM(total_runs)::numeric / NULLIF(SUM(wickets), 0), 2) as runs_per_wicket
        FROM venue_innings
        GROUP BY venue
        ORDER BY avg_innings_score DESC
        """
        
        comparison_data = execute_raw_sql(db, comparison_query)
        batting_comparison = execute_raw_sql(db, batting_comparison_query)
        
        return {
            "venues_compared": venue_list,
            "comparison_data": comparison_data,
            "batting_comparison": batting_comparison
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in compare_venues: {str(e)}")
        print(f"Venues parameter: {venues}")
        raise HTTPException(status_code=500, detail=f"Error comparing venues: {str(e)}")