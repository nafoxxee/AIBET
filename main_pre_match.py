#!/usr/bin/env python3
"""
AIBET Analytics Platform - Pre-Match Main Entry Point
Полностью pre-match система без live данных
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

async def scheduled_pre_match_update():
    """Запланированное обновление pre-match данных (каждые 6 часов)"""
    logger.info("🔄 Starting Pre-Match data update (every 6 hours)")
    
    while True:
        try:
            logger.info("🔄 Starting Pre-Match update cycle...")
            
            # 1. Обновление CS2 pre-match матчей
            from data_sources.pre_match.cs2_pre_match import cs2_pre_match_source
            cs2_matches = await cs2_pre_match_source.get_pre_match_matches()
            logger.info(f"✅ Updated {len(cs2_matches)} CS2 pre-match matches")
            
            # 2. Обновление КХЛ pre-match матчей
            from data_sources.pre_match.khl_pre_match import khl_pre_match_source
            khl_matches = await khl_pre_match_source.get_pre_match_matches()
            logger.info(f"✅ Updated {len(khl_matches)} KHL pre-match matches")
            
            # 3. Сохранение в базу данных
            from database_pre_match import pre_match_db
            await pre_match_db.initialize()
            
            for match in cs2_matches + khl_matches:
                try:
                    await pre_match_db.add_match(match)
                except Exception as e:
                    logger.warning(f"⚠️ Error saving match: {e}")
            
            # 4. Обучение ML если достаточно исторических данных
            historical_count = await pre_match_db.get_historical_match_count()
            if historical_count >= 30:
                logger.info("🤖 Training Pre-Match ML models...")
                from ml_models_pre_match import PreMatchMLModels
                ml = PreMatchMLModels(pre_match_db)
                
                # Обучаем модели для обоих видов спорта
                await ml.train_models('cs2')
                await ml.train_models('khl')
            else:
                logger.info(f"⏳ Not enough historical data for ML ({historical_count}/30)")
            
            # 5. Генерация pre-match сигналов
            from signal_generator_pre_match import PreMatchSignalGenerator
            signal_gen = PreMatchSignalGenerator(pre_match_db)
            signals = await signal_gen.generate_signals()
            logger.info(f"🎯 Generated {len(signals)} pre-match signals")
            
            # 6. Публикация сигналов в Telegram
            if signals:
                from telegram_publisher_pre_match import PreMatchTelegramPublisher
                publisher = PreMatchTelegramPublisher()
                for signal in signals:
                    await publisher.publish_signal(signal)
            
            logger.info("✅ Pre-Match update cycle completed")
            
        except Exception as e:
            logger.error(f"❌ Error in pre-match update: {e}")
        
        # Ожидание 6 часов (21600 секунд)
        logger.info("⏰ Waiting 6 hours for next pre-match update...")
        await asyncio.sleep(21600)

async def health_server():
    """Health сервер для Render (только для бота)"""
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI()
    
    @app.get("/health")
    async def health():
        return {
            "status": "ok", 
            "service": "pre_match_bot", 
            "timestamp": datetime.now().isoformat(),
            "mode": "pre_match"
        }
    
    @app.get("/")
    async def root():
        return {
            "message": "AIBET Pre-Match Bot Health Server", 
            "status": "running",
            "mode": "pre_match"
        }
    
    config = uvicorn.Config(app, host="0.0.0.0", port=1001, log_level="info")
    server = uvicorn.Server(config)
    
    return server

async def start_api_server():
    """Запуск Pre-Match API сервера"""
    logger.info("🚀 Starting Pre-Match API Server")
    
    import uvicorn
    from api_server_pre_match import app
    
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
    """Запуск Pre-Match Telegram бота"""
    logger.info("🤖 Starting Pre-Match Telegram Bot")
    
    try:
        from telegram_bot_pre_match import PreMatchTelegramBot
        from database_pre_match import pre_match_db
        
        # Инициализация базы данных
        await pre_match_db.initialize()
        
        # Инициализация тестовых данных
        await pre_match_db.initialize_test_data()
        
        # Создание и запуск бота
        bot = PreMatchTelegramBot(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            admin_id=int(os.getenv("ADMIN_ID", "379036860")),
            db_manager=pre_match_db
        )
        
        await bot.start()
        return bot
        
    except Exception as e:
        logger.error(f"❌ Error starting Pre-Match Telegram bot: {e}")
        raise

async def main():
    """Главная функция запуска"""
    logger.info("🚀 Starting AIBET Analytics Platform (Pre-Match Mode)")
    
    # Определение типа сервиса
    service_type = os.getenv("SERVICE_TYPE", "web")
    logger.info(f"🔧 Service type: {service_type}")
    logger.info("📊 Mode: PRE-MATCH ONLY (No Live Data)")
    
    try:
        if service_type == "web":
            # Запуск API сервера с фоновыми задачами
            logger.info("🌐 Starting Web Service (Pre-Match API + Background Tasks)")
            
            # Запуск фоновой задачи
            global background_task
            background_task = asyncio.create_task(scheduled_pre_match_update())
            
            # Запуск API сервера
            await start_api_server()
            
        elif service_type == "bot":
            # Запуск Telegram бота с health сервером
            logger.info("🤖 Starting Bot Service (Pre-Match Telegram + Health)")
            
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
        logger.info("🏁 AIBET Pre-Match Platform stopped")

if __name__ == "__main__":
    asyncio.run(main())
