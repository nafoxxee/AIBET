#!/usr/bin/env python3
"""
AIBET Analytics Platform - Match Updater
Автоматическое обновление матчей каждые 5 минут
"""

import asyncio
import logging
from datetime import datetime
from parsers.cs2_parser import cs2_parser
from parsers.khl_parser import khl_parser
from database import db_manager

logger = logging.getLogger(__name__)

class MatchUpdater:
    def __init__(self):
        self.running = False
        self.update_interval = 300  # 5 минут
    
    async def start(self):
        """Запуск автоматического обновления"""
        if self.running:
            logger.warning("⚠️ Match updater already running")
            return
        
        self.running = True
        logger.info("🔄 Starting automatic match updater")
        
        while self.running:
            try:
                await self.update_all_matches()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.exception(f"❌ Error in match updater loop: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
    
    async def stop(self):
        """Остановка обновления"""
        self.running = False
        logger.info("⏹️ Match updater stopped")
    
    async def update_all_matches(self):
        """Обновление всех матчей"""
        logger.info("🔄 Updating matches from all sources")
        
        # Обновляем CS2 матчи
        try:
            cs2_matches = await cs2_parser.update_matches()
            logger.info(f"🔴 Updated {len(cs2_matches)} CS2 matches")
        except Exception as e:
            logger.warning(f"⚠️ Error updating CS2 matches: {e}")
        
        # Обновляем КХЛ матчи
        try:
            khl_matches = await khl_parser.update_matches()
            logger.info(f"🏒 Updated {len(khl_matches)} KHL matches")
        except Exception as e:
            logger.warning(f"⚠️ Error updating KHL matches: {e}")
        
        # Обновляем статусы существующих матчей
        try:
            await self.update_match_statuses()
        except Exception as e:
            logger.warning(f"⚠️ Error updating match statuses: {e}")
        
        logger.info("✅ Match update cycle completed")
    
    async def update_match_statuses(self):
        """Обновление статусов существующих матчей"""
        try:
            # Получаем все активные матчи
            matches = await db_manager.get_matches(status=["upcoming", "live"], limit=100)
            
            updated_count = 0
            for match in matches:
                try:
                    # Здесь можно добавить логику обновления статуса
                    # Например, проверку времени начала матча
                    if match.status == "upcoming" and match.start_time:
                        if datetime.utcnow() >= match.start_time:
                            # Обновляем статус на live
                            match.status = "live"
                            await db_manager.update_match(match)
                            updated_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error updating match {match.id}: {e}")
                    continue
            
            if updated_count > 0:
                logger.info(f"🔄 Updated {updated_count} match statuses")
                
        except Exception as e:
            logger.warning(f"⚠️ Error in update_match_statuses: {e}")

# Глобальный экземпляр
match_updater = MatchUpdater()
