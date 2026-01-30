#!/usr/bin/env python3
"""
AI BET Analytics Platform - Main Application
Telegram Bot + Mini App + Backend API + ML System
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from config import config
from bot import TelegramBot
from scheduler import scheduler
from api_server import start_api_server

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class AIBetApplication:
    """Основное приложение AI BET Analytics Platform"""
    
    def __init__(self):
        self.telegram_bot: Optional[TelegramBot] = None
        self.api_runner = None
        self.running = False
        
    async def initialize(self):
        """Инициализация компонентов приложения"""
        try:
            logger.info("🚀 Инициализация AI BET Analytics Platform...")
            
            # Проверка конфигурации
            self._validate_config()
            
            # Инициализация Telegram бота
            if config.telegram.bot_token:
                self.telegram_bot = TelegramBot()
                await self.telegram_bot.initialize()
                logger.info("✅ Telegram бот инициализирован")
            else:
                logger.warning("⚠️  Telegram бот не настроен")
            
            # Инициализация планировщика
            await scheduler.initialize()
            logger.info("✅ Планировщик инициализирован")
            
            # Запуск API сервера
            self.api_runner = await start_api_server(
                host=config.api.host,
                port=config.api.port
            )
            logger.info(f"✅ API сервер запущен на {config.api.host}:{config.api.port}")
            
            logger.info("🎯 AI BET Analytics Platform успешно инициализирована!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            raise
    
    def _validate_config(self):
        """Проверка конфигурации"""
        if not config.telegram.bot_token:
            logger.warning("⚠️  TELEGRAM_BOT_TOKEN не настроен")
        
        if not config.telegram.cs2_channel_id:
            logger.warning("⚠️  CS2_CHANNEL_ID не настроен")
        
        if not config.telegram.khl_channel_id:
            logger.warning("⚠️  KHL_CHANNEL_ID не настроен")
        
        if not config.telegram.admin_ids:
            logger.warning("⚠️  ADMIN_TELEGRAM_IDS не настроены")
        
        logger.info(f"📋 Конфигурация:")
        logger.info(f"   - API сервер: {config.api.host}:{config.api.port}")
        logger.info(f"   - База данных: {config.database.path}")
        logger.info(f"   - Админы: {len(config.telegram.admin_ids)} пользователей")
    
    async def start(self):
        """Запуск приложения"""
        try:
            await self.initialize()
            self.running = True
            
            logger.info("🎮 Запуск основных компонентов...")
            
            # Запуск Telegram бота
            if self.telegram_bot:
                telegram_task = asyncio.create_task(
                    self.telegram_bot.run()
                )
                logger.info("📱 Telegram бот запущен")
            
            # Запуск планировщика
            scheduler_task = asyncio.create_task(scheduler.start())
            logger.info("⏰ Планировщик запущен")
            
            # Отправка сообщения о запуске
            if self.telegram_bot:
                await self._send_startup_message()
            
            logger.info("🎉 AI BET Analytics Platform успешно запущена!")
            logger.info("📱 Mini App доступна через Telegram")
            logger.info(f"🌐 API документация: http://{config.api.host}:{config.api.port}/api")
            
            # Основной цикл работы
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска: {e}")
            await self.stop()
            raise
    
    async def _main_loop(self):
        """Основной цикл приложения"""
        try:
            while self.running:
                # Проверка состояния компонентов
                await self._health_check()
                
                # Ожидание перед следующей проверкой
                await asyncio.sleep(60)  # Проверка каждую минуту
                
        except asyncio.CancelledError:
            logger.info("🛑 Основной цикл остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка в основном цикле: {e}")
    
    async def _health_check(self):
        """Проверка состояния системы"""
        try:
            # Проверка API сервера
            if not self.api_runner:
                logger.warning("⚠️  API сервер не активен")
            
            # Проверка планировщика
            if not scheduler.running:
                logger.warning("⚠️  Планировщик не активен")
            
            # Проверка Telegram бота
            if self.telegram_bot:
                try:
                    bot_info = await self.telegram_bot.bot.get_me()
                    logger.debug(f"🤖 Bot status: {bot_info.username}")
                except Exception as e:
                    logger.warning(f"⚠️  Ошибка проверки Telegram бота: {e}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка health check: {e}")
    
    async def _send_startup_message(self):
        """Отправка сообщения о запуске"""
        try:
            startup_message = (
                "🚀 **AI BET Analytics Platform запущена!**\n\n"
                "📊 **Система активна:**\n"
                "• CS2 аналитика: ✅\n"
                "• КХЛ аналитика: ✅\n"
                "• ML модели: ✅\n"
                "• Mini App: ✅\n"
                "• API сервер: ✅\n\n"
                f"🌐 Mini App доступна в Telegram\n"
                f"📈 Каналы: @aibetcsgo, @aibetkhl"
            )
            
            if config.telegram.cs2_channel_id:
                await self.telegram_bot.bot.send_message(
                    chat_id=config.telegram.cs2_channel_id,
                    text=startup_message,
                    parse_mode="Markdown"
                )
            
            logger.info("📢 Стартовое сообщение отправлено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки стартового сообщения: {e}")
    
    async def stop(self):
        """Остановка приложения"""
        logger.info("🛑 Остановка AI BET Analytics Platform...")
        
        self.running = False
        
        try:
            # Остановка планировщика
            if scheduler.running:
                await scheduler.stop()
                logger.info("⏰ Планировщик остановлен")
            
            # Остановка Telegram бота
            if self.telegram_bot:
                await self.telegram_bot.dp.stop_polling()
                await self.telegram_bot.bot.session.close()
                logger.info("📱 Telegram бот остановлен")
            
            # Остановка API сервера
            if self.api_runner:
                await self.api_runner.cleanup()
                logger.info("🌐 API сервер остановлен")
            
            logger.info("✅ AI BET Analytics Platform успешно остановлена")
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки: {e}")


# Глобальный экземпляр приложения
app = AIBetApplication()


# Обработчики сигналов для graceful shutdown
def signal_handler(signum, frame):
    """Обработчик сигналов для корректной остановки"""
    logger.info(f"📡 Получен сигнал {signum}, остановка приложения...")
    asyncio.create_task(app.stop())


async def main():
    """Основная функция"""
    # Установка обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Запуск приложения
        await app.start()
    except KeyboardInterrupt:
        logger.info("🛑 Получен KeyboardInterrupt")
    except Exception as e:
        logger.error(f"💀 Фатальная ошибка: {e}")
    finally:
        await app.stop()


if __name__ == "__main__":
    # Проверка версии Python
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)
    
    # Создание директории для логов
    import os
    os.makedirs("logs", exist_ok=True)
    
    # Запуск приложения
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До свидания!")
    except Exception as e:
        logger.error(f"💀 Фатальная ошибка: {e}")
        sys.exit(1)
