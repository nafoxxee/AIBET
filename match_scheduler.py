#!/usr/bin/env python3
"""
AIBET Analytics Platform - Match Scheduler
Планировщик регулярного обновления матчей
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from database import db_manager
from parsers.cs2_parser import cs2_parser
from parsers.khl_parser import khl_parser

logger = logging.getLogger(__name__)

class MatchScheduler:
    def __init__(self):
        self.cs2_parser = cs2_parser
        self.khl_parser = khl_parser
        self._running = False
        self._tasks = []
        self._last_update = {}
        
    async def start(self):
        """Запуск планировщика"""
        if self._running:
            logger.warning("⚠️ Match scheduler already running")
            return
            
        logger.info("🚀 Starting Match Scheduler")
        self._running = True
        
        # Запускаем фоновые задачи
        self._tasks = [
            asyncio.create_task(self.cs2_update_loop()),
            asyncio.create_task(self.khl_update_loop()),
            asyncio.create_task(self.cleanup_loop()),
            asyncio.create_task(self.status_loop())
        ]
        
        logger.info("✅ Match Scheduler started successfully")
    
    async def stop(self):
        """Остановка планировщика"""
        if not self._running:
            return
            
        logger.info("🛑 Stopping Match Scheduler")
        self._running = False
        
        # Отменяем все задачи
        for task in self._tasks:
            task.cancel()
        
        # Ждем завершения
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        logger.info("✅ Match Scheduler stopped")
    
    async def cs2_update_loop(self):
        """Цикл обновления CS2 матчей"""
        logger.info("🔴 Starting CS2 update loop")
        
        while self._running:
            try:
                logger.info("🔴 Updating CS2 matches...")
                
                # Обновляем матчи
                await self.cs2_parser.update_matches()
                
                # Сохраняем время обновления
                self._last_update['cs2'] = datetime.now()
                
                # Получаем статистику
                matches = await db_manager.get_matches(sport="cs2", limit=100)
                live_matches = len([m for m in matches if m.status == "live"])
                upcoming_matches = len([m for m in matches if m.status == "upcoming"])
                
                logger.info(f"🔴 CS2 update completed: {live_matches} live, {upcoming_matches} upcoming")
                
                # Ждем 5 минут до следующего обновления
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"❌ Error in CS2 update loop: {e}")
                await asyncio.sleep(60)  # Ждем 1 минуту при ошибке
    
    async def khl_update_loop(self):
        """Цикл обновления KHL матчей"""
        logger.info("🏒 Starting KHL update loop")
        
        while self._running:
            try:
                logger.info("🏒 Updating KHL matches...")
                
                # Обновляем матчи
                await self.khl_parser.update_matches()
                
                # Сохраняем время обновления
                self._last_update['khl'] = datetime.now()
                
                # Получаем статистику
                matches = await db_manager.get_matches(sport="khl", limit=100)
                live_matches = len([m for m in matches if m.status == "live"])
                upcoming_matches = len([m for m in matches if m.status == "upcoming"])
                
                logger.info(f"🏒 KHL update completed: {live_matches} live, {upcoming_matches} upcoming")
                
                # Ждем 7 минут до следующего обновления (чтобы не нагружать)
                await asyncio.sleep(420)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"❌ Error in KHL update loop: {e}")
                await asyncio.sleep(60)  # Ждем 1 минуту при ошибке
    
    async def cleanup_loop(self):
        """Цикл очистки старых матчей"""
        logger.info("🧹 Starting cleanup loop")
        
        while self._running:
            try:
                # Каждые 6 часов очищаем старые матчи
                await asyncio.sleep(21600)
                
                if not self._running:
                    break
                
                logger.info("🧹 Cleaning up old matches...")
                
                # Удаляем матчи старше 7 дней
                cutoff_date = datetime.now() - timedelta(days=7)
                
                # В реальной реализации здесь было бы удаление из БД
                old_matches = await db_manager.get_matches(limit=1000)
                old_matches = [
                    match for match in old_matches
                    if match.created_at and match.created_at < cutoff_date
                ]
                
                logger.info(f"🧹 Found {len(old_matches)} old matches to clean")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"❌ Error in cleanup loop: {e}")
    
    async def status_loop(self):
        """Цикл статуса"""
        logger.info("📊 Starting status loop")
        
        while self._running:
            try:
                # Каждые 30 минут выводим статус
                await asyncio.sleep(1800)
                
                if not self._running:
                    break
                
                # Получаем общую статистику
                all_matches = await db_manager.get_matches(limit=1000)
                cs2_matches = [m for m in all_matches if m.sport == "cs2"]
                khl_matches = [m for m in all_matches if m.sport == "khl"]
                
                live_matches = len([m for m in all_matches if m.status == "live"])
                upcoming_matches = len([m for m in all_matches if m.status == "upcoming"])
                
                logger.info("📊 Match Scheduler Status:")
                logger.info(f"  📊 Total matches: {len(all_matches)}")
                logger.info(f"  🔴 CS2 matches: {len(cs2_matches)}")
                logger.info(f"  🏒 KHL matches: {len(khl_matches)}")
                logger.info(f"  🔴 Live matches: {live_matches}")
                logger.info(f"  ⏰ Upcoming matches: {upcoming_matches}")
                
                # Показываем время последнего обновления
                for sport, last_time in self._last_update.items():
                    if last_time:
                        time_diff = datetime.now() - last_time
                        logger.info(f"  🔄 {sport.upper()} last update: {time_diff} ago")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"❌ Error in status loop: {e}")
    
    async def force_update(self, sport: str = None):
        """Принудительное обновление"""
        logger.info(f"🔄 Force update requested for sport: {sport or 'all'}")
        
        try:
            if sport == "cs2" or sport is None:
                await self.cs2_parser.update_matches()
                self._last_update['cs2'] = datetime.now()
                logger.info("✅ CS2 force update completed")
            
            if sport == "khl" or sport is None:
                await self.khl_parser.update_matches()
                self._last_update['khl'] = datetime.now()
                logger.info("✅ KHL force update completed")
                
        except Exception as e:
            logger.exception(f"❌ Error in force update: {e}")
    
    def get_status(self) -> Dict:
        """Получить статус планировщика"""
        return {
            "running": self._running,
            "last_update": self._last_update,
            "tasks_count": len(self._tasks)
        }

# Глобальный экземпляр
match_scheduler = MatchScheduler()
