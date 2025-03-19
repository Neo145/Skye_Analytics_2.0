# app/routers/ipl_records.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from typing import List, Dict, Any

router = APIRouter(
    prefix="/api/ipl-records",
    tags=["IPL Records"],
    responses={404: {"description": "Not found"}}
)

@router.get("/most-runs")
def get_most_runs(
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    """Get players with most runs in IPL history."""
    query = """
    WITH player_runs AS (
        SELECT 
            batsman as player_name,
            SUM(runs_batsman) as total_runs,
            COUNT(DISTINCT filename) as matches_played,
            ROUND(SUM(runs_batsman)::numeric / COUNT(DISTINCT filename), 2) as batting_average
        FROM innings_data
        GROUP BY batsman
    )
    SELECT 
        player_name,
        total_runs,
        matches_played,
        batting_average
    FROM player_runs
    ORDER BY total_runs DESC
    LIMIT :limit
    """
    
    try:
        results = db.execute(text(query), {"limit": limit}).fetchall()
        return {
            "category": "Most Runs in IPL",
            "records": [
                {
                    "player": row[0],
                    "total_runs": row[1],
                    "matches_played": row[2],
                    "batting_average": row[3]
                } for row in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/most-hundreds")
def get_most_hundreds(
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    """Get players with most hundreds in IPL history."""
    query = """
    WITH centuries AS (
        SELECT 
            batsman,
            COUNT(*) as hundreds,
            SUM(runs_batsman) as total_runs
        FROM (
            SELECT 
                batsman, 
                filename,
                SUM(runs_batsman) as runs_batsman
            FROM innings_data
            GROUP BY batsman, filename
        ) AS innings
        WHERE runs_batsman >= 100
        GROUP BY batsman
    )
    SELECT 
        batsman as player_name,
        hundreds,
        total_runs
    FROM centuries
    ORDER BY hundreds DESC, total_runs DESC
    LIMIT :limit
    """
    
    try:
        results = db.execute(text(query), {"limit": limit}).fetchall()
        return {
            "category": "Most Hundreds in IPL",
            "records": [
                {
                    "player": row[0],
                    "hundreds": row[1],
                    "total_runs": row[2]
                } for row in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/most-fifties")
def get_most_fifties(
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    """Get players with most fifties in IPL history."""
    query = """
    WITH fifties AS (
        SELECT 
            batsman,
            COUNT(*) as fifties,
            SUM(runs_batsman) as total_runs
        FROM (
            SELECT 
                batsman, 
                filename,
                SUM(runs_batsman) as runs_batsman
            FROM innings_data
            GROUP BY batsman, filename
        ) AS innings
        WHERE runs_batsman >= 50 AND runs_batsman < 100
        GROUP BY batsman
    )
    SELECT 
        batsman as player_name,
        fifties,
        total_runs
    FROM fifties
    ORDER BY fifties DESC, total_runs DESC
    LIMIT :limit
    """
    
    try:
        results = db.execute(text(query), {"limit": limit}).fetchall()
        return {
            "category": "Most Fifties in IPL",
            "records": [
                {
                    "player": row[0],
                    "fifties": row[1],
                    "total_runs": row[2]
                } for row in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/most-ducks")
def get_most_ducks(
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    """Get players with most ducks in IPL history."""
    query = """
    WITH duck_stats AS (
        SELECT 
            batsman,
            COUNT(*) as ducks,
            COUNT(DISTINCT filename) as total_matches
        FROM innings_data
        WHERE runs_batsman = 0
        GROUP BY batsman
    )
    SELECT 
        batsman as player_name,
        ducks,
        total_matches,
        ROUND(ducks::numeric / total_matches * 100, 2) as duck_percentage
    FROM duck_stats
    ORDER BY ducks DESC
    LIMIT :limit
    """
    
    try:
        results = db.execute(text(query), {"limit": limit}).fetchall()
        return {
            "category": "Most Ducks in IPL",
            "records": [
                {
                    "player": row[0],
                    "ducks": row[1],
                    "total_matches": row[2],
                    "duck_percentage": row[3]
                } for row in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/highest-batting-average")
def get_highest_batting_average(
    min_matches: int = 20,
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    """Get players with highest batting average in IPL history."""
    query = """
    WITH player_stats AS (
        SELECT 
            batsman as player_name,
            COUNT(DISTINCT filename) as matches_played,
            SUM(runs_batsman) as total_runs,
            COUNT(*) as total_innings,
            ROUND(SUM(runs_batsman)::numeric / NULLIF(COUNT(*) - COUNT(CASE WHEN runs_batsman = 0 THEN 1 END), 0), 2) as batting_average
        FROM innings_data
        GROUP BY batsman
        HAVING COUNT(DISTINCT filename) >= :min_matches
    )
    SELECT 
        player_name,
        matches_played,
        total_runs,
        batting_average
    FROM player_stats
    ORDER BY batting_average DESC
    LIMIT :limit
    """
    
    try:
        results = db.execute(text(query), {
            "min_matches": min_matches,
            "limit": limit
        }).fetchall()
        return {
            "category": "Highest Batting Average in IPL",
            "records": [
                {
                    "player": row[0],
                    "matches_played": row[1],
                    "total_runs": row[2],
                    "batting_average": row[3]
                } for row in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/highest-individual-score")
def get_highest_individual_score(
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    """Get highest individual scores in IPL history."""
    query = """
    WITH innings_scores AS (
        SELECT 
            batsman,
            filename,
            SUM(runs_batsman) as innings_score
        FROM innings_data
        GROUP BY batsman, filename
    )
    SELECT 
        batsman as player_name,
        MAX(innings_score) as highest_score,
        filename as match_id
    FROM innings_scores
    ORDER BY highest_score DESC
    LIMIT :limit
    """
    
    try:
        results = db.execute(text(query), {"limit": limit}).fetchall()
        return {
            "category": "Highest Individual Score in IPL",
            "records": [
                {
                    "player": row[0],
                    "highest_score": row[1],
                    "match_id": row[2]
                } for row in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/most-sixes")
def get_most_sixes(
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    """Get players with most sixes in IPL history."""
    query = """
    WITH six_stats AS (
        SELECT 
            batsman as player_name,
            COUNT(*) as total_sixes,
            COUNT(DISTINCT filename) as matches_played
        FROM innings_data
        WHERE runs_batsman = 6
        GROUP BY batsman
    )
    SELECT 
        player_name,
        total_sixes,
        matches_played,
        ROUND(total_sixes::numeric / matches_played, 2) as sixes_per_match
    FROM six_stats
    ORDER BY total_sixes DESC
    LIMIT :limit
    """
    
    try:
        results = db.execute(text(query), {"limit": limit}).fetchall()
        return {
            "category": "Most Sixes in IPL",
            "records": [
                {
                    "player": row[0],
                    "total_sixes": row[1],
                    "matches_played": row[2],
                    "sixes_per_match": row[3]
                } for row in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add more record-related endpoints for the remaining categories