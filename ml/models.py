"""
AIBET MVP ML Models
Machine learning models for predictions
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
import pickle
import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MLModel:
    """Base ML model class"""
    
    def __init__(self, model_name: str, sport: str):
        self.model_name = model_name
        self.sport = sport
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.is_trained = False
        self.model_path = f"models/{sport}_{model_name}.pkl"
        self.scaler_path = f"models/{sport}_{model_name}_scaler.pkl"
        
        # Create models directory
        os.makedirs("models", exist_ok=True)
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """Train the model"""
        try:
            # Store feature columns
            self.feature_columns = X.columns.tolist()
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            y_proba = self.model.predict_proba(X_test_scaled)
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
            
            metrics = {
                'accuracy': accuracy,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            # Add AUC if binary classification
            if len(np.unique(y)) == 2:
                metrics['auc'] = roc_auc_score(y_test, y_proba[:, 1])
            
            self.is_trained = True
            logger.info(f"✅ {self.model_name} trained for {self.sport}: accuracy={accuracy:.3f}")
            
            # Save model
            self.save_model()
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error training {self.model_name}: {e}")
            raise
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction for a single match"""
        try:
            if not self.is_trained:
                raise ValueError(f"Model {self.model_name} is not trained")
            
            # Convert to DataFrame
            X = pd.DataFrame([features])
            
            # Ensure all features are present
            for col in self.feature_columns:
                if col not in X.columns:
                    X[col] = 0
            
            # Order columns correctly
            X = X[self.feature_columns]
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            prediction = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            
            # Get class labels
            classes = self.model.classes_
            prob_dict = dict(zip(classes, probabilities))
            
            return {
                'prediction': prediction,
                'probabilities': prob_dict,
                'confidence': max(probabilities) * 100
            }
            
        except Exception as e:
            logger.error(f"❌ Error predicting with {self.model_name}: {e}")
            return {
                'prediction': 'team1',
                'probabilities': {'team1': 0.5, 'team2': 0.5, 'draw': 0.0},
                'confidence': 50.0
            }
    
    def save_model(self):
        """Save model and scaler"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            # Save metadata
            metadata = {
                'model_name': self.model_name,
                'sport': self.sport,
                'feature_columns': self.feature_columns,
                'is_trained': self.is_trained,
                'trained_at': datetime.now().isoformat()
            }
            
            metadata_path = f"models/{self.sport}_{self.model_name}_metadata.json"
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"💾 Saved {self.model_name} model for {self.sport}")
            
        except Exception as e:
            logger.error(f"❌ Error saving {self.model_name}: {e}")
    
    def load_model(self) -> bool:
        """Load model and scaler"""
        try:
            if not os.path.exists(self.model_path) or not os.path.exists(self.scaler_path):
                return False
            
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            # Load metadata
            metadata_path = f"models/{self.sport}_{self.model_name}_metadata.json"
            if os.path.exists(metadata_path):
                import json
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                self.feature_columns = metadata.get('feature_columns', [])
                self.is_trained = metadata.get('is_trained', False)
            
            logger.info(f"📥 Loaded {self.model_name} model for {self.sport}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading {self.model_name}: {e}")
            return False

class LogisticRegressionModel(MLModel):
    """Logistic Regression model"""
    
    def __init__(self, sport: str):
        super().__init__("logistic_regression", sport)
        self.model = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced'
        )

class RandomForestModel(MLModel):
    """Random Forest model"""
    
    def __init__(self, sport: str):
        super().__init__("random_forest", sport)
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10,
            class_weight='balanced'
        )

class ModelManager:
    """Manage multiple ML models"""
    
    def __init__(self):
        self.models = {}
        self.default_models = [LogisticRegressionModel, RandomForestModel]
    
    def get_model(self, sport: str, model_type: str = "logistic_regression") -> MLModel:
        """Get or create model"""
        key = f"{sport}_{model_type}"
        
        if key not in self.models:
            if model_type == "logistic_regression":
                self.models[key] = LogisticRegressionModel(sport)
            elif model_type == "random_forest":
                self.models[key] = RandomForestModel(sport)
            else:
                raise ValueError(f"Unknown model type: {model_type}")
        
        return self.models[key]
    
    def train_all_models(self, sport: str, X: pd.DataFrame, y: pd.Series) -> Dict[str, Dict[str, float]]:
        """Train all models for a sport"""
        results = {}
        
        for model_class in self.default_models:
            model_name = model_class.__name__.replace("Model", "").lower()
            
            try:
                model = self.get_model(sport, model_name)
                metrics = model.train(X, y)
                results[model_name] = metrics
                
            except Exception as e:
                logger.error(f"❌ Error training {model_name} for {sport}: {e}")
                results[model_name] = {'error': str(e)}
        
        return results
    
    def load_all_models(self, sport: str) -> bool:
        """Load all models for a sport"""
        success = True
        
        for model_class in self.default_models:
            model_name = model_class.__name__.replace("Model", "").lower()
            
            try:
                model = self.get_model(sport, model_name)
                if not model.load_model():
                    success = False
                    
            except Exception as e:
                logger.error(f"❌ Error loading {model_name} for {sport}: {e}")
                success = False
        
        return success
    
    def predict_ensemble(self, sport: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make ensemble prediction"""
        predictions = {}
        
        for model_class in self.default_models:
            model_name = model_class.__name__.replace("Model", "").lower()
            
            try:
                model = self.get_model(sport, model_name)
                if model.is_trained:
                    pred = model.predict(features)
                    predictions[model_name] = pred
                    
            except Exception as e:
                logger.error(f"❌ Error predicting with {model_name}: {e}")
                continue
        
        if not predictions:
            return {
                'prediction': 'team1',
                'probabilities': {'team1': 0.5, 'team2': 0.5, 'draw': 0.0},
                'confidence': 50.0,
                'method': 'fallback'
            }
        
        # Simple voting ensemble
        votes = {}
        total_confidence = 0
        
        for model_name, pred in predictions.items():
            pred_class = pred['prediction']
            votes[pred_class] = votes.get(pred_class, 0) + 1
            total_confidence += pred['confidence']
        
        # Get winner by votes
        winner = max(votes.keys(), key=lambda x: votes[x])
        avg_confidence = total_confidence / len(predictions)
        
        # Average probabilities
        avg_probs = {'team1': 0, 'team2': 0, 'draw': 0}
        for pred in predictions.values():
            for outcome, prob in pred['probabilities'].items():
                avg_probs[outcome] += prob
        
        for outcome in avg_probs:
            avg_probs[outcome] /= len(predictions)
        
        return {
            'prediction': winner,
            'probabilities': avg_probs,
            'confidence': avg_confidence,
            'method': 'ensemble',
            'models_used': list(predictions.keys())
        }
