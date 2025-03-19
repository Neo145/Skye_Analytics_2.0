from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from app.database import get_db
from app.utils.db_utils import query_to_dataframe, execute_raw_sql
from app.models.venue import (
    VenueBasic, 
    VenueDetailResponse, 
    TeamVenuePerformance,
    VenueTeamPerformanceResponse,
    VenuePitchCharacteristics,
    VenueMatchList,
    VenueListResponse,
    VenueSeasonTrends
)

router = APIRouter(
    prefix="/api/venue-analysis",
    tags=["Venue Analysis"],
    responses={404: {"description": "Not found"}},
)


def get_match_data_by_venue(db: Session, venue_name: Optional[str] = None, team: Optional[str] = None, season: Optional[int] = None):
    """
    Retrieve match data filtered by venue, team, and season
    """
    # Get match info data
    match_query = """
    SELECT filename, season, match_date, venue, city, team1, team2, 
           toss_winner, toss_decision, winner, margin, player_of_match
    FROM match_info
    WHERE 1=1
    """
    
    params = {}
    
    # Add venue filter if specified
    if venue_name:
        match_query += " AND venue = :venue"
        params["venue"] = venue_name
    
    # Add team filter if specified
    if team:
        match_query += " AND (team1 = :team OR team2 = :team)"
        params["team"] = team
    
    # Add season filter if specified
    if season:
        match_query += " AND season = :season"
        params["season"] = season
    
    # Execute match query
    matches_df = query_to_dataframe(db, match_query, params)
    
    if matches_df.empty:
        if venue_name:
            raise HTTPException(status_code=404, detail=f"No data found for venue: {venue_name}")
        else:
            raise HTTPException(status_code=404, detail="No match data found")
    
    # Get innings data for these matches
    filenames = matches_df['filename'].tolist()
    filename_placeholders = ','.join([f":{i}" for i in range(len(filenames))])
    filename_params = {str(i): filename for i, filename in enumerate(filenames)}
    
    innings_query = f"""
    SELECT filename, innings_type, team, over_ball, batsman, bowler, 
           non_striker, runs_batsman, runs_total, extras_type, 
           extras_runs, wicket_details
    FROM innings_data
    WHERE filename IN ({filename_placeholders})
    """
    
    # Execute innings query
    innings_df = query_to_dataframe(db, innings_query, filename_params)
    
    return matches_df, innings_df


@router.get("/venues", response_model=VenueListResponse)
def get_venues(db: Session = Depends(get_db)):
    """
    Get a list of all venues with basic statistics
    """
    query = """
    SELECT venue, city, COUNT(*) as total_matches
    FROM match_info
    GROUP BY venue, city
    ORDER BY total_matches DESC
    """
    
    df = query_to_dataframe(db, query)
    
    if df.empty:
        return VenueListResponse(count=0, venues=[])
    
    venues = []
    for _, row in df.iterrows():
        venues.append(VenueBasic(
            name=row["venue"],
            city=row.get("city"),
            total_matches=int(row["total_matches"])
        ))
    
    return VenueListResponse(count=len(venues), venues=venues)


