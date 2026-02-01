#!/usr/bin/env python3
"""
AIBET Analytics Platform - Pre-Match ML Models
ML модели для pre-match анализа на основе исторических данных
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
import random

logger = logging.getLogger(__name__)

class PreMatchMLModels:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.models_path = "models_pre_match"
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
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42, max_depth=8)
        }
        
        self.scalers = {
            'logistic_regression': StandardScaler(),
            'random_forest': StandardScaler()
        }
        
        logger.info("✅ Pre-Match ML models initialized")
    
    async def collect_training_data(self, sport: str, min_matches: int = 50) -> Optional[pd.DataFrame]:
        """Сбор исторических данных для обучения"""
        try:
            # Получаем исторические матчи
            matches = await self.db_manager.get_historical_matches(sport=sport, limit=500)
            
            if len(matches) < min_matches:
                logger.warning(f"⚠️ Not enough historical matches for training: {len(matches)}/{min_matches}")
                return None
            
            logger.info(f"📊 Collecting historical training data: {len(matches)} matches")
            
            training_data = []
            
            for match in matches:
                try:
                    # Получаем статистику команд
                    stats1 = await self.db_manager.get_team_stats(match['team1'], sport)
                    stats2 = await self.db_manager.get_team_stats(match['team2'], sport)
                    
                    if not stats1 or not stats2:
                        # Создаем базовую статистику если нет
                        stats1 = self._create_basic_stats(match['team1'], sport)
                        stats2 = self._create_basic_stats(match['team2'], sport)
                    
                    # Создаем фичи
                    features = self._extract_pre_match_features(stats1, stats2, match)
                    
                    # Определяем результат
                    result = match.get('result', 'unknown')
                    if result in ['team1', 'team2', 'draw']:
                        features['result'] = result
                        training_data.append(features)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error processing historical match {match['id']}: {e}")
                    continue
            
            if not training_data:
                logger.error("❌ No training data collected")
                return None
            
            df = pd.DataFrame(training_data)
            logger.info(f"✅ Historical training data collected: {len(df)} samples")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error collecting historical training data: {e}")
            return None
    
    def _create_basic_stats(self, team_name: str, sport: str) -> Dict:
        """Создать базовую статистику для команды"""
        return {
            'matches_played': 30,
            'wins': random.randint(12, 20),
            'losses': 0,
            'draws': 0,
            'goals_for': random.randint(50, 100) if sport == 'khl' else random.randint(500, 800),
            'goals_against': random.randint(40, 90) if sport == 'khl' else random.randint(400, 700),
            'recent_form': ['W', 'L', 'W', 'W', 'L'],
            'win_rate': 0.55
        }
    
    def _extract_pre_match_features(self, stats1: Dict, stats2: Dict, match: Dict) -> Dict:
        """Извлечение pre-match фичей"""
        features = {}
        
        # Базовые фичи команды 1
        features['team1_win_rate'] = stats1.get('win_rate', 0.5)
        features['team1_matches_played'] = stats1.get('matches_played', 30)
        features['team1_wins'] = stats1.get('wins', 15)
        features['team1_losses'] = stats1.get('losses', 15)
        features['team1_draws'] = stats1.get('draws', 0)
        
        # Базовые фичи команды 2
        features['team2_win_rate'] = stats2.get('win_rate', 0.5)
        features['team2_matches_played'] = stats2.get('matches_played', 30)
        features['team2_wins'] = stats2.get('wins', 15)
        features['team2_losses'] = stats2.get('losses', 15)
        features['team2_draws'] = stats2.get('draws', 0)
        
        # Разностные фичи
        features['win_rate_diff'] = features['team1_win_rate'] - features['team2_win_rate']
        features['matches_diff'] = features['team1_matches_played'] - features['team2_matches_played']
        features['wins_diff'] = features['team1_wins'] - features['team2_wins']
        
        # Фичи формы
        recent_form1 = stats1.get('recent_form', [])
        recent_form2 = stats2.get('recent_form', [])
        
        features['team1_recent_wins'] = recent_form1.count('W') if recent_form1 else 0
        features['team2_recent_wins'] = recent_form2.count('W') if recent_form2 else 0
        features['team1_recent_losses'] = recent_form1.count('L') if recent_form1 else 0
        features['team2_recent_losses'] = recent_form2.count('L') if recent_form2 else 0
        
        # Специфичные фичи для спорта
        if match['sport'] == 'khl':
            features['team1_goals_for_avg'] = stats1.get('goals_for', 100) / max(stats1.get('matches_played', 30), 1)
            features['team2_goals_for_avg'] = stats2.get('goals_for', 100) / max(stats2.get('matches_played', 30), 1)
            features['team1_goals_against_avg'] = stats1.get('goals_against', 90) / max(stats1.get('matches_played', 30), 1)
            features['team2_goals_against_avg'] = stats2.get('goals_against', 90) / max(stats2.get('matches_played', 30), 1)
            features['goals_diff'] = features['team1_goals_for_avg'] - features['team2_goals_for_avg']
        else:
            # CS2 специфичные фичи
            features['team1_rank'] = match.get('features', {}).get('team1_rank', 10)
            features['team2_rank'] = match.get('features', {}).get('team2_rank', 10)
            features['rank_diff'] = features['team1_rank'] - features['team2_rank']
        
        return features
    
    async def train_models(self, sport: str = 'cs2') -> bool:
        """Обучение моделей на исторических данных"""
        try:
            logger.info(f"🤖 Training Pre-Match ML models for {sport}")
            
            # Сбор данных
            df = await self.collect_training_data(sport, min_matches=30)
            if df is None:
                logger.warning(f"⚠️ Not enough historical data for training {sport}")
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
                    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=3)
                    
                    results[model_name] = {
                        'accuracy': accuracy,
                        'cv_mean': cv_scores.mean(),
                        'cv_std': cv_scores.std()
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
            
            logger.info(f"✅ Pre-Match ML models training completed for {sport}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error training pre-match models: {e}")
            return False
    
    async def load_models(self, sport: str) -> bool:
        """Загрузка обученных моделей"""
        try:
            metadata_path = os.path.join(self.models_path, f"{sport}_metadata.pkl")
            
            if not os.path.exists(metadata_path):
                logger.warning(f"⚠️ No trained pre-match models found for {sport}")
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
            
            logger.info(f"✅ Pre-Match models loaded for {sport}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading pre-match models: {e}")
            return False
    
    async def predict_match(self, match: Dict, sport: str) -> Dict[str, Any]:
        """Прогнозирование pre-match матча"""
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
            
            if not stats1:
                stats1 = self._create_basic_stats(match['team1'], sport)
            if not stats2:
                stats2 = self._create_basic_stats(match['team2'], sport)
            
            # Извлечение фичей
            features = self._extract_pre_match_features(stats1, stats2, match)
            
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
            
            return {
                'prediction': ensemble_pred['prediction'],
                'confidence': ensemble_pred['confidence'],
                'team1_probability': ensemble_pred.get('team1_probability', 0.5),
                'team2_probability': ensemble_pred.get('team2_probability', 0.5),
                'draw_probability': ensemble_pred.get('draw_probability', 0.0),
                'method': 'pre_match_ensemble',
                'analysis_type': 'pre_match'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in pre-match prediction: {e}")
            return self._rule_based_prediction(match, sport)
    
    def _rule_based_prediction(self, match: Dict, sport: str) -> Dict[str, Any]:
        """Rule-based прогноз для pre-match"""
        try:
            # Простая логика на основе базовых факторов
            team1_strength = 0.5
            team2_strength = 0.5
            
            # Учитываем турнир (если известен)
            tournament = match.get('tournament', '').lower()
            if 'major' in tournament or 'premier' in tournament:
                # В крупных турнирах топ команды сильнее
                if any(top in match['team1'].lower() for top in ['navi', 'faze', 'g2']):
                    team1_strength += 0.1
                if any(top in match['team2'].lower() for top in ['navi', 'faze', 'g2']):
                    team2_strength += 0.1
            
            # Нормализация
            total_strength = team1_strength + team2_strength
            team1_prob = team1_strength / total_strength
            team2_prob = team2_strength / total_strength
            
            # Определяем победителя
            if abs(team1_prob - team2_prob) < 0.05:
                prediction = 'draw' if sport == 'khl' else 'team1'
                confidence = 0.5
            elif team1_prob > team2_prob:
                prediction = 'team1'
                confidence = team1_prob
            else:
                prediction = 'team2'
                confidence = team2_prob
            
            return {
                'prediction': prediction,
                'confidence': confidence,
                'team1_probability': team1_prob,
                'team2_probability': team2_prob,
                'draw_probability': 0.1 if sport == 'khl' else 0.0,
                'method': 'pre_match_rule_based',
                'analysis_type': 'pre_match'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in pre-match rule-based prediction: {e}")
            return {
                'prediction': 'team1',
                'confidence': 0.5,
                'team1_probability': 0.5,
                'team2_probability': 0.5,
                'draw_probability': 0.0,
                'method': 'pre_match_fallback',
                'analysis_type': 'pre_match'
            }
    
    def _ensemble_predictions(self, predictions: Dict) -> Dict:
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
                return {
                    'prediction': 'team1',
                    'confidence': 0.5,
                    'team1_probability': 0.5,
                    'team2_probability': 0.5,
                    'draw_probability': 0.0
                }
            
            winner = max(votes.keys(), key=lambda x: votes[x])
            
            # Усредненная вероятность
            avg_confidence = total_confidence / len(predictions) / len(predictions)
            
            result = {
                'prediction': winner,
                'confidence': avg_confidence,
                'team1_probability': avg_confidence if winner == 'team1' else (1 - avg_confidence),
                'team2_probability': avg_confidence if winner == 'team2' else (1 - avg_confidence),
                'draw_probability': 0.0
            }
            
            # Добавляем draw вероятность для КХЛ
            if 'draw' in predictions.get('logistic_regression', {}).get('probabilities', {}):
                result['draw_probability'] = predictions['logistic_regression']['probabilities']['draw']
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in pre-match ensemble: {e}")
            return {
                'prediction': 'team1',
                'confidence': 0.5,
                'team1_probability': 0.5,
                'team2_probability': 0.5,
                'draw_probability': 0.0
            }
