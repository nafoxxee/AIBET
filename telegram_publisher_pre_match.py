#!/usr/bin/env python3
"""
AIBET Analytics Platform - Pre-Match Telegram Publisher
Публикация pre-match сигналов в каналы
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Optional
from aiogram import Bot
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)

class PreMatchTelegramPublisher:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.cs2_channel = os.getenv("CS2_CHANNEL", "@aibetcsgo")
        self.khl_channel = os.getenv("KHL_CHANNEL", "@aibetkhl")
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found")
        
        self.bot = Bot(token=self.bot_token, parse_mode=ParseMode.HTML)
        
        logger.info(f"✅ Pre-Match Telegram Publisher initialized")
        logger.info(f"📢 CS2 Channel: {self.cs2_channel}")
        logger.info(f"📢 KHL Channel: {self.khl_channel}")
    
    async def publish_signal(self, signal: Dict) -> bool:
        """Публикация pre-match сигнала в соответствующий канал"""
        try:
            sport = signal['sport']
            
            if sport == 'cs2':
                return await self._publish_to_cs2_channel(signal)
            elif sport == 'khl':
                return await self._publish_to_khl_channel(signal)
            else:
                logger.warning(f"⚠️ Unknown sport: {sport}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error publishing pre-match signal: {e}")
            return False
    
    async def _publish_to_cs2_channel(self, signal: Dict) -> bool:
        """Публикация в CS2 канал"""
        try:
            message = self._format_cs2_pre_match_signal(signal)
            
            await self.bot.send_message(
                chat_id=self.cs2_channel,
                text=message,
                disable_web_page_preview=True
            )
            
            logger.info(f"✅ Published CS2 Pre-Match signal to {self.cs2_channel}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error publishing to CS2 channel: {e}")
            return False
    
    async def _publish_to_khl_channel(self, signal: Dict) -> bool:
        """Публикация в КХЛ канал"""
        try:
            message = self._format_khl_pre_match_signal(signal)
            
            await self.bot.send_message(
                chat_id=self.khl_channel,
                text=message,
                disable_web_page_preview=True
            )
            
            logger.info(f"✅ Published KHL Pre-Match signal to {self.khl_channel}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error publishing to KHL channel: {e}")
            return False
    
    def _format_cs2_pre_match_signal(self, signal: Dict) -> str:
        """Форматирование pre-match сигнала для CS2"""
        try:
            confidence = signal['probability']
            confidence_level = signal.get('confidence', 'Средняя')
            
            # Эмодзи в зависимости от уровня уверенности
            if confidence >= 85:
                prediction_emoji = "🔥"
            elif confidence >= 75:
                prediction_emoji = "✅"
            else:
                prediction_emoji = "⚠️"
            
            message = f"""
🔫 <b>AIBET CS2 PRE-MATCH СИГНАЛ</b> {prediction_emoji}

🎯 <b>{signal['team1']}</b> vs <b>{signal['team2']}</b>
🏆 {signal['tournament']}
📅 {signal['date']}

🎯 <b>Прогноз:</b> {signal['prediction'].upper()}
📊 <b>Вероятность:</b> {confidence:.1f}% ({confidence_level})
📈 <b>Анализ:</b> Pre-Match

💡 <b>Рекомендация:</b>
{signal['recommendation']}

📋 <b>Факты:</b>
{signal['facts']}

