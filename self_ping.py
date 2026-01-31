#!/usr/bin/env python3
"""
AIBET Analytics Platform - Self-Ping Service
Keep-alive для Render Free Tier
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Optional
import os

logger = logging.getLogger(__name__)

class SelfPingService:
    def __init__(self, web_url: str, bot_url: str):
        self.web_url = web_url
        self.bot_url = bot_url
        self.ping_interval = 240  # 4 минуты (меньше 5 минут)
        self.timeout = 30
        self._running = False
        self._task = None
    
    async def start(self):
        """Запуск self-ping сервиса"""
        if self._running:
            return
        
        logger.info("🏓 Starting Self-Ping Service")
        self._running = True
        self._task = asyncio.create_task(self._ping_loop())
    
    async def stop(self):
        """Остановка self-ping сервиса"""
        if not self._running:
            return
        
        logger.info("🏓 Stopping Self-Ping Service")
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _ping_loop(self):
        """Основной цикл пингов"""
        while self._running:
            try:
                # Ping веб-сервис
                await self._ping_service(self.web_url, "Web App")
                
                # Ping бота (если есть отдельный URL)
                if self.bot_url and self.bot_url != self.web_url:
                    await self._ping_service(self.bot_url, "Telegram Bot")
                
                # Ждем следующего пинга
                await asyncio.sleep(self.ping_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ping loop: {e}")
                await asyncio.sleep(60)  # Ждем 1 минуту при ошибке
    
    async def _ping_service(self, url: str, service_name: str):
        """Пинг конкретного сервиса"""
        try:
            # Добавляем health endpoint
            health_url = f"{url.rstrip('/')}/api/health"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                start_time = datetime.now()
                
                async with session.get(health_url) as response:
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()
                    
                    if response.status == 200:
                        logger.info(f"🏓 {service_name} - OK ({response.status}) - {response_time:.2f}s")
                        return True
                    else:
                        logger.warning(f"🏓 {service_name} - HTTP {response.status} - {response_time:.2f}s")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error(f"🏓 {service_name} - Timeout after {self.timeout}s")
            return False
        except Exception as e:
            logger.error(f"🏓 {service_name} - Error: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, bool]:
        """Тест соединения с сервисами"""
        results = {}
        
        # Тест веб-сервиса
        results['web'] = await self._ping_service(self.web_url, "Web App")
        
        # Тест бота
        if self.bot_url and self.bot_url != self.web_url:
            results['bot'] = await self._ping_service(self.bot_url, "Telegram Bot")
        else:
            results['bot'] = results['web']
        
        return results
    
    async def get_service_status(self) -> Dict[str, any]:
        """Получить статус сервисов"""
        try:
            # Тестируем соединение
            connection_results = await self.test_connection()
            
            # Формируем статус
            status = {
                'running': self._running,
                'ping_interval': self.ping_interval,
                'last_check': datetime.now().isoformat(),
                'services': connection_results,
                'uptime': datetime.now().isoformat() if self._running else None
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                'running': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def set_ping_interval(self, seconds: int):
        """Установить интервал пинга"""
        if 60 <= seconds <= 300:  # От 1 до 5 минут
            self.ping_interval = seconds
            logger.info(f"🏓 Ping interval set to {seconds}s")
        else:
            logger.warning(f"Invalid ping interval: {seconds}s (must be 60-300s)")
    
    def get_next_ping_time(self) -> datetime:
        """Время следующего пинга"""
        if self._task and self._task.done():
            return datetime.now()
        
        # Это приблизительное время
        return datetime.now() + timedelta(seconds=self.ping_interval)

# Глобальный экземпляр
self_ping_service: Optional[SelfPingService] = None

def initialize_self_ping(web_url: str, bot_url: str = None):
    """Инициализация self-ping сервиса"""
    global self_ping_service
    self_ping_service = SelfPingService(web_url, bot_url)
    return self_ping_service

async def start_self_ping():
    """Запуск self-ping"""
    if self_ping_service:
        await self_ping_service.start()

async def stop_self_ping():
    """Остановка self-ping"""
    if self_ping_service:
        await self_ping_service.stop()

def get_self_ping_status() -> Optional[Dict[str, any]]:
    """Получить статус self-ping"""
    if self_ping_service:
        return asyncio.create_task(self_ping_service.get_service_status())
    return None
