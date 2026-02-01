#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real Auto Publisher
Автоматическая публикация сигналов в Telegram каналы
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from aiogram import Bot
from database import db_manager
from signal_generator_real import real_signal_generator

logger = logging.getLogger(__name__)

class RealAutoPublisher:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.bot = None
        self.cs2_channel = "@aibetcsgo"
        self.khl_channel = "@aibetkhl"
        self.publish_cooldown_minutes = 60
        self.max_daily_posts = 10
        self._initialized = False
    
    async def initialize(self):
        """Инициализация авто-паблишера"""
        if self._initialized:
            return
        
        logger.info("📱 Initializing Real Auto Publisher")
        
        try:
            # Инициализируем бот
            self.bot = Bot(token=self.bot_token)
            
            # Проверяем соединение
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Connected to bot: @{bot_info.username}")
            
            self._initialized = True
            logger.info("✅ Real Auto Publisher initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Real Auto Publisher: {e}")
            raise
    
    async def publish_pending_signals(self):
        """Публикация ожидающих сигналов"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Получаем неопубликованные сигналы с высокой уверенностью
            all_signals = await db_manager.get_signals(published=False, limit=50)
            
            # Фильтруем сигналы с уверенностью >= 70%
            high_confidence_signals = [
                signal for signal in all_signals
                if signal.confidence >= 0.70
            ]
            
            if not high_confidence_signals:
                logger.info("📢 No high confidence signals to publish")
                return 0
            
            # Проверяем лимит публикаций за сегодня
            today_published = await self.get_today_published_count()
            remaining_posts = self.max_daily_posts - today_published
            
            if remaining_posts <= 0:
                logger.info(f"📢 Daily post limit reached ({today_published}/{self.max_daily_posts})")
                return 0
            
            # Сортируем по уверенности и времени
            high_confidence_signals.sort(key=lambda x: (x.confidence, x.created_at), reverse=True)
            
            published_count = 0
            for signal in high_confidence_signals[:remaining_posts]:
                try:
                    # Проверяем cooldown для канала
                    channel = self.cs2_channel if signal.sport == "cs2" else self.khl_channel
                    if not await self.check_channel_cooldown(channel):
                        logger.info(f"📢 Channel cooldown active for {channel}")
                        continue
                    
                    # Публикуем сигнал
                    success = await self.publish_signal_to_channel(signal, channel)
                    if success:
                        # Обновляем статус в базе
                        await db_manager.update_signal_published(signal.id, True)
                        published_count += 1
                        logger.info(f"📢 Published signal to {channel}: {signal.signal[:50]}...")
                        
                        # Небольшая задержка между публикациями
                        await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"❌ Error publishing signal {signal.id}: {e}")
                    continue
            
            logger.info(f"📢 Published {published_count} signals to channels")
            return published_count
            
        except Exception as e:
            logger.error(f"❌ Error in publish_pending_signals: {e}")
            return 0
    
    async def publish_signal_to_channel(self, signal, channel: str) -> bool:
        """Публикация сигнала в канал"""
        try:
            # Форматируем сообщение
            message = self.format_signal_message(signal)
            
            # Публикуем в канал
            await self.bot.send_message(
                chat_id=channel,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            logger.info(f"📱 Successfully published to {channel}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error publishing to {channel}: {e}")
            return False
    
    def format_signal_message(self, signal) -> str:
        """Форматирование сообщения сигнала"""
        confidence_percent = int(signal.confidence * 100)
        
        # Определяем эмодзи и название спорта
        if signal.sport == "cs2":
            emoji = "🔴"
            sport_name = "CS2"
        elif signal.sport == "khl":
            emoji = "🏒"
            sport_name = "КХЛ"
        else:
            emoji = "📊"
            sport_name = signal.sport.upper()
        
        # Формируем сообщение
        message = (
            f"<b>{emoji} AIBET SIGNAL</b>\n\n"
            f"<b>{sport_name}:</b>\n"
            f"{signal.signal}\n\n"
            f"<b>🎯 AI Confidence:</b> {confidence_percent}%\n"
            f"<b>🕐 Time:</b> {signal.created_at.strftime('%H:%M')}\n\n"
            f"<i>⚠️ Это не финансовая рекомендация. Ставьте ответственно.</i>"
        )
        
        return message
    
    async def check_channel_cooldown(self, channel: str) -> bool:
        """Проверка cooldown для публикации в канал"""
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
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking channel cooldown: {e}")
            return False
    
    async def get_today_published_count(self) -> int:
        """Получить количество публикаций за сегодня"""
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Получаем все опубликованные сигналы
            all_published = await db_manager.get_signals(published=True, limit=100)
            
            # Фильтруем сегодняшние
            today_published = [
                signal for signal in all_published
                if signal.created_at and signal.created_at >= today
            ]
            
            return len(today_published)
            
        except Exception as e:
            logger.error(f"❌ Error getting today published count: {e}")
            return 0
    
    async def start_auto_publishing(self):
        """Запуск авто-публикации"""
        logger.info("🚀 Starting auto publishing service")
        
        while True:
            try:
                # Публикуем ожидающие сигналы
                await self.publish_pending_signals()
                
                # Пауза 15 минут
                await asyncio.sleep(900)
                
            except Exception as e:
                logger.error(f"❌ Error in auto publishing loop: {e}")
                await asyncio.sleep(300)  # 5 минут при ошибке
    
    async def get_publishing_stats(self) -> Dict[str, Any]:
        """Получить статистику публикаций"""
        try:
            today_published = await self.get_today_published_count()
            
            # Получаем статистику по каналам
            cs2_signals = await db_manager.get_signals(sport="cs2", published=True, limit=100)
            khl_signals = await db_manager.get_signals(sport="khl", published=True, limit=100)
            
            return {
                'today_published': today_published,
                'max_daily_posts': self.max_daily_posts,
                'total_cs2_published': len(cs2_signals),
                'total_khl_published': len(khl_signals),
                'cs2_channel': self.cs2_channel,
                'khl_channel': self.khl_channel,
                'cooldown_minutes': self.publish_cooldown_minutes
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting publishing stats: {e}")
            return {}

# Глобальная функция для создания экземпляра
def create_real_auto_publisher(bot_token: str) -> RealAutoPublisher:
    """Создание экземпляра авто-паблишера"""
    return RealAutoPublisher(bot_token)
