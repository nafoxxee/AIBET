#!/usr/bin/env python3
"""
AIBET Analytics Platform - Telegram Publisher
Автоматическая публикация сигналов в Telegram каналы
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

from aiogram import Bot, Dispatcher, types
from database import Signal, db_manager
from signal_generator import signal_generator

logger = logging.getLogger(__name__)

class TelegramPublisher:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.bot = None
        self.cs2_channel = "@aibetcsgo"
        self.khl_channel = "@aibetkhl"
        self.publish_cooldown_minutes = 60
        self._initialized = False
    
    async def initialize(self):
        """Инициализация Telegram Publisher"""
        if self._initialized:
            return
            
        logger.info("📱 Initializing Telegram Publisher")
        
        # Проверяем токен ДО создания бота
        if not self.bot_token or not isinstance(self.bot_token, str):
            logger.warning("Telegram publisher disabled: token missing or invalid")
            self._initialized = True  # Помечаем как инициализированный, но отключенный
            return
        
        try:
            # Инициализируем бот
            self.bot = Bot(token=self.bot_token)
            
            # Проверяем соединение
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Connected to bot: @{bot_info.username}")
            
            self._initialized = True
            logger.info("✅ Telegram Publisher initialized successfully")
            
        except Exception as e:
            logger.warning(f"Telegram publisher disabled: {e}")
            self._initialized = True  # Помечаем как инициализированный, но отключенный
    
    async def publish_signal(self, signal: Signal) -> bool:
        """Публикация сигнала в соответствующий канал"""
        if not self._initialized:
            await self.initialize()
        
        # Проверяем, что бот доступен
        if not self.bot:
            logger.warning("Cannot publish signal: bot not available")
            return False
        
        try:
            # Определяем канал
            channel = self.cs2_channel if signal.sport == "cs2" else self.khl_channel
            
            # Проверяем cooldown
            if not await self.check_publish_cooldown(channel):
                logger.info(f"Publish cooldown active for {channel}")
                return False
            
            # Форматируем сообщение
            message = await self.format_signal_message(signal)
            
            # Публикуем в канал
            await self.bot.send_message(
                chat_id=channel,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            # Обновляем статус публикации
            await db_manager.update_signal_published(signal.id, True)
            
            logger.info(f"📱 Published signal to {channel}: {signal.signal[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing signal: {e}")
            return False
    
    async def format_signal_message(self, signal: Signal) -> str:
        """Форматирование сообщения сигнала"""
        # Базовое форматирование
        message = signal.signal
        
        # Добавляем временную метку
        timestamp = signal.created_at.strftime("%H:%M")
        message = f"<b>🕐 {timestamp}</b>\n\n{message}"
        
        # Добавляем дисклеймер
        message += "\n\n<i>⚠️ Это не финансовая рекомендация. Ставьте ответственно.</i>"
        
        return message
    
    async def check_publish_cooldown(self, channel: str) -> bool:
        """Проверка cooldown для публикации"""
        try:
            # Получаем последние опубликованные сигналы для канала
            sport = "cs2" if channel == self.cs2_channel else "khl"
            published_signals = await db_manager.get_signals(
                sport=sport, 
                published=True, 
                limit=10
            )
            
            if not published_signals:
                return True
            
            # Проверяем последний сигнал
            last_signal = published_signals[0]
            if last_signal.created_at:
                time_diff = datetime.now() - last_signal.created_at
                cooldown_seconds = self.publish_cooldown_minutes * 60
                
                if time_diff.total_seconds() < cooldown_seconds:
                    logger.info(f"Publish cooldown active for {channel}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking publish cooldown: {e}")
            return True
    
    async def publish_pending_signals(self) -> int:
        """Публикация всех ожидающих сигналов"""
        if not self._initialized:
            await self.initialize()
        
        logger.info("📱 Publishing pending signals")
        
        try:
            # Получаем неопубликованные сигналы
            pending_signals = await db_manager.get_signals(published=False, limit=50)
            
            if not pending_signals:
                logger.info("No pending signals to publish")
                return 0
            
            published_count = 0
            
            for signal in pending_signals:
                # Проверяем, что сигнал достаточно свежий
                if signal.created_at and signal.created_at < datetime.now() - timedelta(hours=24):
                    # Слишком старый сигнал, пропускаем
                    continue
                
                success = await self.publish_signal(signal)
                if success:
                    published_count += 1
                    
                    # Небольшая задержка между публикациями
                    await asyncio.sleep(2)
            
            logger.info(f"📱 Published {published_count} signals")
            return published_count
            
        except Exception as e:
            logger.error(f"Error publishing pending signals: {e}")
            return 0
    
    async def publish_daily_summary(self) -> bool:
        """Публикация дневной сводки"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Получаем статистику за сегодня
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Получаем сегодняшние сигналы
            all_signals = await db_manager.get_signals(limit=1000)
            today_signals = [
                signal for signal in all_signals
                if signal.created_at and signal.created_at >= today
            ]
            
            if not today_signals:
                return False
            
            # Формируем сводку
            cs2_signals = [s for s in today_signals if s.sport == "cs2"]
            khl_signals = [s for s in today_signals if s.sport == "khl"]
            
            avg_confidence = sum(s.confidence for s in today_signals) / len(today_signals)
            
            summary_message = (
                f"<b>📊 Дневная сводка AIBET</b>\n\n"
                f"🕐 Дата: {datetime.now().strftime('%d.%m.%Y')}\n"
                f"🎯 Всего сигналов: {len(today_signals)}\n"
                f"🔫 CS2: {len(cs2_signals)}\n"
                f"🏒 КХЛ: {len(khl_signals)}\n"
                f"📈 Средняя уверенность: {avg_confidence:.1%}\n\n"
                f"<i>Следите за сигналами в реальном времени!</i>"
            )
            
            # Публикуем в оба канала
            await self.bot.send_message(
                chat_id=self.cs2_channel,
                text=summary_message,
                parse_mode="HTML"
            )
            
            await self.bot.send_message(
                chat_id=self.khl_channel,
                text=summary_message,
                parse_mode="HTML"
            )
            
            logger.info("📱 Published daily summary")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing daily summary: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Тест соединения с Telegram"""
        if not self._initialized:
            await self.initialize()
        
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Bot connection test successful: @{bot_info.username}")
            return True
            
        except Exception as e:
            logger.error(f"Bot connection test failed: {e}")
            return False
    
    async def get_channel_info(self, channel: str) -> Dict[str, any]:
        """Получить информацию о канале"""
        if not self._initialized:
            await self.initialize()
        
        try:
            chat = await self.bot.get_chat(channel)
            return {
                'id': chat.id,
                'title': chat.title,
                'type': chat.type,
                'member_count': getattr(chat, 'member_count', None)
            }
            
        except Exception as e:
            logger.error(f"Error getting channel info for {channel}: {e}")
            return {}
    
    async def send_test_message(self, channel: str) -> bool:
        """Отправить тестовое сообщение"""
        if not self._initialized:
            await self.initialize()
        
        try:
            test_message = (
                f"<b>🧪 Тестовое сообщение AIBET</b>\n\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
                f"🤖 Бот работает корректно\n\n"
                f"<i>Это тестовое сообщение для проверки работы системы.</i>"
            )
            
            await self.bot.send_message(
                chat_id=channel,
                text=test_message,
                parse_mode="HTML"
            )
            
            logger.info(f"📱 Sent test message to {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending test message to {channel}: {e}")
            return False
    
    async def cleanup_old_published_signals(self, days: int = 7):
        """Очистка старых опубликованных сигналов"""
        logger.info(f"🧹 Cleaning up old published signals")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Получаем старые опубликованные сигналы
            old_signals = await db_manager.get_signals(published=True, limit=1000)
            old_signals = [
                signal for signal in old_signals
                if signal.created_at and signal.created_at < cutoff_date
            ]
            
            # В реальной реализации здесь было бы удаление из БД
            logger.info(f"🧹 Found {len(old_signals)} old published signals")
            
        except Exception as e:
            logger.error(f"Error cleaning up old published signals: {e}")
    
    async def get_publishing_statistics(self) -> Dict[str, any]:
        """Получить статистику публикации"""
        try:
            # Получаем все сигналы
            all_signals = await db_manager.get_signals(limit=1000)
            
            # Статистика по публикации
            published_signals = [s for s in all_signals if s.published]
            unpublished_signals = [s for s in all_signals if not s.published]
            
            # Статистика по видам спорта
            cs2_published = [s for s in published_signals if s.sport == "cs2"]
            khl_published = [s for s in published_signals if s.sport == "khl"]
            
            # Сегодняшние публикации
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_published = [
                s for s in published_signals
                if s.created_at and s.created_at >= today
            ]
            
            statistics = {
                'total_signals': len(all_signals),
                'published_signals': len(published_signals),
                'unpublished_signals': len(unpublished_signals),
                'cs2_published': len(cs2_published),
                'khl_published': len(khl_published),
                'today_published': len(today_published),
                'publish_rate': (len(published_signals) / len(all_signals)) * 100 if all_signals else 0
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting publishing statistics: {e}")
            return {}

# Глобальный экземпляр publisher
def create_telegram_publisher(bot_token: str) -> TelegramPublisher:
    """Создание экземпляра Telegram Publisher"""
    return TelegramPublisher(bot_token)
