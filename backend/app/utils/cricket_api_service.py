import requests
import json
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from app.database import get_db, engine
from sqlalchemy import text

# API Configuration
API_BASE_URL = "https://api.cricapi.com/v1"
API_KEY = "52b08390-6e7b-4233-b038-b39ed015ede7"  # Your API key

class CricketAPIService:
    def __init__(self, api_key: str = API_KEY):
        self.api_key = api_key
        self.base_url = API_BASE_URL
    
    def fetch_current_matches(self, offset: int = 0) -> Dict[str, Any]:
        """
        Fetch current/recent matches from the Cricket API
        """
        endpoint = f"{self.base_url}/currentMatches"
        params = {
            "apikey": self.api_key,
            "offset": offset
        }
        
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Request failed with status code {response.status_code}: {response.text}")
            
    def fetch_upcoming_matches(self) -> Dict[str, Any]:
        """
        Fetch upcoming matches from the Cricket API
        """
        endpoint = f"{self.base_url}/matches"
        params = {
            "apikey": self.api_key
        }
        
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Request failed with status code {response.status_code}: {response.text}")
    
    def fetch_match_info(self, match_id: str) -> Dict[str, Any]:
        """
        Fetch detailed information for a specific match
        """
        endpoint = f"{self.base_url}/match_info"
        params = {
            "apikey": self.api_key,
            "id": match_id
        }
        
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Request failed with status code {response.status_code}: {response.text}")
    
    def fetch_series_info(self, series_id: str) -> Dict[str, Any]:
        """
        Fetch detailed information for a specific series
        """
        endpoint = f"{self.base_url}/series_info"
        params = {
            "apikey": self.api_key,
            "id": series_id
        }
        
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Request failed with status code {response.status_code}: {response.text}")
    
    def fetch_player_info(self, player_id: str) -> Dict[str, Any]:
        """
        Fetch detailed information for a specific player
        """
        endpoint = f"{self.base_url}/players_info"
        params = {
            "apikey": self.api_key,
            "id": player_id
        }
        
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Request failed with status code {response.status_code}: {response.text}")
    
    def search_players(self, name: str, offset: int = 0) -> Dict[str, Any]:
        """
        Search for players by name
        """
        endpoint = f"{self.base_url}/players"
        params = {
            "apikey": self.api_key,
            "offset": offset,
            "search": name
        }
        
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Request failed with status code {response.status_code}: {response.text}")
    
    def search_series(self, name: str, offset: int = 0) -> Dict[str, Any]:
        """
        Search for series by name
        """
        endpoint = f"{self.base_url}/series"
        params = {
            "apikey": self.api_key,
            "offset": offset,
            "search": name
        }
        
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API Request failed with status code {response.status_code}: {response.text}")

# Database operations
def save_matches_to_db(db: Session, matches_data: List[Dict[str, Any]]) -> int:
    """
    Save match data to the database
    
    Args:
        db: Database session
        matches_data: List of match data dictionaries from API
        
    Returns:
        Number of matches saved
    """
    saved_count = 0
    
    for match in matches_data:
        # Extract year from the match date
        match_year = None
        if "date" in match and match["date"]:
            try:
                match_year = int(match["date"].split("-")[0])
            except (ValueError, IndexError):
                pass
        
        # Convert teams and score to JSONB
        teams_json = json.dumps(match.get("teams", []))
        score_json = json.dumps(match.get("score", []))
        toss_json = json.dumps(match.get("toss", {}))
        
        # Create SQL statement to insert match
        sql = text("""
            INSERT INTO cricket_matches 
            (id, name, match_type, status, venue, date, date_time_gmt, 
             series_id, teams, score, toss, result, year, raw_data, created_at)
            VALUES 
            (:id, :name, :match_type, :status, :venue, :date, :date_time_gmt,
             :series_id, :teams::jsonb, :score::jsonb, :toss::jsonb, :result, :year, :raw_data::jsonb, NOW())
            ON CONFLICT (id) DO UPDATE
            SET 
                status = EXCLUDED.status,
                score = EXCLUDED.score::jsonb,
                raw_data = EXCLUDED.raw_data::jsonb,
                result = EXCLUDED.result
            RETURNING id
        """)
        
        try:
            result = db.execute(sql, {
                "id": match.get("id"),
                "name": match.get("name"),
                "match_type": match.get("matchType"),
                "status": match.get("status"),
                "venue": match.get("venue"),
                "date": match.get("date"),
                "date_time_gmt": match.get("dateTimeGMT"),
                "series_id": match.get("series_id"),
                "teams": teams_json,
                "score": score_json,
                "toss": toss_json,
                "result": match.get("status"),  # Using status as result
                "year": match_year,
                "raw_data": json.dumps(match)
            })
            
            db.commit()
            saved_count += 1
        except Exception as e:
            db.rollback()
            print(f"Error saving match {match.get('id')}: {str(e)}")
    
    return saved_count

