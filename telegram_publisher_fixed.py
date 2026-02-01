#!/usr/bin/env python3
"""
AIBET Analytics Platform - Fixed Telegram Publisher
Публикация сигналов в каналы
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Optional
from aiogram import Bot
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)

class TelegramPublisherFixed:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.cs2_channel = os.getenv("CS2_CHANNEL", "@aibetcsgo")
        self.khl_channel = os.getenv("KHL_CHANNEL", "@aibetkhl")
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found")
        
        self.bot = Bot(token=self.bot_token, parse_mode=ParseMode.HTML)
        
        logger.info(f"✅ Telegram Publisher initialized")
        logger.info(f"📢 CS2 Channel: {self.cs2_channel}")
        logger.info(f"📢 KHL Channel: {self.khl_channel}")
    
    async def publish_signal(self, signal: Dict) -> bool:
        """Публикация сигнала в соответствующий канал"""
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
            logger.error(f"❌ Error publishing signal: {e}")
            return False
    
    async def _publish_to_cs2_channel(self, signal: Dict) -> bool:
        """Публикация в CS2 канал"""
        try:
            message = self._format_cs2_signal(signal)
            
            await self.bot.send_message(
                chat_id=self.cs2_channel,
                text=message,
                disable_web_page_preview=True
            )
            
            logger.info(f"✅ Published CS2 signal to {self.cs2_channel}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error publishing to CS2 channel: {e}")
            return False
    
    async def _publish_to_khl_channel(self, signal: Dict) -> bool:
        """Публикация в КХЛ канал"""
        try:
            message = self._format_khl_signal(signal)
            
            await self.bot.send_message(
                chat_id=self.khl_channel,
                text=message,
                disable_web_page_preview=True
            )
            
            logger.info(f"✅ Published KHL signal to {self.khl_channel}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error publishing to KHL channel: {e}")
            return False
    
    def _format_cs2_signal(self, signal: Dict) -> str:
        """Форматирование сигнала для CS2"""
        try:
            confidence = signal['probability']
            prediction_emoji = "🔥" if confidence >= 85 else "✅" if confidence >= 75 else "⚠️"
            
            message = f"""
🔫 <b>AIBET CS2 СИГНАЛ</b> {prediction_emoji}

🎯 <b>{signal['team1']}</b> vs <b>{signal['team2']}</b>
🏆 {signal['tournament']}
📅 {signal['date']}

🎯 <b>Прогноз:</b> {signal['prediction'].upper()}
📊 <b>Вероятность:</b> {confidence:.1f}%

💡 <b>Рекомендация:</b>
{signal['recommendation']}

📋 <b>Факты:</b>
{signal['facts']}

⚠️ <i>Ставьте ответственно. Это аналитика, не гарантия.</i>
#AIBET #CS2 #Аналитика
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error formatting CS2 signal: {e}")
            return "📊 CS2 сигнал (ошибка форматирования)"
    
    def _format_khl_signal(self, signal: Dict) -> str:
        """Форматирование сигнала для КХЛ"""
        try:
            confidence = signal['probability']
            prediction_emoji = "🏒" if confidence >= 85 else "✅" if confidence >= 75 else "⚠️"
            
            message = f"""
🏒 <b>AIBET КХЛ СИГНАЛ</b> {prediction_emoji}

🎯 <b>{signal['team1']}</b> vs <b>{signal['team2']}</b>
🏆 {signal['tournament']}
📅 {signal['date']}

🎯 <b>Прогноз:</b> {signal['prediction'].upper()}
📊 <b>Вероятность:</b> {confidence:.1f}%

💡 <b>Рекомендация:</b>
{signal['recommendation']}

📋 <b>Факты:</b>
{signal['facts']}

⚠️ <i>Ставьте ответственно. Это аналитика, не гарантия.</i>
#AIBET #КХЛ #Аналитика
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error formatting KHL signal: {e}")
            return "📊 КХЛ сигнал (ошибка форматирования)"
    
    async def publish_daily_summary(self) -> bool:
        """Публикация дневного дайджеста"""
        try:
            # Получаем статистику за день
            from signal_generator_fixed import SignalGeneratorFixed
            from database_fixed import DatabaseManager
            
            db = DatabaseManager()
            await db.initialize()
            
            signal_gen = SignalGeneratorFixed(db)
            active_signals = await signal_gen.get_active_signals()
            
            if not active_signals:
                return True  # Нечего публиковать
            
            # Группируем по видам спорта
            cs2_signals = [s for s in active_signals if s['sport'] == 'cs2']
            khl_signals = [s for s in active_signals if s['sport'] == 'khl']
            
            # Формируем сообщение
            message = f"""
📊 <b>AIBET ДНЕВНОЙ ДАЙДЖЕСТ</b>
📅 {datetime.now().strftime('%d.%m.%Y')}

🔫 <b>CS2 сигналы:</b> {len(cs2_signals)}
🏒 <b>КХЛ сигналы:</b> {len(khl_signals)}
📈 <b>Всего сигналов:</b> {len(active_signals)}

🎯 <b>Топ сигналы дня:</b>
"""
            
            # Добавляем топ сигналы
            top_signals = sorted(active_signals, key=lambda x: x['probability'], reverse=True)[:3]
            
            for i, signal in enumerate(top_signals, 1):
                sport_emoji = "🔫" if signal['sport'] == 'cs2' else "🏒"
                message += f"\n{i}. {sport_emoji} {signal['team1']} vs {signal['team2']} - {signal['probability']:.1f}%"
            
            message += "\n\n📢 Подписывайтесь на каналы:\n@aibetcsgo | @aibetkhl"
            
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
            
            logger.info("✅ Daily summary published")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error publishing daily summary: {e}")
            return False
    
    async def publish_system_status(self, status: str) -> bool:
        """Публикация статуса системы"""
        try:
            message = f"""
🔧 <b>AIBET СТАТУС СИСТЕМЫ</b>

📊 {status}
📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}

🤖 Система работает в штатном режиме
📡 Парсеры активны
🎯 ML модели обучены
📢 Сигналы генерируются
            """.strip()
            
            # Публикуем только в CS2 канал (основной)
            await self.bot.send_message(
                chat_id=self.cs2_channel,
                text=message,
                disable_web_page_preview=True
            )
            
            logger.info("✅ System status published")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error publishing system status: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Тест подключения к Telegram"""
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Bot connected: @{bot_info.username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Bot connection failed: {e}")
            return False

# Глобальный экземпляр
_telegram_publisher = None

def get_telegram_publisher() -> TelegramPublisherFixed:
    """Получить глобальный экземпляр publisher"""
    global _telegram_publisher
    if _telegram_publisher is None:
        _telegram_publisher = TelegramPublisherFixed()
    return _telegram_publisher

async def create_telegram_publisher() -> TelegramPublisherFixed:
    """Создание экземпляра publisher"""
    return TelegramPublisherFixed()
