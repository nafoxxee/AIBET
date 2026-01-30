import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import joblib
import os

logger = logging.getLogger(__name__)


class KHLPredictor:
    """KHL match outcome predictor using trained ML models"""
    
    def __init__(self, model_path: str = "khl/ml/models/"):
        self.model_path = model_path
        self.classifier = None
        self.regressor = None
        self.scaler = None
        self.feature_columns = []
        
        # Load models on initialization
        self.load_models()
    
    def load_models(self) -> bool:
        """Load trained ML models"""
        try:
            self.classifier = joblib.load(os.path.join(self.model_path, 'classifier.pkl'))
            self.regressor = joblib.load(os.path.join(self.model_path, 'regressor.pkl'))
            self.scaler = joblib.load(os.path.join(self.model_path, 'scaler.pkl'))
            self.feature_columns = joblib.load(os.path.join(self.model_path, 'feature_columns.pkl'))
            
            logger.info("KHL ML models loaded successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Could not load KHL models: {e}")
            return False
    
    def predict_match(self, match_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Predict match outcome"""
        try:
            if not self.classifier or not self.regressor:
                logger.warning("Models not loaded")
                return None
            
            # Extract features
            features = self._extract_prediction_features(match_data)
            if not features:
                return None
            
            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features)
            if feature_vector is None:
                return None
            
            # Scale features
            feature_vector_scaled = self.scaler.transform([feature_vector])
            
            # Make predictions
            win_probabilities = self.classifier.predict_proba(feature_vector_scaled)[0]
            predicted_winner_class = self.classifier.predict(feature_vector_scaled)[0]
            predicted_total_goals = self.regressor.predict(feature_vector_scaled)[0]
            
            # Convert class to winner
            winner_map = {0: 'draw', 1: 'team1', 2: 'team2'}
            predicted_winner = winner_map.get(predicted_winner_class, 'unknown')
            
            # Create prediction result
            prediction = {
                'match_id': match_data.get('match_id', ''),
                'predicted_winner': predicted_winner,
                'team1_win_probability': float(win_probabilities[1]),
                'team2_win_probability': float(win_probabilities[2]),
                'draw_probability': float(win_probabilities[0]),
                'predicted_total_goals': float(predicted_total_goals),
                'confidence_score': self._calculate_confidence_score(win_probabilities),
                'model_version': 'v1.0',
                'prediction_time': datetime.now().isoformat(),
                'feature_importance': self._get_feature_importance(features),
                'risk_assessment': self._assess_risk(win_probabilities, features),
                'period_predictions': self._predict_periods(match_data, predicted_total_goals)
            }
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting KHL match: {e}")
            return None
    
    def _extract_prediction_features(self, match_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract features for prediction"""
        try:
            trainer = __import__('khl.ml.trainer', fromlist=['KHLMLTrainer']).KHLMLTrainer()
            return trainer._extract_features(match_data)
            
        except Exception as e:
            logger.warning(f"Error extracting KHL prediction features: {e}")
            return None
    
    def _prepare_feature_vector(self, features: Dict[str, Any]) -> Optional[List[float]]:
        """Prepare feature vector for prediction"""
        try:
            vector = []
            
            for col in self.feature_columns:
                if col in features:
                    vector.append(float(features[col]))
                else:
                    vector.append(0.0)  # Default value for missing features
            
            return vector
            
        except Exception as e:
            logger.warning(f"Error preparing KHL feature vector: {e}")
            return None
    
    def _calculate_confidence_score(self, win_probabilities: np.ndarray) -> float:
        """Calculate confidence score based on prediction probability"""
        try:
            # Higher confidence when probability is more decisive
            max_prob = max(win_probabilities)
            second_max_prob = sorted(win_probabilities)[-2]
            
            # Confidence based on probability difference
            prob_diff = max_prob - second_max_prob
            
            # Scale to 0-1 range
            confidence = min(prob_diff * 2, 1.0)
            
            return float(confidence)
            
        except Exception as e:
            logger.warning(f"Error calculating KHL confidence score: {e}")
            return 0.5
    
    def _get_feature_importance(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Get feature importance for this prediction"""
        try:
            if not self.classifier:
                return {}
            
            # Get global feature importance
            global_importance = self.classifier.feature_importances_
            
            # Create importance dictionary
            importance_dict = {}
            for i, feature in enumerate(self.feature_columns):
                if i < len(global_importance):
                    importance_dict[feature] = float(global_importance[i])
            
            # Sort by importance
            sorted_importance = dict(
                sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:5]
            )
            
            return sorted_importance
            
        except Exception as e:
            logger.warning(f"Error getting KHL feature importance: {e}")
            return {}
    
    def _assess_risk(self, win_probabilities: np.ndarray, features: Dict[str, Any]) -> Dict[str, Any]:
        """Assess prediction risk"""
        try:
            risk_assessment = {
                'risk_level': 'medium',
                'risk_factors': [],
                'recommendation': ''
            }
            
            max_prob = max(win_probabilities)
            draw_prob = win_probabilities[0]
            
            # Risk level based on confidence
            if max_prob >= 0.65:
                risk_assessment['risk_level'] = 'low'
            elif max_prob >= 0.45:
                risk_assessment['risk_level'] = 'medium'
            else:
                risk_assessment['risk_level'] = 'high'
            
            # Identify risk factors
            if draw_prob > 0.25:
                risk_assessment['risk_factors'].append('High draw probability')
            
            if features.get('odds_volatility', 0) > 0.05:
                risk_assessment['risk_factors'].append('High odds volatility')
            
            if features.get('market_efficiency', 0.5) < 0.4:
                risk_assessment['risk_factors'].append('Low market efficiency')
            
            # Check for close match odds
            team1_odds = features.get('team1_odds', 0)
            team2_odds = features.get('team2_odds', 0)
            
            if team1_odds > 0 and team2_odds > 0:
                odds_diff = abs(team1_odds - team2_odds)
                if odds_diff < 0.15:
                    risk_assessment['risk_factors'].append('Very close match odds')
            
            # Generate recommendation
            if risk_assessment['risk_level'] == 'low' and len(risk_assessment['risk_factors']) == 0:
                risk_assessment['recommendation'] = 'Strong prediction - consider betting'
            elif risk_assessment['risk_level'] == 'medium':
                risk_assessment['recommendation'] = 'Moderate confidence - proceed with caution'
            else:
                risk_assessment['recommendation'] = 'High risk - consider skipping or small stake'
            
            return risk_assessment
            
        except Exception as e:
            logger.warning(f"Error assessing KHL prediction risk: {e}")
            return {'risk_level': 'unknown', 'risk_factors': [], 'recommendation': 'Unable to assess risk'}
    
    def _predict_periods(self, match_data: Dict[str, Any], predicted_total_goals: float) -> Dict[str, Any]:
        """Predict period-by-period outcomes"""
        try:
            # Distribute total goals across periods
            period_distribution = {
                'period1': max(0.0, predicted_total_goals * 0.3),
                'period2': max(0.0, predicted_total_goals * 0.35),
                'period3': max(0.0, predicted_total_goals * 0.35)
            }
            
            # Adjust for match characteristics
            odds_data = match_data.get('odds', {})
            period_odds = odds_data.get('period_odds', {})
            
            if period_odds:
                # Adjust based on period odds
                for period in ['period1', 'period2', 'period3']:
                    period_key = period.replace('period', 'period')  # period1 -> period1
                    if period_key in period_odds:
                        team1_odds = period_odds[period_key].get('team1', 2.5)
                        team2_odds = period_odds[period_key].get('team2', 2.5)
                        
                        # Lower odds indicate higher scoring probability
                        avg_odds = (team1_odds + team2_odds) / 2
                        if avg_odds < 2.2:
                            period_distribution[period] *= 1.2
                        elif avg_odds > 2.8:
                            period_distribution[period] *= 0.8
            
            # Round to reasonable values
            for period in period_distribution:
                period_distribution[period] = round(period_distribution[period], 1)
            
            # Calculate overtime probability
            score_diff = abs(predicted_total_goals - 5.5)  # Distance from average total
            overtime_prob = max(0.1, min(0.4, 0.25 - score_diff * 0.05))
            
            return {
                'period_goals': period_distribution,
                'overtime_probability': overtime_prob,
                'most_likely_period': max(period_distribution, key=period_distribution.get)
            }
            
        except Exception as e:
            logger.warning(f"Error predicting KHL periods: {e}")
            return {
                'period_goals': {'period1': 1.5, 'period2': 1.8, 'period3': 1.7},
                'overtime_probability': 0.2,
                'most_likely_period': 'period2'
            }
    
    def predict_multiple_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict outcomes for multiple matches"""
        predictions = []
        
        for match in matches:
            prediction = self.predict_match(match)
            if prediction:
                predictions.append(prediction)
        
        logger.info(f"Generated KHL predictions for {len(predictions)} matches")
        return predictions
    
    def analyze_prediction_accuracy(self, predictions: List[Dict[str, Any]], 
                                  actual_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze prediction accuracy against actual results"""
        try:
            if len(predictions) != len(actual_results):
                return {'error': 'Mismatch between predictions and results'}
            
            correct_predictions = 0
            confidence_scores = []
            risk_levels = {'low': 0, 'medium': 0, 'high': 0}
            risk_accuracy = {'low': [], 'medium': [], 'high': []}
            total_goals_errors = []
            
            for pred, actual in zip(predictions, actual_results):
                predicted_winner = pred.get('predicted_winner', '')
                actual_winner = actual.get('winner', '')
                
                if predicted_winner == actual_winner:
                    correct_predictions += 1
                
                confidence_scores.append(pred.get('confidence_score', 0))
                
                risk_level = pred.get('risk_assessment', {}).get('risk_level', 'medium')
                risk_levels[risk_level] += 1
                
                is_correct = predicted_winner == actual_winner
                risk_accuracy[risk_level].append(is_correct)
                
                # Total goals accuracy
                predicted_total = pred.get('predicted_total_goals', 0)
                actual_total = actual.get('total_goals', 0)
                total_goals_errors.append(abs(predicted_total - actual_total))
            
            accuracy = correct_predictions / len(predictions) if predictions else 0
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
            avg_goals_error = np.mean(total_goals_errors) if total_goals_errors else 0
            
            # Calculate accuracy by risk level
            risk_level_accuracy = {}
            for level in ['low', 'medium', 'high']:
                level_predictions = risk_accuracy[level]
                if level_predictions:
                    risk_level_accuracy[level] = sum(level_predictions) / len(level_predictions)
                else:
                    risk_level_accuracy[level] = 0
            
            analysis = {
                'total_predictions': len(predictions),
                'correct_predictions': correct_predictions,
                'accuracy': accuracy,
                'average_confidence': avg_confidence,
                'average_goals_error': avg_goals_error,
                'risk_distribution': risk_levels,
                'accuracy_by_risk': risk_level_accuracy,
                'confidence_correlation': np.corrcoef(confidence_scores, 
                    [1 if p == r.get('winner', '') else 0 for p, r in zip(predictions, actual_results)])[0, 1] if len(predictions) > 1 else 0
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing KHL prediction accuracy: {e}")
            return {'error': str(e)}


async def predict_khl_matches(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Predict outcomes for KHL matches"""
    predictor = KHLPredictor()
    
    if not predictor.load_models():
        logger.warning("Could not load KHL ML models for prediction")
        return []
    
    return predictor.predict_multiple_matches(matches)


async def khl_prediction_task():
    """KHL prediction task for scheduler"""
    logger.info("Starting KHL match predictions")
    
    try:
        # Get matches to predict
        from storage.database import get_upcoming_khl_matches
        matches = await get_upcoming_khl_matches()
        
        if matches:
            predictions = await predict_khl_matches(matches)
            
            if predictions:
                # Store predictions
                from storage.database import store_khl_predictions
                await store_khl_predictions(predictions)
                
                # Send high-confidence predictions to Telegram
                high_confidence_predictions = [
                    p for p in predictions 
                    if p.get('confidence_score', 0) >= 0.65
                ]
                
                if high_confidence_predictions:
                    from app.main import telegram_sender
                    for prediction in high_confidence_predictions[:2]:  # Top 2 predictions
                        # Find corresponding match
                        match = next((m for m in matches if m.get('match_id') == prediction['match_id']), None)
                        
                        if match:
                            await telegram_sender.send_khl_analysis({
                                'match': match,
                                'scenarios': [{
                                    'name': 'ML Prediction',
                                    'confidence': prediction['confidence_score'],
                                    'description': f"Predicted winner: {prediction['predicted_winner']}",
                                    'factors': [
                                        f"Team1 win prob: {prediction['team1_win_probability']:.1%}",
                                        f"Team2 win prob: {prediction['team2_win_probability']:.1%}",
                                        f"Draw prob: {prediction['draw_probability']:.1%}",
                                        f"Risk level: {prediction['risk_assessment']['risk_level']}"
                                    ],
                                    'recommendation': prediction['risk_assessment']['recommendation']
                                }],
                                'recommendation': {
                                    'text': f"ML predicts {prediction['predicted_winner']} with {prediction['confidence_score']:.1%} confidence",
                                    'confidence': prediction['confidence_score']
                                }
                            })
                
                logger.info(f"Generated {len(predictions)} KHL predictions, {len(high_confidence_predictions)} high confidence")
            else:
                logger.info("No KHL predictions generated")
        
    except Exception as e:
        logger.error(f"KHL prediction task failed: {e}")


def setup_khl_prediction_tasks(scheduler):
    """Setup KHL prediction tasks"""
    scheduler.add_task('khl_predictions', khl_prediction_task, 600)  # Every 10 minutes
    logger.info("KHL prediction tasks setup complete")
