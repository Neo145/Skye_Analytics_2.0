# backend/app/ml/advanced_feature_engineering.py
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import joblib

class AdvancedFeatureEngineering:
    def __init__(self, db_connection_string):
        self.engine = create_engine(db_connection_string)
    
    def fetch_comprehensive_data(self):
        """
        Fetch comprehensive match and player data
        """
        query = """
        WITH 
        player_performance AS (
            SELECT 
                batsman,
                season,
                SUM(runs_batsman) as total_runs,
                COUNT(DISTINCT filename) as matches_played,
                ROUND(AVG(runs_batsman), 2) as avg_runs_per_innings,
                ROUND(SUM(runs_batsman) * 100.0 / COUNT(*), 2) as strike_rate,
                SUM(CASE WHEN runs_batsman >= 50 THEN 1 ELSE 0 END) as fifties,
                SUM(CASE WHEN runs_batsman >= 100 THEN 1 ELSE 0 END) as hundreds
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            GROUP BY batsman, season
        ),
        bowling_performance AS (
            SELECT 
                bowler,
                season,
                COUNT(DISTINCT filename) as matches_played,
                SUM(CASE WHEN wicket_details IS NOT NULL AND wicket_details != '' THEN 1 ELSE 0 END) as wickets,
                ROUND(SUM(runs_total) * 1.0 / (COUNT(*) / 6), 2) as economy_rate
            FROM innings_data i
            JOIN match_info m ON i.filename = m.filename
            GROUP BY bowler, season
        ),
        team_performance AS (
            SELECT 
                team_name,
                season,
                COUNT(*) as matches_played,
                SUM(CASE WHEN winner = team_name THEN 1 ELSE 0 END) as matches_won,
                ROUND(SUM(CASE WHEN winner = team_name THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as win_percentage,
                ROUND(AVG(CASE 
                    WHEN toss_winner = team_name AND toss_decision = 'bat' THEN 1.0
                    WHEN toss_winner = team_name AND toss_decision = 'field' THEN 0.0
                    ELSE 0.5
                END), 2) as toss_bat_decision_rate
            FROM (
                SELECT team1 as team_name, * FROM match_info
                UNION ALL
                SELECT team2 as team_name, * FROM match_info
            ) m
            GROUP BY team_name, season
        ),
        venue_performance AS (
            SELECT 
                venue,
                season,
                COUNT(*) as matches_played,
                ROUND(SUM(CASE WHEN winner = team1 THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 2) as team1_win_rate,
                ROUND(SUM(CASE WHEN toss_decision = 'bat' THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 2) as bat_first_percentage
            FROM match_info
            GROUP BY venue, season
        )
        SELECT 
            m.match_date,
            m.team1,
            m.team2,
            m.toss_winner,
            m.toss_decision,
            m.venue,
            m.winner,
            m.season,
            
            # Player performance metrics
            COALESCE(t1_top_bat.total_runs, 0) as team1_top_batsman_runs,
            COALESCE(t1_top_bowl.wickets, 0) as team1_top_bowler_wickets,
            COALESCE(t2_top_bat.total_runs, 0) as team2_top_batsman_runs,
            COALESCE(t2_top_bowl.wickets, 0) as team2_top_bowler_wickets,
            
            # Team performance metrics
            COALESCE(t1_perf.win_percentage, 0) as team1_win_percentage,
            COALESCE(t2_perf.win_percentage, 0) as team2_win_percentage,
            COALESCE(t1_perf.toss_bat_decision_rate, 0) as team1_toss_bat_rate,
            COALESCE(t2_perf.toss_bat_decision_rate, 0) as team2_toss_bat_rate,
            
            # Venue performance metrics
            COALESCE(v_perf.team1_win_rate, 0) as venue_team1_win_rate,
            COALESCE(v_perf.bat_first_percentage, 0) as venue_bat_first_percentage,
            
            # Head-to-head metrics
            COALESCE(h2h.team1_win_percentage, 0) as head_to_head_win_percentage
        FROM 
            match_info m
        # Top batsman for team1
        LEFT JOIN (
            SELECT season, batsman, total_runs
            FROM (
                SELECT 
                    season, 
                    batsman, 
                    total_runs,
                    RANK() OVER (PARTITION BY season ORDER BY total_runs DESC) as rank
                FROM player_performance
            ) ranked
            WHERE rank = 1
        ) t1_top_bat ON t1_top_bat.season = m.season AND t1_top_bat.batsman IN (
            SELECT DISTINCT batsman 
            FROM innings_data 
            JOIN match_info ON innings_data.filename = match_info.filename 
            WHERE match_info.team1 = m.team1
        )
        # Top bowler for team1
        LEFT JOIN (
            SELECT season, bowler, wickets
            FROM (
                SELECT 
                    season, 
                    bowler, 
                    wickets,
                    RANK() OVER (PARTITION BY season ORDER BY wickets DESC) as rank
                FROM bowling_performance
            ) ranked
            WHERE rank = 1
        ) t1_top_bowl ON t1_top_bowl.season = m.season AND t1_top_bowl.bowler IN (
            SELECT DISTINCT bowler 
            FROM innings_data 
            JOIN match_info ON innings_data.filename = match_info.filename 
            WHERE match_info.team1 = m.team1
        )
        # Similar joins for team2
        LEFT JOIN (
            SELECT season, batsman, total_runs
            FROM (
                SELECT 
                    season, 
                    batsman, 
                    total_runs,
                    RANK() OVER (PARTITION BY season ORDER BY total_runs DESC) as rank
                FROM player_performance
            ) ranked
            WHERE rank = 1
        ) t2_top_bat ON t2_top_bat.season = m.season AND t2_top_bat.batsman IN (
            SELECT DISTINCT batsman 
            FROM innings_data 
            JOIN match_info ON innings_data.filename = match_info.filename 
            WHERE match_info.team2 = m.team2
        )
        LEFT JOIN (
            SELECT season, bowler, wickets
            FROM (
                SELECT 
                    season, 
                    bowler, 
                    wickets,
                    RANK() OVER (PARTITION BY season ORDER BY wickets DESC) as rank
                FROM bowling_performance
            ) ranked
            WHERE rank = 1
        ) t2_top_bowl ON t2_top_bowl.season = m.season AND t2_top_bowl.bowler IN (
            SELECT DISTINCT bowler 
            FROM innings_data 
            JOIN match_info ON innings_data.filename = match_info.filename 
            WHERE match_info.team2 = m.team2
        )
        # Team performance
        LEFT JOIN team_performance t1_perf ON t1_perf.team_name = m.team1 AND t1_perf.season = m.season
        LEFT JOIN team_performance t2_perf ON t2_perf.team_name = m.team2 AND t2_perf.season = m.season
        # Venue performance
        LEFT JOIN venue_performance v_perf ON v_perf.venue = m.venue AND v_perf.season = m.season
        # Head-to-head performance
        LEFT JOIN (
            SELECT 
                team1_name, 
                team2_name, 
                season,
                ROUND(SUM(CASE WHEN winner = team1_name THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 2) as team1_win_percentage
            FROM match_info
            WHERE team1 IN (SELECT DISTINCT team1 FROM match_info)
              AND team2 IN (SELECT DISTINCT team2 FROM match_info)
            GROUP BY team1_name, team2_name, season
        ) h2h ON h2h.team1_name = m.team1 
              AND h2h.team2_name = m.team2 
              AND h2h.season = m.season
        """
        
        return pd.read_sql(query, self.engine)
    
    def engineer_advanced_features(self, df):
        """
        Create advanced features for match prediction
        """
        # Relative team strength features
        df['team_strength_diff'] = df['team1_win_percentage'] - df['team2_win_percentage']
        df['top_batsman_runs_diff'] = df['team1_top_batsman_runs'] - df['team2_top_batsman_runs']
        df['top_bowler_wickets_diff'] = df['team1_top_bowler_wickets'] - df['team2_top_bowler_wickets']
        
        # Toss and venue features
        df['toss_advantage'] = (df['toss_winner'] == df['team1']).astype(int)
        df['venue_bias'] = df['venue_team1_win_rate'] - 50  # Deviation from 50%
        
        # Head-to-head and historical performance features
        df['head_to_head_advantage'] = df['head_to_head_win_percentage'] - 50
        
        # Contextual features
        df['recent_form_weight'] = np.where(
            df['team1_win_percentage'] > df['team2_win_percentage'], 
            1.2, 
            0.8
        )
        
        # Interaction features
        df['toss_venue_interaction'] = df['toss_advantage'] * df['venue_bias']
        df['team_strength_venue_interaction'] = df['team_strength_diff'] * df['venue_bias']
        
        # Encode the target variable
        df['match_result'] = (df['winner'] == df['team1']).astype(int)
        
        return df
    
    def prepare_ml_dataset(self, df):
        """
        Prepare the final dataset for machine learning
        """
        # Select and prepare features
        feature_columns = [
            'team1_win_percentage', 
            'team2_win_percentage',
            'team_strength_diff',
            'top_batsman_runs_diff',
            'top_bowler_wickets_diff',
            'toss_advantage',
            'venue_bias',
            'head_to_head_advantage',
            'recent_form_weight',
            'toss_venue_interaction',
            'team_strength_venue_interaction',
            'team1_toss_bat_rate',
            'team2_toss_bat_rate',
            'venue_bat_first_percentage'
        ]
        
        # Handle any remaining missing values
        X = df[feature_columns].fillna(df[feature_columns].mean())
        y = df['match_result']
        
        return X, y
    
    def feature_importance_analysis(self, X, y, model):
        """
        Analyze feature importance
        """
        importances = model.feature_importances_
        feature_importances = sorted(
            zip(X.columns, importances), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        print("Feature Importances:")
        for feature, importance in feature_importances:
            print(f"{feature}: {importance}")
        
        return feature_importances

class AdvancedModelTrainer:
    @staticmethod
    def train_advanced_model(X_train, y_train, X_test, y_test):
        """
        Train multiple models and compare their performance
        """
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.svm import SVC
        from sklearn.metrics import accuracy_score, classification_report
        
        # Models to compare
        models = {
            'Random Forest': RandomForestClassifier(n_estimators=200, random_state=42),
            'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, random_state=42),
            'Logistic Regression': LogisticRegression(max_iter=1000),
            'Support Vector Machine': SVC(probability=True)
        }
        
        # Train and evaluate models
        results = {}
        for name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            results[name] = {
                'model': model,
                'accuracy': accuracy,
                'classification_report': classification_report(y_test, y_pred)
            }
            
            print(f"\n{name} Results:")
            print(f"Accuracy: {accuracy}")
            print("Classification Report:\n", results[name]['classification_report'])
        
        return results

def main():
    import os
    from sklearn.model_selection import train_test_split
    
    # Database connection
    DB_CONNECTION = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/ipl_db')
    
    # Advanced Feature Engineering
    feature_engineer = AdvancedFeatureEngineering(DB_CONNECTION)
    
    # Fetch and preprocess data
    df = feature_engineer.fetch_comprehensive_data()
    df = feature_engineer.engineer_advanced_features(df)
    
    # Prepare ML dataset
    X, y = feature_engineer.prepare_ml_dataset(df)
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train models
    model_results = AdvancedModelTrainer.train_advanced_model(
        X_train, y_train, X_test, y_test
    )
    
    # Select the best model (based on accuracy)
    best_model_name = max(model_results, key=lambda x: model_results[x]['accuracy'])
    best_model = model_results[best_model_name]['model']
    
    # Save the best model and feature set
    import joblib
    os.makedirs('models', exist_ok=True)
    joblib.dump(best_model, 'models/advanced_ipl_predictor.joblib')
    joblib.dump(X.columns.tolist(), 'models/feature_columns.joblib')

if __name__ == '__main__':
    main()