#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real ML Models Pipeline
ML models with RandomForest, GradientBoosting, LogisticRegression
"""

import asyncio
import logging
import numpy as np
import pandas as pd
import pickle
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import json

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, roc_curve
from sklearn.calibration import calibration_curve

from feature_engineering_real import feature_engineering, TeamFeatures
from database import Match, db_manager

logger = logging.getLogger(__name__)

# Global instance
ml_models = RealMLModels()

@dataclass
class PredictionResult:
    """Prediction result with confidence"""
    match_id: str
    team1: str
    team2: str
    sport: str
    prediction: int  # 1 for team1 win, 0 for team2 win
    confidence: float  # 0.0 to 1.0
    probabilities: Dict[str, float]  # {team1: prob, team2: prob}
    model_used: str
    features_used: int
    timestamp: datetime
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ModelMetrics:
    """Model performance metrics"""
    model_name: str
    accuracy: float
    roc_auc: float
    precision: float
    recall: float
    f1_score: float
    calibration_score: float
    cross_val_mean: float
    cross_val_std: float
    training_samples: int
    test_samples: int
    last_trained: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_name': self.model_name,
            'accuracy': self.accuracy,
            'roc_auc': self.roc_auc,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'calibration_score': self.calibration_score,
            'cross_val_mean': self.cross_val_mean,
            'cross_val_std': self.cross_val_std,
            'training_samples': self.training_samples,
            'test_samples': self.test_samples,
            'last_trained': self.last_trained.isoformat()
        }

class RealMLModels:
    def __init__(self):
        self.name = "Real ML Models"
        self.models_path = "models/"
        self.min_training_samples = 100
        self.confidence_threshold = 0.70
        
        # Create models directory
        os.makedirs(self.models_path, exist_ok=True)
        
        # Initialize models
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            ),
            'logistic_regression': LogisticRegression(
                random_state=42,
                max_iter=1000,
                n_jobs=-1
            )
        }
        
        # Scaler for features
        self.scaler = StandardScaler()
        
        # Model metadata
        self.model_metrics = {}
        self.is_trained = False
        self.feature_names = []
        
        # Load existing models if available
        self._load_models()
    
    def _load_models(self):
        """Load existing models from disk"""
        try:
            for model_name in self.models.keys():
                model_path = os.path.join(self.models_path, f"{model_name}.pkl")
                scaler_path = os.path.join(self.models_path, f"{model_name}_scaler.pkl")
                metrics_path = os.path.join(self.models_path, f"{model_name}_metrics.json")
                
                if os.path.exists(model_path):
                    with open(model_path, 'rb') as f:
                        self.models[model_name] = pickle.load(f)
                    
                    if os.path.exists(scaler_path):
                        with open(scaler_path, 'rb') as f:
                            if model_name == 'random_forest':  # Use one scaler for all
                                self.scaler = pickle.load(f)
                    
                    if os.path.exists(metrics_path):
                        with open(metrics_path, 'r') as f:
                            metrics_data = json.load(f)
                            self.model_metrics[model_name] = ModelMetrics(
                                model_name=metrics_data['model_name'],
                                accuracy=metrics_data['accuracy'],
                                roc_auc=metrics_data['roc_auc'],
                                precision=metrics_data['precision'],
                                recall=metrics_data['recall'],
                                f1_score=metrics_data['f1_score'],
                                calibration_score=metrics_data['calibration_score'],
                                cross_val_mean=metrics_data['cross_val_mean'],
                                cross_val_std=metrics_data['cross_val_std'],
                                training_samples=metrics_data['training_samples'],
                                test_samples=metrics_data['test_samples'],
                                last_trained=datetime.fromisoformat(metrics_data['last_trained'])
                            )
                    
                    logger.info(f"✅ Loaded {model_name} model")
            
            if self.model_metrics:
                self.is_trained = True
                logger.info(f"✅ Loaded {len(self.model_metrics)} trained models")
            
        except Exception as e:
            logger.error(f"❌ Error loading models: {e}")
    
    async def train_models(self, sport: str = None, force_retrain: bool = False):
        """Train all ML models"""
        logger.info(f"🤖 Training ML models for {sport or 'all sports'}")
        
        try:
            # Get training data
            if sport:
                X, y = await feature_engineering.get_training_data(sport, limit=2000)
            else:
                # Train on both sports
                X_cs2, y_cs2 = await feature_engineering.get_training_data('cs2', limit=1000)
                X_khl, y_khl = await feature_engineering.get_training_data('khl', limit=1000)
                
                if len(X_cs2) > 0 and len(X_khl) > 0:
                    X = np.vstack([X_cs2, X_khl])
                    y = np.hstack([y_cs2, y_khl])
                else:
                    X = X_cs2 if len(X_cs2) > len(X_khl) else X_khl
                    y = y_cs2 if len(X_cs2) > len(X_khl) else y_khl
            
            if len(X) < self.min_training_samples:
                logger.warning(f"⚠️ Insufficient training data: {len(X)} samples (need {self.min_training_samples})")
                return False
            
            logger.info(f"📊 Training with {len(X)} samples")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Store feature names (for debugging)
            self.feature_names = [f"feature_{i}" for i in range(X.shape[1])]
            
            # Train each model
            for model_name, model in self.models.items():
                try:
                    logger.info(f"🔧 Training {model_name}")
                    
                    # Train model
                    if model_name == 'random_forest':
                        model.fit(X_train_scaled, y_train)
                    elif model_name == 'gradient_boosting':
                        model.fit(X_train_scaled, y_train)
                    elif model_name == 'logistic_regression':
                        model.fit(X_train_scaled, y_train)
                    
                    # Evaluate model
                    metrics = await self._evaluate_model(
                        model, model_name, X_train_scaled, X_test_scaled, y_train, y_test
                    )
                    
                    # Save model and metrics
                    await self._save_model(model, model_name, metrics)
                    
                    logger.info(f"✅ Trained {model_name} - Accuracy: {metrics.accuracy:.3f}")
                    
                except Exception as e:
                    logger.error(f"❌ Error training {model_name}: {e}")
                    continue
            
            self.is_trained = True
            logger.info("✅ All models trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in training pipeline: {e}")
            return False
    
    async def _evaluate_model(self, model, model_name: str, X_train: np.ndarray, 
                            X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray) -> ModelMetrics:
        """Evaluate model performance"""
        try:
            # Predictions
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Basic metrics
            accuracy = accuracy_score(y_test, y_pred)
            roc_auc = roc_auc_score(y_test, y_pred_proba)
            
            # Classification report
            report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            precision = report['weighted avg']['precision']
            recall = report['weighted avg']['recall']
            f1_score = report['weighted avg']['f1-score']
            
            # Calibration score
            fraction_of_positives, mean_predicted_value = calibration_curve(y_test, y_pred_proba, n_bins=10)
            calibration_score = np.mean(np.abs(fraction_of_positives - mean_predicted_value))
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
            
            return ModelMetrics(
                model_name=model_name,
                accuracy=accuracy,
                roc_auc=roc_auc,
                precision=precision,
                recall=recall,
                f1_score=f1_score,
                calibration_score=calibration_score,
                cross_val_mean=cv_mean,
                cross_val_std=cv_std,
                training_samples=len(X_train),
                test_samples=len(X_test),
                last_trained=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ Error evaluating {model_name}: {e}")
            return ModelMetrics(
                model_name=model_name,
                accuracy=0.0, roc_auc=0.0, precision=0.0, recall=0.0, f1_score=0.0,
                calibration_score=0.0, cross_val_mean=0.0, cross_val_std=0.0,
                training_samples=0, test_samples=0, last_trained=datetime.now()
            )
    
    async def _save_model(self, model, model_name: str, metrics: ModelMetrics):
        """Save model and metrics to disk"""
        try:
            # Save model
            model_path = os.path.join(self.models_path, f"{model_name}.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            # Save scaler (only once)
            if model_name == 'random_forest':
                scaler_path = os.path.join(self.models_path, f"{model_name}_scaler.pkl")
                with open(scaler_path, 'wb') as f:
                    pickle.dump(self.scaler, f)
            
            # Save metrics
            metrics_path = os.path.join(self.models_path, f"{model_name}_metrics.json")
            with open(metrics_path, 'w') as f:
                json.dump(metrics.to_dict(), f, indent=2)
            
            self.model_metrics[model_name] = metrics
            
        except Exception as e:
            logger.error(f"❌ Error saving {model_name}: {e}")
    
    async def predict_match(self, match: Match) -> Optional[PredictionResult]:
        """Predict match outcome"""
        if not self.is_trained:
            logger.warning("⚠️ Models not trained yet")
            return None
        
        try:
            # Get features for both teams
            team1_features, team2_features = await feature_engineering.extract_features_for_match(match)
            
            # Convert to feature vector
            team1_dict = feature_engineering.features_to_dict(team1_features)
            team2_dict = feature_engineering.features_to_dict(team2_features)
            
            feature_vector = []
            for key in team1_dict.keys():
                feature_vector.append(team1_dict[key])
                feature_vector.append(team2_dict[key])
            
            X = np.array([feature_vector])
            X_scaled = self.scaler.transform(X)
            
            # Get predictions from all models
            predictions = {}
            confidences = {}
            
            for model_name, model in self.models.items():
                if model_name in self.model_metrics:
                    try:
                        pred_proba = model.predict_proba(X_scaled)[0]
                        pred = model.predict(X_scaled)[0]
                        
                        predictions[model_name] = pred
                        confidences[model_name] = max(pred_proba)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error predicting with {model_name}: {e}")
                        continue
            
            if not predictions:
                logger.warning("⚠️ No successful predictions")
                return None
            
            # Ensemble prediction (weighted average by model accuracy)
            weighted_pred = 0
            total_weight = 0
            
            for model_name, pred in predictions.items():
                weight = self.model_metrics[model_name].accuracy
                weighted_pred += pred * weight
                total_weight += weight
            
            final_prediction = int(round(weighted_pred / total_weight))
            final_confidence = np.mean(list(confidences.values()))
            
            # Get probabilities for the winning team
            team1_prob = 1 - final_prediction if final_prediction == 0 else final_confidence
            team2_prob = final_confidence if final_prediction == 0 else 1 - final_confidence
            
            # Determine which model was most confident
            best_model = max(confidences.keys(), key=lambda k: confidences[k])
            
            result = PredictionResult(
                match_id=str(match.id) if match.id else f"match_{datetime.now().timestamp()}",
                team1=match.team1,
                team2=match.team2,
                sport=match.sport,
                prediction=final_prediction,
                confidence=final_confidence,
                probabilities={
                    match.team1: team1_prob,
                    match.team2: team2_prob
                },
                model_used=best_model,
                features_used=len(feature_vector),
                timestamp=datetime.now()
            )
            
            logger.info(f"🎯 Prediction for {match.team1} vs {match.team2}: {match.team1 if final_prediction == 1 else match.team2} ({final_confidence:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error predicting match: {e}")
            return None
    
    async def predict_upcoming_matches(self, sport: str = None, limit: int = 20) -> List[PredictionResult]:
        """Predict upcoming matches"""
        try:
            # Get upcoming matches
            matches = await db_manager.get_matches(
                sport=sport, 
                status='upcoming', 
                limit=limit
            )
            
            predictions = []
            for match in matches:
                prediction = await self.predict_match(match)
                if prediction and prediction.confidence >= self.confidence_threshold:
                    predictions.append(prediction)
            
            # Sort by confidence
            predictions.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info(f"🎯 Generated {len(predictions)} high-confidence predictions")
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Error predicting upcoming matches: {e}")
            return []
    
    async def get_model_status(self) -> Dict[str, Any]:
        """Get model training status and metrics"""
        return {
            'is_trained': self.is_trained,
            'models_count': len(self.model_metrics),
            'confidence_threshold': self.confidence_threshold,
            'feature_count': len(self.feature_names),
            'models': {name: metrics.to_dict() for name, metrics in self.model_metrics.items()},
            'last_update': max([m.last_trained for m in self.model_metrics.values()]).isoformat() if self.model_metrics else None
        }
    
    async def retrain_if_needed(self, days_threshold: int = 7):
        """Retrain models if they are old"""
        if not self.model_metrics:
            logger.info("🤖 No models found, training from scratch")
            return await self.train_models()
        
        oldest_model = min(self.model_metrics.values(), key=lambda x: x.last_trained)
        days_since_training = (datetime.now() - oldest_model.last_trained).days
        
        if days_since_training >= days_threshold:
            logger.info(f"🤖 Models are {days_since_training} days old, retraining")
            return await self.train_models()
        else:
            logger.info(f"✅ Models are recent ({days_since_training} days old)")
            return True
    
    async def hyperparameter_tuning(self, sport: str = None):
        """Perform hyperparameter tuning for better performance"""
        logger.info("🔧 Starting hyperparameter tuning")
        
        try:
            # Get training data
            X, y = await feature_engineering.get_training_data(sport, limit=1000)
            
            if len(X) < 200:
                logger.warning("⚠️ Insufficient data for hyperparameter tuning")
                return False
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Hyperparameter grids
            param_grids = {
                'random_forest': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, 15, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                },
                'gradient_boosting': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7],
                    'subsample': [0.8, 0.9, 1.0]
                },
                'logistic_regression': {
                    'C': [0.1, 1.0, 10.0, 100.0],
                    'penalty': ['l1', 'l2'],
                    'solver': ['liblinear', 'saga']
                }
            }
            
            # Tune each model
            for model_name, model in self.models.items():
                if model_name in param_grids:
                    logger.info(f"🔧 Tuning {model_name}")
                    
                    grid_search = GridSearchCV(
                        model, 
                        param_grids[model_name], 
                        cv=3, 
                        scoring='accuracy',
                        n_jobs=-1,
                        verbose=1
                    )
                    
                    grid_search.fit(X_train_scaled, y_train)
                    
                    # Update model with best parameters
                    self.models[model_name] = grid_search.best_estimator_
                    
                    logger.info(f"✅ Best params for {model_name}: {grid_search.best_params_}")
            
            # Retrain with best parameters
            return await self.train_models(sport)
            
        except Exception as e:
            logger.error(f"❌ Error in hyperparameter tuning: {e}")
            return False

# Global instance
ml_models = RealMLModels()
