# app/ml/data_preparation.py
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.preprocessing import LabelEncoder, StandardScaler

class AdvancedFeatureEngineering:
    def __init__(self, db_connection_string):
        try:
            self.engine = create_engine(db_connection_string)
            self.scaler = StandardScaler()
            self.label_encoder = LabelEncoder()
            
            # Test connection
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                print("Database connection successful!")
        except Exception as e:
            print(f"Database connection error: {e}")
            raise
    
    def fetch_comprehensive_data(self):
        """
        Fetch comprehensive match data for training the prediction model
        """
        query = """
        SELECT 
            match_date,
            team1,
            team2,
            toss_winner,
            toss_decision,
            venue,
            winner,
            season
        FROM 
            match_info
        LIMIT 1000
        """
        
        try:
            df = pd.read_sql(query, self.engine)
            
            # Verify data was fetched
            if df.empty:
                raise ValueError("No data found in match_info table")
            
            print(f"Fetched {len(df)} rows of match data")
            return df
        except Exception as e:
            print(f"Error fetching match data: {e}")
            raise
    
    def engineer_advanced_features(self, df):
        """
        Create advanced features for match prediction
        """
        # Encode categorical variables
        categorical_columns = ['team1', 'team2', 'toss_winner', 'toss_decision', 'venue']
        for col in categorical_columns:
            df[f'{col}_encoded'] = self.label_encoder.fit_transform(df[col].astype(str))
        
        # Feature engineering
        df['toss_advantage'] = (df['toss_winner'] == df['team1']).astype(int)
        
        # Target variable
        df['match_result'] = (df['winner'] == df['team1']).astype(int)
        
        return df
    
    def prepare_ml_dataset(self, df):
        """
        Prepare the final dataset for machine learning
        """
        # Select features
        feature_columns = [
            'team1_encoded', 
            'team2_encoded', 
            'toss_winner_encoded', 
            'toss_decision_encoded', 
            'venue_encoded',
            'season',
            'toss_advantage'
        ]
        
        # Handle missing values
        X = df[feature_columns].fillna(df[feature_columns].mean())
        y = df['match_result']
        
        # Scale the features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y