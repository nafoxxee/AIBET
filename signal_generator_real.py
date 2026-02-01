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
from ml_real import real_ml_models

logger = logging.getLogger(__name__)

class RealSignalGenerator:
    def __init__(self):
        self.name = "Real Signal Generator"
        self.min_confidence = 0.70
        self.max_signals_per_day = 10
        self.signal_cooldown_minutes = 60
        self._initialized = False
    
    async def initialize(self):
        """Инициализация генератора сигналов"""
        if self._initialized:
            return
        
        logger.info("🎯 Initializing Real Signal Generator")
        
        # Убеждаемся, что ML модели инициализированы
        await real_ml_models.initialize()
        
        self._initialized = True
        logger.info("✅ Real Signal Generator initialized successfully")
    
    async def generate_signals(self) -> List[Signal]:
        """Генерация сигналов"""
        if not self._initialized:
            await self.initialize()
        
        logger.info("🎯 Generating real signals")
        
        try:
            # Проверяем лимит сигналов за сегодня
            today_signals = await self.get_today_signals()
            if len(today_signals) >= self.max_signals_per_day:
                logger.info(f"⚠️ Already generated {len(today_signals)} signals today (max: {self.max_signals_per_day})")
                return []
            
            # Получаем live и upcoming матчи
            live_matches = await db_manager.get_live_matches(limit=20)
            upcoming_matches = await db_manager.get_upcoming_matches(limit=30)
            
            # Фильтруем upcoming матчи (только ближайшие 24 часа)
            upcoming_filtered = []
            now = datetime.utcnow()
            for match in upcoming_matches:
                if match.start_time and (match.start_time - now) <= timedelta(hours=24):
                    upcoming_filtered.append(match)
            
            all_matches = live_matches + upcoming_filtered
            logger.info(f"📊 Analyzing {len(live_matches)} live and {len(upcoming_filtered)} upcoming matches")
            
            generated_signals = []
            
            for match in all_matches:
                try:
                    # Проверяем cooldown для этого матча
                    if await self.is_match_in_cooldown(match):
                        continue
                    
                    # Получаем предсказание от ML моделей
                    prediction = await real_ml_models.predict_match(match)
                    
                    if not prediction:
                        logger.debug(f"⚠️ No prediction available for {match.team1} vs {match.team2}")
                        continue
                    
                    # Проверяем уверенность
                    if prediction['confidence'] < self.min_confidence:
                        logger.debug(f"⚠️ Low confidence ({prediction['confidence']:.2f}) for {match.team1} vs {match.team2}")
                        continue
                    
                    # Создаем сигнал
                    signal = await self.create_signal(match, prediction)
                    if signal:
                        generated_signals.append(signal)
                        logger.info(f"✅ Generated signal for {match.sport}: {match.team1} vs {match.team2} (confidence: {prediction['confidence']:.2f})")
                    
                    # Проверяем лимит
                    if len(generated_signals) >= (self.max_signals_per_day - len(today_signals)):
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error processing match {match.team1} vs {match.team2}: {e}")
                    continue
            
            logger.info(f"🎯 Generated {len(generated_signals)} new signals")
            return generated_signals
            
        except Exception as e:
            logger.error(f"❌ Error generating signals: {e}")
            return []
    
    async def create_signal(self, match: Match, prediction: Dict[str, Any]) -> Optional[Signal]:
        """Создание сигнала из предсказания"""
        try:
            # Формируем текст сигнала
            signal_text = self.format_signal_text(match, prediction)
            
            # Создаем объект сигнала
            signal = Signal(
                sport=match.sport,
                signal=signal_text,
                confidence=prediction['confidence'],
                match_id=match.id,
                published=False,
                created_at=datetime.now()
            )
            
            # Сохраняем в базу данных
            signal_id = await db_manager.add_signal(signal)
            signal.id = signal_id
            
            logger.info(f"💾 Signal saved: {signal_text[:50]}...")
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error creating signal: {e}")
            return None
    
    def format_signal_text(self, match: Match, prediction: Dict[str, Any]) -> str:
        """Форматирование текста сигнала"""
        confidence_percent = int(prediction['confidence'] * 100)
        explanation = prediction.get('explanation', 'Анализ на основе статистики')
        
        if match.sport == "cs2":
            emoji = "🔴"
            sport_name = "CS2"
        elif match.sport == "khl":
            emoji = "🏒"
            sport_name = "КХЛ"
        else:
            emoji = "📊"
            sport_name = match.sport.upper()
        
        # Формируем текст
        text = (
            f"{emoji} {sport_name}: {match.team1} vs {match.team2}\n"
            f"🎯 Прогноз: {prediction['prediction']}\n"
            f"📊 Уверенность: {confidence_percent}%\n"
            f"🧠 Анализ: {explanation}"
        )
        
        # Добавляем турнир если доступен
        if match.features and 'tournament' in match.features:
            tournament = match.features['tournament']
            if tournament != 'Unknown':
                text += f"\n🏆 Турнир: {tournament}"
        
        return text
    
    async def get_today_signals(self) -> List[Signal]:
        """Получить сигналы за сегодня"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Получаем все сигналы
        all_signals = await db_manager.get_signals(limit=100)
        
        # Фильтруем сегодняшние
        today_signals = [
            signal for signal in all_signals
            if signal.created_at and signal.created_at >= today
        ]
        
        return today_signals
    
    async def is_match_in_cooldown(self, match: Match) -> bool:
        """Проверка cooldown для матча"""
        try:
            # Получаем последние сигналы
            recent_signals = await db_manager.get_signals(limit=50)
            
            for signal in recent_signals:
                if signal.match_id == match.id:
                    time_diff = datetime.now() - signal.created_at
                    if time_diff.total_seconds() < (self.signal_cooldown_minutes * 60):
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking cooldown: {e}")
            return False
    
    async def get_high_confidence_signals(self, min_confidence: float = 0.80) -> List[Signal]:
        """Получить сигналы с высокой уверенностью"""
        try:
            all_signals = await db_manager.get_signals(limit=100)
            
            high_confidence_signals = [
                signal for signal in all_signals
                if signal.confidence >= min_confidence
            ]
            
            # Сортируем по уверенности
            high_confidence_signals.sort(key=lambda x: x.confidence, reverse=True)
            
            return high_confidence_signals[:10]  # Возвращаем топ-10
            
        except Exception as e:
            logger.error(f"❌ Error getting high confidence signals: {e}")
            return []
    
    async def get_signal_statistics(self) -> Dict[str, Any]:
        """Получить статистику сигналов"""
        try:
            # Сигналы за последние 7 дней
            week_ago = datetime.now() - timedelta(days=7)
            all_signals = await db_manager.get_signals(limit=500)
            
            week_signals = [
                signal for signal in all_signals
                if signal.created_at and signal.created_at >= week_ago
            ]
            
            # Статистика по видам спорта
            cs2_signals = [s for s in week_signals if s.sport == "cs2"]
            khl_signals = [s for s in week_signals if s.sport == "khl"]
            
            # Средняя уверенность
            avg_confidence = sum(s.confidence for s in week_signals) / len(week_signals) if week_signals else 0
            
            # Опубликованные сигналы
            published_signals = [s for s in week_signals if s.published]
            
            return {
                'total_week_signals': len(week_signals),
                'cs2_signals': len(cs2_signals),
                'khl_signals': len(khl_signals),
                'published_signals': len(published_signals),
                'avg_confidence': round(avg_confidence, 3),
                'high_confidence_signals': len([s for s in week_signals if s.confidence >= 0.80]),
                'last_signal_time': week_signals[0].created_at.isoformat() if week_signals else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting signal statistics: {e}")
            return {}
    
    def get_generator_stats(self) -> Dict[str, Any]:
        """Получить статистику генератора"""
        return {
            'initialized': self._initialized,
            'min_confidence': self.min_confidence,
            'max_signals_per_day': self.max_signals_per_day,
            'signal_cooldown_minutes': self.signal_cooldown_minutes
        }

# Глобальный экземпляр
real_signal_generator = RealSignalGenerator()
