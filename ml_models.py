#!/usr/bin/env python3
"""
AIBET Analytics Platform - ML Models
RandomForestClassifier + LogisticRegression для анализа матчей
"""

import asyncio
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import pickle
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any

from database import Match, Signal, db_manager

logger = logging.getLogger(__name__)

class AdvancedMLModels:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.rf_model = None
        self.lr_model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'rating_diff',
            'home_advantage',
            'tournament_importance',
            'stage_importance',
            'format_importance',
            'team1_form',
            'team2_form',
            'h2h_advantage'
        ]
        self.models_path = "models/"
        self._initialized = False
    
    async def initialize(self):
        """Безопасная инициализация ML моделей"""
        if self._initialized:
            return
        
        # Проверяем доступность БД
        if not self.db_manager:
            logger.warning("⚠️ DB not initialized, skipping ML init")
            self._initialized = True  # Помечаем как инициализированный, но без моделей
            return
            
        logger.info("🤖 Initializing ML Models")
        
        # Создаем директорию для моделей
        import os
        os.makedirs(self.models_path, exist_ok=True)
        
        try:
            # Пытаемся загрузить существующие модели
            await self.load_models()
            
            if self.rf_model is None or self.lr_model is None:
                logger.info("📚 No existing models found, will train later")
                # НЕ обучаем сразу, а откладываем на фон
                self._initialized = True
                logger.info("✅ ML Models initialized (training scheduled for background)")
            else:
                logger.info("✅ Existing models loaded successfully")
                self._initialized = True
                logger.info("✅ ML Models initialized successfully")
            
        except Exception as e:
            logger.exception(f"❌ Error initializing ML models: {e}")
            # НЕ падаем, а помечаем как инициализированный без моделей
            self._initialized = True
            logger.warning("⚠️ ML Models initialized without training (will retry later)")
    
    def extract_features(self, match: Match) -> np.ndarray:
        """Извлечение признаков из матча"""
        features = match.features or {}
        
        # Рейтинговая разница
        rating_diff = features.get('rating_diff', 0)
        if rating_diff is None:
            rating_diff = 0
        
        # Преимущество домашней площадки
        home_advantage = 1 if features.get('home_advantage', False) else 0
        
        # Важность турнира
        tournament = features.get('tournament', '').lower()
        tournament_importance = 0
        if any(word in tournament for word in ['final', 'playoff', 'championship']):
            tournament_importance = 3
        elif any(word in tournament for word in ['semifinal', 'quarterfinal']):
            tournament_importance = 2
        elif 'regular' in tournament:
            tournament_importance = 1
        
        # Важность стадии
        stage = features.get('stage', '').lower()
        stage_importance = 0
        if 'final' in stage:
            stage_importance = 3
        elif 'semifinal' in stage:
            stage_importance = 2
        elif 'playoff' in stage:
            stage_importance = 2
        elif 'group' in stage:
            stage_importance = 1
        
        # Важность формата
        format_type = features.get('format', '').upper()
        format_importance = 0
        if 'BO5' in format_type:
            format_importance = 3
        elif 'BO3' in format_type:
            format_importance = 2
        elif 'BO1' in format_type:
            format_importance = 1
        
        # Форма команд (симуляция на основе рейтинга)
        team1_rating = features.get('team1_rating', 50)
        team2_rating = features.get('team2_rating', 50)
        
        # Форма команды 1 (основана на рейтинге)
        team1_form = min(max(team1_rating / 20, 1), 5)  # Нормализуем 1-5
        
        # Форма команды 2 (основана на рейтинге)
        team2_form = min(max(team2_rating / 20, 1), 5)  # Нормализуем 1-5
        
        # H2H преимущество (симуляция)
        h2h_advantage = np.random.normal(0, 0.5)  # Случайное преимущество
        
        feature_vector = np.array([
            rating_diff,
            home_advantage,
            tournament_importance,
            stage_importance,
            format_importance,
            team1_form,
            team2_form,
            h2h_advantage
        ])
        
        return feature_vector
    
    def create_training_data(self, matches: List[Match]) -> Tuple[np.ndarray, np.ndarray]:
        """Создание обучающих данных из матчей"""
        X = []
        y = []
        
        for match in matches:
            if match.status != 'finished' or not match.score:
                continue
            
            # Извлекаем признаки
            features = self.extract_features(match)
            X.append(features)
            
            # Определяем результат (1 - победа команды 1, 0 - победа команды 2)
            try:
                score_parts = match.score.split(':')
                if len(score_parts) >= 2:
                    score1 = int(score_parts[0])
                    score2 = int(score_parts[1])
                    result = 1 if score1 > score2 else 0
                    y.append(result)
            except:
                continue
        
        return np.array(X), np.array(y)
    
    async def train_models(self):
        """Безопасное обучение ML моделей"""
        logger.info("🎯 Training ML Models")
        
        # Проверяем доступность БД
        if not self.db_manager:
            logger.warning("⚠️ DB not initialized, skipping ML training")
            return
        
        try:
            # Получаем завершенные матчи для обучения
            matches = await self.db_manager.get_matches(status="finished", limit=1000)
            
            if len(matches) < 100:
                logger.warning(f"⚠️ Not enough data for ML training: {len(matches)} matches (need 100+)")
                # Создаем минимальные синтетические данные для базовой работы
                logger.info("📚 Creating synthetic data for basic ML functionality")
                X, y = self.create_synthetic_data()
            else:
                logger.info(f"📚 Using {len(matches)} matches for training")
                X, y = self.create_training_data(matches)
            
            if len(X) < 20:
                logger.warning(f"⚠️ Insufficient training data: {len(X)} samples")
                return
            
            logger.info(f"📊 Training with {len(X)} samples")
            
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
                random_state=42
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
            
            logger.info("✅ ML Models trained successfully")
            
        except Exception as e:
            logger.exception(f"❌ Error training models: {e}")
            # НЕ падаем, а продолжаем работу
            logger.warning("⚠️ ML training failed, continuing without models")
    
    async def save_models(self):
        """Сохранение моделей в файлы"""
        try:
            # Сохраняем RandomForest
            rf_path = f"{self.models_path}random_forest.pkl"
            with open(rf_path, 'wb') as f:
                pickle.dump(self.rf_model, f)
            logger.info(f"💾 RandomForest saved to {rf_path}")
            
            # Сохраняем LogisticRegression
            lr_path = f"{self.models_path}logistic_regression.pkl"
            with open(lr_path, 'wb') as f:
                pickle.dump(self.lr_model, f)
            logger.info(f"💾 LogisticRegression saved to {lr_path}")
            
            # Сохраняем scaler
            scaler_path = f"{self.models_path}scaler.pkl"
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info(f"💾 Scaler saved to {scaler_path}")
            
        except Exception as e:
            logger.exception(f"❌ Error saving models: {e}")
            raise
    
    async def load_models(self):
        """Загрузка моделей из файлов"""
        try:
            # Загружаем RandomForest
            rf_path = f"{self.models_path}random_forest.pkl"
            if os.path.exists(rf_path):
                with open(rf_path, 'rb') as f:
                    self.rf_model = pickle.load(f)
                logger.info(f"📂 RandomForest loaded from {rf_path}")
            
            # Загружаем LogisticRegression
            lr_path = f"{self.models_path}logistic_regression.pkl"
            if os.path.exists(lr_path):
                with open(lr_path, 'rb') as f:
                    self.lr_model = pickle.load(f)
                logger.info(f"📂 LogisticRegression loaded from {lr_path}")
            
            # Загружаем scaler
            scaler_path = f"{self.models_path}scaler.pkl"
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info(f"📂 Scaler loaded from {scaler_path}")
                
        except Exception as e:
            logger.exception(f"❌ Error loading models: {e}")
            # При ошибке сбрасываем модели
            self.rf_model = None
            self.lr_model = None
    
    def create_synthetic_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Создание синтетических данных для обучения"""
        n_samples = 500
        X = []
        y = []
        
        for i in range(n_samples):
            # Генерируем случайные признаки
            rating_diff = np.random.normal(0, 20)
            home_advantage = np.random.choice([0, 1])
            tournament_importance = np.random.choice([0, 1, 2, 3])
            stage_importance = np.random.choice([0, 1, 2, 3])
            format_importance = np.random.choice([0, 1, 2, 3])
            team1_form = np.random.uniform(1, 5)
            team2_form = np.random.uniform(1, 5)
            h2h_advantage = np.random.normal(0, 0.5)
            
            features = np.array([
                rating_diff, home_advantage, tournament_importance,
                stage_importance, format_importance, team1_form,
                team2_form, h2h_advantage
            ])
            
            X.append(features)
            
            # Генерируем результат с некоторой логикой
            score = (rating_diff * 0.3 + 
                    home_advantage * 0.2 + 
                    (team1_form - team2_form) * 0.3 +
                    np.random.normal(0, 1))
            
            result = 1 if score > 0 else 0
            y.append(result)
        
        return np.array(X), np.array(y)
    
    def create_basic_models(self):
        """Создание базовых моделей"""
        logger.info("Creating basic ML models")
        
        # Создаем простые модели с базовыми параметрами
        self.rf_model = RandomForestClassifier(
            n_estimators=50,
            max_depth=5,
            random_state=42
        )
        
        self.lr_model = LogisticRegression(
            random_state=42,
            max_iter=500
        )
        
        # Обучаем на синтетических данных
        X, y = self.create_synthetic_data()
        X_scaled = self.scaler.fit_transform(X)
        
        self.rf_model.fit(X_scaled, y)
        self.lr_model.fit(X_scaled, y)
    
    async def predict_match(self, match: Match) -> Optional[Dict]:
        """Безопасное предсказание матча"""
        try:
            # Проверяем, доступны ли модели
            if not self.rf_model or not self.lr_model:
                logger.debug("⚠️ ML models not ready for prediction")
                return None
            
            # Извлекаем признаки
            features = self.extract_features(match)
            features_scaled = self.scaler.transform([features])
            
            # Получаем предсказания
            rf_pred = self.rf_model.predict(features_scaled)[0]
            rf_proba = self.rf_model.predict_proba(features_scaled)[0]
            
            lr_pred = self.lr_model.predict(features_scaled)[0]
            lr_proba = self.lr_model.predict_proba(features_scaled)[0]
            
            # Усредняем уверенность
            confidence = (rf_proba.max() + lr_proba.max()) / 2
            
            # Определяем финальное предсказание
            prediction = "Team 1" if rf_pred == 1 else "Team 2"
            
            return {
                "prediction": prediction,
                "confidence": confidence,
                "rf_confidence": rf_proba.max(),
                "lr_confidence": lr_proba.max()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error in ML prediction: {e}")
            return None
    
    def generate_analysis(self, match: Match, confidence: float, feature_importance: Dict[str, float]) -> str:
        """Генерация текстового анализа"""
        analysis_parts = []
        
        # Анализ уверенности
        if confidence >= 0.75:
            analysis_parts.append("Высокая уверенность в предсказании")
        elif confidence >= 0.65:
            analysis_parts.append("Средняя уверенность в предсказании")
        else:
            analysis_parts.append("Низкая уверенность, рекомендуется осторожность")
        
        # Анализ рейтингов
        rating_diff = match.features.get('rating_diff', 0) if match.features else 0
        if rating_diff > 10:
            analysis_parts.append(f"Значительное преимущество {match.team1} по рейтингу")
        elif rating_diff < -10:
            analysis_parts.append(f"Значительное преимущество {match.team2} по рейтингу")
        
        # Анализ формата
        format_type = match.features.get('format', '') if match.features else ''
        if 'BO3' in format_type or 'BO5' in format_type:
            analysis_parts.append("Длинный формат дает преимущество более стабильной команде")
        
        # Анализ турнира
        tournament = match.features.get('tournament', '') if match.features else ''
        if any(word in tournament.lower() for word in ['final', 'playoff']):
            analysis_parts.append("Матч плей-офф повышает мотивацию команд")
        
        return ". ".join(analysis_parts) + "."
    
    async def generate_signals(self, min_confidence: float = 0.70) -> List[Signal]:
        """Генерация сигналов на основе ML предсказаний"""
        logger.info(f"🎯 Generating signals with min confidence: {min_confidence}")
        
        signals = []
        
        try:
            # Получаем предстоящие матчи
            matches = await self.db_manager.get_matches(status="upcoming", limit=50)
            
            for match in matches:
                # Пропускаем матчи, которые скоро начнутся
                if match.start_time and match.start_time < datetime.now() + timedelta(minutes=30):
                    continue
                
                # Получаем предсказание
                prediction = await self.predict_match(match)
                
                # Проверяем уверенность
                if prediction['confidence'] >= min_confidence:
                    # Создаем сигнал
                    signal_text = f"AIBET AI SIGNAL 🎯\n"
                    signal_text += f"Матч: {match.team1} vs {match.team2}\n"
                    signal_text += f"Ставка: Победа {prediction['prediction']}\n"
                    signal_text += f"Вероятность: {prediction['confidence']:.1%}\n"
                    signal_text += f"AI-анализ: {prediction['analysis']}"
                    
                    signal = Signal(
                        match_id=match.id,
                        sport=match.sport,
                        signal=signal_text,
                        confidence=prediction['confidence'],
                        published=False
                    )
                    
                    signals.append(signal)
            
            logger.info(f"🎯 Generated {len(signals)} signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return []
    
    async def save_models(self):
        """Сохранение моделей в файлы"""
        try:
            import os
            os.makedirs(self.models_path, exist_ok=True)
            
            # Сохраняем RandomForest
            with open(f"{self.models_path}/random_forest.pkl", 'wb') as f:
                pickle.dump(self.rf_model, f)
            
            # Сохраняем LogisticRegression
            with open(f"{self.models_path}/logistic_regression.pkl", 'wb') as f:
                pickle.dump(self.lr_model, f)
            
            # Сохраняем scaler
            with open(f"{self.models_path}/scaler.pkl", 'wb') as f:
                pickle.dump(self.scaler, f)
            
            logger.info("💾 Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    async def load_models(self):
        """Загрузка моделей из файлов"""
        try:
            import os
            
            # Загружаем RandomForest
            rf_path = f"{self.models_path}/random_forest.pkl"
            if os.path.exists(rf_path):
                with open(rf_path, 'rb') as f:
                    self.rf_model = pickle.load(f)
            
            # Загружаем LogisticRegression
            lr_path = f"{self.models_path}/logistic_regression.pkl"
            if os.path.exists(lr_path):
                with open(lr_path, 'rb') as f:
                    self.lr_model = pickle.load(f)
            
            # Загружаем scaler
            scaler_path = f"{self.models_path}/scaler.pkl"
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            # Если моделей нет, обучаем их
            if self.rf_model is None or self.lr_model is None:
                await self.train_models()
            
            logger.info("📂 Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            await self.train_models()

# Глобальный экземпляр ML моделей
ml_models = AdvancedMLModels()
