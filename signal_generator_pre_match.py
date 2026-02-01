#!/usr/bin/env python3
"""
AIBET Analytics Platform - Pre-Match Signal Generator
Генерация сигналов только для pre-match матчей
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from ml_models_pre_match import PreMatchMLModels

logger = logging.getLogger(__name__)

class PreMatchSignalGenerator:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.ml_models = PreMatchMLModels(db_manager)
        self.min_confidence = 65  # Минимальная вероятность для pre-match сигнала
        self.max_signals_per_day = 8  # Максимум сигналов в день для pre-match
        
    async def generate_signals(self) -> List[Dict]:
        """Генерация pre-match сигналов"""
        try:
            logger.info("🎯 Starting Pre-Match signal generation")
            
            # Получаем предстоящие pre-match матчи
            upcoming_matches = await self.db_manager.get_upcoming_matches()
            
            if not upcoming_matches:
                logger.info("📊 No upcoming pre-match matches for signal generation")
                return []
            
            # Проверяем лимит сигналов за день
            today_signals = await self._get_today_signals_count()
            if today_signals >= self.max_signals_per_day:
                logger.info(f"📊 Pre-Match signal limit reached: {today_signals}/{self.max_signals_per_day}")
                return []
            
            signals = []
            
            for match in upcoming_matches:
                try:
                    # Пропускаем, если уже есть сигнал на этот матч
                    if await self._signal_exists_for_match(match['id']):
                        continue
                    
                    # Получаем pre-match прогноз
                    prediction = await self.ml_models.predict_match(match, match['sport'])
                    
                    # Проверяем confidence
                    confidence = prediction.get('confidence', 0) * 100  # Конвертация в проценты
                    
                    if confidence >= self.min_confidence:
                        # Создаем pre-match сигнал
                        signal = await self._create_pre_match_signal(match, prediction, confidence)
                        
                        if signal:
                            signals.append(signal)
                            logger.info(f"✅ Pre-Match signal created: {match['team1']} vs {match['team2']} ({confidence:.1f}%)")
                    
                    # Проверяем лимит
                    current_signals = today_signals + len(signals)
                    if current_signals >= self.max_signals_per_day:
                        logger.info(f"📊 Pre-Match signal limit reached: {current_signals}/{self.max_signals_per_day}")
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error processing pre-match match {match['id']}: {e}")
                    continue
            
            logger.info(f"✅ Generated {len(signals)} pre-match signals")
            return signals
            
        except Exception as e:
            logger.error(f"❌ Error in pre-match signal generation: {e}")
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
            logger.error(f"❌ Error counting today pre-match signals: {e}")
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
            logger.error(f"❌ Error checking pre-match signal existence: {e}")
            return False
    
    async def _create_pre_match_signal(self, match: Dict, prediction: Dict, confidence: float) -> Optional[Dict]:
        """Создание pre-match сигнала"""
        try:
            # Определяем рекомендацию
            recommendation = self._generate_pre_match_recommendation(match, prediction, confidence)
            
            # Факты для pre-match сигнала
            facts = self._generate_pre_match_facts(match, prediction)
            
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
                'confidence': self._get_confidence_level(confidence),
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
            logger.error(f"❌ Error creating pre-match signal: {e}")
            return None
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Определить уровень уверенности"""
        if confidence >= 85:
            return "Высокая"
        elif confidence >= 75:
            return "Средняя"
        elif confidence >= 65:
            return "Низкая"
        else:
            return "Очень низкая"
    
    def _generate_pre_match_recommendation(self, match: Dict, prediction: Dict, confidence: float) -> str:
        """Генерация pre-match рекомендации"""
        try:
            sport = match['sport']
            prediction_winner = prediction['prediction']
            method = prediction.get('method', 'unknown')
            
            if sport == 'cs2':
                if confidence >= 85:
                    return f"🔥 СИЛЬНЫЙ СИГНАЛ на {prediction_winner.upper()} - Pre-Match анализ"
                elif confidence >= 75:
                    return f"✅ Pre-Match: Рассмотреть {prediction_winner.upper()}"
                else:
                    return f"⚠️ Pre-Match: {prediction_winner.upper()} с осторожностью"
            
            elif sport == 'khl':
                if confidence >= 85:
                    return f"🏒 СИЛЬНЫЙ Pre-Match сигнал на {prediction_winner.upper()}"
                elif confidence >= 75:
                    return f"✅ Pre-Match: Рассмотреть {prediction_winner.upper()}"
                else:
                    return f"⚠️ Pre-Match: {prediction_winner.upper()} с осторожностью"
            
            return f"📊 Pre-Match анализ показывает преимущество"
            
        except Exception as e:
            logger.error(f"❌ Error generating pre-match recommendation: {e}")
            return "📊 Pre-Match анализ на основе статистики"
    
    def _generate_pre_match_facts(self, match: Dict, prediction: Dict) -> str:
        """Генерация фактов для pre-match сигнала"""
        try:
            facts = []
            
            # Базовые факты
            facts.append(f"🏆 Турнир: {match['tournament']}")
            facts.append(f"📅 Дата матча: {match['date']}")
            facts.append(f"📊 Статус: Pre-Match анализ")
            
            # Факты о прогнозе
            confidence = prediction.get('confidence', 0) * 100
            facts.append(f"🎯 Вероятность: {confidence:.1f}%")
            
            # Метод прогноза
            method = prediction.get('method', 'unknown')
            if method == 'pre_match_ensemble':
                facts.append("🤖 Pre-Match ML ансамбль")
            elif method == 'pre_match_rule_based':
                facts.append("📊 Pre-Match статистический анализ")
            else:
                facts.append("🔬 Комплексный Pre-Match анализ")
            
            # Дополнительные факты
            if match.get('format'):
                facts.append(f"📋 Формат: {match['format']}")
            
            # Аналитические факты
            facts.append("📈 Анализ на основе исторических данных")
            facts.append("⚡ Без live-данных, только pre-match")
            
            return "\n".join(facts)
            
        except Exception as e:
            logger.error(f"❌ Error generating pre-match facts: {e}")
            return "📊 Pre-Match анализ статистических данных"
    
    async def publish_signal_to_channel(self, signal: Dict) -> bool:
        """Публикация pre-match сигнала в Telegram канал"""
        try:
            from telegram_publisher_pre_match import PreMatchTelegramPublisher
            
            publisher = PreMatchTelegramPublisher()
            success = await publisher.publish_signal(signal)
            
            if success:
                # Отмечаем сигнал как опубликованный
                await self.db_manager.mark_signal_published(signal['id'])
                logger.info(f"✅ Pre-Match signal published to channel: {signal['id']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error publishing pre-match signal: {e}")
            return False
    
    async def get_active_signals(self, sport: Optional[str] = None) -> List[Dict]:
        """Получить активные pre-match сигналы"""
        try:
            signals = await self.db_manager.get_signals(sport=sport, published=True)
            
            # Фильтруем только актуальные pre-match сигналы (не старше 48 часов)
            active_signals = []
            now = datetime.now()
            
            for signal in signals:
                signal_time = datetime.fromisoformat(signal['created_at'])
                if (now - signal_time) <= timedelta(hours=48):
                    active_signals.append(signal)
            
            return active_signals
            
        except Exception as e:
            logger.error(f"❌ Error getting active pre-match signals: {e}")
            return []
    
    async def update_signal_results(self):
        """Обновление результатов pre-match сигналов"""
        try:
            # Получаем необработанные сигналы
            signals = await self.db_manager.get_signals(published=True)
            
            for signal in signals:
                try:
                    # Проверяем результат матча
                    match = await self.db_manager.get_matches_by_id(signal['match_id'])
                    
                    if match and match['status'] == 'finished':
                        # Определяем результат сигнала
                        signal_result = self._evaluate_pre_match_signal_result(signal, match)
                        
                        # Обновляем результат
                        await self._save_signal_result(signal['id'], signal_result)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error updating pre-match signal {signal['id']}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"❌ Error updating pre-match signal results: {e}")
    
    def _evaluate_pre_match_signal_result(self, signal: Dict, match: Dict) -> str:
        """Оценка результата pre-match сигнала"""
        try:
            signal_prediction = signal['prediction']
            
            # Определяем победителя матча
            if match.get('final_score'):
                score = match['final_score']
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
            logger.error(f"❌ Error evaluating pre-match signal result: {e}")
            return 'unknown'
    
    async def _save_signal_result(self, signal_id: int, result: str):
        """Сохранение результата сигнала"""
        try:
            # Здесь должна быть логика сохранения результатов
            logger.info(f"📊 Pre-Match Signal {signal_id} result: {result}")
            
        except Exception as e:
            logger.error(f"❌ Error saving pre-match signal result: {e}")
