import asyncio
import logging
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

from database import Match, Signal, DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class Scenario:
    """Структура сценария"""
    name: str
    confidence: str  # LOW, MEDIUM, HIGH
    probability: float
    explanation: str
    factors: List[str]
    recommendation: str


@dataclass
class AnalysisResult:
    """Результат анализа матча"""
    match_id: str
    sport: str
    scenarios: List[Scenario]
    overall_confidence: str
    win_probability: float
    key_factors: List[str]
    timestamp: datetime


class BaseAnalyzer(ABC):
    """Базовый класс анализатора"""
    
    def __init__(self, db_manager: DatabaseManager, sport: str):
        self.db_manager = db_manager
        self.sport = sport
        self.classifier = None
        self.regressor = None
        self.model_accuracy = 0.0
        self.last_trained = None
        self.training_data = []
    
    async def initialize(self):
        """Инициализация анализатора"""
        await self._load_models()
        logger.info(f"{self.__class__.__name__} initialized for {self.sport}")
    
    async def analyze_match(self, match: Match) -> AnalysisResult:
        """Анализ матча"""
        try:
            # Получаем исторические данные
            historical_data = await self._get_historical_data(match)
            
            # Анализируем коэффициенты
            odds_analysis = self._analyze_odds(match)
            
            # Анализируем сценарии
            scenarios = await self._detect_scenarios(match, historical_data, odds_analysis)
            
            # Определяем общую уверенность
            overall_confidence = self._calculate_overall_confidence(scenarios)
            
            # Рассчитываем вероятность победы
            win_probability = await self._calculate_win_probability(match, scenarios)
            
            # Определяем ключевые факторы
            key_factors = self._extract_key_factors(scenarios, odds_analysis)
            
            return AnalysisResult(
                match_id=match.id,
                sport=self.sport,
                scenarios=scenarios,
                overall_confidence=overall_confidence,
                win_probability=win_probability,
                key_factors=key_factors,
                timestamp=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"Error analyzing match {match.id}: {e}")
            return self._create_default_analysis(match)
    
    async def _get_historical_data(self, match: Match) -> List[Dict]:
        """Получение исторических данных"""
        try:
            # Получаем прошлые матчи команд
            past_matches = await self.db_manager.get_upcoming_matches(
                sport=self.sport, 
                hours=24*7  # За последнюю неделю
            )
            
            # Фильтруем матчи с участием этих команд
            team_matches = [
                m for m in past_matches 
                if m.team1 == match.team1 or m.team2 == match.team1 or
                   m.team1 == match.team2 or m.team2 == match.team2
            ]
            
            historical_data = []
            for past_match in team_matches:
                historical_data.append({
                    'team1': past_match.team1,
                    'team2': past_match.team2,
                    'odds1': past_match.odds1,
                    'odds2': past_match.odds2,
                    'result': self._get_match_result(past_match)
                })
            
            return historical_data
        
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []
    
    def _analyze_odds(self, match: Match) -> Dict[str, Any]:
        """Анализ коэффициентов"""
        try:
            analysis = {}
            
            # Анализ фаворита
            if match.odds1 < match.odds2:
                analysis['favorite'] = match.team1
                analysis['favorite_odds'] = match.odds1
                analysis['underdog_odds'] = match.odds2
            else:
                analysis['favorite'] = match.team2
                analysis['favorite_odds'] = match.odds2
                analysis['underdog_odds'] = match.odds1
            
            # Анализ перекоса
            odds_ratio = max(match.odds1, match.odds2) / min(match.odds1, match.odds2)
            analysis['odds_ratio'] = odds_ratio
            analysis['is_skewed'] = odds_ratio > 2.0
            
            # Анализ маржи букмекера
            if match.odds_draw:
                implied_prob = (1/match.odds1 + 1/match.odds2 + 1/match.odds_draw)
            else:
                implied_prob = (1/match.odds1 + 1/match.odds2)
            
            analysis['bookmaker_margin'] = (implied_prob - 1) * 100
            analysis['is_high_margin'] = analysis['bookmaker_margin'] > 10
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing odds: {e}")
            return {}
    
    @abstractmethod
    async def _detect_scenarios(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> List[Scenario]:
        """Обнаружение сценариев (реализуется в дочерних классах)"""
        pass
    
    def _calculate_overall_confidence(self, scenarios: List[Scenario]) -> str:
        """Расчет общей уверенности"""
        if not scenarios:
            return "LOW"
        
        # Учитываем количество и уверенность сценариев
        high_confidence_count = sum(1 for s in scenarios if s.confidence == "HIGH")
        medium_confidence_count = sum(1 for s in scenarios if s.confidence == "MEDIUM")
        
        if high_confidence_count >= 2:
            return "HIGH"
        elif high_confidence_count >= 1 or medium_confidence_count >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _calculate_win_probability(self, match: Match, scenarios: List[Scenario]) -> float:
        """Расчет вероятности победы"""
        try:
            if not self.classifier:
                return 0.5
            
            # Создаем признаки для предсказания
            features = self._create_features(match, scenarios)
            
            # Предсказываем вероятность
            probability = self.classifier.predict_proba([features])[0]
            
            # Возвращаем вероятность для фаворита
            return max(probability)
        
        except Exception as e:
            logger.error(f"Error calculating win probability: {e}")
            return 0.5
    
    def _create_features(self, match: Match, scenarios: List[Scenario]) -> List[float]:
        """Создание признаков для ML модели"""
        features = [
            match.odds1,
            match.odds2,
            match.odds_draw if match.odds_draw else 0.0,
            abs(match.odds1 - match.odds2),
            max(match.odds1, match.odds2) / min(match.odds1, match.odds2),
            len(scenarios),
            sum(1 for s in scenarios if s.confidence == "HIGH"),
            sum(1 for s in scenarios if s.confidence == "MEDIUM"),
            sum(1 for s in scenarios if s.confidence == "LOW"),
            sum(s.probability for s in scenarios) / len(scenarios) if scenarios else 0.0
        ]
        
        return features
    
    def _extract_key_factors(self, scenarios: List[Scenario], odds_analysis: Dict) -> List[str]:
        """Извлечение ключевых факторов"""
        factors = []
        
        # Добавляем факторы из сценариев
        for scenario in scenarios:
            factors.extend(scenario.factors)
        
        # Добавляем факторы из анализа коэффициентов
        if odds_analysis.get('is_skewed'):
            factors.append("Высокий перекос коэффициентов")
        
        if odds_analysis.get('is_high_margin'):
            factors.append("Высокая маржа букмекера")
        
        # Удаляем дубликаты и возвращаем
        return list(set(factors))
    
    def _get_match_result(self, match: Match) -> Optional[str]:
        """Получение результата матча"""
        if match.status != 'finished' or match.score1 is None or match.score2 is None:
            return None
        
        if match.score1 > match.score2:
            return 'team1'
        elif match.score2 > match.score1:
            return 'team2'
        else:
            return 'draw'
    
    def _create_default_analysis(self, match: Match) -> AnalysisResult:
        """Создание анализа по умолчанию"""
        default_scenario = Scenario(
            name="Недостаточно данных",
            confidence="LOW",
            probability=0.5,
            explanation="Недостаточно исторических данных для анализа",
            factors=["Новое противостояние", "Ограниченная статистика"],
            recommendation="Требуется осторожность"
        )
        
        return AnalysisResult(
            match_id=match.id,
            sport=self.sport,
            scenarios=[default_scenario],
            overall_confidence="LOW",
            win_probability=0.5,
            key_factors=["Недостаточно данных"],
            timestamp=datetime.now()
        )
    
    async def train_models(self):
        """Обучение ML моделей"""
        try:
            # Получаем обучающие данные
            training_data = await self._prepare_training_data()
            
            if len(training_data) < 50:  # Минимальное количество данных
                logger.warning(f"Insufficient training data for {self.sport}: {len(training_data)} samples")
                return
            
            # Создаем DataFrame
            df = pd.DataFrame(training_data)
            
            # Подготавливаем признаки и цели
            X = df.drop(['result'], axis=1)
            y = df['result']
            
            # Разделяем данные
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Обучаем классификатор
            self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.classifier.fit(X_train, y_train)
            
            # Оцениваем точность
            y_pred = self.classifier.predict(X_test)
            self.model_accuracy = accuracy_score(y_test, y_pred)
            
            # Обучаем регрессор для вероятностей
            self.regressor = GradientBoostingRegressor(n_estimators=100, random_state=42)
            self.regressor.fit(X_train, y_train.map({'team1': 1, 'team2': 0, 'draw': 0.5}))
            
            self.last_trained = datetime.now()
            
            # Сохраняем модели
            await self._save_models()
            
            logger.info(f"Models trained for {self.sport}. Accuracy: {self.model_accuracy:.2f}")
        
        except Exception as e:
            logger.error(f"Error training models for {self.sport}: {e}")
    
    async def _prepare_training_data(self) -> List[Dict]:
        """Подготовка обучающих данных"""
        training_data = []
        
        try:
            # Получаем все матчи с результатами
            all_matches = await self.db_manager.get_upcoming_matches(sport=self.sport, hours=24*30)  # За 30 дней
            
            for match in all_matches:
                if match.status == 'finished' and match.score1 is not None:
                    # Получаем сигналы для этого матча
                    signals = await self.db_manager.get_signals(sport=self.sport, limit=1000)
                    match_signals = [s for s in signals if s.match_id == match.id]
                    
                    # Создаем обучающий пример
                    features = self._create_training_features(match, match_signals)
                    result = self._get_match_result(match)
                    
                    if result:
                        features['result'] = result
                        training_data.append(features)
        
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
        
        return training_data
    
    def _create_training_features(self, match: Match, signals: List[Signal]) -> Dict:
        """Создание признаков для обучения"""
        features = {
            'odds1': match.odds1,
            'odds2': match.odds2,
            'odds_draw': match.odds_draw if match.odds_draw else 0.0,
            'odds_diff': abs(match.odds1 - match.odds2),
            'odds_ratio': max(match.odds1, match.odds2) / min(match.odds1, match.odds2),
            'signal_count': len(signals),
            'high_confidence_signals': sum(1 for s in signals if s.confidence == "HIGH"),
            'avg_probability': sum(s.probability for s in signals) / len(signals) if signals else 0.0,
            'tournament_strength': self._get_tournament_strength(match.tournament)
        }
        
        return features
    
    def _get_tournament_strength(self, tournament: str) -> float:
        """Оценка силы турнира"""
        # Простая эвристика для оценки силы турнира
        high_tournaments = ['Major', 'IEM', 'ESL Pro League', 'Playoffs']
        medium_tournaments = ['Regular Season', 'Group Stage']
        
        if any(high in tournament for high in high_tournaments):
            return 1.0
        elif any(medium in tournament for medium in medium_tournaments):
            return 0.7
        else:
            return 0.5
    
    async def _load_models(self):
        """Загрузка моделей"""
        try:
            # Загружаем классификатор
            classifier_model = await self.db_manager.get_ml_model(self.sport, 'classifier')
            if classifier_model:
                self.classifier = joblib.load(classifier_model.model_data)
                self.model_accuracy = classifier_model.accuracy
                self.last_trained = classifier_model.last_trained
            
            # Загружаем регрессор
            regressor_model = await self.db_manager.get_ml_model(self.sport, 'regressor')
            if regressor_model:
                self.regressor = joblib.load(regressor_model.model_data)
        
        except Exception as e:
            logger.error(f"Error loading models for {self.sport}: {e}")
    
    async def _save_models(self):
        """Сохранение моделей"""
        try:
            if self.classifier:
                model_data = joblib.dumps(self.classifier)
                from database import MLModel
                model = MLModel(
                    sport=self.sport,
                    model_type='classifier',
                    model_data=model_data,
                    accuracy=self.model_accuracy,
                    last_trained=self.last_trained,
                    training_samples=len(self.training_data)
                )
                await self.db_manager.save_ml_model(model)
            
            if self.regressor:
                model_data = joblib.dumps(self.regressor)
                from database import MLModel
                model = MLModel(
                    sport=self.sport,
                    model_type='regressor',
                    model_data=model_data,
                    accuracy=self.model_accuracy,
                    last_trained=self.last_trained,
                    training_samples=len(self.training_data)
                )
                await self.db_manager.save_ml_model(model)
        
        except Exception as e:
            logger.error(f"Error saving models for {self.sport}: {e}")
