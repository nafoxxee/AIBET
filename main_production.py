#!/usr/bin/env python3
"""
AIBET Analytics Platform - Production Main Entry Point
Полностью интегрированный запуск с реальными данными
"""

import asyncio
import logging
import os
import sys
import signal
from datetime import datetime
from typing import Optional

# Создание директории для логов ПЕРЕД настройкой
os.makedirs("logs", exist_ok=True)

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

# Глобальные переменные для управления процессами
telegram_bot = None
api_server = None
background_tasks = []

async def start_background_tasks():
    """Запуск фоновых задач"""
    logger.info("🔄 Starting background tasks")
    
    # Обновление матчей каждые 5 минут
    async def update_matches_task():
        while True:
            try:
                logger.info("🔄 Updating matches...")
                
                # Обновление CS2 матчей
                from parsers.cs2_parser import CS2Parser
                cs2_parser = CS2Parser()
                cs2_matches = await cs2_parser.parse_matches()
                logger.info(f"✅ Updated {len(cs2_matches)} CS2 matches")
                
                # Обновление KHL матчей
                from parsers.khl_parser import KHLParser
                khl_parser = KHLParser()
                khl_matches = await khl_parser.parse_matches()
                logger.info(f"✅ Updated {len(khl_matches)} KHL matches")
                
                # Сохранение в базу
                from database import db_manager
                for match in cs2_matches + khl_matches:
                    try:
                        await db_manager.add_match(match)
                    except Exception as e:
                        logger.warning(f"⚠️ Error saving match: {e}")
                
                logger.info("✅ Matches update completed")
                
            except Exception as e:
                logger.error(f"❌ Error in matches update: {e}")
            
            await asyncio.sleep(300)  # 5 минут
    
    # Обновление коэффициентов каждые 5 минут
    async def update_odds_task():
        while True:
            try:
                logger.info("💰 Updating odds...")
                
                from parsers.odds_parser import odds_parser
                
                # Обновление CS2 коэффициентов
                cs2_odds = await odds_parser.get_all_odds('cs2')
                logger.info(f"✅ Updated {len(cs2_odds)} CS2 odds")
                
                # Обновление KHL коэффициентов
                khl_odds = await odds_parser.get_all_odds('khl')
                logger.info(f"✅ Updated {len(khl_odds)} KHL odds")
                
                logger.info("✅ Odds update completed")
                
            except Exception as e:
                logger.error(f"❌ Error in odds update: {e}")
            
            await asyncio.sleep(300)  # 5 минут
    
    # Генерация сигналов каждый час
    async def generate_signals_task():
        while True:
            try:
                logger.info("🎯 Generating signals...")
                
                from signal_generator_real_clean import real_signal_generator
                signals = await real_signal_generator.generate_signals()
                logger.info(f"✅ Generated {len(signals)} signals")
                
            except Exception as e:
                logger.error(f"❌ Error in signal generation: {e}")
            
            await asyncio.sleep(3600)  # 1 час
    
    # Запуск задач
    tasks = [
        asyncio.create_task(update_matches_task()),
        asyncio.create_task(update_odds_task()),
        asyncio.create_task(generate_signals_task())
    ]
    
    background_tasks.extend(tasks)
    return tasks

async def health_server():
    """Health сервер для Render (только для бота)"""
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI()
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "bot", "timestamp": datetime.now().isoformat()}
    
    @app.get("/")
    async def root():
        return {"message": "AIBET Production Bot Health Server", "status": "running"}
    
    config = uvicorn.Config(app, host="0.0.0.0", port=1001, log_level="info")
    server = uvicorn.Server(config)
    
    return server

async def start_api_server():
    """Запуск API сервера"""
    logger.info("🚀 Starting API Server")
    
    import uvicorn
    from api_server_real import app
    
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=1000, 
        log_level="info",
        access_log=True
    )
    server = uvicorn.Server(config)
    
    await server.serve()

async def start_telegram_bot():
    """Запуск Telegram бота"""
    logger.info("🤖 Starting Telegram Bot")
    
    try:
        from telegram_bot_real_clean import create_bot
        
        bot = create_bot()
        await bot.start_polling()
        
        return bot
        
    except Exception as e:
        logger.error(f"❌ Error starting Telegram bot: {e}")
        return None

async def main():
    """Главная функция"""
    service_type = os.getenv("SERVICE_TYPE", "web")
    
    logger.info(f"🚀 Starting AIBET Production - Service: {service_type}")
    
    try:
        if service_type == "web":
            # Запуск API сервера и фоновых задач
            logger.info("📡 Starting Web Service (API + Background Tasks)")
            
            # Запуск фоновых задач
            bg_tasks = await start_background_tasks()
            
            # Запуск API сервера
            await start_api_server()
            
        elif service_type == "bot":
            # Запуск Telegram бота с health check
            logger.info("🤖 Starting Bot Service")
            
            # Запуск health сервера
            health_server_instance = await health_server()
            
            # Запуск бота
            bot = await start_telegram_bot()
            
            if bot:
                # Запускаем health сервер и бота параллельно
                tasks = [
                    health_server_instance.serve(),
                    bot.start_polling()
                ]
                
                await asyncio.gather(*tasks)
            else:
                # Если бот не запустился, запускаем только health сервер
                await health_server_instance.serve()
        
        else:
            logger.error(f"❌ Unknown service type: {service_type}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Service stopped by user")
    except Exception as e:
        logger.error(f"❌ Service error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Очистка
        logger.info("🧹 Cleaning up...")
        
        # Отмена фоновых задач
        for task in background_tasks:
            if not task.done():
                task.cancel()
        
        logger.info("✅ Service stopped gracefully")

def signal_handler(signum, frame):
    """Обработчик сигналов"""
    logger.info(f"🛑 Received signal {signum}")
    sys.exit(0)

if __name__ == "__main__":
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запуск
    asyncio.run(main())
