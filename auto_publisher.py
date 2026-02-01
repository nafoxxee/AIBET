#!/usr/bin/env python3
"""
AIBET Analytics Platform - Auto Signal Publisher
Автоматическая публикация сигналов в Telegram каналы
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from database import Signal, db_manager
from signal_generator import signal_generator
from telegram_publisher import create_telegram_publisher

logger = logging.getLogger(__name__)

class AutoSignalPublisher:
    def __init__(self):
        self.publisher = None
        self.cs2_channel = "@aibetcsgo"
        self.khl_channel = "@aibetkhl"
        self.publish_cooldown_minutes = 60
        self._initialized = False
        self._last_publish = {}
    
    async def initialize(self):
        """Инициализация автопаблишера"""
        if self._initialized:
            return
        
        logger.info("📱 Initializing Auto Signal Publisher")
        
        try:
            # Инициализируем Telegram publisher
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                raise ValueError("TELEGRAM_BOT_TOKEN not found")
            
            self.publisher = create_telegram_publisher(bot_token)
            await self.publisher.initialize()
            
            self._initialized = True
            logger.info("✅ Auto Signal Publisher initialized successfully")
            
        except Exception as e:
            logger.exception(f"❌ Error initializing Auto Signal Publisher: {e}")
            raise
    
    async def start_auto_publishing(self):
        """Запуск автоматической публикации"""
        if not self._initialized:
            await self.initialize()
        
        logger.info("🚀 Starting auto signal publishing")
        
        while True:
            try:
                # Проверяем наличие непубликованных сигналов
                await self.publish_pending_signals()
                
                # Ждем 5 минут до следующей проверки
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"❌ Error in auto publishing loop: {e}")
                await asyncio.sleep(60)  # Ждем 1 минуту при ошибке
    
    async def publish_pending_signals(self) -> int:
        """Публикация ожидающих сигналов"""
        try:
            # Получаем непубликованные сигналы
            pending_signals = await db_manager.get_signals(published=False, limit=20)
            
            if not pending_signals:
                logger.debug("📭 No pending signals to publish")
                return 0
            
            logger.info(f"📢 Found {len(pending_signals)} pending signals")
            
            published_count = 0
            
            for signal in pending_signals:
                try:
                    # Проверяем cooldown для публикации
                    if await self.is_publish_in_cooldown(signal):
                        continue
                    
                    # Определяем канал для публикации
                    channel = self.cs2_channel if signal.sport == "cs2" else self.khl_channel
                    
                    # Форматируем сообщение
                    message = self.format_publish_message(signal)
                    
                    # Публикуем в канал
                    success = await self.publisher.publish_to_channel(channel, message)
                    
                    if success:
                        # Обновляем статус сигнала
                        signal.published = True
                        signal.published_at = datetime.now()
                        await db_manager.update_signal(signal.id, signal)
                        
                        published_count += 1
                        logger.info(f"✅ Published signal to {channel}: {signal.signal[:50]}...")
                        
                        # Сохраняем время публикации
                        self._last_publish[signal.sport] = datetime.now()
                    else:
                        logger.warning(f"⚠️ Failed to publish signal to {channel}")
                
                except Exception as e:
                    logger.exception(f"❌ Error publishing signal {signal.id}: {e}")
                    continue
            
            logger.info(f"📢 Published {published_count} signals")
            return published_count
            
        except Exception as e:
            logger.exception(f"❌ Error publishing pending signals: {e}")
            return 0
    
    def format_publish_message(self, signal: Signal) -> str:
        """Форматирование сообщения для публикации"""
        confidence_percent = int(signal.confidence * 100)
        
        # Определяем эмодзи для вида спорта
        sport_emoji = "🔴" if signal.sport == "cs2" else "🏒"
        
        message = (
            f"{sport_emoji} <b>AIBET SIGNAL</b>\\n\\n"
            f"{signal.signal}\\n\\n"
            f"🎯 <b>Уверенность: {confidence_percent}%</b>\\n"
            f"🕐 <i>{signal.created_at.strftime('%H:%M')}</i>\\n\\n"
            f"<i>🤖 AI анализ с точностью >70%</i>"
        )
        
        return message
    
    async def is_publish_in_cooldown(self, signal: Signal) -> bool:
        """Проверка cooldown для публикации"""
        try:
            last_publish = self._last_publish.get(signal.sport)
            if not last_publish:
                return False
            
            time_diff = datetime.now() - last_publish
            cooldown_seconds = self.publish_cooldown_minutes * 60
            
            return time_diff.total_seconds() < cooldown_seconds
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking publish cooldown: {e}")
            return False
    
    async def publish_daily_summary(self):
        """Публикация дневной сводки"""
        try:
            # Получаем статистику за сегодня
            stats = await signal_generator.get_signal_statistics()
            
            if stats["today_signals"] == 0:
                return  # Нет сигналов сегодня
            
            # Формируем сводку
            summary = self.format_daily_summary(stats)
            
            # Публикуем в оба канала
            for channel in [self.cs2_channel, self.khl_channel]:
                await self.publisher.publish_to_channel(channel, summary)
            
            logger.info("📊 Daily summary published")
            
        except Exception as e:
            logger.exception(f"❌ Error publishing daily summary: {e}")
    
    def format_daily_summary(self, stats: Dict) -> str:
        """Форматирование дневной сводки"""
        return (
            f"📊 <b>AIBET DAILY SUMMARY</b>\\n\\n"
            f"📢 Сигналов сегодня: <b>{stats['today_signals']}</b>\\n"
            f"🔴 CS2: <b>{stats['cs2_signals']}</b>\\n"
            f"🏒 КХЛ: <b>{stats['khl_signals']}</b>\\n"
            f"📈 Средняя уверенность: <b>{stats['avg_confidence']:.1%}</b>\\n\\n"
            f"<i>🤖 AI работает для вас 24/7</i>"
        )
    
    async def force_publish_signals(self, limit: int = 5) -> int:
        """Принудительная публикация сигналов"""
        logger.info(f"🚀 Force publishing up to {limit} signals")
        
        try:
            # Получаем лучшие непубликованные сигналы
            pending_signals = await db_manager.get_signals(published=False, limit=limit)
            
            # Сортируем по уверенности
            pending_signals.sort(key=lambda x: x.confidence, reverse=True)
            
            published_count = 0
            
            for signal in pending_signals:
                try:
                    channel = self.cs2_channel if signal.sport == "cs2" else self.khl_channel
                    message = self.format_publish_message(signal)
                    
                    success = await self.publisher.publish_to_channel(channel, message)
                    
                    if success:
                        signal.published = True
                        signal.published_at = datetime.now()
                        await db_manager.update_signal(signal.id, signal)
                        
                        published_count += 1
                        logger.info(f"✅ Force published: {signal.signal[:50]}...")
                
                except Exception as e:
                    logger.exception(f"❌ Error force publishing signal {signal.id}: {e}")
                    continue
            
            logger.info(f"🚀 Force published {published_count} signals")
            return published_count
            
        except Exception as e:
            logger.exception(f"❌ Error in force publish: {e}")
            return 0
    
    async def get_publish_status(self) -> Dict:
        """Получить статус публикации"""
        try:
            stats = await signal_generator.get_signal_statistics()
            
            return {
                "initialized": self._initialized,
                "last_publish": self._last_publish,
                "pending_signals": stats["total_signals"] - stats["published_signals"],
                "published_today": stats["today_signals"],
                "success_rate": stats["success_rate"]
            }
            
        except Exception as e:
            logger.exception(f"❌ Error getting publish status: {e}")
            return {"error": str(e)}

# Глобальный экземпляр
auto_publisher = AutoSignalPublisher()
