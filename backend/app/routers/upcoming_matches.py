# app/routers/upcoming_matches.py (using SQLAlchemy models)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from app.database import get_db
from app.utils.cricket_api_service import CricketAPIService
from app.models.upcoming_matches import UpcomingMatch

router = APIRouter(
    prefix="/api/ipl",
    tags=["IPL Matches"],
    responses={404: {"description": "Not found"}},
)

def format_match_data(match: Dict[str, Any]) -> Dict[str, Any]:
    """Format match data for frontend consumption"""
    # Parse date and time
    match_datetime = None
    if "dateTimeGMT" in match and match["dateTimeGMT"]:
        try:
            match_datetime = datetime.strptime(match["dateTimeGMT"], "%Y-%m-%dT%H:%M:%S")
            match_date = match_datetime.strftime("%d %b %Y")
            match_time = match_datetime.strftime("%H:%M")
        except ValueError:
            match_date = match.get("dateTimeGMT", "").split("T")[0]
            match_time = "TBD"
    else:
        match_date = "TBD"
        match_time = "TBD"
    
    # Extract team names without brackets if present
    team1 = match.get("t1", "")
    team2 = match.get("t2", "")
    
    if "[" in team1:
        team1_name = team1.split("[")[0].strip()
        team1_code = team1.split("[")[1].replace("]", "").strip()
    else:
        team1_name = team1
        team1_code = ""
        
    if "[" in team2:
        team2_name = team2.split("[")[0].strip()
        team2_code = team2.split("[")[1].replace("]", "").strip()
    else:
        team2_name = team2
        team2_code = ""
    
    # Format scores
    team1_score = match.get("t1s", "")
    team2_score = match.get("t2s", "")
    
    return {
        "id": match.get("id", ""),
        "match_date": match_date,
        "match_time": match_time,
        "match_type": match.get("matchType", ""),
        "status": match.get("status", ""),
        "match_state": match.get("ms", ""),
        "team1": {
            "name": team1_name,
            "code": team1_code,
            "score": team1_score,
            "image": match.get("t1img", "")
        },
        "team2": {
            "name": team2_name,
            "code": team2_code,
            "score": team2_score,
            "image": match.get("t2img", "")
        },
        "series": match.get("series", ""),
        "venue": match.get("venue", ""),
        "raw_data": match
    }

def save_upcoming_matches_to_db(db: Session, matches: List[Dict[str, Any]]) -> int:
    """Save upcoming matches to database using SQLAlchemy models"""
    saved_count = 0
    
    try:
        for match in matches:
            # Skip if not IPL match
            if "series" not in match or "Indian Premier League" not in match.get("series", ""):
                continue
                
            match_date = None
            if "dateTimeGMT" in match and match["dateTimeGMT"]:
                try:
                    match_date = datetime.strptime(match["dateTimeGMT"], "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    pass
            
            # Check if match already exists
            existing_match = db.query(UpcomingMatch).filter(UpcomingMatch.id == match.get("id")).first()
            
            if existing_match:
                # Update existing match
                existing_match.match_date = match_date
                existing_match.team1 = match.get("t1", "")
                existing_match.team2 = match.get("t2", "")
                existing_match.series = match.get("series", "")
                existing_match.raw_data = match
            else:
                # Create new match
                new_match = UpcomingMatch(
                    id=match.get("id"),
                    match_date=match_date,
                    team1=match.get("t1", ""),
                    team2=match.get("t2", ""),
                    series=match.get("series", ""),
                    raw_data=match
                )
                db.add(new_match)
            
            saved_count += 1
        
        db.commit()
        return saved_count
    except Exception as e:
        db.rollback()
        print(f"Error in save_upcoming_matches_to_db: {str(e)}")
        return 0

@router.get("/upcoming-matches")
async def get_upcoming_matches(
    refresh: bool = Query(True, description="Fetch data directly from the API"),
    db: Session = Depends(get_db)
):
    """
    Get upcoming IPL matches.
    Always fetches fresh data from the API by default.
    """
    try:
        if refresh:
            # Fetch fresh data from API
            api_service = CricketAPIService()
            response = api_service.fetch_upcoming_matches()
            
            if "data" not in response or not response["data"]:
                return {"message": "No upcoming matches found", "matches": []}
            
            # Filter for IPL matches only
            ipl_matches = [match for match in response["data"] 
                          if "series" in match and "Indian Premier League" in match.get("series", "")]
            
            # Format match data for frontend
            formatted_matches = [format_match_data(match) for match in ipl_matches]
            
            # Sort by date (closest first)
            sorted_matches = sorted(
                formatted_matches, 
                key=lambda m: m.get("raw_data", {}).get("dateTimeGMT", "")
            )
            
            # Store in database for future use
            save_upcoming_matches_to_db(db, ipl_matches)
            
            return {
                "matches": sorted_matches,
                "count": len(sorted_matches),
                "source": "api"
            }
        else:
            # Fetch from database using SQLAlchemy
            matches_db = db.query(UpcomingMatch).filter(
                UpcomingMatch.series.like("%Indian Premier League%")
            ).order_by(UpcomingMatch.match_date).all()
            
            matches = []
            for match_db in matches_db:
                match_data = match_db.raw_data
                matches.append(format_match_data(match_data))
            
            return {
                "matches": matches,
                "count": len(matches),
                "source": "database"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching upcoming matches: {str(e)}")