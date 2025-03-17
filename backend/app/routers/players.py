from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.utils.db_utils import execute_raw_sql, query_to_dataframe

router = APIRouter(
    prefix="/api/players",
    tags=["Players"],
    responses={404: {"description": "Not found"}},
)

@router.get("/all")
def get_all_players(db: Session = Depends(get_db)):
    """Get all players with their roles."""
    try:
        # Query to get all player names and determine their roles
        query = """
        WITH batsmen AS (
            SELECT DISTINCT batsman as player_name FROM innings_data WHERE batsman IS NOT NULL
        ),
        bowlers AS (
            SELECT DISTINCT bowler as player_name FROM innings_data WHERE bowler IS NOT NULL
        ),
        player_of_match AS (
            SELECT DISTINCT player_of_match as player_name FROM match_info WHERE player_of_match IS NOT NULL
        ),
        batting_stats AS (
            SELECT 
                batsman as player_name,
                COUNT(*) as balls_faced,
                SUM(runs_batsman) as runs_scored
            FROM innings_data
            WHERE batsman IS NOT NULL
            GROUP BY batsman
        ),
        bowling_stats AS (
            SELECT 
                bowler as player_name,
                COUNT(*) as balls_bowled,
                COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) as wickets
            FROM innings_data
            WHERE bowler IS NOT NULL
            GROUP BY bowler
        ),
        combined_stats AS (
            SELECT 
                COALESCE(bat.player_name, bowl.player_name) as player_name,
                COALESCE(bat.balls_faced, 0) as balls_faced,
                COALESCE(bat.runs_scored, 0) as runs_scored,
                COALESCE(bowl.balls_bowled, 0) as balls_bowled,
                COALESCE(bowl.wickets, 0) as wickets
            FROM batting_stats bat
            FULL OUTER JOIN bowling_stats bowl ON bat.player_name = bowl.player_name
        ),
        player_roles AS (
            SELECT 
                player_name,
                CASE 
                    WHEN balls_faced > 0 AND balls_bowled = 0 THEN 'Batsman'
                    WHEN balls_faced = 0 AND balls_bowled > 0 THEN 'Bowler'
                    WHEN balls_faced > 0 AND balls_bowled > 0 THEN 'All-Rounder'
                    ELSE 'Unknown'
                END as role,
                balls_faced,
                runs_scored,
                balls_bowled,
                wickets
            FROM combined_stats
        )
        SELECT 
            player_name,
            role,
            balls_faced,
            runs_scored,
            balls_bowled,
            wickets,
            CASE
                WHEN EXISTS (SELECT 1 FROM player_of_match pom WHERE pom.player_name = pr.player_name) THEN true
                ELSE false
            END as has_won_pom
        FROM player_roles pr
        ORDER BY 
            CASE role
                WHEN 'All-Rounder' THEN 1
                WHEN 'Batsman' THEN 2
                WHEN 'Bowler' THEN 3
                ELSE 4
            END,
            player_name
        """
        
        players = execute_raw_sql(db, query)
        
        return {
            "players": players,
            "count": len(players)
        }
    
    except Exception as e:
        error_detail = f"Error fetching all players: {str(e)}"
        print(error_detail)  # Print to server logs for debugging
        raise HTTPException(status_code=500, detail=error_detail)

@router.get("/search")
def search_players(
    query: str = Query(..., min_length=2, description="Player name search query"),
    db: Session = Depends(get_db)
):
    """Search for players by name."""
    try:
        # Simplified search query to avoid potential issues with LIKE or Boolean conversions
        search_query = """
        WITH player_names AS (
            SELECT batsman as player_name, COUNT(*) as appearances FROM innings_data GROUP BY batsman
            UNION ALL
            SELECT bowler as player_name, COUNT(*) as appearances FROM innings_data GROUP BY bowler
            UNION ALL
            SELECT player_of_match as player_name, COUNT(*) as appearances FROM match_info GROUP BY player_of_match
        )
        SELECT DISTINCT 
            player_name,
            SUM(appearances) as total_appearances
        FROM player_names
        WHERE player_name IS NOT NULL AND player_name LIKE :search_term
        GROUP BY player_name
        ORDER BY total_appearances DESC
        LIMIT 20
        """
        
        params = {
            "search_term": f"%{query}%"
        }
        
        players = execute_raw_sql(db, search_query, params)
        
        if not players:
            return {"players": [], "count": 0}
        
        return {"players": players, "count": len(players)}
    
    except Exception as e:
        # Add more detailed error information to help diagnose
        error_detail = f"Error searching players: {str(e)}"
        print(error_detail)  # Print to server logs for debugging
        raise HTTPException(status_code=500, detail=error_detail)

