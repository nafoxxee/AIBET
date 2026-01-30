import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
import joblib
import os

logger = logging.getLogger(__name__)


class CS2MLTrainer:
    """Machine learning trainer for CS2 match predictions"""
    
    def __init__(self, model_path: str = "cs2/ml/models/"):
        self.model_path = model_path
        os.makedirs(model_path, exist_ok=True)
        
        self.classifier = None
        self.regressor = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.target_column = 'result'
        
        # Model types
        self.classifier_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.regressor_model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=6,
            random_state=42
        )
    
    def prepare_dataset(self, matches: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare dataset for training"""
        try:
            data_rows = []
            
            for match in matches:
                row = self._extract_features(match)
                if row:
                    data_rows.append(row)
            
            if not data_rows:
                logger.warning("No valid data rows extracted")
                return pd.DataFrame()
            
            df = pd.DataFrame(data_rows)
            logger.info(f"Prepared dataset with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error preparing dataset: {e}")
            return pd.DataFrame()
    
    def _extract_features(self, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract features from match data"""
        try:
            features = {}
            
            # Basic match info
            features['match_id'] = match.get('match_id', '')
            features['tier'] = self._encode_tier(match.get('tier', 'C'))
            
            # Odds features
            odds_data = match.get('odds', {})
            avg_odds = odds_data.get('average_odds', {})
            features['team1_odds'] = avg_odds.get('team1', 0)
            features['team2_odds'] = avg_odds.get('team2', 0)
            features['odds_ratio'] = features['team1_odds'] / (features['team2_odds'] + 0.001)
            
            # Public bias features
            public_money = odds_data.get('public_money', {})
            features['team1_public_pct'] = public_money.get('team1_percentage', 50)
            features['team2_public_pct'] = public_money.get('team2_percentage', 50)
            features['public_bias_strength'] = abs(features['team1_public_pct'] - 50) / 50
            
            # Market analysis features
            analysis = odds_data.get('analysis', {})
            features['is_heavy_favorite'] = 1 if analysis.get('is_heavy_favorite', False) else 0
            features['public_bias_detected'] = 1 if analysis.get('public_bias_detected', False) else 0
            features['market_efficiency'] = analysis.get('market_efficiency', 0.5)
            
            # Odds movement features
            movement_history = odds_data.get('movement_history', [])
            if len(movement_history) >= 2:
                recent = movement_history[-1]
                previous = movement_history[-2]
                features['odds_movement'] = recent.get('team1_odds', 0) - previous.get('team1_odds', 0)
                features['odds_volatility'] = abs(features['odds_movement'])
            else:
                features['odds_movement'] = 0
                features['odds_volatility'] = 0
            
            # Lineup features
            match_info = match.get('match_info', {})
            lineups = match_info.get('lineups', {})
            features['team1_players'] = len(lineups.get('team1', []))
            features['team2_players'] = len(lineups.get('team2', []))
            
            stand_ins = match_info.get('stand_ins', {})
            features['team1_stand_in'] = 1 if stand_ins.get('team1', False) else 0
            features['team2_stand_in'] = 1 if stand_ins.get('team2', False) else 0
            
            # Tournament features
            features['tournament_importance'] = self._calculate_tournament_importance(match.get('tournament', ''))
            
            # Time features
            match_time = match.get('time', '')
            features['hour_of_day'] = self._extract_hour(match_time)
            features['is_weekend'] = 1 if self._is_weekend(match.get('parsed_at', '')) else 0
            
            # Target variable (result)
            result = match.get('result', {})
            if result:
                features['result'] = 1 if result.get('winner') == 'team1' else 0
                features['score_diff'] = result.get('score_diff', 0)
            else:
                # For prediction (no result), we'll handle this separately
                features['result'] = -1  # Unknown
                features['score_diff'] = 0
            
            return features
            
        except Exception as e:
            logger.warning(f"Error extracting features from match: {e}")
            return None
    
    def _encode_tier(self, tier: str) -> int:
        """Encode tournament tier"""
        tier_mapping = {'S': 4, 'A': 3, 'B': 2, 'C': 1}
        return tier_mapping.get(tier.upper(), 1)
    
    def _calculate_tournament_importance(self, tournament: str) -> float:
        """Calculate tournament importance score"""
        tournament_lower = tournament.lower()
        
        if any(keyword in tournament_lower for keyword in ['major', 'world final']):
            return 1.0
        elif any(keyword in tournament_lower for keyword in ['iem', 'blast', 'esl pro league']):
            return 0.8
        elif any(keyword in tournament_lower for keyword in ['challenger', 'pinnacle']):
            return 0.6
        else:
            return 0.4
    
    def _extract_hour(self, time_str: str) -> int:
        """Extract hour from time string"""
        try:
            if ':' in time_str:
                hour = int(time_str.split(':')[0])
                return hour
        except:
            pass
        return 12  # Default to noon
    
    def _is_weekend(self, date_str: str) -> bool:
        """Check if date is weekend"""
        try:
            if date_str:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return date.weekday() >= 5
        except:
            pass
        return False
    
    def train_models(self, dataset_path: str = "cs2/ml/dataset.csv") -> bool:
        """Train ML models"""
        try:
            # Load or create dataset
            if os.path.exists(dataset_path):
                df = pd.read_csv(dataset_path)
            else:
                logger.warning(f"Dataset not found at {dataset_path}")
                return False
            
            if len(df) < 50:
                logger.warning("Insufficient data for training")
                return False
            
            # Prepare features and targets
            df_train = df[df['result'] != -1].copy()  # Only use matches with results
            
            if len(df_train) < 30:
                logger.warning("Insufficient training data with results")
                return False
            
            # Feature columns (exclude non-feature columns)
            exclude_cols = ['match_id', 'result', 'score_diff']
            self.feature_columns = [col for col in df_train.columns if col not in exclude_cols]
            
            X = df_train[self.feature_columns].fillna(0)
            y_classification = df_train['result']
            y_regression = df_train['score_diff']
            
            # Split data
            X_train, X_test, y_cls_train, y_cls_test = train_test_split(
                X, y_classification, test_size=0.2, random_state=42
            )
            _, _, y_reg_train, y_reg_test = train_test_split(
                X, y_regression, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train classification model
            self.classifier_model.fit(X_train_scaled, y_cls_train)
            cls_pred = self.classifier_model.predict(X_test_scaled)
            cls_accuracy = accuracy_score(y_cls_test, cls_pred)
            
            # Train regression model
            self.regressor_model.fit(X_train_scaled, y_reg_train)
            reg_pred = self.regressor_model.predict(X_test_scaled)
            reg_rmse = np.sqrt(mean_squared_error(y_reg_test, reg_pred))
            reg_r2 = r2_score(y_reg_test, reg_pred)
            
            logger.info(f"Classification accuracy: {cls_accuracy:.3f}")
            logger.info(f"Regression RMSE: {reg_rmse:.3f}, R2: {reg_r2:.3f}")
            
            # Save models
            self._save_models()
            
            return True
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return False
    
    def _save_models(self):
        """Save trained models"""
        try:
            joblib.dump(self.classifier_model, os.path.join(self.model_path, 'classifier.pkl'))
            joblib.dump(self.regressor_model, os.path.join(self.model_path, 'regressor.pkl'))
            joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler.pkl'))
            joblib.dump(self.feature_columns, os.path.join(self.model_path, 'feature_columns.pkl'))
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self) -> bool:
        """Load trained models"""
        try:
            self.classifier_model = joblib.load(os.path.join(self.model_path, 'classifier.pkl'))
            self.regressor_model = joblib.load(os.path.join(self.model_path, 'regressor.pkl'))
            self.scaler = joblib.load(os.path.join(self.model_path, 'scaler.pkl'))
            self.feature_columns = joblib.load(os.path.join(self.model_path, 'feature_columns.pkl'))
            
            logger.info("Models loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def evaluate_models(self, test_data: pd.DataFrame) -> Dict[str, Any]:
        """Evaluate model performance"""
        try:
            if not self.classifier_model or not self.regressor_model:
                return {'error': 'Models not trained'}
            
            # Prepare test data
            test_data_filtered = test_data[test_data['result'] != -1].copy()
            
            if len(test_data_filtered) == 0:
                return {'error': 'No test data with results'}
            
            X_test = test_data_filtered[self.feature_columns].fillna(0)
            X_test_scaled = self.scaler.transform(X_test)
            
            y_true_cls = test_data_filtered['result']
            y_true_reg = test_data_filtered['score_diff']
            
            # Classification evaluation
            y_pred_cls = self.classifier_model.predict(X_test_scaled)
            y_pred_cls_proba = self.classifier_model.predict_proba(X_test_scaled)
            
            cls_report = classification_report(y_true_cls, y_pred_cls, output_dict=True)
            
            # Regression evaluation
            y_pred_reg = self.regressor_model.predict(X_test_scaled)
            reg_rmse = np.sqrt(mean_squared_error(y_true_reg, y_pred_reg))
            reg_r2 = r2_score(y_true_reg, y_pred_reg)
            
            evaluation = {
                'classification': {
                    'accuracy': accuracy_score(y_true_cls, y_pred_cls),
                    'report': cls_report,
                    'sample_predictions': y_pred_cls_proba[:5].tolist()
                },
                'regression': {
                    'rmse': reg_rmse,
                    'r2_score': reg_r2,
                    'sample_predictions': list(zip(y_true_reg[:5], y_pred_reg[:5]))
                },
                'feature_importance': dict(zip(
                    self.feature_columns,
                    self.classifier_model.feature_importances_
                ))
            }
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating models: {e}")
            return {'error': str(e)}


async def train_cs2_models():
    """Train CS2 ML models"""
    trainer = CS2MLTrainer()
    
    try:
        # Get historical match data
        from storage.database import get_historical_cs2_matches
        historical_matches = await get_historical_cs2_matches()
        
        if len(historical_matches) < 30:
            logger.warning("Insufficient historical data for training")
            return False
        
        # Prepare dataset
        dataset = trainer.prepare_dataset(historical_matches)
        
        if len(dataset) == 0:
            logger.warning("Failed to prepare dataset")
            return False
        
        # Save dataset
        dataset.to_csv("cs2/ml/dataset.csv", index=False)
        
        # Train models
        success = trainer.train_models()
        
        if success:
            # Evaluate models
            evaluation = trainer.evaluate_models(dataset)
            logger.info(f"Model evaluation: {evaluation}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in CS2 model training: {e}")
        return False


async def cs2_ml_training_task():
    """CS2 ML training task for scheduler"""
    logger.info("Starting CS2 ML model training")
    
    try:
        success = await train_cs2_models()
        
        if success:
            logger.info("CS2 ML models trained successfully")
        else:
            logger.warning("CS2 ML model training failed")
        
    except Exception as e:
        logger.error(f"CS2 ML training task failed: {e}")


def setup_cs2_ml_tasks(scheduler):
    """Setup CS2 ML training tasks"""
    scheduler.add_task('cs2_ml_training', cs2_ml_training_task, 86400)  # Every 24 hours
    logger.info("CS2 ML training tasks setup complete")