@router.get("/venue/{venue_name}", response_model=VenueDetailResponse)
def get_venue_details(
    venue_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a specific venue
    """
    # Get match data for the venue
    matches_df, innings_df = get_match_data_by_venue(db, venue_name=venue_name, season=season)
    
    total_matches = len(matches_df)
    city = matches_df["city"].iloc[0] if "city" in matches_df.columns else None
    
    # Calculate first and second innings scores
    first_innings = innings_df[innings_df["innings_type"] == "1st innings"]
    second_innings = innings_df[innings_df["innings_type"] == "2nd innings"]
    
    # Group by filename and calculate total runs per innings
    if not first_innings.empty:
        first_innings_scores = first_innings.groupby("filename")["runs_total"].sum()
        avg_first_innings = first_innings_scores.mean()
        
        # Find highest and lowest scores
        highest_score_filename = first_innings_scores.idxmax() if not first_innings_scores.empty else None
        lowest_score_filename = first_innings_scores.idxmin() if not first_innings_scores.empty else None
        
        # Get match details for highest and lowest scores
        highest_score_match = matches_df[matches_df["filename"] == highest_score_filename].iloc[0].to_dict() if highest_score_filename in matches_df["filename"].values else {}
        lowest_score_match = matches_df[matches_df["filename"] == lowest_score_filename].iloc[0].to_dict() if lowest_score_filename in matches_df["filename"].values else {}
        
        highest_score = {
            "score": int(first_innings_scores.max()) if not first_innings_scores.empty else 0,
            "team": highest_score_match.get("team1", "Unknown"),
            "opponent": highest_score_match.get("team2", "Unknown"),
            "season": highest_score_match.get("season", "Unknown"),
            "match_date": highest_score_match.get("match_date", "Unknown"),
        }
        
        lowest_score = {
            "score": int(first_innings_scores.min()) if not first_innings_scores.empty else 0,
            "team": lowest_score_match.get("team1", "Unknown"),
            "opponent": lowest_score_match.get("team2", "Unknown"),
            "season": lowest_score_match.get("season", "Unknown"),
            "match_date": lowest_score_match.get("match_date", "Unknown"),
        }
    else:
        avg_first_innings = 0
        highest_score = {
            "score": 0,
            "team": "Unknown",
            "opponent": "Unknown",
            "season": "Unknown",
            "match_date": "Unknown",
        }
        lowest_score = {
            "score": 0,
            "team": "Unknown",
            "opponent": "Unknown",
            "season": "Unknown",
            "match_date": "Unknown",
        }
    
    # Second innings average
    if not second_innings.empty:
        second_innings_scores = second_innings.groupby("filename")["runs_total"].sum()
        avg_second_innings = second_innings_scores.mean()
    else:
        avg_second_innings = 0
    
    # Toss and batting first statistics
    toss_winners = matches_df[matches_df["toss_winner"] == matches_df["winner"]]
    toss_win_match_win_percentage = len(toss_winners) / total_matches * 100 if total_matches > 0 else 0
    
    batting_first_winners = matches_df[
        (matches_df["toss_winner"] == matches_df["team1"]) & 
        (matches_df["toss_decision"] == "bat") & 
        (matches_df["winner"] == matches_df["team1"])
    ]
    batting_first_win_count = len(batting_first_winners)
    
    total_batting_first = len(matches_df[
        (matches_df["toss_winner"] == matches_df["team1"]) & 
        (matches_df["toss_decision"] == "bat")
    ])
    
    batting_first_win_percentage = batting_first_win_count / total_batting_first * 100 if total_batting_first > 0 else 0
    
    # Player stats at the venue
    batsman_runs = innings_df.groupby("batsman")["runs_batsman"].sum().reset_index()
    most_runs_player = batsman_runs.sort_values("runs_batsman", ascending=False).iloc[0] if not batsman_runs.empty else {"batsman": "Unknown", "runs_batsman": 0}
    
    bowler_wickets = innings_df[innings_df["wicket_details"].notna()].groupby("bowler").size().reset_index(name="wickets")
    most_wickets_player = bowler_wickets.sort_values("wickets", ascending=False).iloc[0] if not bowler_wickets.empty else {"bowler": "Unknown", "wickets": 0}
    
    most_runs = {
        "player": most_runs_player.get("batsman", "Unknown"),
        "runs": int(most_runs_player.get("runs_batsman", 0)),
    }
    
    most_wickets = {
        "player": most_wickets_player.get("bowler", "Unknown"),
        "wickets": int(most_wickets_player.get("wickets", 0)),
    }
    
    # Matches by season
    matches_by_season = dict(matches_df["season"].value_counts())
    matches_by_season = {str(k): int(v) for k, v in matches_by_season.items()}
    
    return VenueDetailResponse(
        name=venue_name,
        city=city,
        total_matches=total_matches,
        avg_first_innings_score=float(avg_first_innings),
        avg_second_innings_score=float(avg_second_innings),
        highest_score=highest_score,
        lowest_score=lowest_score,
        toss_win_match_win_percentage=float(toss_win_match_win_percentage),
        batting_first_win_percentage=float(batting_first_win_percentage),
        most_runs=most_runs,
        most_wickets=most_wickets,
        matches_by_season=matches_by_season
    )


@router.get("/venue/{venue_name}/team-performance", response_model=VenueTeamPerformanceResponse)
def get_team_performance_at_venue(
    venue_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get performance statistics for all teams at a specific venue
    """
    # Get match data for the venue
    matches_df, innings_df = get_match_data_by_venue(db, venue_name=venue_name, season=season)
    
    total_matches = len(matches_df)
    city = matches_df["city"].iloc[0] if "city" in matches_df.columns else None
    
    # Get all teams that played at this venue
    teams = pd.concat([matches_df["team1"], matches_df["team2"]]).unique()
    
    team_performances = []
    for team in teams:
        # Matches where this team played
        team_matches = matches_df[(matches_df["team1"] == team) | (matches_df["team2"] == team)]
        matches_played = len(team_matches)
        
        # Matches won by this team
        matches_won = len(team_matches[team_matches["winner"] == team])
        win_percentage = matches_won / matches_played * 100 if matches_played > 0 else 0
        
        # Team's batting performance - get only innings where this team was batting
        team_batting = innings_df[
            (innings_df["team"] == team) & 
            (innings_df["filename"].isin(team_matches["filename"].tolist()))
        ]
        
        # Calculate average runs per match
        team_match_runs = team_batting.groupby("filename")["runs_batsman"].sum()
        avg_runs = team_match_runs.mean() if not team_match_runs.empty else 0
        
        # Find highest score
        highest_score_data = {}
        if not team_match_runs.empty:
            highest_score_filename = team_match_runs.idxmax()
            highest_score_match = team_matches[team_matches["filename"] == highest_score_filename]
            
            if not highest_score_match.empty:
                match_data = highest_score_match.iloc[0]
                opponent = match_data["team2"] if match_data["team1"] == team else match_data["team1"]
                
                highest_score_data = {
                    "score": int(team_match_runs.max()),
                    "opponent": opponent,
                    "season": match_data["season"],
                    "match_date": match_data["match_date"],
                }
        
        if not highest_score_data:
            highest_score_data = {
                "score": 0,
                "opponent": "Unknown",
                "season": "Unknown",
                "match_date": "Unknown",
            }
        
        # Team's bowling performance - find wickets taken against opposition
        opposition_teams = []
        for _, match in team_matches.iterrows():
            if match["team1"] == team:
                opposition_teams.append(match["team2"])
            else:
                opposition_teams.append(match["team1"])
        
        # Find innings where opposition teams were batting
        opposition_batting = innings_df[
            (innings_df["team"].isin(opposition_teams)) & 
            (innings_df["filename"].isin(team_matches["filename"].tolist()))
        ]
        
        # Count wickets
        wickets_taken = opposition_batting[opposition_batting["wicket_details"].notna()]
        wickets_by_match = wickets_taken.groupby("filename").size()
        avg_wickets = wickets_by_match.mean() if not wickets_by_match.empty else 0
        
        # Find best bowling performance
        best_bowling_data = {}
        if not wickets_taken.empty:
            # Group by filename and bowler to get wickets per bowler per match
            bowler_match_wickets = wickets_taken.groupby(["filename", "bowler"]).size().reset_index(name="wickets")
            
            # Filter for bowlers likely from this team
            # Note: This is an approximation since we don't have direct team-bowler mapping
            if not bowler_match_wickets.empty:
                best_bowling_idx = bowler_match_wickets["wickets"].idxmax()
                best_bowling_row = bowler_match_wickets.iloc[best_bowling_idx]
                
                match_info = matches_df[matches_df["filename"] == best_bowling_row["filename"]]
                if not match_info.empty:
                    match_data = match_info.iloc[0]
                    opponent = match_data["team2"] if match_data["team1"] == team else match_data["team1"]
                    
                    best_bowling_data = {
                        "bowler": best_bowling_row["bowler"],
                        "wickets": int(best_bowling_row["wickets"]),
                        "opponent": opponent,
                        "season": match_data["season"],
                        "match_date": match_data["match_date"],
                    }
        
        if not best_bowling_data:
            best_bowling_data = {
                "bowler": "Unknown",
                "wickets": 0,
                "opponent": "Unknown",
                "season": "Unknown",
                "match_date": "Unknown",
            }
        
        team_performances.append(TeamVenuePerformance(
            team=team,
            matches_played=matches_played,
            matches_won=matches_won,
            win_percentage=float(win_percentage),
            avg_runs_scored=float(avg_runs),
            highest_score=highest_score_data,
            avg_wickets_taken=float(avg_wickets),
            best_bowling=best_bowling_data
        ))
    
    return VenueTeamPerformanceResponse(
        venue_name=venue_name,
        city=city,
        total_matches=total_matches,
        team_performances=team_performances
    )


@router.get("/venue/{venue_name}/pitch-characteristics", response_model=VenuePitchCharacteristics)
def get_venue_pitch_characteristics(
    venue_name: str,
    db: Session = Depends(get_db)
):
    """
    Analyze pitch characteristics for a specific venue
    """
    # Get match data for the venue
    matches_df, innings_df = get_match_data_by_venue(db, venue_name=venue_name)
    
    city = matches_df["city"].iloc[0] if "city" in matches_df.columns else None
    total_matches = len(matches_df)
    
    # Calculate first and second innings scores
    first_innings = innings_df[innings_df["innings_type"] == "1st innings"]
    second_innings = innings_df[innings_df["innings_type"] == "2nd innings"]
    
    first_innings_scores = first_innings.groupby("filename")["runs_total"].sum() if not first_innings.empty else pd.Series()
    second_innings_scores = second_innings.groupby("filename")["runs_total"].sum() if not second_innings.empty else pd.Series()
    
    avg_first_innings = first_innings_scores.mean() if not first_innings_scores.empty else 0
    avg_second_innings = second_innings_scores.mean() if not second_innings_scores.empty else 0
    
    # Calculate average run rate
    total_balls = len(innings_df)
    total_runs = innings_df["runs_total"].sum()
    avg_run_rate = (total_runs / (total_balls/6)) if total_balls > 0 else 0  # Convert to per over
    
    # Count boundaries
    fours = len(innings_df[innings_df["runs_batsman"] == 4])
    sixes = len(innings_df[innings_df["runs_batsman"] == 6])
    
    avg_boundaries = {
        "fours": fours / total_matches if total_matches > 0 else 0,
        "sixes": sixes / total_matches if total_matches > 0 else 0
    }
    
    # Count wickets
    total_wickets = len(innings_df[innings_df["wicket_details"].notna()])
    avg_wickets = total_wickets / total_matches if total_matches > 0 else 0
    
    # Analyze spin vs pace effectiveness
    # Assuming we can identify spinners and pacers by name patterns
    spinners = innings_df[innings_df["bowler"].str.contains("spin|Spin|Chahal|Ashwin|Jadeja|Rashid|Tahir|Narine", case=False, na=False)]
    pacers = innings_df[innings_df["bowler"].str.contains("pace|Pace|Bumrah|Shami|Steyn|Malinga|Cummins|Archer", case=False, na=False)]
    
    spin_wickets = len(spinners[spinners["wicket_details"].notna()])
    pace_wickets = len(pacers[pacers["wicket_details"].notna()])
    
    spin_balls = len(spinners)
    pace_balls = len(pacers)
    
    spin_effectiveness = (spin_wickets / spin_balls * 100) if spin_balls > 0 else 0
    pace_effectiveness = (pace_wickets / pace_balls * 100) if pace_balls > 0 else 0
    
    # Normalize to 0-10 scale
    batting_friendly_score = 10 - (avg_wickets / 20 * 10)  # Lower wickets = more batting friendly
    batting_friendly_score = min(10, max(0, batting_friendly_score))
    
    # Determine pitch behavior description
    if avg_first_innings > avg_second_innings + 20:
        behavior = "Deteriorates significantly, favors batting first"
    elif avg_second_innings > avg_first_innings + 20:
        behavior = "Improves with time, favors chasing"
    elif spin_effectiveness > pace_effectiveness + 2:
        behavior = "Assists spin bowling"
    elif pace_effectiveness > spin_effectiveness + 2:
        behavior = "Assists pace bowling"
    elif avg_run_rate > 9:
        behavior = "High-scoring, batting friendly pitch"
    elif avg_run_rate < 7:
        behavior = "Low-scoring, bowling friendly pitch"
    else:
        behavior = "Balanced pitch, good contest between bat and ball"
    
    return VenuePitchCharacteristics(
        venue_name=venue_name,
        city=city,
        batting_friendly_score=float(batting_friendly_score),
        avg_run_rate=float(avg_run_rate),
        avg_boundaries_per_match=avg_boundaries,
        avg_wickets_per_match=float(avg_wickets),
        spin_effectiveness=float(min(10, max(0, spin_effectiveness / 10))),
        pace_effectiveness=float(min(10, max(0, pace_effectiveness / 10))),
        avg_first_innings_score=float(avg_first_innings),
        avg_second_innings_score=float(avg_second_innings),
        historic_pitch_behavior=behavior
    )


@router.get("/venue/{venue_name}/matches", response_model=VenueMatchList)
def get_venue_matches(
    venue_name: str,
    team: Optional[str] = None,
    season: Optional[int] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get list of matches played at a specific venue
    """
    # Get match data for the venue
    matches_df, innings_df = get_match_data_by_venue(db, venue_name=venue_name, team=team, season=season)
    
    total_matches = len(matches_df)
    city = matches_df["city"].iloc[0] if "city" in matches_df.columns else None
    
    # Sort by date (recent first) and limit results
    if "match_date" in matches_df.columns:
        try:
            matches_df["match_date"] = pd.to_datetime(matches_df["match_date"], errors="coerce")
            matches_df = matches_df.sort_values("match_date", ascending=False)
        except:
            # If date conversion fails, don't sort
            pass
    
    matches_df = matches_df.head(limit)
    
    # Format match data
    matches = []
    for _, match in matches_df.iterrows():
        # Calculate scores for each innings
        match_innings = innings_df[innings_df["filename"] == match["filename"]]
        
        first_innings = match_innings[match_innings["innings_type"] == "1st innings"]
        second_innings = match_innings[match_innings["innings_type"] == "2nd innings"]
        
        team1_score = first_innings["runs_total"].sum() if not first_innings.empty else 0
        team2_score = second_innings["runs_total"].sum() if not second_innings.empty else 0
        
        match_date = match["match_date"]
        if isinstance(match_date, pd.Timestamp):
            match_date = match_date.strftime("%Y-%m-%d")
        
        match_data = {
            "filename": match["filename"],
            "season": int(match["season"]) if "season" in match and pd.notna(match["season"]) else None,
            "match_date": match_date,
            "team1": match.get("team1"),
            "team2": match.get("team2"),
            "toss_winner": match.get("toss_winner"),
            "toss_decision": match.get("toss_decision"),
            "winner": match.get("winner"),
            "margin": match.get("margin"),
            "player_of_match": match.get("player_of_match"),
            "team1_score": int(team1_score),
            "team2_score": int(team2_score)
        }
        
        matches.append(match_data)
    
    return VenueMatchList(
        venue_name=venue_name,
        city=city,
        total_matches=total_matches,
        matches=matches
    )


@router.get("/venue/{venue_name}/season-trends", response_model=VenueSeasonTrends)
def get_venue_season_trends(
    venue_name: str,
    db: Session = Depends(get_db)
):
    """
    Get season-by-season trends for a specific venue
    """
    # Get match data for the venue
    matches_df, innings_df = get_match_data_by_venue(db, venue_name=venue_name)
    
    city = matches_df["city"].iloc[0] if "city" in matches_df.columns else None
    
    # Group by season
    seasons = sorted(matches_df["season"].unique())
    season_data = []
    
    for season in seasons:
        # Get matches for this season
        season_matches = matches_df[matches_df["season"] == season]
        season_filenames = season_matches["filename"].tolist()
        
        # Get innings for these matches
        season_innings = innings_df[innings_df["filename"].isin(season_filenames)]
        
        # Split by innings type
        first_innings = season_innings[season_innings["innings_type"] == "1st innings"]
        second_innings = season_innings[season_innings["innings_type"] == "2nd innings"]
        
        # Calculate average scores
        first_innings_scores = first_innings.groupby("filename")["runs_total"].sum() if not first_innings.empty else pd.Series()
        second_innings_scores = second_innings.groupby("filename")["runs_total"].sum() if not second_innings.empty else pd.Series()
        
        avg_first_innings = first_innings_scores.mean() if not first_innings_scores.empty else 0
        avg_second_innings = second_innings_scores.mean() if not second_innings_scores.empty else 0
        
        # Count boundaries
        fours = len(season_innings[season_innings["runs_batsman"] == 4])
        sixes = len(season_innings[season_innings["runs_batsman"] == 6])
        
        # Count wickets
        wickets = len(season_innings[season_innings["wicket_details"].notna()])
        
        # Toss statistics
        toss_winner_won = len(season_matches[season_matches["toss_winner"] == season_matches["winner"]])
        
        batting_first_winners = season_matches[
            (season_matches["toss_winner"] == season_matches["team1"]) & 
            (season_matches["toss_decision"] == "bat") & 
            (season_matches["winner"] == season_matches["team1"])
        ]
        batting_first_win_count = len(batting_first_winners)
        
        total_batting_first = len(season_matches[
            (season_matches["toss_winner"] == season_matches["team1"]) & 
            (season_matches["toss_decision"] == "bat")
        ])
        
        toss_win_percent = (toss_winner_won / len(season_matches) * 100) if len(season_matches) > 0 else 0
        batting_first_win_percent = (batting_first_win_count / total_batting_first * 100) if total_batting_first > 0 else 0
        
        season_data.append({
            "season": int(season),
            "matches_played": len(season_matches),
            "avg_first_innings_score": float(avg_first_innings),
            "avg_second_innings_score": float(avg_second_innings),
            "boundaries": {
                "fours": int(fours),
                "sixes": int(sixes)
            },
            "wickets": int(wickets),
            "toss_winner_won_percentage": float(toss_win_percent),
            "batting_first_won_percentage": float(batting_first_win_percent),
        })
    
    return VenueSeasonTrends(
        venue_name=venue_name,
        city=city,
        season_data=season_data
    )


@router.get("/team/{team_name}/venue-performance")
def get_team_performance_by_venues(
    team_name: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get a team's performance across different venues
    """
    # Get match data for the team
    matches_df, innings_df = get_match_data_by_venue(db, team=team_name, season=season)
    
    # Group by venue
    venues = matches_df["venue"].unique()
    venue_performances = []
    
    for venue in venues:
        # Get matches at this venue
        venue_matches = matches_df[matches_df["venue"] == venue]
        venue_filenames = venue_matches["filename"].tolist()
        
        total_matches = len(venue_matches)
        wins = len(venue_matches[venue_matches["winner"] == team_name])
        win_percentage = wins / total_matches * 100 if total_matches > 0 else 0
        
        # Team's batting at this venue
        team_batting = innings_df[
            (innings_df["team"] == team_name) & 
            (innings_df["filename"].isin(venue_filenames))
        ]
        
        # Aggregate stats
        total_runs = team_batting["runs_batsman"].sum()
        avg_runs_per_match = total_runs / total_matches if total_matches > 0 else 0
        
        # Find highest score at this venue
        match_runs = team_batting.groupby("filename")["runs_batsman"].sum() if not team_batting.empty else pd.Series()
        highest_score = match_runs.max() if not match_runs.empty else 0
        
        # Get opposition teams
        opposition_teams = []
        for _, match in venue_matches.iterrows():
            opposition = match["team2"] if match["team1"] == team_name else match["team1"]
            opposition_teams.append(opposition)
        
        # Find innings where opposition teams were batting
        opposition_batting = innings_df[
            (innings_df["team"].isin(opposition_teams)) & 
            (innings_df["filename"].isin(venue_filenames))
        ]
        
        # Count wickets taken against opposition
        team_bowling_wickets = opposition_batting[opposition_batting["wicket_details"].notna()]
        total_wickets = len(team_bowling_wickets)
        avg_wickets_per_match = total_wickets / total_matches if total_matches > 0 else 0
        
        # City information
        city = venue_matches["city"].iloc[0] if "city" in venue_matches.columns else None
        
        venue_performances.append({
            "venue": venue,
            "city": city,
            "matches_played": total_matches,
            "matches_won": wins,
            "win_percentage": float(win_percentage),
            "total_runs_scored": int(total_runs),
            "avg_runs_per_match": float(avg_runs_per_match),
            "highest_team_score": int(highest_score),
            "total_wickets_taken": total_wickets,
            "avg_wickets_per_match": float(avg_wickets_per_match)
        })
    
    # Sort by win percentage (descending)
    venue_performances = sorted(venue_performances, key=lambda x: x["win_percentage"], reverse=True)
    
    return {
        "team": team_name,
        "total_venues_played": len(venue_performances),
        "venue_performances": venue_performances
    }