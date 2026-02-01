"""
AIBET MVP Predictor
Main prediction engine that combines feature engineering and ML models
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .feature_engineer import FeatureEngineer
from .models import ModelManager

logger = logging.getLogger(__name__)

class Predictor:
    """Main prediction engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.feature_engineer = FeatureEngineer(db)
        self.model_manager = ModelManager()
        self.min_confidence = 65.0  # Minimum confidence for signals
        self.min_value = 0.1  # Minimum value score
        
    def initialize_models(self, sport: str) -> bool:
        """Initialize ML models for a sport"""
        try:
            # Try to load existing models
            if self.model_manager.load_all_models(sport):
                logger.info(f"✅ Loaded existing models for {sport}")
                return True
            
            # Train new models if no existing ones
            logger.info(f"🔄 Training new models for {sport}...")
            success = self.train_models(sport)
            
            if success:
                logger.info(f"✅ Successfully trained models for {sport}")
            else:
                logger.warning(f"⚠️ Failed to train models for {sport}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error initializing models for {sport}: {e}")
            return False
    
    def train_models(self, sport: str) -> bool:
        """Train ML models for a sport"""
        try:
            # Get training data
            X, y = self._prepare_training_data(sport)
            
            if len(X) < 50:  # Minimum samples for training
                logger.warning(f"⚠️ Not enough training data for {sport}: {len(X)} samples")
                return False
            
            # Train all models
            results = self.model_manager.train_all_models(sport, X, y)
            
            # Log results
            for model_name, metrics in results.items():
                if 'error' not in metrics:
                    logger.info(f"✅ {model_name} for {sport}: accuracy={metrics.get('accuracy', 0):.3f}")
                else:
                    logger.error(f"❌ {model_name} for {sport}: {metrics['error']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error training models for {sport}: {e}")
            return False
    
    def predict_match(self, match_id: int) -> Dict[str, Any]:
        """Make prediction for a match"""
        try:
            from database.models import Match
            
            # Get match
            match = self.db.query(Match).filter(Match.id == match_id).first()
            if not match:
                return {'error': 'Match not found'}
            
            # Initialize models if needed
            if not self.model_manager.get_model(match.sport).is_trained:
                if not self.initialize_models(match.sport):
                    return self._fallback_prediction(match)
            
            # Extract features
            features = self.feature_engineer.extract_features(match_id)
            if not features:
                return self._fallback_prediction(match)
            
            # Make prediction
            prediction = self.model_manager.predict_ensemble(match.sport, features)
            
            # Add metadata
            prediction.update({
                'match_id': match_id,
                'sport': match.sport,
                'team1': match.team1.name if match.team1 else 'Unknown',
                'team2': match.team2.name if match.team2 else 'Unknown',
                'date': match.date.isoformat() if match.date else None,
                'features_count': len(features),
                'explanation': self._generate_explanation(features, prediction)
            })
            
            # Calculate value score
            prediction['value_score'] = self._calculate_value_score(prediction)
            
            return prediction
            
        except Exception as e:
            logger.error(f"❌ Error predicting match {match_id}: {e}")
            return {'error': str(e)}
    
    def generate_signals(self, sport: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Generate betting signals for upcoming matches"""
        try:
            from database.models import Match, Signal
            
            # Get upcoming matches
            upcoming_matches = self.db.query(Match).filter(
                Match.sport == sport,
                Match.is_upcoming == True,
                Match.date > datetime.now()
            ).order_by(Match.date).limit(limit * 2).all()  # Get more to filter
            
            signals = []
            
            for match in upcoming_matches:
                # Make prediction
                prediction = self.predict_match(match.id)
                
                if 'error' in prediction:
                    continue
                
                # Check if signal meets criteria
                if self._is_signal_worthy(prediction):
                    signal = self._create_signal(match, prediction)
                    signals.append(signal)
                    
                    # Save to database
                    db_signal = Signal(
                        match_id=match.id,
                        sport=sport,
                        prediction=prediction['prediction'],
                        probability=prediction['probabilities'][prediction['prediction']],
                        confidence=prediction['confidence'],
                        value_score=prediction['value_score'],
                        explanation=prediction['explanation'],
                        features_used=features,
                        model_version="ensemble_v1.0"
                    )
                    
                    self.db.add(db_signal)
                    
                    if len(signals) >= limit:
                        break
            
            # Commit signals
            self.db.commit()
            
            logger.info(f"🎯 Generated {len(signals)} signals for {sport}")
            return signals
            
        except Exception as e:
            logger.error(f"❌ Error generating signals for {sport}: {e}")
            return []
    
    def _prepare_training_data(self, sport: str) -> tuple:
        """Prepare training data from historical matches"""
        try:
            from database.models import Match
            
            # Get historical matches
            matches = self.db.query(Match).filter(
                Match.sport == sport,
                Match.result != 'upcoming',
                Match.result.isnot(None)
            ).all()
            
            if len(matches) < 50:
                return pd.DataFrame(), pd.Series()
            
            # Extract features and labels
            features_list = []
            labels = []
            
            for match in matches:
                # Extract features
                features = self.feature_engineer.extract_features(match.id)
                if features:
                    features_list.append(features)
                    labels.append(match.result)
            
            if not features_list:
                return pd.DataFrame(), pd.Series()
            
            # Convert to DataFrame
            X = pd.DataFrame(features_list)
            y = pd.Series(labels)
            
            # Remove any rows with NaN values
            mask = X.notna().all(axis=1)
            X = X[mask]
            y = y[mask]
            
            logger.info(f"📊 Prepared {len(X)} training samples for {sport}")
            return X, y
            
        except Exception as e:
            logger.error(f"❌ Error preparing training data for {sport}: {e}")
            return pd.DataFrame(), pd.Series()
    
    def _fallback_prediction(self, match) -> Dict[str, Any]:
        """Fallback prediction when models are not available"""
        try:
            # Simple rule-based prediction
            team1_rating = match.team1.rating if match.team1 else 1500
            team2_rating = match.team2.rating if match.team2 else 1500
            
            rating_diff = team1_rating - team2_rating
            prob1 = 1 / (1 + 10 ** (-rating_diff / 400))
            
            prediction = 'team1' if prob1 > 0.5 else 'team2'
            confidence = max(prob1, 1 - prob1) * 100
            
            return {
                'prediction': prediction,
                'probabilities': {
                    'team1': prob1,
                    'team2': 1 - prob1,
                    'draw': 0.0
                },
                'confidence': confidence,
                'method': 'rule_based_fallback',
                'explanation': f"Based on ELO rating difference: {rating_diff:+.0f}",
                'value_score': 0.0
            }
            
        except Exception as e:
            logger.error(f"❌ Error in fallback prediction: {e}")
            return {
                'prediction': 'team1',
                'probabilities': {'team1': 0.5, 'team2': 0.5, 'draw': 0.0},
                'confidence': 50.0,
                'method': 'random_fallback',
                'explanation': 'Random fallback due to error',
                'value_score': 0.0
            }
    
    def _generate_explanation(self, features: Dict[str, Any], prediction: Dict[str, Any]) -> str:
        """Generate human-readable explanation"""
        try:
            explanations = []
            
            # Rating difference
            if 'rating_difference' in features:
                diff = features['rating_difference']
                if abs(diff) > 50:
                    explanations.append(f"Rating advantage: {diff:+.0f}")
            
            # Recent form
            if 'recent_winrate_diff' in features:
                diff = features['recent_winrate_diff']
                if abs(diff) > 0.2:
                    explanations.append(f"Recent form advantage: {diff:+.1%}")
            
            # H2H record
            if 'h2h_team1_winrate' in features:
                h2h_wr = features['h2h_team1_winrate']
                if abs(h2h_wr - 0.5) > 0.1:
                    explanations.append(f"H2H record: {h2h_wr:.1%}")
            
            # Home advantage
            if features.get('team1_is_home', 0):
                explanations.append("Home advantage")
            
            # Map/arena specific
            if 'map_winrate_diff' in features:
                diff = features['map_winrate_diff']
                if abs(diff) > 0.1:
                    explanations.append(f"Map performance: {diff:+.1%}")
            
            if not explanations:
                explanations.append("Based on overall team strength")
            
            return "Signal based on: " + ", ".join(explanations)
            
        except Exception as e:
            logger.error(f"❌ Error generating explanation: {e}")
            return "Based on team analysis"
    
    def _calculate_value_score(self, prediction: Dict[str, Any]) -> float:
        """Calculate value score (probability vs implied odds)"""
        try:
            # Simplified value calculation
            # In real implementation, this would compare with actual betting odds
            probability = prediction['probabilities'][prediction['prediction']]
            confidence = prediction['confidence']
            
            # Value score based on confidence and probability
            value_score = (confidence / 100) * probability
            
            # Add some randomness for demonstration
            import random
            value_score += random.uniform(-0.05, 0.05)
            
            return max(0.0, min(1.0, value_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating value score: {e}")
            return 0.0
    
    def _is_signal_worthy(self, prediction: Dict[str, Any]) -> bool:
        """Check if prediction meets signal criteria"""
        try:
            # Check confidence
            if prediction['confidence'] < self.min_confidence:
                return False
            
            # Check value score
            if prediction['value_score'] < self.min_value:
                return False
            
            # Additional checks can be added here
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking signal worthiness: {e}")
            return False
    
    def _create_signal(self, match, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Create signal object"""
        return {
            'match_id': match.id,
            'team1': match.team1.name if match.team1 else 'Unknown',
            'team2': match.team2.name if match.team2 else 'Unknown',
            'sport': match.sport,
            'date': match.date.isoformat() if match.date else None,
            'prediction': prediction['prediction'],
            'probability': prediction['probabilities'][prediction['prediction']],
            'confidence': prediction['confidence'],
            'value_score': prediction['value_score'],
            'explanation': prediction['explanation'],
            'created_at': datetime.now().isoformat()
        }
