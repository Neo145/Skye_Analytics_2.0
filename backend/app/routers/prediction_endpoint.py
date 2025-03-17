# backend/app/routers/prediction_endpoint.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, 
    confusion_matrix, 
    classification_report, 
    roc_auc_score
)
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(
    prefix="/api/match-prediction",
    tags=["Match Prediction"]
)

class MatchPredictionRequest(BaseModel):
    team1: str
    team2: str
    venue: str
    season: int
    toss_winner: str
    toss_decision: str

class ModelPerformanceResponse(BaseModel):
    accuracy: float
    confusion_matrix: List[List[int]]
    classification_report: Dict[str, Dict[str, float]]
    roc_auc: float

@router.post("/predict")
def predict_match_outcome(
    prediction_request: MatchPredictionRequest,
    db: Session = Depends(get_db)
):
    try:
        # Load the trained model and feature columns
        model = joblib.load('models/advanced_ipl_predictor.joblib')
        feature_columns = joblib.load('models/feature_columns.joblib')
        
        # Fetch comprehensive match data for feature engineering
        query = f"""
        SELECT 
            team1_win_percentage, 
            team2_win_percentage,
            -- Add other feature columns from your advanced feature engineering
            COALESCE(team1_recent_win_rate, 0.5) as team1_recent_win_rate,
            COALESCE(team2_recent_win_rate, 0.5) as team2_recent_win_rate,
            COALESCE(venue_win_rate, 0.5) as venue_win_rate
        FROM match_info m
        LEFT JOIN (
            SELECT 
                team_name, 
                AVG(win_percentage) as team1_recent_win_rate
            FROM team_season_stats
            WHERE season = {prediction_request.season}
            GROUP BY team_name
        ) t1 ON m.team1 = t1.team_name
        LEFT JOIN (
            SELECT 
                team_name, 
                AVG(win_percentage) as team2_recent_win_rate
            FROM team_season_stats
            WHERE season = {prediction_request.season}
            GROUP BY team_name
        ) t2 ON m.team2 = t2.team_name
        LEFT JOIN (
            SELECT 
                venue, 
                AVG(CASE WHEN winner = team1 THEN 1.0 ELSE 0.0 END) as venue_win_rate
            FROM match_info
            WHERE season = {prediction_request.season}
            GROUP BY venue
        ) v ON m.venue = v.venue
        WHERE 
            m.team1 = '{prediction_request.team1}' AND 
            m.team2 = '{prediction_request.team2}' AND
            m.venue = '{prediction_request.venue}' AND
            m.season = {prediction_request.season}
        LIMIT 1
        """
        
        # Execute the query
        features_df = pd.read_sql(query, db.bind)
        
        # If no exact match found, use default values
        if features_df.empty:
            features_df = pd.DataFrame({
                'team1_win_percentage': [0.5],
                'team2_win_percentage': [0.5],
                'team1_recent_win_rate': [0.5],
                'team2_recent_win_rate': [0.5],
                'venue_win_rate': [0.5]
            })
        
        # Prepare features
        features = features_df[feature_columns].values
        
        # Predict probabilities
        probabilities = model.predict_proba(features)[0]
        
        return {
            "team1": prediction_request.team1,
            "team2": prediction_request.team2,
            "team1_win_probability": probabilities[1],
            "team2_win_probability": probabilities[0],
            "prediction": prediction_request.team1 if probabilities[1] > 0.5 else prediction_request.team2
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-performance")
def get_model_performance(db: Session = Depends(get_db)):
    try:
        # Load the trained model and feature columns
        model = joblib.load('models/advanced_ipl_predictor.joblib')
        feature_columns = joblib.load('models/feature_columns.joblib')
        
        # Fetch comprehensive test dataset
        query = """
        SELECT 
            team1, 
            team2, 
            venue, 
            season, 
            winner,
            team1_win_percentage, 
            team2_win_percentage,
            -- Add other feature columns from your advanced feature engineering
            COALESCE(team1_recent_win_rate, 0.5) as team1_recent_win_rate,
            COALESCE(team2_recent_win_rate, 0.5) as team2_recent_win_rate,
            COALESCE(venue_win_rate, 0.5) as venue_win_rate
        FROM match_info m
        LEFT JOIN (
            SELECT 
                team_name, 
                season,
                AVG(win_percentage) as team1_recent_win_rate
            FROM team_season_stats
            GROUP BY team_name, season
        ) t1 ON m.team1 = t1.team_name AND m.season = t1.season
        LEFT JOIN (
            SELECT 
                team_name, 
                season,
                AVG(win_percentage) as team2_recent_win_rate
            FROM team_season_stats
            GROUP BY team_name, season
        ) t2 ON m.team2 = t2.team_name AND m.season = t2.season
        LEFT JOIN (
            SELECT 
                venue, 
                season,
                AVG(CASE WHEN winner = team1 THEN 1.0 ELSE 0.0 END) as venue_win_rate
            FROM match_info
            GROUP BY venue, season
        ) v ON m.venue = v.venue AND m.season = v.season
        """
        
        # Execute the query
        test_df = pd.read_sql(query, db.bind)
        
        # Prepare features and target
        X_test = test_df[feature_columns]
        y_test = (test_df['winner'] == test_df['team1']).astype(int)
        
        # Predict
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Calculate performance metrics
        accuracy = accuracy_score(y_test, y_pred)
        conf_matrix = confusion_matrix(y_test, y_pred).tolist()
        class_report = classification_report(y_test, y_pred, output_dict=True)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        return ModelPerformanceResponse(
            accuracy=accuracy,
            confusion_matrix=conf_matrix,
            classification_report=class_report,
            roc_auc=roc_auc
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))