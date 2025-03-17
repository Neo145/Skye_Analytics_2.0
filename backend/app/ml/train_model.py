# app/ml/train_model.py
import os
import joblib
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, 
    classification_report, 
    confusion_matrix, 
    roc_auc_score
)

# Correct import with full module path
from app.ml.data_preparation import AdvancedFeatureEngineering

def train_ipl_prediction_model():
    # Construct database connection string using provided credentials
    DB_CONNECTION = (
        f"postgresql://{os.getenv('DB_USER', 'skye')}:"
        f"{os.getenv('DB_PASSWORD', 'skyeneo4280')}@"
        f"{os.getenv('DB_HOST', 'ipl-db-0824.c5aso8akkkbg.eu-north-1.rds.amazonaws.com')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.getenv('DB_NAME', 'postgres')}"
    )
    
    # Prepare data
    feature_engineer = AdvancedFeatureEngineering(DB_CONNECTION)
    
    try:
        # Fetch and preprocess data
        df = feature_engineer.fetch_comprehensive_data()
        df = feature_engineer.engineer_advanced_features(df)
        
        # Prepare ML dataset
        X, y = feature_engineer.prepare_ml_dataset(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Define multiple models to compare
        models = {
            'Random Forest': RandomForestClassifier(
                n_estimators=200, 
                max_depth=10, 
                min_samples_split=5, 
                random_state=42
            ),
            'Gradient Boosting': GradientBoostingClassifier(
                n_estimators=200, 
                learning_rate=0.1, 
                max_depth=5, 
                random_state=42
            ),
            'Logistic Regression': LogisticRegression(
                max_iter=1000, 
                C=0.1
            ),
            'Support Vector Machine': SVC(
                kernel='rbf', 
                probability=True, 
                C=1.0
            )
        }
        
        # Train and evaluate models
        best_model = None
        best_score = 0
        model_performances = {}
        
        for name, model in models.items():
            # Perform cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5)
            
            # Train the model
            model.fit(X_train, y_train)
            
            # Predictions
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Evaluate model
            accuracy = accuracy_score(y_test, y_pred)
            roc_auc = roc_auc_score(y_test, y_pred_proba)
            
            # Store performance metrics
            model_performances[name] = {
                'accuracy': accuracy,
                'roc_auc': roc_auc,
                'cross_val_scores': cv_scores,
                'classification_report': classification_report(y_test, y_pred),
                'confusion_matrix': confusion_matrix(y_test, y_pred)
            }
            
            # Print results
            print(f"\n{name} Results:")
            print(f"Accuracy: {accuracy}")
            print(f"ROC AUC: {roc_auc}")
            print(f"Cross-validation Scores: {cv_scores}")
            print("Classification Report:\n", 
                  classification_report(y_test, y_pred))
            
            # Track the best model
            if roc_auc > best_score:
                best_model = model
                best_score = roc_auc
        
        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)
        
        # Save the best model and performance metrics
        joblib.dump(best_model, 'models/ipl_match_predictor.joblib')
        joblib.dump(model_performances, 'models/model_performances.joblib')
        
        print("\nBest Model:", type(best_model).__name__)
        print(f"Best ROC AUC Score: {best_score}")
        
    except Exception as e:
        print(f"Error during model training: {e}")
        raise

if __name__ == '__main__':
    train_ipl_prediction_model()