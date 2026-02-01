#!/usr/bin/env python3
"""
AIBET Analytics Platform - Signal Generator
Генерация сигналов с confidence ≥ 0.70 и автоматическая публикация
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

from database import Signal, db_manager
from ml_models import ml_models

logger = logging.getLogger(__name__)

class SignalGenerator:
    def __init__(self):
        self.min_confidence = 0.70
        self.max_signals_per_day = 10
        self.signal_cooldown_minutes = 30
        self._initialized = False
    
    async def initialize(self):
        """Инициализация генератора сигналов"""
        if self._initialized:
            return
            
        logger.info("🎯 Initializing Signal Generator")
        
        # Убеждаемся, что ML модели инициализированы
        await ml_models.initialize()
        
        self._initialized = True
        logger.info("✅ Signal Generator initialized successfully")
    
    async def generate_daily_signals(self) -> List[Signal]:
        """Генерация дневных сигналов"""
        if not self._initialized:
            await self.initialize()
        
        logger.info("🎯 Generating daily signals")
        
        try:
            # Проверяем лимит сигналов за сегодня
            today_signals = await self.get_today_signals()
            if len(today_signals) >= self.max_signals_per_day:
                logger.info(f"⚠️ Already generated {len(today_signals)} signals today (max: {self.max_signals_per_day})")
                return []
            
            # Получаем live и upcoming матчи
            live_matches = await db_manager.get_matches(status="live", limit=20)
            upcoming_matches = await db_manager.get_matches(status="upcoming", limit=20)
            
            all_matches = live_matches + upcoming_matches
            logger.info(f"📊 Analyzing {len(live_matches)} live and {len(upcoming_matches)} upcoming matches")
            
            generated_signals = []
            
            for match in all_matches:
                try:
                    # Проверяем cooldown для этого матча
                    if await self.is_match_in_cooldown(match):
                        continue
                    
                    # Получаем предсказание от ML моделей
                    prediction = await ml_models.predict_match(match)
                    
                    if not prediction or prediction['confidence'] < self.min_confidence:
                        logger.debug(f"⚠️ Low confidence ({prediction.get('confidence', 0):.2f}) for {match.team1} vs {match.team2}")
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
            logger.exception(f"❌ Error generating daily signals: {e}")
            return []
    
    async def create_signal(self, match, prediction) -> Optional[Signal]:
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
            logger.exception(f"❌ Error creating signal: {e}")
            return None
    
    def format_signal_text(self, match, prediction) -> str:
        """Форматирование текста сигнала"""
        confidence_percent = int(prediction['confidence'] * 100)
        
        if match.sport == "cs2":
            return f"🔴 CS2: {match.team1} vs {match.team2}\\n🎯 Прогноз: {prediction['prediction']}\\n📊 Уверенность: {confidence_percent}%\\n🏆 {match.features.get('tournament', 'Unknown')}"
        elif match.sport == "khl":
            return f"🏒 КХЛ: {match.team1} vs {match.team2}\\n🎯 Прогноз: {prediction['prediction']}\\n📊 Уверенность: {confidence_percent}%\\n🏆 {match.features.get('tournament', 'Unknown')}"
        else:
            return f"📊 {match.sport.upper()}: {match.team1} vs {match.team2}\\n🎯 Прогноз: {prediction['prediction']}\\n📊 Уверенность: {confidence_percent}%"
    
    async def get_today_signals(self) -> List[Signal]:
        """Получить сигналы за сегодня"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Получаем все сигналы
        all_signals = await db_manager.get_signals(limit=1000)
        
        # Фильтруем сегодняшние
        today_signals = [
            signal for signal in all_signals
            if signal.created_at and signal.created_at >= today
        ]
        
        return today_signals
    
    async def is_match_in_cooldown(self, match) -> bool:
        """Проверка cooldown для матча"""
        try:
            # Получаем последние сигналы для этого матча
            recent_signals = await db_manager.get_signals(limit=100)
            
            for signal in recent_signals:
                if signal.match_id == match.id:
                    time_diff = datetime.now() - signal.created_at
                    if time_diff.total_seconds() < (self.signal_cooldown_minutes * 60):
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking cooldown: {e}")
            return False
    
    async def analyze_live_matches(self) -> List[Signal]:
        """Анализ live матчей для генерации срочных сигналов"""
        logger.info("🔴 Analyzing live matches for urgent signals")
        
        try:
            # Получаем только live матчи
            live_matches = await db_manager.get_matches(status="live", limit=10)
            
            urgent_signals = []
            
            for match in live_matches:
                try:
                    # Для live матчей используем более низкий порог
                    prediction = await ml_models.predict_match(match)
                    
                    if not prediction or prediction['confidence'] < 0.65:  # Более низкий порог для live
                        continue
                    
                    # Проверяем cooldown
                    if await self.is_match_in_cooldown(match):
                        continue
                    
                    # Создаем срочный сигнал
                    signal = await self.create_signal(match, prediction)
                    if signal:
                        urgent_signals.append(signal)
                        logger.info(f"🚨 URGENT signal for live {match.sport}: {match.team1} vs {match.team2}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Error analyzing live match {match.team1} vs {match.team2}: {e}")
                    continue
            
            return urgent_signals
            
        except Exception as e:
            logger.exception(f"❌ Error analyzing live matches: {e}")
            return []
    
    async def get_signal_statistics(self) -> Dict:
        """Получить статистику сигналов"""
        try:
            all_signals = await db_manager.get_signals(limit=1000)
            
            total_signals = len(all_signals)
            published_signals = len([s for s in all_signals if s.published])
            
            # Статистика по видам спорта
            cs2_signals = len([s for s in all_signals if s.sport == "cs2"])
            khl_signals = len([s for s in all_signals if s.sport == "khl"])
            
            # Средняя уверенность
            avg_confidence = sum(s.confidence for s in all_signals) / len(all_signals) if all_signals else 0
            
            # Сигналы за сегодня
            today_signals = await self.get_today_signals()
            
            return {
                "total_signals": total_signals,
                "published_signals": published_signals,
                "cs2_signals": cs2_signals,
                "khl_signals": khl_signals,
                "avg_confidence": avg_confidence,
                "today_signals": len(today_signals),
                "success_rate": published_signals / total_signals if total_signals > 0 else 0
            }
            
        except Exception as e:
            logger.exception(f"❌ Error getting signal statistics: {e}")
            return {}
    
    def set_confidence_threshold(self, threshold: float):
        """Установить порог уверенности"""
        if 0.5 <= threshold <= 1.0:
            self.min_confidence = threshold
            logger.info(f"🎯 Confidence threshold set to {threshold}")
        else:
            logger.warning(f"⚠️ Invalid confidence threshold: {threshold}")

# Глобальный экземпляр
signal_generator = SignalGenerator()
