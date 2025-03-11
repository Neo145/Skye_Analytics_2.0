from sqlalchemy import text
from sqlalchemy.orm import Session
import pandas as pd

def execute_raw_sql(db: Session, query: str, params: dict = None):
    """
    Execute raw SQL query and return results.
    
    Args:
        db (Session): SQLAlchemy database session
        query (str): SQL query string
        params (dict, optional): Parameters for the SQL query
        
    Returns:
        List[dict]: Query results as list of dictionaries
    """
    result = db.execute(text(query), params or {})
    column_names = result.keys()
    
    return [dict(zip(column_names, row)) for row in result.fetchall()]

def query_to_dataframe(db: Session, query: str, params: dict = None):
    """
    Execute SQL query and return results as a pandas DataFrame.
    
    Args:
        db (Session): SQLAlchemy database session
        query (str): SQL query string
        params (dict, optional): Parameters for the SQL query
        
    Returns:
        pandas.DataFrame: Query results as a DataFrame
    """
    result = db.execute(text(query), params or {})
    return pd.DataFrame(result.fetchall(), columns=result.keys())

def get_distinct_values(db: Session, table: str, column: str):
    """
    Get distinct values from a specific column in a table.
    
    Args:
        db (Session): SQLAlchemy database session
        table (str): Table name
        column (str): Column name
        
    Returns:
        List: List of distinct values
    """
    query = f"SELECT DISTINCT {column} FROM {table} ORDER BY {column}"
    result = db.execute(text(query))
    return [row[0] for row in result.fetchall()]

def get_match_count(db: Session):
    """
    Get total number of matches in the database.
    
    Args:
        db (Session): SQLAlchemy database session
        
    Returns:
        int: Total number of matches
    """
    query = "SELECT COUNT(*) FROM match_info"
    result = db.execute(text(query)).scalar()
    return result

def get_seasons(db: Session):
    """
    Get list of all seasons in the database.
    
    Args:
        db (Session): SQLAlchemy database session
        
    Returns:
        List[int]: List of seasons
    """
    query = "SELECT DISTINCT season FROM match_info ORDER BY season"
    result = db.execute(text(query))
    return [row[0] for row in result.fetchall()]

def get_teams(db: Session):
    """
    Get list of all teams that have played in IPL.
    
    Args:
        db (Session): SQLAlchemy database session
        
    Returns:
        List[str]: List of team names
    """
    query = """
    SELECT DISTINCT team 
    FROM (
        SELECT team1 as team FROM match_info
        UNION
        SELECT team2 as team FROM match_info
    ) as teams
    ORDER BY team
    """
    result = db.execute(text(query))
    return [row[0] for row in result.fetchall()]

def get_venues(db: Session):
    """
    Get list of all venues where IPL matches have been played.
    
    Args:
        db (Session): SQLAlchemy database session
        
    Returns:
        List[str]: List of venue names
    """
    query = "SELECT DISTINCT venue FROM match_info ORDER BY venue"
    result = db.execute(text(query))
    return [row[0] for row in result.fetchall()]

def get_players(db: Session):
    """
    Get list of all players who have played in IPL.
    
    Args:
        db (Session): SQLAlchemy database session
        
    Returns:
        List[str]: List of player names
    """
    query = """
    SELECT DISTINCT player 
    FROM (
        SELECT batsman as player FROM innings_data
        UNION
        SELECT bowler as player FROM innings_data
        UNION
        SELECT non_striker as player FROM innings_data
        UNION
        SELECT player_of_match as player FROM match_info
    ) as players
    WHERE player IS NOT NULL
    ORDER BY player
    """
    result = db.execute(text(query))
    return [row[0] for row in result.fetchall()]