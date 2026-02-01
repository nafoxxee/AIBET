#!/usr/bin/env python3
"""
AIBET Analytics Platform - Fixed Signal Generator
Генерация сигналов только на основе реальных данных
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from ml_models_fixed import MLModelsFixed

logger = logging.getLogger(__name__)

class SignalGeneratorFixed:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.ml_models = MLModelsFixed(db_manager)
        self.min_confidence = 70  # Минимальная вероятность для сигнала
        self.max_signals_per_day = 10  # Максимум сигналов в день
        
    async def generate_signals(self) -> List[Dict]:
        """Генерация сигналов для предстоящих матчей"""
        try:
            logger.info("🎯 Starting signal generation")
            
            # Получаем предстоящие матчи
            upcoming_matches = await self.db_manager.get_upcoming_matches()
            
            if not upcoming_matches:
                logger.info("📊 No upcoming matches for signal generation")
                return []
            
            # Проверяем лимит сигналов за день
            today_signals = await self._get_today_signals_count()
            if today_signals >= self.max_signals_per_day:
                logger.info(f"📊 Signal limit reached: {today_signals}/{self.max_signals_per_day}")
                return []
            
            signals = []
            
            for match in upcoming_matches:
                try:
                    # Пропускаем, если уже есть сигнал на этот матч
                    if await self._signal_exists_for_match(match['id']):
                        continue
                    
                    # Получаем прогноз
                    prediction = await self.ml_models.predict_match(match, match['sport'])
                    
                    # Проверяем confidence
                    confidence = prediction.get('confidence', 0) * 100  # Конвертация в проценты
                    
                    if confidence >= self.min_confidence:
                        # Создаем сигнал
                        signal = await self._create_signal(match, prediction, confidence)
                        
                        if signal:
                            signals.append(signal)
                            logger.info(f"✅ Signal created: {match['team1']} vs {match['team2']} ({confidence:.1f}%)")
                    
                    # Проверяем лимит
                    current_signals = today_signals + len(signals)
                    if current_signals >= self.max_signals_per_day:
                        logger.info(f"📊 Signal limit reached: {current_signals}/{self.max_signals_per_day}")
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error processing match {match['id']}: {e}")
                    continue
            
            logger.info(f"✅ Generated {len(signals)} signals")
            return signals
            
        except Exception as e:
            logger.error(f"❌ Error in signal generation: {e}")
            return []
    
    async def _get_today_signals_count(self) -> int:
        """Получить количество сигналов за сегодня"""
        try:
            today = datetime.now().date()
            signals = await self.db_manager.get_signals()
            
            today_count = 0
            for signal in signals:
                signal_date = datetime.fromisoformat(signal['created_at']).date()
                if signal_date == today:
                    today_count += 1
            
            return today_count
            
        except Exception as e:
            logger.error(f"❌ Error counting today signals: {e}")
            return 0
    
    async def _signal_exists_for_match(self, match_id: int) -> bool:
        """Проверить, существует ли сигнал для матча"""
        try:
            signals = await self.db_manager.get_signals()
            
            for signal in signals:
                if signal['match_id'] == match_id:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking signal existence: {e}")
            return False
    
    async def _create_signal(self, match: Dict, prediction: Dict, confidence: float) -> Optional[Dict]:
        """Создание сигнала"""
        try:
            # Определяем рекомендацию
            recommendation = self._generate_recommendation(match, prediction, confidence)
            
            # Факты для сигнала
            facts = self._generate_facts(match, prediction)
            
            # Создаем сигнал
            signal_data = {
                'match_id': match['id'],
                'sport': match['sport'],
                'team1': match['team1'],
                'team2': match['team2'],
                'tournament': match['tournament'],
                'date': match['date'],
                'prediction': prediction['prediction'],
                'probability': confidence,
                'facts': facts,
                'recommendation': recommendation
            }
            
            # Сохраняем в базу
            signal_id = await self.db_manager.add_signal(signal_data)
            
            if signal_id > 0:
                signal_data['id'] = signal_id
                return signal_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error creating signal: {e}")
            return None
    
    def _generate_recommendation(self, match: Dict, prediction: Dict, confidence: float) -> str:
        """Генерация рекомендации"""
        try:
            sport = match['sport']
            prediction_winner = prediction['prediction']
            
            if sport == 'cs2':
                if confidence >= 85:
                    return f"🔥 СТАВКА НА {prediction_winner.upper()} - Высокая уверенность"
                elif confidence >= 75:
                    return f"✅ Рассмотреть ставку на {prediction_winner.upper()}"
                else:
                    return f"⚠️ {prediction_winner.upper()} с осторожностью"
            
            elif sport == 'khl':
                if confidence >= 85:
                    return f"🏒 СТАВКА НА {prediction_winner.upper()} - Высокая уверенность"
                elif confidence >= 75:
                    return f"✅ Рассмотреть ставку на {prediction_winner.upper()}"
                else:
                    return f"⚠️ {prediction_winner.upper()} с осторожностью"
            
            return "📊 Анализ показывает преимущество"
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendation: {e}")
            return "📊 Прогноз на основе анализа"
    
    def _generate_facts(self, match: Dict, prediction: Dict) -> str:
        """Генерация фактов для сигнала"""
        try:
            facts = []
            
            # Базовые факты
            facts.append(f"🏆 Турнир: {match['tournament']}")
            facts.append(f"📅 Дата: {match['date']}")
            
            # Факты о прогнозе
            confidence = prediction.get('confidence', 0) * 100
            facts.append(f"🎯 Вероятность: {confidence:.1f}%")
            
            # Метод прогноза
            method = prediction.get('method', 'unknown')
            if method == 'ensemble':
                facts.append("🤖 Прогноз на основе ML ансамбля")
            elif method == 'rule_based':
                facts.append("📊 Прогноз на основе статистики")
            else:
                facts.append("🔬 Комплексный анализ")
            
            # Дополнительные факты
            if match.get('format'):
                facts.append(f"📋 Формат: {match['format']}")
            
            return "\n".join(facts)
            
        except Exception as e:
            logger.error(f"❌ Error generating facts: {e}")
            return "📊 Анализ статистических данных"
    
    async def publish_signal_to_channel(self, signal: Dict) -> bool:
        """Публикация сигнала в Telegram канал"""
        try:
            from telegram_publisher_fixed import TelegramPublisherFixed
            
            publisher = TelegramPublisherFixed()
            success = await publisher.publish_signal(signal)
            
            if success:
                # Отмечаем сигнал как опубликованный
                await self.db_manager.mark_signal_published(signal['id'])
                logger.info(f"✅ Signal published to channel: {signal['id']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error publishing signal: {e}")
            return False
    
    async def get_active_signals(self, sport: Optional[str] = None) -> List[Dict]:
        """Получить активные сигналы"""
        try:
            signals = await self.db_manager.get_signals(sport=sport, published=True)
            
            # Фильтруем только актуальные сигналы (не старше 24 часов)
            active_signals = []
            now = datetime.now()
            
            for signal in signals:
                signal_time = datetime.fromisoformat(signal['created_at'])
                if (now - signal_time) <= timedelta(hours=24):
                    active_signals.append(signal)
            
            return active_signals
            
        except Exception as e:
            logger.error(f"❌ Error getting active signals: {e}")
            return []
    
    async def update_signal_results(self):
        """Обновление результатов сигналов"""
        try:
            # Получаем необработанные сигналы
            signals = await self.db_manager.get_signals(published=True)
            
            for signal in signals:
                try:
                    # Проверяем результат матча
                    match = await self.db_manager.get_matches_by_id(signal['match_id'])
                    
                    if match and match['status'] == 'finished':
                        # Определяем результат сигнала
                        signal_result = self._evaluate_signal_result(signal, match)
                        
                        # Обновляем результат
                        await self._save_signal_result(signal['id'], signal_result)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error updating signal {signal['id']}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error updating signal results: {e}")
    
    def _evaluate_signal_result(self, signal: Dict, match: Dict) -> str:
        """Оценка результата сигнала"""
        try:
            signal_prediction = signal['prediction']
            
            # Определяем победителя матча
            if match.get('score'):
                score = match['score']
                if ':' in score:
                    scores = score.split(':')
                    if len(scores) == 2:
                        team1_score = int(scores[0].strip())
                        team2_score = int(scores[1].strip())
                        
                        if team1_score > team2_score:
                            actual_winner = 'team1'
                        elif team2_score > team1_score:
                            actual_winner = 'team2'
                        else:
                            actual_winner = 'draw'
                        
                        # Сравниваем с прогнозом
                        if signal_prediction == actual_winner:
                            return 'win'
                        else:
                            return 'loss'
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"❌ Error evaluating signal result: {e}")
            return 'unknown'
    
    async def _save_signal_result(self, signal_id: int, result: str):
        """Сохранение результата сигнала"""
        try:
            # Здесь должна быть логика сохранения результатов
            # В текущей структуре БД нет таблицы для результатов сигналов
            logger.info(f"📊 Signal {signal_id} result: {result}")
            
        except Exception as e:
            logger.error(f"❌ Error saving signal result: {e}")
