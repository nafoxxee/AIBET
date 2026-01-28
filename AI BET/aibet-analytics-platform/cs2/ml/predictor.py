import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import joblib
import os

logger = logging.getLogger(__name__)


class CS2Predictor:
    """CS2 match outcome predictor using trained ML models"""
    
    def __init__(self, model_path: str = "cs2/ml/models/"):
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
            
            logger.info("CS2 ML models loaded successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Could not load CS2 models: {e}")
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
            win_probability = self.classifier.predict_proba(feature_vector_scaled)[0]
            predicted_winner = self.classifier.predict(feature_vector_scaled)[0]
            predicted_score_diff = self.regressor.predict(feature_vector_scaled)[0]
            
            # Create prediction result
            prediction = {
                'match_id': match_data.get('match_id', ''),
                'predicted_winner': 'team1' if predicted_winner == 1 else 'team2',
                'team1_win_probability': float(win_probability[1]),
                'team2_win_probability': float(win_probability[0]),
                'predicted_score_diff': float(predicted_score_diff),
                'confidence_score': self._calculate_confidence_score(win_probability),
                'model_version': 'v1.0',
                'prediction_time': datetime.now().isoformat(),
                'feature_importance': self._get_feature_importance(features),
                'risk_assessment': self._assess_risk(win_probability, features)
            }
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting match: {e}")
            return None
    
    def _extract_prediction_features(self, match_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract features for prediction"""
        try:
            trainer = __import__('cs2.ml.trainer', fromlist=['CS2MLTrainer']).CS2MLTrainer()
            return trainer._extract_features(match_data)
            
        except Exception as e:
            logger.warning(f"Error extracting prediction features: {e}")
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
            logger.warning(f"Error preparing feature vector: {e}")
            return None
    
    def _calculate_confidence_score(self, win_probability: np.ndarray) -> float:
        """Calculate confidence score based on prediction probability"""
        try:
            # Higher confidence when probability is more decisive
            max_prob = max(win_probability)
            min_prob = min(win_probability)
            
            # Confidence based on probability difference
            prob_diff = max_prob - min_prob
            
            # Scale to 0-1 range
            confidence = min(prob_diff * 2, 1.0)
            
            return float(confidence)
            
        except Exception as e:
            logger.warning(f"Error calculating confidence score: {e}")
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
            logger.warning(f"Error getting feature importance: {e}")
            return {}
    
    def _assess_risk(self, win_probability: np.ndarray, features: Dict[str, Any]) -> Dict[str, Any]:
        """Assess prediction risk"""
        try:
            risk_assessment = {
                'risk_level': 'medium',
                'risk_factors': [],
                'recommendation': ''
            }
            
            max_prob = max(win_probability)
            
            # Risk level based on confidence
            if max_prob >= 0.75:
                risk_assessment['risk_level'] = 'low'
            elif max_prob >= 0.60:
                risk_assessment['risk_level'] = 'medium'
            else:
                risk_assessment['risk_level'] = 'high'
            
            # Identify risk factors
            if features.get('team1_stand_in', 0) or features.get('team2_stand_in', 0):
                risk_assessment['risk_factors'].append('Stand-in players detected')
            
            if features.get('odds_volatility', 0) > 0.1:
                risk_assessment['risk_factors'].append('High odds volatility')
            
            if features.get('public_bias_strength', 0) > 0.6:
                risk_assessment['risk_factors'].append('Extreme public bias')
            
            if features.get('market_efficiency', 0.5) < 0.3:
                risk_assessment['risk_factors'].append('Low market efficiency')
            
            # Generate recommendation
            if risk_assessment['risk_level'] == 'low' and len(risk_assessment['risk_factors']) == 0:
                risk_assessment['recommendation'] = 'Strong prediction - consider betting'
            elif risk_assessment['risk_level'] == 'medium':
                risk_assessment['recommendation'] = 'Moderate confidence - proceed with caution'
            else:
                risk_assessment['recommendation'] = 'High risk - consider skipping or small stake'
            
            return risk_assessment
            
        except Exception as e:
            logger.warning(f"Error assessing risk: {e}")
            return {'risk_level': 'unknown', 'risk_factors': [], 'recommendation': 'Unable to assess risk'}
    
    def predict_multiple_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict outcomes for multiple matches"""
        predictions = []
        
        for match in matches:
            prediction = self.predict_match(match)
            if prediction:
                predictions.append(prediction)
        
        logger.info(f"Generated predictions for {len(predictions)} matches")
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
            
            accuracy = correct_predictions / len(predictions) if predictions else 0
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
            
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
                'risk_distribution': risk_levels,
                'accuracy_by_risk': risk_level_accuracy,
                'confidence_correlation': np.corrcoef(confidence_scores, 
                    [1 if p == r.get('winner', '') else 0 for p, r in zip(predictions, actual_results)])[0, 1] if len(predictions) > 1 else 0
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing prediction accuracy: {e}")
            return {'error': str(e)}


async def predict_cs2_matches(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Predict outcomes for CS2 matches"""
    predictor = CS2Predictor()
    
    if not predictor.load_models():
        logger.warning("Could not load ML models for prediction")
        return []
    
    return predictor.predict_multiple_matches(matches)


async def cs2_prediction_task():
    """CS2 prediction task for scheduler"""
    logger.info("Starting CS2 match predictions")
    
    try:
        # Get matches to predict
        from storage.database import get_upcoming_cs2_matches
        matches = await get_upcoming_cs2_matches()
        
        if matches:
            predictions = await predict_cs2_matches(matches)
            
            if predictions:
                # Store predictions
                from storage.database import store_cs2_predictions
                await store_cs2_predictions(predictions)
                
                # Send high-confidence predictions to Telegram
                high_confidence_predictions = [
                    p for p in predictions 
                    if p.get('confidence_score', 0) >= 0.7
                ]
                
                if high_confidence_predictions:
                    from app.main import telegram_sender
                    for prediction in high_confidence_predictions[:2]:  # Top 2 predictions
                        # Find corresponding match
                        match = next((m for m in matches if m.get('match_id') == prediction['match_id']), None)
                        
                        if match:
                            await telegram_sender.send_cs2_analysis({
                                'match': match,
                                'scenarios': [{
                                    'name': 'ML Prediction',
                                    'confidence': prediction['confidence_score'],
                                    'description': f"Predicted winner: {prediction['predicted_winner']}",
                                    'factors': [
                                        f"Team1 win prob: {prediction['team1_win_probability']:.1%}",
                                        f"Team2 win prob: {prediction['team2_win_probability']:.1%}",
                                        f"Risk level: {prediction['risk_assessment']['risk_level']}"
                                    ],
                                    'recommendation': prediction['risk_assessment']['recommendation']
                                }],
                                'recommendation': {
                                    'text': f"ML predicts {prediction['predicted_winner']} with {prediction['confidence_score']:.1%} confidence",
                                    'confidence': prediction['confidence_score']
                                }
                            })
                
                logger.info(f"Generated {len(predictions)} predictions, {len(high_confidence_predictions)} high confidence")
            else:
                logger.info("No predictions generated")
        
    except Exception as e:
        logger.error(f"CS2 prediction task failed: {e}")


def setup_cs2_prediction_tasks(scheduler):
    """Setup CS2 prediction tasks"""
    scheduler.add_task('cs2_predictions', cs2_prediction_task, 600)  # Every 10 minutes
    logger.info("CS2 prediction tasks setup complete")
