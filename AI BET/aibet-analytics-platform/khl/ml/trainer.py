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


class KHLMLTrainer:
    """Machine learning trainer for KHL match predictions"""
    
    def __init__(self, model_path: str = "khl/ml/models/"):
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
            logger.info(f"Prepared KHL dataset with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error preparing KHL dataset: {e}")
            return pd.DataFrame()
    
    def _extract_features(self, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract features from match data"""
        try:
            features = {}
            
            # Basic match info
            features['match_id'] = match.get('match_id', '')
            features['home_advantage'] = match.get('home_advantage', 0.08)
            
            # Odds features
            odds_data = match.get('odds', {})
            avg_odds = odds_data.get('average_odds', {})
            features['team1_odds'] = avg_odds.get('team1', 0)
            features['team2_odds'] = avg_odds.get('team2', 0)
            features['draw_odds'] = avg_odds.get('draw', 0)
            features['odds_ratio'] = features['team1_odds'] / (features['team2_odds'] + 0.001)
            
            # Handicap features
            handicap_odds = odds_data.get('handicap_odds', {})
            features['handicap_line'] = handicap_odds.get('line', -1.5)
            features['team1_handicap_odds'] = handicap_odds.get('team1_odds', 0)
            features['team2_handicap_odds'] = handicap_odds.get('team2_odds', 0)
            
            # Total goals features
            total_odds = odds_data.get('total_odds', {})
            features['total_line'] = total_odds.get('line', 5.5)
            features['over_odds'] = total_odds.get('over_odds', 0)
            features['under_odds'] = total_odds.get('under_odds', 0)
            
            # Period odds features
            period_odds = odds_data.get('period_odds', {})
            if period_odds:
                features['period1_team1_odds'] = period_odds.get('period1', {}).get('team1', 0)
                features['period1_team2_odds'] = period_odds.get('period1', {}).get('team2', 0)
                features['period2_team1_odds'] = period_odds.get('period2', {}).get('team1', 0)
                features['period2_team2_odds'] = period_odds.get('period2', {}).get('team2', 0)
                features['period3_team1_odds'] = period_odds.get('period3', {}).get('team1', 0)
                features['period3_team2_odds'] = period_odds.get('period3', {}).get('team2', 0)
            else:
                # Default values if no period odds
                features['period1_team1_odds'] = 2.5
                features['period1_team2_odds'] = 2.5
                features['period2_team1_odds'] = 2.3
                features['period2_team2_odds'] = 2.3
                features['period3_team1_odds'] = 2.1
                features['period3_team2_odds'] = 2.1
            
            # Market analysis features
            analysis = odds_data.get('analysis', {})
            features['is_close_match'] = 1 if analysis.get('is_close_match', False) else 0
            features['draw_probability'] = analysis.get('draw_probability', 0)
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
            
            # Team statistics features
            match_details = match.get('match_details', {})
            team1_stats = match_details.get('team1_stats', {})
            team2_stats = match_details.get('team2_stats', {})
            
            # Team 1 stats
            features['team1_recent_form'] = self._encode_recent_form(team1_stats.get('recent_form', []))
            features['team1_home_wins'] = team1_stats.get('home_record', {}).get('wins', 0)
            features['team1_goals_for'] = team1_stats.get('goals_for', 0)
            features['team1_goals_against'] = team1_stats.get('goals_against', 0)
            features['team1_power_play_pct'] = team1_stats.get('power_play_percentage', 0)
            features['team1_penalty_kill_pct'] = team1_stats.get('penalty_kill_percentage', 0)
            
            # Team 2 stats
            features['team2_recent_form'] = self._encode_recent_form(team2_stats.get('recent_form', []))
            features['team2_away_wins'] = team2_stats.get('away_record', {}).get('wins', 0)
            features['team2_goals_for'] = team2_stats.get('goals_for', 0)
            features['team2_goals_against'] = team2_stats.get('goals_against', 0)
            features['team2_power_play_pct'] = team2_stats.get('power_play_percentage', 0)
            features['team2_penalty_kill_pct'] = team2_stats.get('penalty_kill_percentage', 0)
            
            # Head to head features
            head_to_head = match_details.get('head_to_head', {})
            features['total_meetings'] = head_to_head.get('meetings', 0)
            features['team1_h2h_wins'] = head_to_head.get('team1_wins', 0)
            features['team2_h2h_wins'] = head_to_head.get('team2_wins', 0)
            features['h2h_draws'] = head_to_head.get('ot_losses', 0)
            
            # Match importance
            features['match_importance'] = match_details.get('match_importance', 0.6)
            
            # Time features
            match_time = match.get('time', '')
            features['hour_of_day'] = self._extract_hour(match_time)
            features['is_weekend'] = 1 if self._is_weekend(match.get('parsed_at', '')) else 0
            
            # Target variable (result)
            result = match.get('result', {})
            if result:
                if result.get('winner') == 'team1':
                    features['result'] = 1
                elif result.get('winner') == 'team2':
                    features['result'] = 2
                else:  # Draw
                    features['result'] = 0
                features['total_goals'] = result.get('total_goals', 0)
                features['goal_difference'] = result.get('goal_difference', 0)
            else:
                # For prediction (no result), we'll handle this separately
                features['result'] = -1  # Unknown
                features['total_goals'] = 0
                features['goal_difference'] = 0
            
            return features
            
        except Exception as e:
            logger.warning(f"Error extracting features from KHL match: {e}")
            return None
    
    def _encode_recent_form(self, form_list: List[str]) -> float:
        """Encode recent form into numerical value"""
        try:
            if not form_list:
                return 0.5
            
            points = {'W': 3, 'D': 1, 'L': 0}
            total_points = sum(points.get(result.upper(), 0) for result in form_list)
            max_points = len(form_list) * 3
            
            return total_points / max_points if max_points > 0 else 0.5
            
        except Exception as e:
            logger.warning(f"Error encoding recent form: {e}")
            return 0.5
    
    def _extract_hour(self, time_str: str) -> int:
        """Extract hour from time string"""
        try:
            if ':' in time_str:
                hour = int(time_str.split(':')[0])
                return hour
        except:
            pass
        return 19  # Default to evening game time
    
    def _is_weekend(self, date_str: str) -> bool:
        """Check if date is weekend"""
        try:
            if date_str:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return date.weekday() >= 5
        except:
            pass
        return False
    
    def train_models(self, dataset_path: str = "khl/ml/dataset.csv") -> bool:
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
            exclude_cols = ['match_id', 'result', 'total_goals', 'goal_difference']
            self.feature_columns = [col for col in df_train.columns if col not in exclude_cols]
            
            X = df_train[self.feature_columns].fillna(0)
            y_classification = df_train['result']
            y_regression = df_train['total_goals']
            
            # Split data
            X_train, X_test, y_cls_train, y_cls_test = train_test_split(
                X, y_classification, test_size=0.2, random_state=42, stratify=y_classification
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
            
            logger.info(f"KHL Classification accuracy: {cls_accuracy:.3f}")
            logger.info(f"KHL Regression RMSE: {reg_rmse:.3f}, R2: {reg_r2:.3f}")
            
            # Save models
            self._save_models()
            
            return True
            
        except Exception as e:
            logger.error(f"Error training KHL models: {e}")
            return False
    
    def _save_models(self):
        """Save trained models"""
        try:
            joblib.dump(self.classifier_model, os.path.join(self.model_path, 'classifier.pkl'))
            joblib.dump(self.regressor_model, os.path.join(self.model_path, 'regressor.pkl'))
            joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler.pkl'))
            joblib.dump(self.feature_columns, os.path.join(self.model_path, 'feature_columns.pkl'))
            
            logger.info("KHL models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving KHL models: {e}")
    
    def load_models(self) -> bool:
        """Load trained models"""
        try:
            self.classifier_model = joblib.load(os.path.join(self.model_path, 'classifier.pkl'))
            self.regressor_model = joblib.load(os.path.join(self.model_path, 'regressor.pkl'))
            self.scaler = joblib.load(os.path.join(self.model_path, 'scaler.pkl'))
            self.feature_columns = joblib.load(os.path.join(self.model_path, 'feature_columns.pkl'))
            
            logger.info("KHL models loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading KHL models: {e}")
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
            y_true_reg = test_data_filtered['total_goals']
            
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
            logger.error(f"Error evaluating KHL models: {e}")
            return {'error': str(e)}


async def train_khl_models():
    """Train KHL ML models"""
    trainer = KHLMLTrainer()
    
    try:
        # Get historical match data
        from storage.database import get_historical_khl_matches
        historical_matches = await get_historical_khl_matches()
        
        if len(historical_matches) < 30:
            logger.warning("Insufficient historical KHL data for training")
            return False
        
        # Prepare dataset
        dataset = trainer.prepare_dataset(historical_matches)
        
        if len(dataset) == 0:
            logger.warning("Failed to prepare KHL dataset")
            return False
        
        # Save dataset
        dataset.to_csv("khl/ml/dataset.csv", index=False)
        
        # Train models
        success = trainer.train_models()
        
        if success:
            # Evaluate models
            evaluation = trainer.evaluate_models(dataset)
            logger.info(f"KHL model evaluation: {evaluation}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in KHL model training: {e}")
        return False


async def khl_ml_training_task():
    """KHL ML training task for scheduler"""
    logger.info("Starting KHL ML model training")
    
    try:
        success = await train_khl_models()
        
        if success:
            logger.info("KHL ML models trained successfully")
        else:
            logger.warning("KHL ML model training failed")
        
    except Exception as e:
        logger.error(f"KHL ML training task failed: {e}")


def setup_khl_ml_tasks(scheduler):
    """Setup KHL ML training tasks"""
    scheduler.add_task('khl_ml_training', khl_ml_training_task, 86400)  # Every 24 hours
    logger.info("KHL ML training tasks setup complete")
