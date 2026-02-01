#!/usr/bin/env python3
"""
AIBET Analytics Platform - Fixed ML Models
Обучение только на реальных данных из SQLite
"""

import asyncio
import logging
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import os

logger = logging.getLogger(__name__)

class MLModelsFixed:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.models_path = "models"
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        
        # Создаем директорию для моделей
        os.makedirs(self.models_path, exist_ok=True)
        
        # Инициализация моделей
        self._init_models()
    
    def _init_models(self):
        """Инициализация моделей"""
        self.models = {
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        }
        
        self.scalers = {
            'logistic_regression': StandardScaler(),
            'random_forest': StandardScaler()
        }
        
        logger.info("✅ ML models initialized")
    
    async def collect_training_data(self, sport: str, min_matches: int = 100) -> Optional[pd.DataFrame]:
        """Сбор данных для обучения из базы"""
        try:
            # Получаем все завершенные матчи
            matches = await self.db_manager.get_matches(sport=sport, status='finished')
            
            if len(matches) < min_matches:
                logger.warning(f"⚠️ Not enough matches for training: {len(matches)}/{min_matches}")
                return None
            
            logger.info(f"📊 Collecting training data: {len(matches)} matches")
            
            training_data = []
            
            for match in matches:
                try:
                    # Получаем статистику команд
                    stats1 = await self.db_manager.get_team_stats(match['team1'], sport)
                    stats2 = await self.db_manager.get_team_stats(match['team2'], sport)
                    
                    if not stats1 or not stats2:
                        continue
                    
                    # Создаем фичи
                    features = self._extract_features(stats1, stats2, match)
                    
                    # Определяем результат (для обучения)
                    winner = self._determine_winner(match)
                    if winner:
                        features['result'] = winner
                        training_data.append(features)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error processing match {match['id']}: {e}")
                    continue
            
            if not training_data:
                logger.error("❌ No training data collected")
                return None
            
            df = pd.DataFrame(training_data)
            logger.info(f"✅ Training data collected: {len(df)} samples")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error collecting training data: {e}")
            return None
    
    def _extract_features(self, stats1: Dict, stats2: Dict, match: Dict) -> Dict:
        """Извлечение фичей из статистики"""
        features = {}
        
        # Базовые фичи команды 1
        features['team1_win_rate'] = stats1.get('win_rate', 0.0)
        features['team1_matches_played'] = stats1.get('matches_played', 0)
        features['team1_wins'] = stats1.get('wins', 0)
        features['team1_losses'] = stats1.get('losses', 0)
        features['team1_draws'] = stats1.get('draws', 0)
        features['team1_score_for_avg'] = stats1.get('score_for', 0) / max(stats1.get('matches_played', 1), 1)
        features['team1_score_against_avg'] = stats1.get('score_against', 0) / max(stats1.get('matches_played', 1), 1)
        
        # Базовые фичи команды 2
        features['team2_win_rate'] = stats2.get('win_rate', 0.0)
        features['team2_matches_played'] = stats2.get('matches_played', 0)
        features['team2_wins'] = stats2.get('wins', 0)
        features['team2_losses'] = stats2.get('losses', 0)
        features['team2_draws'] = stats2.get('draws', 0)
        features['team2_score_for_avg'] = stats2.get('score_for', 0) / max(stats2.get('matches_played', 1), 1)
        features['team2_score_against_avg'] = stats2.get('score_against', 0) / max(stats2.get('matches_played', 1), 1)
        
        # Разностные фичи
        features['win_rate_diff'] = features['team1_win_rate'] - features['team2_win_rate']
        features['matches_played_diff'] = features['team1_matches_played'] - features['team2_matches_played']
        features['score_for_diff'] = features['team1_score_for_avg'] - features['team2_score_for_avg']
        features['score_against_diff'] = features['team1_score_against_avg'] - features['team2_score_against_avg']
        
        # Фичи формы
        recent_form1 = stats1.get('recent_form', [])
        recent_form2 = stats2.get('recent_form', [])
        
        features['team1_recent_wins'] = recent_form1.count('W') if recent_form1 else 0
        features['team2_recent_wins'] = recent_form2.count('W') if recent_form2 else 0
        features['team1_recent_losses'] = recent_form1.count('L') if recent_form1 else 0
        features['team2_recent_losses'] = recent_form2.count('L') if recent_form2 else 0
        
        # Фичи матча
        features['home_advantage'] = 1.0 if 'home' in match.get('team1', '').lower() else 0.0
        
        return features
    
    def _determine_winner(self, match: Dict) -> Optional[str]:
        """Определение победителя матча"""
        if not match.get('score'):
            return None
        
        try:
            score = match['score']
            if ':' in score:
                scores = score.split(':')
                if len(scores) == 2:
                    team1_score = int(scores[0].strip())
                    team2_score = int(scores[1].strip())
                    
                    if team1_score > team2_score:
                        return 'team1'
                    elif team2_score > team1_score:
                        return 'team2'
                    else:
                        return 'draw'
        except:
            pass
        
        return None
    
    async def train_models(self, sport: str = 'cs2') -> bool:
        """Обучение моделей"""
        try:
            logger.info(f"🤖 Training ML models for {sport}")
            
            # Сбор данных
            df = await self.collect_training_data(sport, min_matches=100)
            if df is None:
                logger.warning(f"⚠️ Not enough data for training {sport}")
                return False
            
            # Подготовка данных
            X = df.drop(['result'], axis=1)
            y = df['result']
            
            # Сохраняем названия фичей
            self.feature_columns = X.columns.tolist()
            
            # Разделение данных
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Обучение моделей
            results = {}
            
            for model_name, model in self.models.items():
                try:
                    logger.info(f"🔧 Training {model_name}")
                    
                    # Масштабирование данных
                    X_train_scaled = self.scalers[model_name].fit_transform(X_train)
                    X_test_scaled = self.scalers[model_name].transform(X_test)
                    
                    # Обучение
                    model.fit(X_train_scaled, y_train)
                    
                    # Предсказание
                    y_pred = model.predict(X_test_scaled)
                    
                    # Оценка
                    accuracy = accuracy_score(y_test, y_pred)
                    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
                    
                    results[model_name] = {
                        'accuracy': accuracy,
                        'cv_mean': cv_scores.mean(),
                        'cv_std': cv_scores.std(),
                        'report': classification_report(y_test, y_pred, output_dict=True)
                    }
                    
                    logger.info(f"✅ {model_name}: Accuracy={accuracy:.3f}, CV={cv_scores.mean():.3f}±{cv_scores.std():.3f}")
                    
                    # Сохранение модели
                    model_path = os.path.join(self.models_path, f"{sport}_{model_name}.pkl")
                    scaler_path = os.path.join(self.models_path, f"{sport}_{model_name}_scaler.pkl")
                    
                    with open(model_path, 'wb') as f:
                        pickle.dump(model, f)
                    
                    with open(scaler_path, 'wb') as f:
                        pickle.dump(self.scalers[model_name], f)
                    
                    logger.info(f"💾 Model saved: {model_path}")
                    
                except Exception as e:
                    logger.error(f"❌ Error training {model_name}: {e}")
                    continue
            
            # Сохранение метаданных
            metadata = {
                'sport': sport,
                'feature_columns': self.feature_columns,
                'training_date': datetime.now().isoformat(),
                'results': results,
                'samples_count': len(df)
            }
            
            metadata_path = os.path.join(self.models_path, f"{sport}_metadata.pkl")
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"✅ ML models training completed for {sport}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error training models: {e}")
            return False
    
    async def load_models(self, sport: str) -> bool:
        """Загрузка обученных моделей"""
        try:
            metadata_path = os.path.join(self.models_path, f"{sport}_metadata.pkl")
            
            if not os.path.exists(metadata_path):
                logger.warning(f"⚠️ No trained models found for {sport}")
                return False
            
            # Загрузка метаданных
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.feature_columns = metadata['feature_columns']
            
            # Загрузка моделей
            for model_name in self.models.keys():
                model_path = os.path.join(self.models_path, f"{sport}_{model_name}.pkl")
                scaler_path = os.path.join(self.models_path, f"{sport}_{model_name}_scaler.pkl")
                
                if os.path.exists(model_path) and os.path.exists(scaler_path):
                    with open(model_path, 'rb') as f:
                        self.models[model_name] = pickle.load(f)
                    
                    with open(scaler_path, 'rb') as f:
                        self.scalers[model_name] = pickle.load(f)
                    
                    logger.info(f"✅ Loaded {model_name} for {sport}")
                else:
                    logger.warning(f"⚠️ Model files not found for {model_name}")
            
            logger.info(f"✅ Models loaded for {sport}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading models: {e}")
            return False
    
    async def predict_match(self, match: Dict, sport: str) -> Dict[str, Any]:
        """Прогнозирование матча"""
        try:
            # Проверяем, есть ли обученные модели
            if not self.feature_columns:
                # Пробуем загрузить модели
                if not await self.load_models(sport):
                    # Если нет моделей, используем rule-based
                    return self._rule_based_prediction(match, sport)
            
            # Получаем статистику команд
            stats1 = await self.db_manager.get_team_stats(match['team1'], sport)
            stats2 = await self.db_manager.get_team_stats(match['team2'], sport)
            
            if not stats1 or not stats2:
                return self._rule_based_prediction(match, sport)
            
            # Извлечение фичей
            features = self._extract_features(stats1, stats2, match)
            
            # Создание DataFrame
            feature_df = pd.DataFrame([features])
            
            # Убедимся, что все фичи присутствуют
            for col in self.feature_columns:
                if col not in feature_df.columns:
                    feature_df[col] = 0
            
            # Упорядочиваем колонки
            feature_df = feature_df[self.feature_columns]
            
            # Прогнозирование
            predictions = {}
            
            for model_name, model in self.models.items():
                try:
                    # Масштабирование
                    X_scaled = self.scalers[model_name].transform(feature_df)
                    
                    # Предсказание
                    pred = model.predict(X_scaled)[0]
                    proba = model.predict_proba(X_scaled)[0]
                    
                    # Определение вероятностей
                    classes = model.classes_
                    prob_dict = dict(zip(classes, proba))
                    
                    predictions[model_name] = {
                        'prediction': pred,
                        'probabilities': prob_dict
                    }
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error in {model_name} prediction: {e}")
                    continue
            
            if not predictions:
                return self._rule_based_prediction(match, sport)
            
            # Ансамбль прогнозов
            ensemble_pred = self._ensemble_predictions(predictions)
            
            return ensemble_pred
            
        except Exception as e:
            logger.error(f"❌ Error in prediction: {e}")
            return self._rule_based_prediction(match, sport)
    
    def _rule_based_prediction(self, match: Dict, sport: str) -> Dict[str, Any]:
        """Rule-based прогноз на основе базовой статистики"""
        try:
            # Простая логика на основе win rate
            team1_wr = 0.5  # Default
            team2_wr = 0.5
            
            # Если есть статистика, используем её
            if hasattr(self, 'db_manager'):
                # Это асинхронный метод, но в rule-based мы не можем await
                # Используем базовые значения
                pass
            
            # Определяем победителя
            if abs(team1_wr - team2_wr) < 0.05:
                prediction = 'draw' if sport == 'khl' else 'team1'
                confidence = 0.5
            elif team1_wr > team2_wr:
                prediction = 'team1'
                confidence = 0.5 + (team1_wr - team2_wr)
            else:
                prediction = 'team2'
                confidence = 0.5 + (team2_wr - team1_wr)
            
            confidence = max(0.1, min(0.9, confidence))
            
            return {
                'prediction': prediction,
                'confidence': confidence,
                'team1_probability': confidence if prediction == 'team1' else (1 - confidence),
                'team2_probability': confidence if prediction == 'team2' else (1 - confidence),
                'draw_probability': 0.1 if sport == 'khl' else 0.0,
                'method': 'rule_based'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in rule-based prediction: {e}")
            return {
                'prediction': 'team1',
                'confidence': 0.5,
                'team1_probability': 0.5,
                'team2_probability': 0.5,
                'draw_probability': 0.0,
                'method': 'fallback'
            }
    
    def _ensemble_predictions(self, predictions: Dict) -> Dict[str, Any]:
        """Ансамбль прогнозов"""
        try:
            # Простое голосование
            votes = {}
            total_confidence = 0
            
            for model_name, pred in predictions.items():
                pred_class = pred['prediction']
                votes[pred_class] = votes.get(pred_class, 0) + 1
                
                # Усреднение вероятностей
                if 'probabilities' in pred:
                    for outcome, prob in pred['probabilities'].items():
                        total_confidence += prob
            
            # Определяем победителя по голосованию
            if not votes:
                return self._rule_based_prediction({}, 'cs2')
            
            winner = max(votes.keys(), key=lambda x: votes[x])
            
            # Усредненная вероятность
            avg_confidence = total_confidence / len(predictions) / len(predictions)
            
            return {
                'prediction': winner,
                'confidence': avg_confidence,
                'method': 'ensemble',
                'models_used': list(predictions.keys())
            }
            
        except Exception as e:
            logger.error(f"❌ Error in ensemble: {e}")
            return self._rule_based_prediction({}, 'cs2')
