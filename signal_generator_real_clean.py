#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real Signal Generator
Генерация сигналов только на основе реальных данных и ML предсказаний
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from database import Match, Signal, db_manager
from ml_models_real import ml_models
from feature_engineering_real import feature_engineering
from parsers.odds_parser import odds_parser

logger = logging.getLogger(__name__)

class RealSignalGenerator:
    def __init__(self):
        self.name = "Real Signal Generator"
        self.min_confidence = 0.70
        self.max_signals_per_day = 10
        self.signal_cooldown_minutes = 60
        self._initialized = False
        
        # Daily tracking
        self.daily_signals_count = 0
        self.last_signal_date = datetime.now().date()
        
        # Signal quality metrics
        self.min_odds_value = 1.5  # Minimum odds for value bet
        self.max_odds_value = 3.0  # Maximum odds for reasonable bet
    
    async def initialize(self):
        """Инициализация генератора сигналов"""
        if self._initialized:
            return
        
        logger.info("🎯 Initializing Real Signal Generator")
        
        # Проверяем, что ML модели готовы
        model_status = await ml_models.get_model_status()
        if not model_status['is_trained']:
            logger.warning("⚠️ ML models not trained, attempting to train...")
            await ml_models.train_models()
        
        self._initialized = True
        logger.info("✅ Real Signal Generator initialized successfully")
    
    async def generate_signals(self) -> List[Signal]:
        """Генерация сигналов"""
        if not self._initialized:
            await self.initialize()
        
        logger.info("🎯 Generating real signals")
        
        try:
            # Проверяем лимит сигналов за сегодня
            today = datetime.now().date()
            if today != self.last_signal_date:
                self.daily_signals_count = 0
                self.last_signal_date = today
            
            if self.daily_signals_count >= self.max_signals_per_day:
                logger.info(f"⚠️ Already generated {self.daily_signals_count} signals today (max: {self.max_signals_per_day})")
                return []
            
            # Получаем прогнозы от ML моделей
            predictions = await ml_models.predict_upcoming_matches(limit=50)
            
            # Фильтруем по confidence
            high_confidence_predictions = [
                p for p in predictions 
                if p.confidence >= self.min_confidence
            ]
            
            if not high_confidence_predictions:
                logger.info("🔴 No high-confidence predictions found")
                return []
            
            # Дополнительная фильтрация и создание сигналов
            signals = []
            available_slots = self.max_signals_per_day - self.daily_signals_count
            
            for prediction in high_confidence_predictions[:available_slots]:
                signal = await self._create_signal_from_prediction(prediction)
                if signal:
                    signals.append(signal)
                    self.daily_signals_count += 1
                    logger.info(f"✅ Generated signal: {signal.team1} vs {signal.team2} - {signal.prediction}")
            
            # Сохраняем сигналы в базу
            for signal in signals:
                try:
                    await db_manager.add_signal(signal)
                except Exception as e:
                    logger.warning(f"⚠️ Error saving signal: {e}")
            
            logger.info(f"🎯 Generated {len(signals)} signals today ({self.daily_signals_count}/{self.max_signals_per_day})")
            return signals
            
        except Exception as e:
            logger.error(f"❌ Error generating signals: {e}")
            return []
    
    async def _create_signal_from_prediction(self, prediction) -> Optional[Signal]:
        """Create signal from ML prediction with quality checks"""
        try:
            # Get match details
            matches = await db_manager.get_matches(limit=100)
            target_match = None
            
            for match in matches:
                if (match.team1 == prediction.team1 and 
                    match.team2 == prediction.team2 and 
                    match.sport == prediction.sport):
                    target_match = match
                    break
            
            if not target_match:
                logger.warning(f"⚠️ Match not found for prediction: {prediction.team1} vs {prediction.team2}")
                return None
            
            # Get odds for value calculation
            odds_data = await odds_parser.get_all_odds(prediction.sport)
            match_odds = []
            
            for odds in odds_data:
                if (odds.team1 == prediction.team1 and odds.team2 == prediction.team2):
                    match_odds.append(odds)
            
            # Calculate average odds
            avg_odds1 = 0.0
            avg_odds2 = 0.0
            
            if match_odds:
                avg_odds1 = sum(o.odds1 for o in match_odds) / len(match_odds)
                avg_odds2 = sum(o.odds2 for o in match_odds) / len(match_odds)
            
            # Determine predicted winner and corresponding odds
            if prediction.prediction == 1:  # Team1 predicted to win
                predicted_winner = prediction.team1
                predicted_odds = avg_odds1
            else:  # Team2 predicted to win
                predicted_winner = prediction.team2
                predicted_odds = avg_odds2
            
            # Quality checks
            if predicted_odds < self.min_odds_value or predicted_odds > self.max_odds_value:
                logger.info(f"⚠️ Odds {predicted_odds} outside value range for {predicted_winner}")
                return None
            
            # Calculate value score
            implied_probability = 1.0 / predicted_odds
            value_score = (prediction.confidence - implied_probability) * 100
            
            if value_score < 5:  # Minimum value threshold
                logger.info(f"⚠️ Low value score {value_score:.1f}% for {predicted_winner}")
                return None
            
            # Create signal
            signal = Signal(
                match_id=str(target_match.id),
                team1=prediction.team1,
                team2=prediction.team2,
                sport=prediction.sport,
                prediction=predicted_winner,
                confidence=prediction.confidence,
                odds=predicted_odds,
                value_score=round(value_score, 2),
                model_used=prediction.model_used,
                features={
                    "prediction_confidence": prediction.confidence,
                    "implied_probability": implied_probability,
                    "value_score": value_score,
                    "bookmakers_count": len(match_odds),
                    "features_used": prediction.features_used
                },
                status="active",
                created_at=datetime.now()
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error creating signal from prediction: {e}")
            return None
    
    async def get_today_signals(self) -> List[Signal]:
        """Получить сигналы за сегодня"""
        try:
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            
            signals = await db_manager.get_signals(
                start_date=today_start,
                limit=100
            )
            
            return signals
            
        except Exception as e:
            logger.error(f"❌ Error getting today's signals: {e}")
            return []
    
    async def get_signal_stats(self) -> Dict[str, Any]:
        """Получить статистику сигналов"""
        try:
            today_signals = await self.get_today_signals()
            
            # Calculate accuracy for completed signals
            completed_signals = [s for s in today_signals if s.status == "completed"]
            correct_signals = [s for s in completed_signals if s.features.get("result") == "win"]
            
            accuracy = len(correct_signals) / len(completed_signals) if completed_signals else 0.0
            
            stats = {
                "today_signals": len(today_signals),
                "completed_signals": len(completed_signals),
                "correct_signals": len(correct_signals),
                "accuracy": round(accuracy, 3),
                "daily_limit": self.max_signals_per_day,
                "remaining_signals": self.max_signals_per_day - self.daily_signals_count,
                "last_generated": max([s.created_at for s in today_signals]).isoformat() if today_signals else None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting signal stats: {e}")
            return {}
    
    async def auto_generate_signals(self):
        """Автоматическая генерация сигналов (для фоновой задачи)"""
        try:
            logger.info("🔄 Auto-generating signals")
            
            signals = await self.generate_signals()
            
            if signals:
                logger.info(f"✅ Auto-generated {len(signals)} signals")
                
                # Здесь можно добавить отправку уведомлений в Telegram
                # или другие действия при генерации сигналов
                
            else:
                logger.info("ℹ️ No signals generated")
                
        except Exception as e:
            logger.error(f"❌ Error in auto signal generation: {e}")

# Global instance
real_signal_generator = RealSignalGenerator()
