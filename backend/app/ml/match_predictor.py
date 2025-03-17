import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

class IPLMatchPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100, 
            random_state=42
        )
    
    def train_model(self, X_train, y_train):
        """
        Train the random forest classifier
        """
        self.model.fit(X_train, y_train)
        return self
    
    def evaluate_model(self, X_test, y_test):
        """
        Evaluate model performance
        """
        y_pred = self.model.predict(X_test)
        print("Model Accuracy:", accuracy_score(y_test, y_pred))
        print("\nClassification Report:\n", classification_report(y_test, y_pred))
        return self
    
    def predict_match(self, match_features):
        """
        Predict match outcome
        """
        probabilities = self.model.predict_proba(match_features)
        return {
            'team1_win_probability': probabilities[0][1],
            'team2_win_probability': probabilities[0][0]
        }
    
    def save_model(self, filepath):
        """
        Save trained model
        """
        joblib.dump(self.model, filepath)
        return self
    
    def load_model(self, filepath):
        """
        Load pre-trained model
        """
        self.model = joblib.load(filepath)
        return self