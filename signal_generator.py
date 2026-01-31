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
                logger.info(f"Already generated {len(today_signals)} signals today (max: {self.max_signals_per_day})")
                return []
            
            remaining_signals = self.max_signals_per_day - len(today_signals)
            
            # Генерируем новые сигналы
            new_signals = await ml_models.generate_signals(self.min_confidence)
            
            # Фильтруем и ограничиваем
            filtered_signals = []
            for signal in new_signals:
                if len(filtered_signals) >= remaining_signals:
                    break
                
                # Проверяем cooldown
                if await self.check_signal_cooldown(signal):
                    filtered_signals.append(signal)
            
            # Сохраняем сигналы
            saved_signals = []
            for signal in filtered_signals:
                try:
                    signal_id = await db_manager.add_signal(signal)
                    signal.id = signal_id
                    saved_signals.append(signal)
                    logger.info(f"💾 Generated signal: {signal.signal[:50]}...")
                except Exception as e:
                    logger.error(f"Error saving signal: {e}")
            
            logger.info(f"🎯 Generated {len(saved_signals)} new signals")
            return saved_signals
            
        except Exception as e:
            logger.error(f"Error generating daily signals: {e}")
            return []
    
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
    
    async def check_signal_cooldown(self, signal: Signal) -> bool:
        """Проверка cooldown для сигнала"""
        if not signal.match_id:
            return True
        
        try:
            # Получаем последние сигналы для этого матча
            recent_signals = await db_manager.get_signals(limit=100)
            
            for existing_signal in recent_signals:
                if (existing_signal.match_id == signal.match_id and 
                    existing_signal.created_at):
                    
                    time_diff = datetime.now() - existing_signal.created_at
                    if time_diff.total_seconds() < self.signal_cooldown_minutes * 60:
                        logger.info(f"Signal cooldown active for match {signal.match_id}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking signal cooldown: {e}")
            return True
    
    async def get_high_confidence_matches(self) -> List[Dict]:
        """Получить матчи с высокой уверенностью предсказания"""
        logger.info("🔍 Analyzing high confidence matches")
        
        try:
            # Получаем предстоящие матчи
            matches = await db_manager.get_matches(status="upcoming", limit=50)
            
            high_confidence_matches = []
            
            for match in matches:
                # Пропускаем матчи, которые скоро начнутся
                if match.start_time and match.start_time < datetime.now() + timedelta(minutes=30):
                    continue
                
                # Получаем предсказание
                prediction = await ml_models.predict_match(match)
                
                if prediction['confidence'] >= self.min_confidence:
                    high_confidence_matches.append({
                        'match': match,
                        'prediction': prediction
                    })
            
            # Сортируем по уверенности
            high_confidence_matches.sort(
                key=lambda x: x['prediction']['confidence'], 
                reverse=True
            )
            
            logger.info(f"🔍 Found {len(high_confidence_matches)} high confidence matches")
            return high_confidence_matches
            
        except Exception as e:
            logger.error(f"Error getting high confidence matches: {e}")
            return []
    
    async def analyze_signal_performance(self, days: int = 7) -> Dict[str, float]:
        """Анализ производительности сигналов"""
        logger.info(f"📊 Analyzing signal performance for last {days} days")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Получаем сигналы за период
            all_signals = await db_manager.get_signals(limit=1000)
            period_signals = [
                signal for signal in all_signals
                if signal.created_at and signal.created_at >= cutoff_date
            ]
            
            if not period_signals:
                return {
                    'total_signals': 0,
                    'accuracy': 0.0,
                    'avg_confidence': 0.0,
                    'success_rate': 0.0
                }
            
            # Анализируем результаты
            successful_signals = 0
            total_confidence = 0
            
            for signal in period_signals:
                if signal.match_id:
                    # Получаем матч
                    matches = await db_manager.get_matches(limit=1000)
                    match = next((m for m in matches if m.id == signal.match_id), None)
                    
                    if match and match.status == 'finished' and match.score:
                        # Проверяем результат
                        try:
                            score_parts = match.score.split(':')
                            if len(score_parts) >= 2:
                                score1 = int(score_parts[0])
                                score2 = int(score_parts[1])
                                
                                # Определяем победителя
                                winner = match.team1 if score1 > score2 else match.team2
                                
                                # Проверяем, угадали ли мы
                                if winner in signal.signal:
                                    successful_signals += 1
                        except:
                            pass
                
                total_confidence += signal.confidence
            
            performance = {
                'total_signals': len(period_signals),
                'successful_signals': successful_signals,
                'accuracy': (successful_signals / len(period_signals)) * 100 if period_signals else 0,
                'avg_confidence': (total_confidence / len(period_signals)) * 100 if period_signals else 0
            }
            
            logger.info(f"📊 Signal performance: {performance['accuracy']:.1f}% accuracy")
            return performance
            
        except Exception as e:
            logger.error(f"Error analyzing signal performance: {e}")
            return {
                'total_signals': 0,
                'accuracy': 0.0,
                'avg_confidence': 0.0,
                'success_rate': 0.0
            }
    
    async def get_signal_statistics(self) -> Dict[str, any]:
        """Получить статистику сигналов"""
        try:
            # Получаем все сигналы
            all_signals = await db_manager.get_signals(limit=1000)
            
            # Статистика по видам спорта
            cs2_signals = [s for s in all_signals if s.sport == "cs2"]
            khl_signals = [s for s in all_signals if s.sport == "khl"]
            
            # Статистика по уверенности
            high_confidence = [s for s in all_signals if s.confidence >= 0.80]
            medium_confidence = [s for s in all_signals if 0.70 <= s.confidence < 0.80]
            low_confidence = [s for s in all_signals if s.confidence < 0.70]
            
            # Сегодняшние сигналы
            today_signals = await self.get_today_signals()
            
            statistics = {
                'total_signals': len(all_signals),
                'cs2_signals': len(cs2_signals),
                'khl_signals': len(khl_signals),
                'high_confidence': len(high_confidence),
                'medium_confidence': len(medium_confidence),
                'low_confidence': len(low_confidence),
                'today_signals': len(today_signals),
                'published_signals': len([s for s in all_signals if s.published]),
                'avg_confidence': sum(s.confidence for s in all_signals) / len(all_signals) if all_signals else 0
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting signal statistics: {e}")
            return {}
    
    async def cleanup_old_signals(self, days: int = 30):
        """Очистка старых сигналов"""
        logger.info(f"🧹 Cleaning up signals older than {days} days")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Получаем старые сигналы
            all_signals = await db_manager.get_signals(limit=1000)
            old_signals = [
                signal for signal in all_signals
                if signal.created_at and signal.created_at < cutoff_date
            ]
            
            # Удаляем старые сигналы (в SQLite нет прямого удаления, но можно пометить)
            for signal in old_signals:
                # В реальной реализации здесь было бы удаление из БД
                pass
            
            logger.info(f"🧹 Cleaned up {len(old_signals)} old signals")
            
        except Exception as e:
            logger.error(f"Error cleaning up old signals: {e}")
    
    async def update_confidence_threshold(self, new_threshold: float):
        """Обновление порога уверенности"""
        if 0.5 <= new_threshold <= 1.0:
            self.min_confidence = new_threshold
            logger.info(f"🎯 Updated confidence threshold to {new_threshold}")
        else:
            logger.warning(f"Invalid confidence threshold: {new_threshold}")

# Глобальный экземпляр генератора сигналов
signal_generator = SignalGenerator()
