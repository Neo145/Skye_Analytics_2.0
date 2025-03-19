from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
import json

class TeamPerformanceService:
    def __init__(self, db: Session):
        """
        Initialize the service with a database session
        
        Args:
            db (Session): SQLAlchemy database session
        """
        self.db = db

    def get_overall_team_performance(
        self, 
        season: Optional[int] = None, 
        min_matches: int = 5, 
        sort_by: str = 'win_percentage'
    ) -> List[Dict[str, Any]]:
        """
        Retrieve comprehensive team performance metrics
        
        Args:
            season: Optional season filter
            min_matches: Minimum matches to be considered
            sort_by: Metric to sort results
        
        Returns:
            List of team performance metrics
        """
        try:
            # Construct dynamic SQL query
            query = text(f"""
                WITH team_performance AS (
                    SELECT 
                        team,
                        COUNT(*) AS total_matches,
                        SUM(CASE WHEN winner = team THEN 1 ELSE 0 END) AS wins,
                        ROUND(SUM(CASE WHEN winner = team THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS win_percentage,
                        
                        -- Recent Performance (Last 10 matches)
                        (
                            SELECT COALESCE(
                                ROUND(
                                    SUM(CASE WHEN m.winner = t.team THEN 1.0 ELSE 0 END) / 
                                    GREATEST(COUNT(*), 1) * 100, 
                                    2
                                ),
                                0
                            )
                            FROM (
                                SELECT team, match_date, winner,
                                ROW_NUMBER() OVER (PARTITION BY team ORDER BY match_date DESC) AS match_rank
                                FROM match_info
                                WHERE team IN (t.team)
                                {'AND season = :season' if season else ''}
                            ) m
                            WHERE m.match_rank <= 10
                        ) AS last_10_performance,
                        
                        -- Winning Streak
                        (
                            SELECT MAX(consecutive_wins)
                            FROM (
                                SELECT 
                                    team, 
                                    SUM(CASE WHEN winner = team THEN 1 ELSE 0 END) OVER (
                                        PARTITION BY team 
                                        ORDER BY match_date 
                                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                                    ) AS running_wins,
                                    COUNT(*) OVER (
                                        PARTITION BY team, 
                                        SUM(CASE WHEN winner != team THEN 1 ELSE 0 END) OVER (
                                            PARTITION BY team 
                                            ORDER BY match_date
                                        )
                                    ) AS consecutive_wins
                                FROM match_info
                                WHERE team IN (t.team)
                                {'AND season = :season' if season else ''}
                            ) streak
                            WHERE team = t.team
                        ) AS max_winning_streak,
                        
                        -- Home vs Away Performance
                        SUM(CASE WHEN venue = 'Wankhede Stadium' AND winner = team THEN 1 ELSE 0 END) AS home_wins,
                        SUM(CASE WHEN venue != 'Wankhede Stadium' AND winner = team THEN 1 ELSE 0 END) AS away_wins
                    
                    FROM (
                        SELECT team, match_date, winner, venue
                        FROM (
                            SELECT team1 AS team, match_date, winner, venue FROM match_info
                            UNION
                            SELECT team2 AS team, match_date, winner, venue FROM match_info
                        ) all_matches
                        {'WHERE season = :season' if season else ''}
                    ) t
                    GROUP BY team
                )
                SELECT 
                    team,
                    total_matches,
                    wins,
                    win_percentage,
                    last_10_performance,
                    max_winning_streak,
                    home_wins,
                    away_wins,
                    ROUND(home_wins * 100.0 / NULLIF(total_matches, 0), 2) AS home_win_ratio,
                    ROUND(away_wins * 100.0 / NULLIF(total_matches, 0), 2) AS away_win_ratio
                FROM team_performance
                WHERE total_matches >= :min_matches
                ORDER BY {sort_by} DESC
            """)
            
            # Prepare query parameters
            params = {
                'min_matches': min_matches,
            }
            if season:
                params['season'] = season
            
            # Execute query
            results = self.db.execute(query, params)
            
            # Convert results to list of dictionaries
            return [
                {
                    "team": row.team,
                    "total_matches": row.total_matches,
                    "wins": row.wins,
                    "win_percentage": row.win_percentage,
                    "last_10_performance": row.last_10_performance,
                    "max_winning_streak": row.max_winning_streak,
                    "home_wins": row.home_wins,
                    "away_wins": row.away_wins,
                    "home_win_ratio": row.home_win_ratio,
                    "away_win_ratio": row.away_win_ratio
                }
                for row in results
            ]
        
        except Exception as e:
            # Log the error and re-raise or handle as needed
            print(f"Error in get_overall_team_performance: {e}")
            raise

    def get_head_to_head_performance(self, team1: str, team2: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive head-to-head performance between two teams
        
        Args:
            team1: First team name
            team2: Second team name
        
        Returns:
            Head-to-head performance metrics
        """
        try:
            query = text("""
                WITH head_to_head AS (
                    SELECT 
                        COUNT(*) AS total_matches,
                        SUM(CASE WHEN winner = :team1 THEN 1 ELSE 0 END) AS team1_wins,
                        SUM(CASE WHEN winner = :team2 THEN 1 ELSE 0 END) AS team2_wins,
                        
                        -- Seasonal Breakdown
                        (
                            SELECT json_agg(
                                json_build_object(
                                    'season', season,
                                    'total_matches', COUNT(*),
                                    'team1_wins', SUM(CASE WHEN winner = :team1 THEN 1 ELSE 0 END),
                                    'team2_wins', SUM(CASE WHEN winner = :team2 THEN 1 ELSE 0 END)
                                )
                            )
                            FROM match_info
                            WHERE 
                                (team1 = :team1 AND team2 = :team2) OR 
                                (team1 = :team2 AND team2 = :team1)
                            GROUP BY season
                        ) AS season_breakdown,
                        
                        -- Average Margin of Victory
                        ROUND(AVG(CASE WHEN winner = :team1 THEN 
                            CASE 
                                WHEN margin ~ '^[0-9]+ runs$' THEN CAST(SPLIT_PART(margin, ' ', 1) AS INTEGER)
                                WHEN margin ~ '^[0-9]+ wickets$' THEN CAST(SPLIT_PART(margin, ' ', 1) AS INTEGER)
                                ELSE 0 
                            END
                        ELSE NULL END), 2) AS avg_margin_team1,
                        
                        ROUND(AVG(CASE WHEN winner = :team2 THEN 
                            CASE 
                                WHEN margin ~ '^[0-9]+ runs$' THEN CAST(SPLIT_PART(margin, ' ', 1) AS INTEGER)
                                WHEN margin ~ '^[0-9]+ wickets$' THEN CAST(SPLIT_PART(margin, ' ', 1) AS INTEGER)
                                ELSE 0 
                            END
                        ELSE NULL END), 2) AS avg_margin_team2,
                        
                        -- Recent Matches
                        (
                            SELECT json_agg(
                                json_build_object(
                                    'match_date', match_date,
                                    'winner', winner,
                                    'margin', margin,
                                    'season', season
                                )
                                ORDER BY match_date DESC
                                LIMIT 5
                            )
                            FROM match_info
                            WHERE 
                                (team1 = :team1 AND team2 = :team2) OR 
                                (team1 = :team2 AND team2 = :team1)
                        ) AS recent_matches
                    FROM match_info
                    WHERE 
                        (team1 = :team1 AND team2 = :team2) OR 
                        (team1 = :team2 AND team2 = :team1)
                )
                SELECT 
                    total_matches,
                    team1_wins,
                    team2_wins,
                    avg_margin_team1,
                    avg_margin_team2,
                    season_breakdown,
                    recent_matches
                FROM head_to_head
            """)
            
            # Execute query
            result = self.db.execute(query, {
                'team1': team1,
                'team2': team2
            }).fetchone()
            
            # If no matches found, return empty result
            if not result:
                return {
                    "team1": team1,
                    "team2": team2,
                    "total_matches": 0,
                    "team1_wins": 0,
                    "team2_wins": 0,
                    "avg_margin_team1": None,
                    "avg_margin_team2": None,
                    "season_breakdown": [],
                    "recent_matches": []
                }
            
            # Convert to dictionary
            return {
                "team1": team1,
                "team2": team2,
                "total_matches": result.total_matches,
                "team1_wins": result.team1_wins,
                "team2_wins": result.team2_wins,
                "avg_margin_team1": result.avg_margin_team1,
                "avg_margin_team2": result.avg_margin_team2,
                "season_breakdown": result.season_breakdown or [],
                "recent_matches": result.recent_matches or []
            }
        
        except Exception as e:
            # Log the error and re-raise or handle as needed
            print(f"Error in get_head_to_head_performance: {e}")
            raise

    def get_performance_trends(self, team: str, seasons: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Retrieve performance trends for a specific team
        
        Args:
            team: Team name
            seasons: Optional list of seasons to analyze
        
        Returns:
            Team performance trends
        """
        try:
            # Construct base query with dynamic season filtering
            query = text(f"""
                WITH team_seasonal_performance AS (
                    SELECT 
                        season,
                        COUNT(*) AS total_matches,
                        SUM(CASE WHEN winner = :team THEN 1 ELSE 0 END) AS wins,
                        ROUND(SUM(CASE WHEN winner = :team THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS win_percentage,
                        SUM(CASE WHEN (team1 = :team OR team2 = :team) AND winner = :team THEN 1 ELSE 0 END) AS total_wins
                    FROM match_info
                    WHERE (team1 = :team OR team2 = :team)
                    {'AND season IN :seasons' if seasons else ''}
                    GROUP BY season
                )
                SELECT 
                    json_agg(
                        json_build_object(
                            'season', season,
                            'total_matches', total_matches,
                            'wins', wins,
                            'win_percentage', win_percentage,
                            'total_wins', total_wins
                        )
                    ) AS seasonal_trends,
                    
                    ROUND(AVG(win_percentage), 2) AS avg_win_percentage,
                    MAX(win_percentage) AS best_season_win_percentage,
                    MIN(win_percentage) AS worst_season_win_percentage
                FROM team_seasonal_performance
            """)
            
            # Prepare query parameters
            params = {'team': team}
            if seasons:
                params['seasons'] = tuple(seasons)
            
            # Execute query
            result = self.db.execute(query, params).fetchone()
            
            # Convert to dictionary
            return {
                "team": team,
                "seasonal_trends": result.seasonal_trends or [],
                "avg_win_percentage": result.avg_win_percentage,
                "best_season_win_percentage": result.best_season_win_percentage,
                "worst_season_win_percentage": result.worst_season_win_percentage
            }
        
        except Exception as e:
            # Log the error and re-raise or handle as needed
            print(f"Error in get_performance_trends: {e}")
            raise

    def get_opponent_performance(self, team: str, top_n: int = 5) -> Dict[str, Any]:
        """
        Retrieve performance against different opponents
        
        Args:
            team: Team name
            top_n: Number of top opponents to return
        
        Returns:
            Performance against different opponents
        """
        try:
            query = text("""
                WITH opponent_performance AS (
                    SELECT 
                        CASE 
                            WHEN team1 = :team THEN team2
                            ELSE team1
                        END AS opponent,
                        COUNT(*) AS total_matches,
                        SUM(CASE WHEN winner = :team THEN 1 ELSE 0 END) AS wins,
                        ROUND(SUM(CASE WHEN winner = :team THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS win_percentage,
                        ROUND(AVG(CASE WHEN winner = :team THEN 
                            CASE 
                                WHEN margin ~ '^[0-9]+ runs$' THEN CAST(SPLIT_PART(margin, ' ', 1) AS INTEGER)
                                WHEN margin ~ '^[0-9]+ wickets$' THEN CAST(SPLIT_PART(margin, ' ', 1) AS INTEGER)
                                ELSE 0 
                            END
                        ELSE NULL END), 2) AS avg_margin_of_victory
                    FROM match_info
                    WHERE team1 = :team OR team2 = :team
                    GROUP BY opponent
                )
                SELECT 
                    json_agg(
                        json_build_object(
                            'opponent', opponent,
                            'total_matches', total_matches,
                            'wins', wins,
                            'win_percentage', win_percentage,
                            'avg_margin_of_victory', avg_margin_of_victory
                        )
                        ORDER BY win_percentage DESC
                    ) AS opponent_performance
                FROM opponent_performance
                LIMIT :top_n
            """)
            
            # Execute query
            result = self.db.execute(query, {
                'team': team,
                'top_n': top_n
            }).fetchone()
            
            # If no data found, return empty result
            if not result or not result.opponent_performance:
                return {
                    "team": team,
                    "opponent_performance": [],
                    "total_opponents_analyzed": 0
                }
            
            # Convert to dictionary
            return {
                "team": team,
                "opponent_performance": result.opponent_performance,
                "total_opponents_analyzed": len(result.opponent_performance)
            }
        
        except Exception as e:
            # Log the error and re-raise or handle as needed
            print(f"Error in get_opponent_performance: {e}")
            raise