def save_series_to_db(db: Session, series_data: Dict[str, Any]) -> bool:
    """
    Save series data to the database
    
    Args:
        db: Database session
        series_data: Series data dictionary from API
        
    Returns:
        Boolean indicating success
    """
    # Extract year from start_date if available
    series_year = None
    if "startDate" in series_data and series_data["startDate"]:
        try:
            series_year = int(series_data["startDate"].split("-")[0])
        except (ValueError, IndexError):
            pass
    
    # Create SQL statement to insert series
    sql = text("""
        INSERT INTO cricket_series 
        (id, name, start_date, end_date, odi, t20, test, squads, matches, year, raw_data, created_at)
        VALUES 
        (:id, :name, :start_date, :end_date, :odi, :t20, :test, :squads, :matches, :year, :raw_data::jsonb, NOW())
        ON CONFLICT (id) DO UPDATE
        SET 
            name = EXCLUDED.name,
            start_date = EXCLUDED.start_date,
            end_date = EXCLUDED.end_date,
            raw_data = EXCLUDED.raw_data::jsonb
        RETURNING id
    """)
    
    try:
        db.execute(sql, {
            "id": series_data.get("id"),
            "name": series_data.get("name"),
            "start_date": series_data.get("startDate"),
            "end_date": series_data.get("endDate"),
            "odi": series_data.get("odi", 0),
            "t20": series_data.get("t20", 0),
            "test": series_data.get("test", 0),
            "squads": series_data.get("squads", 0),
            "matches": series_data.get("matches", 0),
            "year": series_year,
            "raw_data": json.dumps(series_data)
        })
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error saving series {series_data.get('id')}: {str(e)}")
        return False

def save_players_to_db(db: Session, players_data: List[Dict[str, Any]]) -> int:
    """
    Save player data to the database
    
    Args:
        db: Database session
        players_data: List of player data dictionaries from API
        
    Returns:
        Number of players saved
    """
    saved_count = 0
    
    for player in players_data:
        # Create SQL statement to insert player
        sql = text("""
            INSERT INTO ipl_players 
            (id, name, country, playing_role, batting_style, bowling_style, raw_data)
            VALUES 
            (:id, :name, :country, :playing_role, :batting_style, :bowling_style, :raw_data::jsonb)
            ON CONFLICT (id) DO UPDATE
            SET 
                name = EXCLUDED.name,
                country = EXCLUDED.country,
                playing_role = EXCLUDED.playing_role,
                batting_style = EXCLUDED.batting_style,
                bowling_style = EXCLUDED.bowling_style,
                raw_data = EXCLUDED.raw_data::jsonb
            RETURNING id
        """)
        
        try:
            result = db.execute(sql, {
                "id": player.get("id"),
                "name": player.get("name"),
                "country": player.get("country"),
                "playing_role": player.get("playingRole"),
                "batting_style": player.get("battingStyle"),
                "bowling_style": player.get("bowlingStyle"),
                "raw_data": json.dumps(player)
            })
            
            db.commit()
            saved_count += 1
        except Exception as e:
            db.rollback()
            print(f"Error saving player {player.get('id')}: {str(e)}")
    
    return saved_count

# Usage example - to be used in a script or API endpoint
def fetch_and_save_current_matches(db: Session = None):
    """
    Fetch current matches from API and save to database
    """
    api_service = CricketAPIService()
    
    # Create a database session if not provided
    close_db = False
    if db is None:
        db = next(get_db())
        close_db = True
    
    try:
        # Fetch current matches
        matches_response = api_service.fetch_current_matches()
        
        if "data" in matches_response and matches_response["data"]:
            # Save matches to database
            saved_count = save_matches_to_db(db, matches_response["data"])
            print(f"Saved {saved_count} matches to database")
            
            # Fetch and save related series
            for match in matches_response["data"]:
                if "series_id" in match and match["series_id"]:
                    try:
                        series_response = api_service.fetch_series_info(match["series_id"])
                        if "data" in series_response:
                            save_series_to_db(db, series_response["data"])
                    except Exception as e:
                        print(f"Error fetching series {match['series_id']}: {str(e)}")
            
            return saved_count
        else:
            print("No matches data found in API response")
            return 0
    except Exception as e:
        print(f"Error in fetch_and_save_current_matches: {str(e)}")
        return 0
    finally:
        if close_db:
            db.close()

# Example of how to use the API service in a script
if __name__ == "__main__":
    fetch_and_save_current_matches()