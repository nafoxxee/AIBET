#!/usr/bin/env python3
"""
AIBET Analytics - Advanced AI/ML Models
RandomForestClassifier & LogisticRegression for CS:GO & KHL predictions
"""

import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import logging

logger = logging.getLogger(__name__)

class AdvancedMLModels:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.model_performance = {}
        
    async def initialize_models(self):
        """Initialize ML models for CS:GO and KHL"""
        sports = ['cs2', 'khl']
        
        for sport in sports:
            # Try to load existing models
            if await self._load_model(sport):
                logger.info(f"Loaded existing {sport} ML models")
            else:
                # Train new models
                await self._train_models(sport)
    
    async def _train_models(self, sport: str):
        """Train both RandomForest and LogisticRegression models"""
        try:
            logger.info(f"Training ML models for {sport}")
            
            # Get training data
            training_data = await self._prepare_training_data(sport)
            
            if len(training_data) < 100:
                logger.warning(f"Insufficient data for {sport} training: {len(training_data)} samples")
                return
            
            # Prepare features
            X, y = self._prepare_features(training_data)
            
            if len(X) < 50:
                logger.warning(f"Insufficient features for {sport}: {len(X)} samples")
                return
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train RandomForest
            rf_model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight='balanced'
            )
            
            rf_model.fit(X_train_scaled, y_train)
            rf_pred = rf_model.predict(X_test_scaled)
            rf_accuracy = accuracy_score(y_test, rf_pred)
            
            # Train LogisticRegression
            lr_model = LogisticRegression(
                random_state=42,
                max_iter=1000,
                class_weight='balanced',
                solver='liblinear'
            )
            
            lr_model.fit(X_train_scaled, y_train)
            lr_pred = lr_model.predict(X_test_scaled)
            lr_accuracy = accuracy_score(y_test, lr_pred)
            
            # Save models
            self.models[sport] = {
                'random_forest': rf_model,
                'logistic_regression': lr_model
            }
            self.scalers[sport] = scaler
            
            # Store performance metrics
            self.model_performance[sport] = {
                'random_forest': {
                    'accuracy': rf_accuracy,
                    'cv_score': np.mean(cross_val_score(rf_model, X_train_scaled, y_train, cv=5))
                },
                'logistic_regression': {
                    'accuracy': lr_accuracy,
                    'cv_score': np.mean(cross_val_score(lr_model, X_train_scaled, y_train, cv=5))
                }
            }
            
            # Feature importance
            feature_names = self._get_feature_names()
            self.feature_importance[sport] = {
                'random_forest': dict(zip(feature_names, rf_model.feature_importances_)),
                'logistic_regression': dict(zip(feature_names, np.abs(lr_model.coef_[0])))
            }
            
            # Save to database
            await self._save_models(sport)
            
            logger.info(f"{sport} models trained - RF: {rf_accuracy:.3f}, LR: {lr_accuracy:.3f}")
            
        except Exception as e:
            logger.error(f"Error training {sport} models: {e}")
    
    async def predict_match(self, match_data: Dict, sport: str) -> Dict:
        """Advanced match prediction with ensemble methods"""
        try:
            if sport not in self.models:
                return self._default_prediction()
            
            # Extract features
            features = self._extract_match_features(match_data, sport)
            
            if not features:
                return self._default_prediction()
            
            # Scale features
            X = np.array([features])
            X_scaled = self.scalers[sport].transform(X)
            
            # Get predictions from both models
            rf_model = self.models[sport]['random_forest']
            lr_model = self.models[sport]['logistic_regression']
            
            rf_probabilities = rf_model.predict_proba(X_scaled)[0]
            rf_prediction = rf_model.predict(X_scaled)[0]
            
            lr_probabilities = lr_model.predict_proba(X_scaled)[0]
            lr_prediction = lr_model.predict(X_scaled)[0]
            
            # Ensemble prediction (weighted average)
            rf_weight = 0.6  # RandomForest usually performs better
            lr_weight = 0.4
            
            ensemble_probabilities = rf_weight * rf_probabilities + lr_weight * lr_probabilities
            ensemble_prediction = np.argmax(ensemble_probabilities)
            
            # Map prediction to outcome
            outcome_map = {0: 'team1', 1: 'team2', 2: 'draw'}
            predicted_outcome = outcome_map.get(ensemble_prediction, 'team1')
            
            # Calculate confidence
            confidence = max(ensemble_probabilities)
            
            # Generate detailed explanation
            explanation = await self._generate_detailed_explanation(
                match_data, features, ensemble_probabilities, sport
            )
            
            # Get important factors
            important_factors = self._get_important_factors(sport, features, ensemble_prediction)
            
            # Calculate expected value
            expected_value = self._calculate_expected_value(
                match_data, ensemble_probabilities, predicted_outcome
            )
            
            return {
                'prediction': predicted_outcome,
                'confidence': confidence,
                'probabilities': {
                    'team1': ensemble_probabilities[0],
                    'team2': ensemble_probabilities[1] if len(ensemble_probabilities) > 1 else 0.0,
                    'draw': ensemble_probabilities[2] if len(ensemble_probabilities) > 2 else 0.0
                },
                'explanation': explanation,
                'factors': important_factors,
                'expected_value': expected_value,
                'model_performance': self.model_performance.get(sport, {}),
                'prediction_type': self._classify_prediction_type(confidence, expected_value)
            }
            
        except Exception as e:
            logger.error(f"Error predicting match: {e}")
            return self._default_prediction()
    
    async def _prepare_training_data(self, sport: str) -> List[Dict]:
        """Prepare comprehensive training data"""
        try:
            # This would connect to database to get historical matches
            # For now, simulate comprehensive training data
            
            training_data = []
            
            # Generate realistic training samples
            for i in range(500):  # 500 historical matches
                if sport == 'cs2':
                    # CS:GO specific data
                    match_data = {
                        'team1_tier': np.random.choice(['T1', 'T2', 'T3'], p=[0.3, 0.4, 0.3]),
                        'team2_tier': np.random.choice(['T1', 'T2', 'T3'], p=[0.3, 0.4, 0.3]),
                        'team1_form': np.random.uniform(0.2, 0.9),
                        'team2_form': np.random.uniform(0.2, 0.9),
                        'h2h_win_rate': np.random.uniform(0.0, 1.0),
                        'map_advantage': np.random.uniform(-0.3, 0.3),
                        'recent_matches': np.random.randint(5, 30),
                        'odds1': np.random.uniform(1.2, 3.5),
                        'odds2': np.random.uniform(1.2, 3.5),
                        'betting_percentage1': np.random.uniform(20, 80),
                        'betting_percentage2': np.random.uniform(20, 80),
                        'tournament_importance': np.random.uniform(0.5, 1.0),
                        'live_performance': np.random.uniform(0.3, 0.9),
                        'roster_stability': np.random.uniform(0.6, 1.0)
                    }
                else:  # KHL
                    match_data = {
                        'team1_tier': np.random.choice(['T1', 'T2', 'T3'], p=[0.4, 0.4, 0.2]),
                        'team2_tier': np.random.choice(['T1', 'T2', 'T3'], p=[0.4, 0.4, 0.2]),
                        'team1_form': np.random.uniform(0.3, 0.9),
                        'team2_form': np.random.uniform(0.3, 0.9),
                        'h2h_win_rate': np.random.uniform(0.0, 1.0),
                        'home_advantage': np.random.choice([0, 1], p=[0.5, 0.5]),
                        'goal_difference': np.random.uniform(-2, 2),
                        'recent_goals': np.random.uniform(1.5, 4.5),
                        'odds1': np.random.uniform(1.5, 4.0),
                        'odds2': np.random.uniform(1.5, 4.0),
                        'odds_draw': np.random.uniform(3.0, 5.0),
                        'betting_percentage1': np.random.uniform(25, 75),
                        'betting_percentage2': np.random.uniform(25, 75),
                        'betting_percentage_draw': np.random.uniform(5, 25),
                        'tournament_importance': np.random.uniform(0.6, 1.0),
                        'goaltender_rating': np.random.uniform(0.5, 0.95),
                        'power_play_efficiency': np.random.uniform(0.1, 0.3)
                    }
                
                # Simulate outcome based on odds and form
                outcome = self._simulate_outcome(match_data, sport)
                
                training_data.append({
                    'features': match_data,
                    'outcome': outcome
                })
            
            return training_data
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return []
    
    def _simulate_outcome(self, match_data: Dict, sport: str) -> str:
        """Simulate realistic match outcomes"""
        # Calculate win probability based on odds and form
        implied_prob1 = 1 / match_data['odds1']
        implied_prob2 = 1 / match_data['odds2']
        
        if sport == 'cs2':
            # Adjust for team form and tier
            form_factor1 = match_data['team1_form']
            form_factor2 = match_data['team2_form']
            
            tier_bonus = {'T1': 0.1, 'T2': 0.0, 'T3': -0.1}
            tier_factor1 = tier_bonus[match_data['team1_tier']]
            tier_factor2 = tier_bonus[match_data['team2_tier']]
            
            adj_prob1 = implied_prob1 * (1 + form_factor1 + tier_factor1)
            adj_prob2 = implied_prob2 * (1 + form_factor2 + tier_factor2)
        else:  # KHL
            form_factor1 = match_data['team1_form']
            form_factor2 = match_data['team2_form']
            
            home_bonus = 0.1 if match_data.get('home_advantage', 0) == 1 else 0
            
            adj_prob1 = implied_prob1 * (1 + form_factor1 + home_bonus)
            adj_prob2 = implied_prob2 * (1 + form_factor2)
        
        # Normalize probabilities
        total_prob = adj_prob1 + adj_prob2
        if sport == 'khl' and 'odds_draw' in match_data:
            draw_prob = 1 / match_data['odds_draw']
            total_prob += draw_prob
        
        adj_prob1 = adj_prob1 / total_prob
        adj_prob2 = adj_prob2 / total_prob
        
        # Determine outcome
        outcomes = ['team1', 'team2']
        probabilities = [adj_prob1, adj_prob2]
        
        if sport == 'khl' and 'odds_draw' in match_data:
            outcomes.append('draw')
            draw_prob = (1 / match_data['odds_draw']) / total_prob
            probabilities.append(draw_prob)
        
        return np.random.choice(outcomes, p=probabilities)
    
    def _prepare_features(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and labels for training"""
        X = []
        y = []
        
        outcome_map = {'team1': 0, 'team2': 1, 'draw': 2}
        
        for data in training_data:
            features = []
            feature_dict = data['features']
            
            # Convert all features to numerical values
            for key in sorted(feature_dict.keys()):
                value = feature_dict[key]
                if isinstance(value, str):
                    if 'T1' in value:
                        features.append(1.0)
                    elif 'T2' in value:
                        features.append(0.5)
                    elif 'T3' in value:
                        features.append(0.0)
                    else:
                        features.append(0.5)
                else:
                    features.append(float(value))
            
            X.append(features)
            y.append(outcome_map[data['outcome']])
        
        return np.array(X), np.array(y)
    
    def _extract_match_features(self, match_data: Dict, sport: str) -> Optional[List[float]]:
        """Extract features from match data"""
        try:
            features = []
            
            # Basic odds features
            features.append(float(match_data.get('odds1', 2.0)))
            features.append(float(match_data.get('odds2', 2.0)))
            
            if sport == 'khl':
                features.append(float(match_data.get('odds_draw', 4.0)))
            else:
                features.append(0.0)  # No draw in CS:GO
            
            # Implied probabilities
            odds1 = float(match_data.get('odds1', 2.0))
            odds2 = float(match_data.get('odds2', 2.0))
            
            total_prob = 1/odds1 + 1/odds2
            if sport == 'khl' and 'odds_draw' in match_data:
                total_prob += 1/match_data['odds_draw']
            
            features.append((1/odds1) / total_prob)
            features.append((1/odds2) / total_prob)
            
            if sport == 'khl' and 'odds_draw' in match_data:
                features.append((1/match_data['odds_draw']) / total_prob)
            else:
                features.append(0.0)
            
            # Betting percentages
            features.append(float(match_data.get('betting_percentage1', 50)))
            features.append(float(match_data.get('betting_percentage2', 50)))
            
            if sport == 'khl':
                features.append(float(match_data.get('betting_percentage_draw', 10)))
            else:
                features.append(0.0)
            
            # Tournament importance
            features.append(float(match_data.get('tournament_importance', 0.7)))
            
            # Team form (placeholder - would come from historical data)
            features.append(float(match_data.get('team1_form', 0.5)))
            features.append(float(match_data.get('team2_form', 0.5)))
            
            # Head-to-head record
            features.append(float(match_data.get('h2h_win_rate', 0.5)))
            
            # Sport-specific features
            if sport == 'cs2':
                features.append(float(match_data.get('map_advantage', 0.0)))
                features.append(float(match_data.get('live_performance', 0.5)))
                features.append(float(match_data.get('roster_stability', 0.8)))
            else:  # KHL
                features.append(float(match_data.get('home_advantage', 0)))
                features.append(float(match_data.get('goal_difference', 0.0)))
                features.append(float(match_data.get('goaltender_rating', 0.7)))
                features.append(float(match_data.get('power_play_efficiency', 0.2)))
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None
    
    def _get_feature_names(self, sport: str = 'cs2') -> List[str]:
        """Get feature names for explanation"""
        base_features = [
            'odds1', 'odds2', 'odds_draw',
            'implied_prob1', 'implied_prob2', 'implied_prob_draw',
            'betting_perc1', 'betting_perc2', 'betting_perc_draw',
            'tournament_importance',
            'team1_form', 'team2_form',
            'h2h_win_rate'
        ]
        
        if sport == 'cs2':
            sport_features = ['map_advantage', 'live_performance', 'roster_stability']
        else:  # KHL
            sport_features = ['home_advantage', 'goal_difference', 'goaltender_rating', 'power_play_efficiency']
        
        return base_features + sport_features
    
    async def _generate_detailed_explanation(self, match_data: Dict, features: List[float], 
                                          probabilities: np.ndarray, sport: str) -> str:
        """Generate detailed explanation for prediction"""
        try:
            outcome_idx = np.argmax(probabilities)
            confidence = max(probabilities)
            
            outcome_map = {0: 'первой команды', 1: 'второй команды', 2: 'ничья'}
            predicted_outcome = outcome_map[outcome_idx]
            
            explanation = f"🤖 **AI Прогноз:** Победа {predicted_outcome} с вероятностью {confidence:.1%}\n\n"
            
            # Confidence explanation
            if confidence >= 0.85:
                explanation += "🔥 **Высокая уверенность:** Все факторы указывают на этот исход\n"
            elif confidence >= 0.70:
                explanation += "🟡 **Средняя уверенность:** Большинство факторов поддерживают прогноз\n"
            else:
                explanation += "🟢 **Низкая уверенность:** Матч может быть непредсказуемым\n"
            
            # Odds analysis
            odds1 = float(match_data.get('odds1', 2.0))
            odds2 = float(match_data.get('odds2', 2.0))
            
            if outcome_idx == 0:  # Team1 predicted
                if odds1 > 2.0:
                    explanation += f"💰 **Ценность:** Коэффициент {odds1} представляет хорошую ценность\n"
                else:
                    explanation += f"💰 **Подтверждение:** Низкий коэффициент {odds1} подтверждает прогноз\n"
            elif outcome_idx == 1:  # Team2 predicted
                if odds2 > 2.0:
                    explanation += f"💰 **Ценность:** Коэффициент {odds2} представляет хорошую ценность\n"
                else:
                    explanation += f"💰 **Подтверждение:** Низкий коэффициент {odds2} подтверждает прогноз\n"
            
            # Betting percentages
            bet_perc1 = float(match_data.get('betting_percentage1', 50))
            bet_perc2 = float(match_data.get('betting_percentage2', 50))
            
            if abs(bet_perc1 - bet_perc2) > 20:
                explanation += f"📊 **Настрой рынка:** Пользователи ставят на {'первую' if bet_perc1 > bet_perc2 else 'вторую'} команду ({max(bet_perc1, bet_perc2):.0f}%)\n"
            
            # Sport-specific insights
            if sport == 'cs2':
                map_adv = features[13] if len(features) > 13 else 0.5
                if abs(map_adv) > 0.2:
                    explanation += f"🗺️ **Преимущество на картах:** {'Первая' if map_adv > 0 else 'Вторая'} команда имеет преимущество\n"
            else:  # KHL
                home_adv = features[13] if len(features) > 13 else 0
                if home_adv > 0.5:
                    explanation += f"🏠 **Домашнее преимущество:** Первая команда играет дома\n"
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "Прогноз основан на анализе коэффициентов и статистики команд."
    
    def _get_important_factors(self, sport: str, features: List[float], prediction: int) -> List[str]:
        """Get important factors for prediction"""
        factors = []
        
        if sport not in self.feature_importance:
            return ['Анализ коэффициентов', 'Форма команд', 'История встреч']
        
        importance = self.feature_importance[sport]['random_forest']
        feature_names = self._get_feature_names(sport)
        
        # Get top 5 most important features
        sorted_features = sorted(zip(feature_names, importance.values()), key=lambda x: x[1], reverse=True)[:5]
        
        for name, importance_score in sorted_features:
            if importance_score > 0.05:  # Only include significant factors
                if 'odds' in name:
                    factors.append('Анализ коэффициентов')
                elif 'form' in name:
                    factors.append('Текущая форма команд')
                elif 'h2h' in name:
                    factors.append('История личных встреч')
                elif 'betting' in name:
                    factors.append('Настрой рынка ставок')
                elif 'tournament' in name:
                    factors.append('Важность турнира')
                elif sport == 'cs2' and 'map' in name:
                    factors.append('Преимущество на картах')
                elif sport == 'khl' and 'home' in name:
                    factors.append('Домашнее преимущество')
                else:
                    factors.append(f'Фактор: {name}')
        
        return factors[:4]  # Return top 4 factors
    
    def _calculate_expected_value(self, match_data: Dict, probabilities: np.ndarray, predicted_outcome: str) -> float:
        """Calculate expected value for the predicted outcome"""
        try:
            if predicted_outcome == 'team1':
                odds = float(match_data.get('odds1', 2.0))
                prob = probabilities[0]
            elif predicted_outcome == 'team2':
                odds = float(match_data.get('odds2', 2.0))
                prob = probabilities[1] if len(probabilities) > 1 else 0.0
            else:  # draw
                odds = float(match_data.get('odds_draw', 3.0))
                prob = probabilities[2] if len(probabilities) > 2 else 0.0
            
            # Expected value = (probability * odds) - 1
            ev = (prob * odds) - 1
            
            return round(ev, 3)
            
        except Exception as e:
            logger.error(f"Error calculating EV: {e}")
            return 0.0
    
    def _classify_prediction_type(self, confidence: float, expected_value: float) -> str:
        """Classify prediction type based on confidence and EV"""
        if confidence >= 0.80 and expected_value > 0.2:
            return "HIGH_VALUE"
        elif confidence >= 0.75:
            return "HIGH_CONFIDENCE"
        elif confidence >= 0.65 and expected_value > 0.1:
            return "MEDIUM_VALUE"
        elif confidence >= 0.60:
            return "MEDIUM_CONFIDENCE"
        elif expected_value > 0.3:
            return "VALUE_BET"
        else:
            return "LOW_CONFIDENCE"
    
    def _default_prediction(self) -> Dict:
        """Default prediction when models are not available"""
        return {
            'prediction': 'team1',
            'confidence': 0.5,
            'probabilities': {'team1': 0.34, 'team2': 0.33, 'draw': 0.33},
            'explanation': 'Недостаточно данных для точного прогноза.',
            'factors': ['Ограниченная статистика'],
            'expected_value': 0.0,
            'model_performance': {},
            'prediction_type': 'LOW_CONFIDENCE'
        }
    
    async def _load_model(self, sport: str) -> bool:
        """Load models from database"""
        try:
            if not self.db_manager:
                return False
            
            # This would load from database
            # For now, return False to trigger training
            return False
            
        except Exception as e:
            logger.error(f"Error loading {sport} models: {e}")
            return False
    
    async def _save_models(self, sport: str):
        """Save models to database"""
        try:
            if not self.db_manager:
                return
            
            # This would save to database
            logger.info(f"Models for {sport} ready to be saved")
            
        except Exception as e:
            logger.error(f"Error saving {sport} models: {e}")
    
    async def generate_signal(self, match_data: Dict, sport: str) -> Optional[Dict]:
        """Generate trading signal with advanced criteria"""
        try:
            prediction = await self.predict_match(match_data, sport)
            
            # Check if prediction meets signal criteria
            confidence = prediction['confidence']
            prediction_type = prediction['prediction_type']
            expected_value = prediction['expected_value']
            
            # Signal generation criteria
            min_confidence = 0.65
            min_ev = 0.05
            
            if confidence < min_confidence and expected_value < min_ev:
                return None
            
            # Determine signal strength
            if prediction_type in ['HIGH_VALUE', 'HIGH_CONFIDENCE']:
                strength = 'HIGH'
            elif prediction_type in ['MEDIUM_VALUE', 'MEDIUM_CONFIDENCE']:
                strength = 'MEDIUM'
            elif prediction_type == 'VALUE_BET':
                strength = 'MEDIUM'
            else:
                strength = 'LOW'
            
            # Create signal
            signal = {
                'id': f"signal_{sport}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'sport': sport,
                'match': f"{match_data.get('team1', 'Team1')} vs {match_data.get('team2', 'Team2')}",
                'prediction': prediction['prediction'],
                'confidence': confidence,
                'strength': strength,
                'probability': prediction['probabilities'][prediction['prediction']],
                'expected_value': expected_value,
                'odds': match_data.get('odds1') if prediction['prediction'] == 'team1' else match_data.get('odds2'),
                'explanation': prediction['explanation'],
                'factors': prediction['factors'],
                'prediction_type': prediction_type,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Generated {strength} signal for {sport}: {signal['match']}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None