⚠️ <i>Pre-Match анализ. Ставьте ответственно.</i>
#AIBET #CS2 #PreMatch #Аналитика
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error formatting CS2 pre-match signal: {e}")
            return "📊 CS2 Pre-Match сигнал (ошибка форматирования)"
    
    def _format_khl_pre_match_signal(self, signal: Dict) -> str:
        """Форматирование pre-match сигнала для КХЛ"""
        try:
            confidence = signal['probability']
            confidence_level = signal.get('confidence', 'Средняя')
            
            # Эмодзи в зависимости от уровня уверенности
            if confidence >= 85:
                prediction_emoji = "🏒"
            elif confidence >= 75:
                prediction_emoji = "✅"
            else:
                prediction_emoji = "⚠️"
            
            message = f"""
🏒 <b>AIBET КХЛ PRE-MATCH СИГНАЛ</b> {prediction_emoji}

🎯 <b>{signal['team1']}</b> vs <b>{signal['team2']}</b>
🏆 {signal['tournament']}
📅 {signal['date']}

🎯 <b>Прогноз:</b> {signal['prediction'].upper()}
📊 <b>Вероятность:</b> {confidence:.1f}% ({confidence_level})
📈 <b>Анализ:</b> Pre-Match

💡 <b>Рекомендация:</b>
{signal['recommendation']}

📋 <b>Факты:</b>
{signal['facts']}

⚠️ <i>Pre-Match анализ. Ставьте ответственно.</i>
#AIBET #КХЛ #PreMatch #Аналитика
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error formatting KHL pre-match signal: {e}")
            return "📊 КХЛ Pre-Match сигнал (ошибка форматирования)"
    
    async def publish_daily_summary(self) -> bool:
        """Публикация дневного pre-match дайджеста"""
        try:
            # Получаем статистику за день
            from signal_generator_pre_match import PreMatchSignalGenerator
            from database_pre_match import pre_match_db
            
            db = pre_match_db
            await db.initialize()
            
            signal_gen = PreMatchSignalGenerator(db)
            active_signals = await signal_gen.get_active_signals()
            
            if not active_signals:
                return True  # Нечего публиковать
            
            # Группируем по видам спорта
            cs2_signals = [s for s in active_signals if s['sport'] == 'cs2']
            khl_signals = [s for s in active_signals if s['sport'] == 'khl']
            
            # Формируем сообщение
            message = f"""
📊 <b>AIBET PRE-MATCH ДНЕВНОЙ ДАЙДЖЕСТ</b>
📅 {datetime.now().strftime('%d.%m.%Y')}

🔫 <b>CS2 Pre-Match сигналы:</b> {len(cs2_signals)}
🏒 <b>КХЛ Pre-Match сигналы:</b> {len(khl_signals)}
📈 <b>Всего сигналов:</b> {len(active_signals)}

🎯 <b>Топ Pre-Match сигналы дня:</b>
"""
            
            # Добавляем топ сигналы
            top_signals = sorted(active_signals, key=lambda x: x['probability'], reverse=True)[:3]
            
            for i, signal in enumerate(top_signals, 1):
                sport_emoji = "🔫" if signal['sport'] == 'cs2' else "🏒"
                confidence_level = signal.get('confidence', 'Средняя')
                message += f"\n{i}. {sport_emoji} {signal['team1']} vs {signal['team2']} - {signal['probability']:.1f}% ({confidence_level})"
            
            message += "\n\n📢 Подписывайтесь на каналы:\n@aibetcsgo | @aibetkhl"
            message += "\n\n📈 <i>Pre-Match анализ без live данных</i>"
            
            # Публикуем в оба канала
            await self.bot.send_message(
                chat_id=self.cs2_channel,
                text=message,
                disable_web_page_preview=True
            )
            
            if khl_signals:  # Публикуем в КХЛ канал только если есть сигналы
                await self.bot.send_message(
                    chat_id=self.khl_channel,
                    text=message,
                    disable_web_page_preview=True
                )
            
            logger.info("✅ Pre-Match daily summary published")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error publishing pre-match daily summary: {e}")
            return False
    
    async def publish_system_status(self, status: str) -> bool:
        """Публикация статуса pre-match системы"""
        try:
            message = f"""
🔧 <b>AIBET PRE-MATCH СТАТУС СИСТЕМЫ</b>

📊 {status}
📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}

🤖 Pre-Match система работает в штатном режиме
📡 Pre-Match парсеры активны
🎯 ML модели обучены на исторических данных
📢 Pre-Match сигналы генерируются
📈 Анализ только предстоящих матчей

⚡ <i>Режим: Pre-Match (без live данных)</i>
            """.strip()
            
            # Публикуем только в CS2 канал (основной)
            await self.bot.send_message(
                chat_id=self.cs2_channel,
                text=message,
                disable_web_page_preview=True
            )
            
            logger.info("✅ Pre-Match system status published")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error publishing pre-match system status: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Тест подключения к Telegram"""
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Pre-Match Bot connected: @{bot_info.username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pre-Match Bot connection failed: {e}")
            return False

# Глобальный экземпляр
_pre_match_telegram_publisher = None

def get_pre_match_telegram_publisher() -> PreMatchTelegramPublisher:
    """Получить глобальный экземпляр pre-match publisher"""
    global _pre_match_telegram_publisher
    if _pre_match_telegram_publisher is None:
        _pre_match_telegram_publisher = PreMatchTelegramPublisher()
    return _pre_match_telegram_publisher

async def create_pre_match_telegram_publisher() -> PreMatchTelegramPublisher:
    """Создание экземпляра pre-match publisher"""
    return PreMatchTelegramPublisher()
