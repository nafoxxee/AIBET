#!/usr/bin/env python3
"""
AIBET Analytics Platform - Fixed Production Main Entry Point
Исправленная версия согласно требованиям Senior Engineer
"""

import asyncio
import logging
import os
import sys
import signal
from datetime import datetime, timedelta
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
background_task = None

async def scheduled_data_update():
    """Запланированное обновление данных (каждые 6 часов для Render Free)"""
    logger.info("🔄 Starting scheduled data update (every 6 hours)")
    
    while True:
        try:
            logger.info("🔄 Starting data update cycle...")
            
            # 1. Обновление CS2 матчей
            from parsers.cs2_parser_fixed import CS2ParserFixed
            cs2_parser = CS2ParserFixed()
            cs2_matches = await cs2_parser.parse_matches()
            logger.info(f"✅ Updated {len(cs2_matches)} CS2 matches")
            
            # 2. Обновление КХЛ матчей
            from parsers.khl_parser_fixed import KHLParserFixed
            khl_parser = KHLParserFixed()
            khl_matches = await khl_parser.parse_matches()
            logger.info(f"✅ Updated {len(khl_matches)} KHL matches")
            
            # 3. Сохранение в базу данных
            from database_fixed import DatabaseManager
            db = DatabaseManager()
            await db.initialize()
            
            for match in cs2_matches + khl_matches:
                try:
                    await db.add_match(match)
                except Exception as e:
                    logger.warning(f"⚠️ Error saving match: {e}")
            
            # 4. Обучение ML если достаточно данных
            total_matches = await db.get_match_count()
            if total_matches >= 100:
                logger.info("🤖 Training ML models...")
                from ml_models_fixed import MLModelsFixed
                ml = MLModelsFixed(db)
                await ml.train_models()
            else:
                logger.info(f"⏳ Not enough matches for ML ({total_matches}/100)")
            
            # 5. Генерация сигналов
            from signal_generator_fixed import SignalGeneratorFixed
            signal_gen = SignalGeneratorFixed(db)
            signals = await signal_gen.generate_signals()
            logger.info(f"🎯 Generated {len(signals)} signals")
            
            # 6. Публикация сигналов в Telegram
            if signals:
                from telegram_publisher_fixed import TelegramPublisherFixed
                publisher = TelegramPublisherFixed()
                for signal in signals:
                    await publisher.publish_signal(signal)
            
            logger.info("✅ Data update cycle completed")
            
        except Exception as e:
            logger.error(f"❌ Error in data update: {e}")
        
        # Ожидание 6 часов (21600 секунд)
        logger.info("⏰ Waiting 6 hours for next update...")
        await asyncio.sleep(21600)

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
    from api_server_fixed import app
    
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
    """Запуск Telegram бота (только polling, без FastAPI)"""
    logger.info("🤖 Starting Telegram Bot")
    
    try:
        from telegram_bot_fixed import AIBOTTelegramBotFixed
        from database_fixed import DatabaseManager
        
        # Инициализация базы данных
        db = DatabaseManager()
        await db.initialize()
        
        # Создание и запуск бота
        bot = AIBOTTelegramBotFixed(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            admin_id=int(os.getenv("ADMIN_ID", "379036860")),
            db_manager=db
        )
        
        await bot.start()
        return bot
        
    except Exception as e:
        logger.error(f"❌ Error starting Telegram bot: {e}")
        raise

async def main():
    """Главная функция запуска"""
    logger.info("🚀 Starting AIBET Analytics Platform (Fixed Version)")
    
    # Определение типа сервиса
    service_type = os.getenv("SERVICE_TYPE", "web")
    logger.info(f"🔧 Service type: {service_type}")
    
    try:
        if service_type == "web":
            # Запуск API сервера с фоновыми задачами
            logger.info("🌐 Starting Web Service (API + Background Tasks)")
            
            # Запуск фоновой задачи
            global background_task
            background_task = asyncio.create_task(scheduled_data_update())
            
            # Запуск API сервера
            await start_api_server()
            
        elif service_type == "bot":
            # Запуск Telegram бота с health сервером
            logger.info("🤖 Starting Bot Service (Telegram + Health)")
            
            # Запуск health сервера в фоне
            health_srv = await health_server()
            health_task = asyncio.create_task(health_srv.serve())
            
            # Запуск Telegram бота
            await start_telegram_bot()
            
        else:
            logger.error(f"❌ Unknown service type: {service_type}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        # Очистка
        if background_task:
            background_task.cancel()
        logger.info("🏁 AIBET Platform stopped")

if __name__ == "__main__":
    asyncio.run(main())
