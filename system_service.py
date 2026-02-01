#!/usr/bin/env python3
"""
AIBET Analytics Platform - System Service
Автоматический сбор данных, генерация сигналов и публикация
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from database import db_manager
from ml_models import ml_models
from signal_generator import signal_generator
from telegram_publisher import create_telegram_publisher
from auto_publisher import auto_publisher
from parsers.cs2_parser import cs2_parser
from parsers.khl_parser import khl_parser

logger = logging.getLogger(__name__)

class SystemService:
    def __init__(self):
        self.cs2_parser = cs2_parser
        self.khl_parser = khl_parser
        self.publisher = create_telegram_publisher(os.getenv("TELEGRAM_BOT_TOKEN"))
        self.auto_publisher = auto_publisher
        self._running = False
        self._tasks = []
    
    async def start(self):
        """Запуск системного сервиса"""
        if self._running:
            return
        
        logger.info("🚀 Starting System Service")
        self._running = True
        
        # Инициализируем все компоненты
        await self.initialize_components()
        
        # Запускаем фоновые задачи
        self._tasks = [
            asyncio.create_task(self.data_collection_loop()),
            asyncio.create_task(self.signal_generation_loop()),
            asyncio.create_task(self.auto_publishing_loop()),
            asyncio.create_task(self.model_training_loop()),
            asyncio.create_task(self.cleanup_loop())
        ]
        
        logger.info("✅ System Service started successfully")
    
    async def stop(self):
        """Остановка системного сервиса"""
        if not self._running:
            return
        
        logger.info("🛑 Stopping System Service")
        self._running = False
        
        # Отменяем все задачи
        for task in self._tasks:
            task.cancel()
        
        # Ждем завершения
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        logger.info("✅ System Service stopped")
    
    async def initialize_components(self):
        """Инициализация всех компонентов"""
        logger.info("🔧 Initializing components")
        
        try:
            # Инициализируем базу данных
            await db_manager.initialize()
            
            # Инициализируем ML модели
            await ml_models.initialize()
            
            # Инициализируем генератор сигналов
            await signal_generator.initialize()
            
            # Инициализируем publisher
            await self.publisher.initialize()
            
            # Инициализируем автопаблишер
            await self.auto_publisher.initialize()
            
            logger.info("✅ All components initialized")
            
        except Exception as e:
            logger.exception(f"❌ Error initializing components: {e}")
            raise
    
    async def data_collection_loop(self):
        """Цикл сбора данных"""
        logger.info("📊 Starting data collection loop")
        
        while self._running:
            try:
                # Собираем CS2 матчи
                await self.cs2_parser.update_matches()
                
                # Собираем KHL матчи
                await self.khl_parser.update_matches()
                
                # Ждем 5 минут до следующего сбора
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in data collection loop: {e}")
                await asyncio.sleep(60)  # Ждем 1 минуту при ошибке
    
    async def signal_generation_loop(self):
        """Цикл генерации сигналов"""
        logger.info("🎯 Starting signal generation loop")
        
        while self._running:
            try:
                # Генерируем сигналы
                signals = await signal_generator.generate_daily_signals()
                
                # Публикуем сигналы
                if signals:
                    published_count = await self.publisher.publish_pending_signals()
                    logger.info(f"📢 Published {published_count} signals")
                
                # Ждем 30 минут до следующей генерации
                await asyncio.sleep(1800)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in signal generation loop: {e}")
                await asyncio.sleep(3600)  # Ждем 1 час при ошибке
    
    async def auto_publishing_loop(self):
        """Цикл автоматической публикации"""
        logger.info("📱 Starting auto publishing loop")
        
        while self._running:
            try:
                # Публикуем ожидающие сигналы
                published_count = await self.auto_publisher.publish_pending_signals()
                
                if published_count > 0:
                    logger.info(f"📢 Auto-published {published_count} signals")
                
                # Ждем 5 минут до следующей проверки
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"❌ Error in auto publishing loop: {e}")
                await asyncio.sleep(60)  # Ждем 1 минуту при ошибке
    
    async def model_training_loop(self):
        """Цикл обучения моделей"""
        logger.info("🤖 Starting model training loop")
        
        while self._running:
            try:
                # Обучаем модели раз в сутки
                await ml_models.train_models()
                
                # Ждем 24 часа до следующего обучения
                await asyncio.sleep(86400)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in model training loop: {e}")
                await asyncio.sleep(3600)  # Ждем 1 час при ошибке
    
    async def cleanup_loop(self):
        """Цикл очистки старых данных"""
        logger.info("🧹 Starting cleanup loop")
        
        while self._running:
            try:
                # Очищаем старые данные раз в 6 часов
                await self.cleanup_old_data()
                
                # Ждем 6 часов до следующей очистки
                await asyncio.sleep(21600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(3600)  # Ждем 1 час при ошибке
    
    async def cleanup_old_data(self):
        """Очистка старых данных"""
        logger.info("🧹 Cleaning up old data")
        
        try:
            # Удаляем матчи старше 7 дней
            cutoff_date = datetime.now() - timedelta(days=7)
            
            # В реальной реализации здесь было бы удаление из БД
            old_matches = await db_manager.get_matches(limit=1000)
            old_matches = [
                match for match in old_matches
                if match.created_at and match.created_at < cutoff_date
            ]
            
            logger.info(f"🧹 Found {len(old_matches)} old matches to clean")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def get_system_status(self) -> Dict[str, any]:
        """Получить статус системы"""
        try:
            # Получаем статистику
            signals = await db_manager.get_signals(limit=1000)
            matches = await db_manager.get_matches(limit=1000)
            
            # Считаем метрики
            total_signals = len(signals)
            live_matches = len([m for m in matches if m.status == "live"])
            upcoming_matches = len([m for m in matches if m.status == "upcoming"])
            
            status = {
                "running": self._running,
                "total_signals": total_signals,
                "live_matches": live_matches,
                "upcoming_matches": upcoming_matches,
                "last_update": datetime.now().isoformat(),
                "components": {
                    "database": "ok",
                    "ml_models": "ok",
                    "parsers": "ok",
                    "publisher": "ok"
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "running": False,
                "error": str(e),
                "last_update": datetime.now().isoformat()
            }

# Глобальный экземпляр
system_service = SystemService()