@router.get("/{player_name}")
def get_player_stats(
    player_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a specific player."""
    try:
        # First, let's find the player by partial name with a more flexible approach
        find_player_query = """
        WITH player_names AS (
            SELECT batsman as player_name, COUNT(*) as appearances FROM innings_data GROUP BY batsman
            UNION ALL
            SELECT bowler as player_name, COUNT(*) as appearances FROM innings_data GROUP BY bowler
            UNION ALL
            SELECT player_of_match as player_name, COUNT(*) as appearances FROM match_info GROUP BY player_of_match
        )
        SELECT player_name, SUM(appearances) as total_appearances
        FROM player_names
        WHERE 
            player_name IS NOT NULL 
            AND (
                player_name LIKE :exact_match 
                OR player_name LIKE :first_word_match 
                OR player_name LIKE :last_name_match
                OR player_name LIKE :partial_match
            )
        GROUP BY player_name
        ORDER BY 
            CASE 
                WHEN LOWER(player_name) = LOWER(:exact_match) THEN 1
                WHEN LOWER(player_name) LIKE LOWER(:first_word_match) THEN 2
                WHEN LOWER(player_name) LIKE LOWER(:last_name_match) THEN 3
                ELSE 4
            END,
            total_appearances DESC
        LIMIT 1
        """
        
        # Split the player name for more flexible matching
        name_parts = player_name.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        
        search_params = {
            "exact_match": player_name,
            "first_word_match": f"{first_name}%",
            "last_name_match": f"%{last_name}",
            "partial_match": f"%{player_name}%"
        }
        
        players = execute_raw_sql(db, find_player_query, search_params)
        
        if not players:
            raise HTTPException(status_code=404, detail=f"Player not found: {player_name}")
        
        # Use the first matching player name from the database
        exact_player_name = players[0]["player_name"]
        print(f"Found player: {exact_player_name} for search: {player_name}")
        
        # Season filter clause
        season_filter = "AND m.season = :season" if season else ""
        
        # Get player batting statistics by season - FIXED UNION TYPE MISMATCH
        batting_query = f"""
        WITH player_batting AS (
            SELECT 
                i.*,
                m.season,
                m.match_date,
                m.venue,
                m.team1,
                m.team2,
                i.team as batting_team,
                CASE 
                    WHEN i.team = m.team1 THEN m.team2
                    ELSE m.team1
                END as bowling_team
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            WHERE i.batsman = :player_name
            {season_filter}
        ),
        season_stats AS (
            SELECT 
                season::text as season,  -- Convert to text to match with career stats
                COUNT(DISTINCT filename) as matches_played,
                COUNT(*) as balls_faced,
                SUM(runs_batsman) as runs_scored,
                MAX(runs_batsman) as highest_ball,
                ROUND(SUM(runs_batsman)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as strike_rate,
                SUM(CASE WHEN runs_batsman = 4 THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN runs_batsman = 6 THEN 1 ELSE 0 END) as sixes,
                COUNT(DISTINCT CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN filename END) as dismissals,
                ROUND(SUM(runs_batsman)::numeric / NULLIF(COUNT(DISTINCT CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN filename END), 0), 2) as average
            FROM player_batting
            GROUP BY season
            ORDER BY season
        ),
        innings_totals AS (
            SELECT 
                season::text as season,  -- Convert to text to match
                filename,
                innings_type,
                SUM(runs_batsman) as innings_total
            FROM player_batting
            GROUP BY season, filename, innings_type
        ),
        season_with_highest AS (
            SELECT 
                s.season,
                s.matches_played,
                s.balls_faced,
                s.runs_scored,
                MAX(i.innings_total) as highest_score,
                s.strike_rate,
                s.fours,
                s.sixes,
                s.dismissals,
                s.average
            FROM season_stats s
            LEFT JOIN innings_totals i ON s.season = i.season
            GROUP BY 
                s.season, s.matches_played, s.balls_faced, s.runs_scored,
                s.strike_rate, s.fours, s.sixes, s.dismissals, s.average
        ),
        career_totals AS (
            SELECT 
                SUM(runs_batsman) as total_runs,
                COUNT(*) as total_balls,
                SUM(CASE WHEN runs_batsman = 4 THEN 1 ELSE 0 END) as total_fours,
                SUM(CASE WHEN runs_batsman = 6 THEN 1 ELSE 0 END) as total_sixes,
                COUNT(DISTINCT CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN filename END) as total_dismissals,
                COUNT(DISTINCT filename) as total_matches
            FROM player_batting
        ),
        career_innings AS (
            SELECT 
                filename,
                innings_type,
                SUM(runs_batsman) as innings_total
            FROM player_batting
            GROUP BY filename, innings_type
        ),
        career_stats AS (
            SELECT 
                'Career' as season,
                ct.total_matches as matches_played,
                ct.total_balls as balls_faced,
                ct.total_runs as runs_scored,
                MAX(ci.innings_total) as highest_score,
                ROUND(ct.total_runs::numeric / NULLIF(ct.total_balls, 0) * 100, 2) as strike_rate,
                ct.total_fours as fours,
                ct.total_sixes as sixes,
                ct.total_dismissals as dismissals,
                ROUND(ct.total_runs::numeric / NULLIF(ct.total_dismissals, 0), 2) as average
            FROM career_totals ct
            LEFT JOIN career_innings ci ON 1=1
            GROUP BY 
                ct.total_matches, ct.total_balls, ct.total_runs,
                ct.total_fours, ct.total_sixes, ct.total_dismissals
        )
        
        SELECT * FROM season_with_highest
        UNION ALL
        SELECT * FROM career_stats
        ORDER BY 
            CASE WHEN season = 'Career' THEN '9999' ELSE season END
        """
        
        # Get player bowling statistics by season - FIXED UNION TYPE MISMATCH
        bowling_query = f"""
        WITH player_bowling AS (
            SELECT 
                i.*,
                m.season,
                m.match_date,
                m.venue,
                m.team1,
                m.team2,
                i.team as batting_team,
                CASE 
                    WHEN i.team = m.team1 THEN m.team2
                    ELSE m.team1
                END as bowling_team
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            WHERE i.bowler = :player_name
            {season_filter}
        ),
        wickets_by_match AS (
            SELECT 
                filename,
                season::text as season,  -- Convert to text
                COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) as wickets
            FROM player_bowling
            GROUP BY filename, season
        ),
        season_stats AS (
            SELECT 
                pb.season::text as season,  -- Convert to text
                COUNT(DISTINCT pb.filename) as matches_played,
                COUNT(*) as balls_bowled,
                ROUND(COUNT(*) / 6.0, 1) as overs_bowled,
                SUM(pb.runs_total) as runs_conceded,
                SUM(CASE WHEN pb.wicket_details IS NOT NULL AND pb.wicket_details != '' THEN 1 ELSE 0 END) as wickets,
                ROUND(SUM(pb.runs_total)::numeric / NULLIF(COUNT(*) / 6.0, 0), 2) as economy,
                ROUND(SUM(pb.runs_total)::numeric / NULLIF(SUM(CASE WHEN pb.wicket_details IS NOT NULL AND pb.wicket_details != '' THEN 1 ELSE 0 END), 0), 2) as bowling_average,
                CASE 
                    WHEN SUM(CASE WHEN pb.wicket_details IS NOT NULL AND pb.wicket_details != '' THEN 1 ELSE 0 END) > 0 THEN 
                        ROUND(COUNT(*)::numeric / SUM(CASE WHEN pb.wicket_details IS NOT NULL AND pb.wicket_details != '' THEN 1 ELSE 0 END), 2)
                    ELSE NULL
                END as bowling_strike_rate,
                COUNT(DISTINCT CASE WHEN w.wickets >= 3 THEN pb.filename END) as three_plus_wickets,
                COUNT(DISTINCT CASE WHEN w.wickets >= 5 THEN pb.filename END) as five_plus_wickets
            FROM player_bowling pb
            LEFT JOIN wickets_by_match w ON pb.filename = w.filename AND pb.season::text = w.season
            GROUP BY pb.season
            ORDER BY pb.season
        ),
        career_stats AS (
            SELECT 
                'Career' as season,
                COUNT(DISTINCT pb.filename) as matches_played,
                COUNT(*) as balls_bowled,
                ROUND(COUNT(*) / 6.0, 1) as overs_bowled,
                SUM(pb.runs_total) as runs_conceded,
                SUM(CASE WHEN pb.wicket_details IS NOT NULL AND pb.wicket_details != '' THEN 1 ELSE 0 END) as wickets,
                ROUND(SUM(pb.runs_total)::numeric / NULLIF(COUNT(*) / 6.0, 0), 2) as economy,
                ROUND(SUM(pb.runs_total)::numeric / NULLIF(SUM(CASE WHEN pb.wicket_details IS NOT NULL AND pb.wicket_details != '' THEN 1 ELSE 0 END), 0), 2) as bowling_average,
                CASE 
                    WHEN SUM(CASE WHEN pb.wicket_details IS NOT NULL AND pb.wicket_details != '' THEN 1 ELSE 0 END) > 0 THEN 
                        ROUND(COUNT(*)::numeric / SUM(CASE WHEN pb.wicket_details IS NOT NULL AND pb.wicket_details != '' THEN 1 ELSE 0 END), 2)
                    ELSE NULL
                END as bowling_strike_rate,
                COUNT(DISTINCT CASE WHEN w.wickets >= 3 THEN pb.filename END) as three_plus_wickets,
                COUNT(DISTINCT CASE WHEN w.wickets >= 5 THEN pb.filename END) as five_plus_wickets
            FROM player_bowling pb
            LEFT JOIN wickets_by_match w ON pb.filename = w.filename
            GROUP BY 1
        )
        SELECT * FROM season_stats
        UNION ALL
        SELECT * FROM career_stats
        ORDER BY 
            CASE WHEN season = 'Career' THEN '9999' ELSE season END
        """
        
        # Get player teams by season - FIXED TO CONVERT SEASON TO TEXT
        teams_query = f"""
        WITH player_teams AS (
            SELECT DISTINCT
                m.season::text as season,  -- Convert to text
                i.team
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            WHERE i.batsman = :player_name OR i.bowler = :player_name
            {season_filter}
        )
        SELECT 
            season,
            STRING_AGG(team, ', ') as teams
        FROM player_teams
        GROUP BY season
        ORDER BY season
        """
        
        # Get player achievements - FIXED TO CONVERT SEASON TO TEXT
        achievements_query = f"""
        WITH player_of_match AS (
            SELECT 
                season::text as season,  -- Convert to text
                COUNT(*) as count
            FROM match_info
            WHERE player_of_match = :player_name
            {season_filter}
            GROUP BY season
        ),
        fifty_plus AS (
            WITH player_innings AS (
                SELECT 
                    i.filename,
                    i.innings_type,
                    m.season::text as season,  -- Convert to text
                    SUM(i.runs_batsman) as runs
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE i.batsman = :player_name
                {season_filter}
                GROUP BY i.filename, i.innings_type, m.season
            )
            SELECT 
                season,
                COUNT(CASE WHEN runs >= 50 AND runs < 100 THEN 1 END) as fifties,
                COUNT(CASE WHEN runs >= 100 THEN 1 END) as hundreds
            FROM player_innings
            GROUP BY season
        ),
        bowling_milestones AS (
            WITH player_innings AS (
                SELECT 
                    i.filename,
                    i.innings_type,
                    m.season::text as season,  -- Convert to text
                    SUM(CASE WHEN i.wicket_details IS NOT NULL AND i.wicket_details != '' THEN 1 ELSE 0 END) as wickets
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE i.bowler = :player_name
                {season_filter}
                GROUP BY i.filename, i.innings_type, m.season
            )
            SELECT 
                season,
                COUNT(CASE WHEN wickets >= 3 AND wickets < 5 THEN 1 END) as three_wickets,
                COUNT(CASE WHEN wickets >= 5 THEN 1 END) as five_wickets
            FROM player_innings
            GROUP BY season
        )
        
        SELECT 
            COALESCE(pom.season, f.season, bm.season) as season,
            COALESCE(pom.count, 0) as player_of_match_awards,
            COALESCE(f.fifties, 0) as fifties,
            COALESCE(f.hundreds, 0) as hundreds,
            COALESCE(bm.three_wickets, 0) as three_wicket_hauls,
            COALESCE(bm.five_wickets, 0) as five_wicket_hauls
        FROM player_of_match pom
        FULL OUTER JOIN fifty_plus f ON pom.season = f.season
        FULL OUTER JOIN bowling_milestones bm ON COALESCE(pom.season, f.season) = bm.season
        ORDER BY 
            CASE 
                WHEN COALESCE(pom.season, f.season, bm.season) = 'Career' THEN '9999'
                ELSE COALESCE(pom.season, f.season, bm.season)
            END
        """
        
        # Get list of all seasons the player has played - FIXED TO RETURN TEXT SEASONS
        seasons_played_query = """
        SELECT DISTINCT m.season::text as season
        FROM innings_data i
        JOIN match_info m ON i.filename = m.filename
        WHERE i.batsman = :player_name OR i.bowler = :player_name
        ORDER BY season
        """
        
        params = {"player_name": exact_player_name}
        if season:
            params["season"] = season
            
        batting_stats = execute_raw_sql(db, batting_query, params)
        bowling_stats = execute_raw_sql(db, bowling_query, params)
        teams = execute_raw_sql(db, teams_query, params)
        achievements = execute_raw_sql(db, achievements_query, params)
        
        seasons_played = [row["season"] for row in execute_raw_sql(db, seasons_played_query, {"player_name": exact_player_name})]
        
        return {
            "player_name": exact_player_name,
            "searched_for": player_name,
            "batting_statistics": batting_stats,
            "bowling_statistics": bowling_stats,
            "teams_by_season": teams,
            "achievements": achievements,
            "seasons_played": seasons_played,
            "total_seasons_played": len(seasons_played),
            "filters_applied": {
                "season": season
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"Error fetching player stats: {str(e)}"
        print(error_detail)  # Print to server logs for debugging
        raise HTTPException(status_code=500, detail=error_detail)

@router.get("/top/{category}")
def get_top_players(
    category: str = Path(..., description="Category like 'runs', 'wickets', 'sixes'"),
    season: Optional[int] = None,
    limit: int = Query(10, ge=1, le=100, description="Number of players to return"),
    db: Session = Depends(get_db)
):
    """Get top players by different statistical categories."""
    try:
        season_filter = "AND m.season = :season" if season else ""
        
        if category.lower() == 'runs':
            query = f"""
            WITH player_batting AS (
                SELECT 
                    i.batsman as player_name,
                    i.runs_batsman,
                    i.filename,
                    i.innings_type,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            ),
            player_stats AS (
                SELECT 
                    player_name,
                    COUNT(DISTINCT filename) as matches,
                    SUM(runs_batsman) as runs,
                    ROUND(SUM(runs_batsman)::numeric / COUNT(*) * 100, 2) as strike_rate
                FROM player_batting
                GROUP BY player_name
            ),
            innings_totals AS (
                SELECT 
                    player_name,
                    filename,
                    innings_type,
                    SUM(runs_batsman) as innings_runs
                FROM player_batting
                GROUP BY player_name, filename, innings_type
            )
            SELECT 
                ps.player_name,
                ps.matches,
                ps.runs,
                COALESCE(MAX(it.innings_runs), 0) as highest_score,
                ps.strike_rate
            FROM player_stats ps
            LEFT JOIN innings_totals it ON ps.player_name = it.player_name
            GROUP BY ps.player_name, ps.matches, ps.runs, ps.strike_rate
            ORDER BY ps.runs DESC
            LIMIT :limit
            """
        elif category.lower() == 'fours':
            query = f"""
            WITH player_batting AS (
                SELECT 
                    i.batsman as player_name,
                    i.runs_batsman,
                    i.filename,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                SUM(CASE WHEN runs_batsman = 4 THEN 1 ELSE 0 END) as fours,
                SUM(runs_batsman) as runs
            FROM player_batting
            GROUP BY player_name
            ORDER BY fours DESC
            LIMIT :limit
            """
        elif category.lower() == 'sixes':
            query = f"""
            WITH player_batting AS (
                SELECT 
                    i.batsman as player_name,
                    i.runs_batsman,
                    i.filename,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                SUM(CASE WHEN runs_batsman = 6 THEN 1 ELSE 0 END) as sixes,
                SUM(runs_batsman) as runs
            FROM player_batting
            GROUP BY player_name
            ORDER BY sixes DESC
            LIMIT :limit
            """
        elif category.lower() == 'strike_rate':
            query = f"""
            WITH player_batting AS (
                SELECT 
                    i.batsman as player_name,
                    i.runs_batsman,
                    i.filename,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                SUM(runs_batsman) as runs,
                COUNT(*) as balls_faced,
                ROUND(SUM(runs_batsman)::numeric / COUNT(*) * 100, 2) as strike_rate
            FROM player_batting
            GROUP BY player_name
            HAVING COUNT(*) >= 60
            ORDER BY strike_rate DESC
            LIMIT :limit
            """
        elif category.lower() == 'average':
            query = f"""
            WITH player_batting AS (
                SELECT 
                    i.batsman as player_name,
                    i.runs_batsman,
                    i.wicket_details,
                    i.filename,
                    i.innings_type,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                SUM(runs_batsman) as runs,
                COUNT(DISTINCT CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN filename || innings_type END) as dismissals,
                ROUND(SUM(runs_batsman)::numeric / NULLIF(COUNT(DISTINCT CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN filename || innings_type END), 0), 2) as average
            FROM player_batting
            GROUP BY player_name
            HAVING COUNT(DISTINCT filename) >= 5 AND COUNT(DISTINCT CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN filename || innings_type END) > 0
            ORDER BY average DESC
            LIMIT :limit
            """
        elif category.lower() == 'fifties':
            query = f"""
            WITH player_batting AS (
                SELECT 
                    i.batsman as player_name,
                    i.runs_batsman,
                    i.filename,
                    i.innings_type,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            ),
            innings_totals AS (
                SELECT 
                    player_name,
                    filename,
                    innings_type,
                    SUM(runs_batsman) as runs
                FROM player_batting
                GROUP BY player_name, filename, innings_type
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                COUNT(CASE WHEN runs >= 50 AND runs < 100 THEN 1 END) as fifties,
                COUNT(CASE WHEN runs >= 100 THEN 1 END) as hundreds,
                SUM(runs) as total_runs
            FROM innings_totals
            GROUP BY player_name
            ORDER BY fifties DESC, hundreds DESC, total_runs DESC
            LIMIT :limit
            """
        elif category.lower() == 'hundreds':
            query = f"""
            WITH player_batting AS (
                SELECT 
                    i.batsman as player_name,
                    i.runs_batsman,
                    i.filename,
                    i.innings_type,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            ),
            innings_totals AS (
                SELECT 
                    player_name,
                    filename,
                    innings_type,
                    SUM(runs_batsman) as runs
                FROM player_batting
                GROUP BY player_name, filename, innings_type
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                COUNT(CASE WHEN runs >= 100 THEN 1 END) as hundreds,
                COUNT(CASE WHEN runs >= 50 AND runs < 100 THEN 1 END) as fifties,
                SUM(runs) as total_runs
            FROM innings_totals
            GROUP BY player_name
            ORDER BY hundreds DESC, fifties DESC, total_runs DESC
            LIMIT :limit
            """
        elif category.lower() == 'wickets':
            query = f"""
            WITH player_bowling AS (
                SELECT 
                    i.bowler as player_name,
                    i.wicket_details,
                    i.runs_total,
                    i.filename,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) as wickets,
                SUM(runs_total) as runs_conceded,
                ROUND(COUNT(*)::numeric / 6, 1) as overs
            FROM player_bowling
            GROUP BY player_name
            ORDER BY wickets DESC
            LIMIT :limit
            """
        elif category.lower() == 'economy':
            query = f"""
            WITH player_bowling AS (
                SELECT 
                    i.bowler as player_name,
                    i.wicket_details,
                    i.runs_total,
                    i.filename,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                ROUND(COUNT(*)::numeric / 6, 1) as overs,
                SUM(runs_total) as runs_conceded,
                COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) as wickets,
                ROUND(SUM(runs_total)::numeric / (COUNT(*) / 6.0), 2) as economy
            FROM player_bowling
            GROUP BY player_name
            HAVING COUNT(*) >= 60
            ORDER BY economy ASC
            LIMIT :limit
            """
        elif category.lower() == 'bowling_average':
            query = f"""
            WITH player_bowling AS (
                SELECT 
                    i.bowler as player_name,
                    i.wicket_details,
                    i.runs_total,
                    i.filename,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) as wickets,
                SUM(runs_total) as runs_conceded,
                ROUND(SUM(runs_total)::numeric / NULLIF(COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END), 0), 2) as bowling_average
            FROM player_bowling
            GROUP BY player_name
            HAVING COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) >= 10
            ORDER BY bowling_average ASC
            LIMIT :limit
            """
        elif category.lower() == 'bowling_strike_rate':
            query = f"""
            WITH player_bowling AS (
                SELECT 
                    i.bowler as player_name,
                    i.wicket_details,
                    i.runs_total,
                    i.filename,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) as wickets,
                ROUND(COUNT(*)::numeric / NULLIF(COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END), 0), 2) as bowling_strike_rate
            FROM player_bowling
            GROUP BY player_name
            HAVING COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) >= 10
            ORDER BY bowling_strike_rate ASC
            LIMIT :limit
            """
        elif category.lower() == 'three_wickets':
            query = f"""
            WITH player_bowling AS (
                SELECT 
                    i.bowler as player_name,
                    i.wicket_details,
                    i.filename,
                    i.innings_type,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            ),
            innings_wickets AS (
                SELECT 
                    player_name,
                    filename,
                    innings_type,
                    COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) as wickets
                FROM player_bowling
                GROUP BY player_name, filename, innings_type
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                COUNT(CASE WHEN wickets >= 3 AND wickets < 5 THEN 1 END) as three_wickets,
                COUNT(CASE WHEN wickets >= 5 THEN 1 END) as five_wickets,
                SUM(wickets) as total_wickets
            FROM innings_wickets
            GROUP BY player_name
            ORDER BY three_wickets DESC, five_wickets DESC, total_wickets DESC
            LIMIT :limit
            """
        elif category.lower() == 'five_wickets':
            query = f"""
            WITH player_bowling AS (
                SELECT 
                    i.bowler as player_name,
                    i.wicket_details,
                    i.filename,
                    i.innings_type,
                    m.season
                FROM innings_data i
                JOIN match_info m ON i.filename = m.filename
                WHERE 1=1
                {season_filter}
            ),
            innings_wickets AS (
                SELECT 
                    player_name,
                    filename,
                    innings_type,
                    COUNT(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 END) as wickets
                FROM player_bowling
                GROUP BY player_name, filename, innings_type
            )
            SELECT 
                player_name,
                COUNT(DISTINCT filename) as matches,
                COUNT(CASE WHEN wickets >= 5 THEN 1 END) as five_wickets,
                COUNT(CASE WHEN wickets >= 3 AND wickets < 5 THEN 1 END) as three_wickets,
                SUM(wickets) as total_wickets
            FROM innings_wickets
            GROUP BY player_name
            ORDER BY five_wickets DESC, three_wickets DESC, total_wickets DESC
            LIMIT :limit
            """
        else:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
            
        params = {"limit": limit}
        if season:
            params["season"] = season
            
        try:
            top_players = execute_raw_sql(db, query, params)
            
            return {
                "category": category,
                "season": season,
                "players": top_players,
                "count": len(top_players)
            }
        except Exception as query_error:
            error_detail = f"Error executing query: {str(query_error)}\nQuery: {query}\nParams: {params}"
            print(error_detail)
            raise HTTPException(status_code=500, detail=error_detail)
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"Error fetching top players: {str(e)}"
        print(error_detail)  # Print to server logs for debugging
        raise HTTPException(status_code=500, detail=error_detail)