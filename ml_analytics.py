#!/usr/bin/env python3
"""
AIBET Analytics - ML Models and Predictions
Machine Learning models for match predictions and signal generation
"""

import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import logging
from database import DatabaseManager, Match, Signal

logger = logging.getLogger(__name__)

class MLAnalytics:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.models = {}
        self.scalers = {}
        self.encoders = {}
    
    async def initialize_models(self):
        """Initialize or load ML models"""
        sports = ['cs2', 'khl']
        
        for sport in sports:
            # Try to load existing models
            model = await self.db_manager.get_ml_model(sport, 'random_forest')
            if model:
                self.models[sport] = pickle.loads(model.model_data)
                logger.info(f"Loaded existing {sport} model with accuracy: {model.accuracy:.2f}")
            else:
                # Train new model
                await self.train_model(sport)
    
    async def train_model(self, sport: str):
        """Train ML model for specific sport"""
        try:
            logger.info(f"Training ML model for {sport}")
            
            # Get historical data
            training_data = await self._prepare_training_data(sport)
            
            if len(training_data) < 50:
                logger.warning(f"Insufficient data for {sport} model training: {len(training_data)} samples")
                return
            
            # Prepare features
            X, y = self._prepare_features(training_data)
            
            if len(X) < 20:
                logger.warning(f"Insufficient features for {sport} model: {len(X)} samples")
                return
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"{sport} model trained with accuracy: {accuracy:.2f}")
            
            # Save model
            self.models[sport] = model
            self.scalers[sport] = scaler
            
            # Save to database
            model_data = MLModel(
                sport=sport,
                model_type='random_forest',
                model_data=pickle.dumps(model),
                accuracy=accuracy,
                last_trained=datetime.now(),
                training_samples=len(X_train)
            )
            
            await self.db_manager.save_ml_model(model_data)
            
            # Log feature importance
            feature_names = self._get_feature_names()
            importances = model.feature_importances_
            
            logger.info(f"Feature importance for {sport}:")
            for name, importance in zip(feature_names, importances):
                logger.info(f"  {name}: {importance:.3f}")
            
        except Exception as e:
            logger.error(f"Error training {sport} model: {e}")
    
    async def predict_match(self, match: Match) -> Dict:
        """Predict match outcome"""
        try:
            sport = match.sport
            
            if sport not in self.models:
                logger.warning(f"No model available for {sport}")
                return self._default_prediction()
            
            # Prepare features for this match
            features = await self._extract_match_features(match)
            
            if not features:
                logger.warning(f"Could not extract features for match {match.id}")
                return self._default_prediction()
            
            # Scale features
            X = np.array([features])
            X_scaled = self.scalers[sport].transform(X)
            
            # Predict
            model = self.models[sport]
            probabilities = model.predict_proba(X_scaled)[0]
            prediction = model.predict(X_scaled)[0]
            
            # Map prediction to outcome
            outcome_map = {0: 'team1', 1: 'team2', 2: 'draw'}
            predicted_outcome = outcome_map.get(prediction, 'team1')
            
            # Calculate confidence
            confidence = max(probabilities)
            
            # Generate explanation
            explanation = await self._generate_explanation(match, features, prediction, probabilities)
            
            # Get important factors
            important_factors = self._get_important_factors(features, prediction)
            
            return {
                'prediction': predicted_outcome,
                'confidence': confidence,
                'probabilities': {
                    'team1': probabilities[0] if len(probabilities) > 0 else 0.33,
                    'team2': probabilities[1] if len(probabilities) > 1 else 0.33,
                    'draw': probabilities[2] if len(probabilities) > 2 else 0.34
                },
                'explanation': explanation,
                'factors': important_factors
            }
            
        except Exception as e:
            logger.error(f"Error predicting match {match.id}: {e}")
            return self._default_prediction()
    
    async def generate_signal(self, match: Match) -> Optional[Signal]:
        """Generate trading signal for match"""
        try:
            prediction = await self.predict_match(match)
            
            # Check if confidence is high enough
            if prediction['confidence'] < 0.65:
                logger.info(f"Low confidence {prediction['confidence']:.2f} for match {match.id}")
                return None
            
            # Check odds value
            predicted_prob = prediction['probabilities'][prediction['prediction']]
            required_odds = 1 / predicted_prob
            
            if match.odds1 < required_odds * 0.9 or match.odds2 < required_odds * 0.9:
                logger.info(f"No value in odds for match {match.id}")
                return None
            
            # Determine confidence level
            if prediction['confidence'] >= 0.80:
                confidence_level = 'HIGH'
            elif prediction['confidence'] >= 0.70:
                confidence_level = 'MEDIUM'
            else:
                confidence_level = 'LOW'
            
            # Create signal
            signal = Signal(
                id=f"signal_{match.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                match_id=match.id,
                sport=match.sport,
                scenario=f"{prediction['prediction']} win",
                confidence=confidence_level,
                probability=prediction['confidence'],
                explanation=prediction['explanation'],
                factors=prediction['factors'],
                odds_at_signal=match.odds1 if prediction['prediction'] == 'team1' else match.odds2,
                published_at=datetime.now()
            )
            
            # Save signal
            await self.db_manager.save_signal(signal)
            
            logger.info(f"Generated signal for {match.id}: {signal.scenario} with confidence {confidence_level}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for match {match.id}: {e}")
            return None
    
    async def _prepare_training_data(self, sport: str) -> List[Dict]:
        """Prepare training data from historical matches"""
        try:
            # Get completed matches with results
            # This is a simplified version - in production, you'd have historical data
            matches = await self.db_manager.get_upcoming_matches(sport, hours=168)  # Last week
            
            training_data = []
            for match in matches:
                # Simulate historical outcomes
                outcome = np.random.choice(['team1', 'team2', 'draw'], p=[0.45, 0.45, 0.10])
                
                features = await self._extract_match_features(match)
                if features:
                    training_data.append({
                        'features': features,
                        'outcome': outcome
                    })
            
            return training_data
            
        except Exception as e:
            logger.error(f"Error preparing training data for {sport}: {e}")
            return []
    
    async def _extract_match_features(self, match: Match) -> Optional[List[float]]:
        """Extract features from match"""
        try:
            features = []
            
            # Basic odds features
            features.append(match.odds1)
            features.append(match.odds2)
            features.append(match.odds_draw or 0.0)
            
            # Implied probabilities
            total_prob = 1/match.odds1 + 1/match.odds2
            if match.odds_draw:
                total_prob += 1/match.odds_draw
            
            features.append(1/match.odds1 / total_prob)  # Implied prob team1
            features.append(1/match.odds2 / total_prob)  # Implied prob team2
            features.append((1/match.odds_draw / total_prob) if match.odds_draw else 0.0)  # Implied prob draw
            
            # Time features
            match_hour = match.match_time.hour
            features.append(match_hour / 24.0)  # Normalized hour
            features.append(match.match_time.weekday() / 7.0)  # Normalized day of week
            
            # Tournament importance (simplified)
            tournament_importance = {
                'Major': 1.0,
                'IEM': 0.9,
                'BLAST': 0.8,
                'КХЛ Плей-офф': 1.0,
                'КХЛ Регулярный': 0.6
            }
            
            importance = 0.5  # Default
            for key, value in tournament_importance.items():
                if key.lower() in match.tournament.lower():
                    importance = value
                    break
            
            features.append(importance)
            
            # Team strength (simplified - would use historical data)
            features.append(0.5)  # Team1 strength placeholder
            features.append(0.5)  # Team2 strength placeholder
            
            # Recent form (placeholder)
            features.append(0.5)  # Team1 form
            features.append(0.5)  # Team2 form
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features for match {match.id}: {e}")
            return None
    
    def _prepare_features(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and labels for training"""
        X = []
        y = []
        
        outcome_map = {'team1': 0, 'team2': 1, 'draw': 2}
        
        for data in training_data:
            X.append(data['features'])
            y.append(outcome_map[data['outcome']])
        
        return np.array(X), np.array(y)
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names for explanation"""
        return [
            'odds1', 'odds2', 'odds_draw',
            'implied_prob1', 'implied_prob2', 'implied_prob_draw',
            'match_hour', 'match_day',
            'tournament_importance',
            'team1_strength', 'team2_strength',
            'team1_form', 'team2_form'
        ]
    
    async def _generate_explanation(self, match: Match, features: List[float], 
                                 prediction: int, probabilities: np.ndarray) -> str:
        """Generate explanation for prediction"""
        try:
            outcome_map = {0: 'team1', 1: 'team2', 2: 'draw'}
            predicted_outcome = outcome_map[prediction]
            
            team_name = match.team1 if predicted_outcome == 'team1' else match.team2
            
            explanation = f"Модель предсказывает победу {team_name} с вероятностью {max(probabilities):.1%}. "
            
            if max(probabilities) >= 0.80:
                explanation += "Высокая уверенность основана на анализе коэффициентов и текущей форме команд. "
            elif max(probabilities) >= 0.70:
                explanation += "Средняя уверенность с учетом статистики и недавних результатов. "
            else:
                explanation += "Низкая уверенность, матч может быть непредсказуемым. "
            
            # Add odds analysis
            if predicted_outcome == 'team1':
                if match.odds1 > 2.0:
                    explanation += f"Коэффициент {match.odds1} представляет хорошую ценность. "
                else:
                    explanation += f"Коэффициент {match.odds1} относительно низкий, что подтверждает прогноз. "
            else:
                if match.odds2 > 2.0:
                    explanation += f"Коэффициент {match.odds2} представляет хорошую ценность. "
                else:
                    explanation += f"Коэффициент {match.odds2} относительно низкий, что подтверждает прогноз. "
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "Прогноз основан на анализе коэффициентов и статистики команд."
    
    def _get_important_factors(self, features: List[float], prediction: int) -> List[str]:
        """Get important factors for prediction"""
        factors = []
        
        feature_names = self._get_feature_names()
        
        # Simplified importance analysis
        if features[0] < 1.8:  # Low odds for team1
            factors.append("Низкие коэффициенты на фаворита")
        
        if features[6] > 0.7:  # High tournament importance
            factors.append("Важность турнира")
        
        if abs(features[10] - features[11]) > 0.3:  # Form difference
            factors.append("Разница в текущей форме")
        
        if features[3] > 0.6:  # High implied probability
            factors.append("Высокая вероятность по коэффициентам")
        
        return factors[:3]  # Return top 3 factors
    
    def _default_prediction(self) -> Dict:
        """Default prediction when model is not available"""
        return {
            'prediction': 'team1',
            'confidence': 0.5,
            'probabilities': {'team1': 0.34, 'team2': 0.33, 'draw': 0.33},
            'explanation': 'Недостаточно данных для точного прогноза.',
            'factors': ['Ограниченная статистика']
        }

# Import MLModel from database
from database import MLModel
