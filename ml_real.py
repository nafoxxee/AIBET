#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real ML Models
ML модели обучаются только на реальных данных
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any

from database import Match, Signal, db_manager
from feature_engineering import feature_engineering

logger = logging.getLogger(__name__)

class RealMLModels:
    def __init__(self):
        self.name = "Real ML Models"
        self.models_path = "models/"
        self.min_training_samples = 100
        self.confidence_threshold = 0.70
        
        # Модели
        self.rf_model = None
        self.lr_model = None
        self.scaler = StandardScaler()
        
        # Статистика
        self._initialized = False
        self._trained = False
        self.training_stats = {}
        
        # Создаем директорию для моделей
        os.makedirs(self.models_path, exist_ok=True)
    
    async def initialize(self):
        """Инициализация ML моделей"""
        if self._initialized:
            return
        
        logger.info("🤖 Initializing Real ML Models")
        
        try:
            # Проверяем наличие сохраненных моделей
            await self.load_models()
            
            if self.rf_model and self.lr_model:
                logger.info("✅ Loaded existing ML models")
                self._trained = True
            else:
                logger.info("📚 No existing models found, will train when enough data available")
            
            self._initialized = True
            logger.info("✅ Real ML Models initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing ML models: {e}")
            self._initialized = True  # Помечаем как инициализированные, но не обученные
    
    async def train_models(self):
        """Обучение моделей на реальных данных"""
        if not self._initialized:
            await self.initialize()
        
        logger.info("🎯 Training ML models on real data")
        
        try:
            # Получаем завершенные матчи для обучения
            finished_matches = await db_manager.get_finished_matches(limit=1000)
            
            if len(finished_matches) < self.min_training_samples:
                logger.warning(f"⚠️ Not enough data for training: {len(finished_matches)} matches (need {self.min_training_samples})")
                return False
            
            logger.info(f"📊 Using {len(finished_matches)} finished matches for training")
            
            # Создаем обучающие данные
            X, y = await self.create_training_data(finished_matches)
            
            if len(X) < 50:
                logger.warning(f"⚠️ Insufficient training samples: {len(X)}")
                return False
            
            # Нормализуем признаки
            X_scaled = self.scaler.fit_transform(X)
            
            # Разделяем данные
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
            )
            
            # Обучаем RandomForest
            logger.info("🌲 Training RandomForest...")
            self.rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight='balanced'
            )
            self.rf_model.fit(X_train, y_train)
            
            # Оцениваем RandomForest
            rf_pred = self.rf_model.predict(X_test)
            rf_accuracy = accuracy_score(y_test, rf_pred)
            logger.info(f"🌲 RandomForest accuracy: {rf_accuracy:.3f}")
            
            # Обучаем LogisticRegression
            logger.info("📈 Training LogisticRegression...")
            self.lr_model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                class_weight='balanced'
            )
            self.lr_model.fit(X_train, y_train)
            
            # Оцениваем LogisticRegression
            lr_pred = self.lr_model.predict(X_test)
            lr_accuracy = accuracy_score(y_test, lr_pred)
            logger.info(f"📈 LogisticRegression accuracy: {lr_accuracy:.3f}")
            
            # Сохраняем модели
            await self.save_models()
            
            # Обновляем статистику
            self.training_stats = {
                'samples_count': len(X),
                'rf_accuracy': rf_accuracy,
                'lr_accuracy': lr_accuracy,
                'training_date': datetime.now().isoformat(),
                'feature_count': X.shape[1]
            }
            
            self._trained = True
            logger.info(f"✅ Models trained successfully. RF: {rf_accuracy:.3f}, LR: {lr_accuracy:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error training models: {e}")
            return False
    
    async def create_training_data(self, matches: List[Match]) -> Tuple[np.ndarray, np.ndarray]:
        """Создание обучающих данных из матчей"""
        X = []
        y = []
        
        for match in matches:
            try:
                # Пропускаем матчи без счета
                if not match.score or ':' not in match.score:
                    continue
                
                # Создаем признаки
                features = await feature_engineering.create_match_features(match)
                feature_vector = feature_engineering.get_feature_vector(features)
                
                # Определяем результат
                score_parts = match.score.split(':')
                if len(score_parts) >= 2:
                    try:
                        score1 = int(score_parts[0])
                        score2 = int(score_parts[1])
                        result = 1 if score1 > score2 else 0
                    except:
                        continue
                    
                    X.append(feature_vector)
                    y.append(result)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error processing match {match.id}: {e}")
                continue
        
        return np.array(X), np.array(y)
    
    async def predict_match(self, match: Match) -> Optional[Dict[str, Any]]:
        """Предсказание результата матча"""
        if not self._trained or not self.rf_model or not self.lr_model:
            return None
        
        try:
            # Создаем признаки
            features = await feature_engineering.create_match_features(match)
            feature_vector = feature_engineering.get_feature_vector(features)
            
            # Нормализуем
            feature_vector_scaled = self.scaler.transform([feature_vector])
            
            # Предсказания
            rf_pred = self.rf_model.predict_proba(feature_vector_scaled)[0]
            lr_pred = self.lr_model.predict_proba(feature_vector_scaled)[0]
            
            # Ансамбль
            ensemble_pred = (rf_pred + lr_pred) / 2
            
            # Определяем результат и уверенность
            if ensemble_pred[1] > ensemble_pred[0]:
                prediction = f"{match.team1} победит"
                confidence = ensemble_pred[1]
            else:
                prediction = f"{match.team2} победит"
                confidence = ensemble_pred[0]
            
            # Дополнительная информация
            result = {
                'prediction': prediction,
                'confidence': float(confidence),
                'rf_confidence': float(rf_pred[1] if rf_pred[1] > rf_pred[0] else rf_pred[0]),
                'lr_confidence': float(lr_pred[1] if lr_pred[1] > lr_pred[0] else lr_pred[0]),
                'team1_win_prob': float(ensemble_pred[1]),
                'team2_win_prob': float(ensemble_pred[0]),
                'model_type': 'ensemble_rf_lr',
                'features_used': len(feature_vector),
                'prediction_time': datetime.now().isoformat()
            }
            
            # Добавляем объяснение
            result['explanation'] = self._generate_explanation(features, result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error predicting match {match.team1} vs {match.team2}: {e}")
            return None
    
    def _generate_explanation(self, features: Dict[str, Any], prediction: Dict[str, Any]) -> str:
        """Генерация объяснения предсказания"""
        try:
            explanations = []
            
            # Winrate разница
            winrate_diff = features.get('winrate_diff', 0)
            if abs(winrate_diff) > 10:
                if winrate_diff > 0:
                    explanations.append(f"Первая команда имеет winrate выше на {abs(winrate_diff):.1f}%")
                else:
                    explanations.append(f"Вторая команда имеет winrate выше на {abs(winrate_diff):.1f}%")
            
            # Форма
            form_diff = features.get('form_diff', 0)
            if abs(form_diff) > 1:
                if form_diff > 0:
                    explanations.append("Первая команда в лучшей форме")
                else:
                    explanations.append("Вторая команда в лучшей форме")
            
            # H2H преимущество
            h2h_adv = features.get('h2h_team1_advantage', 0.5)
            if h2h_adv > 0.7:
                explanations.append("Исторически доминирует в личных встречах")
            elif h2h_adv < 0.3:
                explanations.append("Исторически уступает в личных встречах")
            
            # Важность турнира
            importance = features.get('importance', 5)
            if importance >= 8:
                explanations.append("Матч высокого уровня (важный турнир)")
            
            return " | ".join(explanations) if explanations else "Баланс сил"
            
        except:
            return "Анализ на основе статистики команд"
    
    async def save_models(self):
        """Сохранение моделей"""
        try:
            # RandomForest
            with open(os.path.join(self.models_path, 'rf_model.pkl'), 'wb') as f:
                pickle.dump(self.rf_model, f)
            
            # LogisticRegression
            with open(os.path.join(self.models_path, 'lr_model.pkl'), 'wb') as f:
                pickle.dump(self.lr_model, f)
            
            # Scaler
            with open(os.path.join(self.models_path, 'scaler.pkl'), 'wb') as f:
                pickle.dump(self.scaler, f)
            
            # Статистика
            with open(os.path.join(self.models_path, 'training_stats.json'), 'w') as f:
                import json
                json.dump(self.training_stats, f, indent=2)
            
            logger.info("💾 Models saved successfully")
            
        except Exception as e:
            logger.error(f"❌ Error saving models: {e}")
    
    async def load_models(self):
        """Загрузка моделей"""
        try:
            # RandomForest
            rf_path = os.path.join(self.models_path, 'rf_model.pkl')
            if os.path.exists(rf_path):
                with open(rf_path, 'rb') as f:
                    self.rf_model = pickle.load(f)
            
            # LogisticRegression
            lr_path = os.path.join(self.models_path, 'lr_model.pkl')
            if os.path.exists(lr_path):
                with open(lr_path, 'rb') as f:
                    self.lr_model = pickle.load(f)
            
            # Scaler
            scaler_path = os.path.join(self.models_path, 'scaler.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            # Статистика
            stats_path = os.path.join(self.models_path, 'training_stats.json')
            if os.path.exists(stats_path):
                with open(stats_path, 'r') as f:
                    import json
                    self.training_stats = json.load(f)
            
            logger.info("📚 Models loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Error loading models: {e}")
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Получение статистики моделей"""
        return {
            'initialized': self._initialized,
            'trained': self._trained,
            'training_stats': self.training_stats,
            'confidence_threshold': self.confidence_threshold,
            'min_training_samples': self.min_training_samples
        }

# Глобальный экземпляр
real_ml_models = RealMLModels()
