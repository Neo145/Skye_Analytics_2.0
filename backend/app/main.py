from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.database import get_db
from app.utils.db_utils import (
    execute_raw_sql, 
    query_to_dataframe,
    get_distinct_values,
    get_match_count,
    get_seasons,
    get_teams,
    get_venues,
    get_players
)

# Import routers
from app.routers import teams, players, matches, venues, toss, head_to_head

# Create FastAPI instance
app = FastAPI(
    title="IPL Analytics 2.0 API",
    description="API for analyzing IPL data from 2008 to 2024",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://skyeanalytics.in",  # Production frontend domain
        "http://localhost:5173",     # Local development
        "https://www.skyeanalytics.in"  # Optional: include www subdomain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(teams.router)
app.include_router(players.router)
app.include_router(matches.router)
app.include_router(venues.router)
app.include_router(toss.router)
app.include_router(head_to_head.router)

# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint to check if API is running."""
    return {"message": "Welcome to IPL Analytics 2.0 API"}

# Database connection test endpoint
@app.get("/db-test")
def test_db_connection(db: Session = Depends(get_db)):
    """Test database connection and return basic stats."""
    try:
        match_count = get_match_count(db)
        seasons = get_seasons(db)
        return {
            "status": "success",
            "database": "connected",
            "match_count": match_count,
            "seasons": seasons
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Get basic cricket entities (teams, venues, players)
@app.get("/entities")
def get_cricket_entities(db: Session = Depends(get_db)):
    """Get basic cricket entities for the frontend."""
    try:
        return {
            "teams": get_teams(db),
            "venues": get_venues(db),
            "seasons": get_seasons(db),
            "match_count": get_match_count(db)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching entities: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)