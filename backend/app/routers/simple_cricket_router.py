from fastapi import APIRouter, HTTPException, Query
import requests
from typing import Dict, Any, List, Optional

router = APIRouter(
    prefix="/api/cricket",
    tags=["Cricket API"],
)

# API Configuration
API_BASE_URL = "https://api.cricapi.com/v1"
API_KEY = "52b08390-6e7b-4233-b038-b39ed015ede7"  # Your API key

@router.get("/matches")
async def get_matches(limit: int = Query(20, description="Number of matches to return")):
    """
    Get current and upcoming cricket matches directly from the Cricket API.
    """
    endpoint = f"{API_BASE_URL}/matches"
    params = {
        "apikey": API_KEY,
        "offset": 0
    }
    
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                # Return only the number of matches requested
                limited_data = data["data"][:limit] if limit > 0 else data["data"]
                return {"matches": limited_data, "count": len(limited_data)}
            else:
                return {"matches": [], "count": 0, "message": "No match data found"}
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"API request failed: {response.text}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching matches: {str(e)}")

@router.get("/match/{match_id}")
async def get_match_details(match_id: str):
    """
    Get detailed information for a specific cricket match.
    """
    endpoint = f"{API_BASE_URL}/match_info"
    params = {
        "apikey": API_KEY,
        "id": match_id
    }
    
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                return data["data"]
            else:
                raise HTTPException(status_code=404, detail="Match details not found")
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"API request failed: {response.text}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching match details: {str(e)}")

@router.get("/series")
async def get_series(search: Optional[str] = None):
    """
    Get cricket series information or search for series.
    """
    endpoint = f"{API_BASE_URL}/series"
    params = {
        "apikey": API_KEY,
        "offset": 0
    }
    
    if search:
        params["search"] = search
    
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                return {"series": data["data"], "count": len(data["data"])}
            else:
                return {"series": [], "count": 0, "message": "No series data found"}
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"API request failed: {response.text}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching series: {str(e)}")

@router.get("/series/{series_id}")
async def get_series_details(series_id: str):
    """
    Get detailed information for a specific cricket series.
    """
    endpoint = f"{API_BASE_URL}/series_info"
    params = {
        "apikey": API_KEY,
        "id": series_id
    }
    
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                return data["data"]
            else:
                raise HTTPException(status_code=404, detail="Series details not found")
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"API request failed: {response.text}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching series details: {str(e)}")

@router.get("/players")
async def search_players(search: str = Query(..., description="Player name to search for")):
    """
    Search for cricket players by name.
    """
    endpoint = f"{API_BASE_URL}/players"
    params = {
        "apikey": API_KEY,
        "offset": 0,
        "search": search
    }
    
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                return {"players": data["data"], "count": len(data["data"])}
            else:
                return {"players": [], "count": 0, "message": "No players found"}
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"API request failed: {response.text}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching players: {str(e)}")

@router.get("/player/{player_id}")
async def get_player_details(player_id: str):
    """
    Get detailed information for a specific cricket player.
    """
    endpoint = f"{API_BASE_URL}/players_info"
    params = {
        "apikey": API_KEY,
        "id": player_id
    }
    
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                return data["data"]
            else:
                raise HTTPException(status_code=404, detail="Player details not found")
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"API request failed: {response.text}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching player details: {str(e)}")