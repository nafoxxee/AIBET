#!/usr/bin/env python3
"""
AIBET Analytics Platform - Main Entry Point
Production Ready с автоматическим запуском системных сервисов
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

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
        return {"message": "AIBET Telegram Bot Health Check"}
    
    config = uvicorn.Config(app, host="0.0.0.0", port=10001, log_level="info")
    server = uvicorn.Server(config)
    
    logger.info("🏥 Health server starting on port 10001")
    await server.serve()

async def initialize_database():
    """Инициализация базы данных"""
    logger.info("🗄️ Initializing Database")
    try:
        from database import db_manager
        await db_manager.initialize()
        logger.info("✅ Database initialized successfully")
        return db_manager
    except Exception as e:
        logger.exception(f"❌ Error initializing database: {e}")
        raise

async def start_initial_data_collection(db_manager):
    """Начальный сбор данных"""
    logger.info("📊 Starting initial data collection")
    try:
        from parsers.cs2_parser import cs2_parser
        from parsers.khl_parser import khl_parser
        
        # Запускаем парсеры для начального сбора данных
        await cs2_parser.update_matches()
        await khl_parser.update_matches()
        
        logger.info("✅ Initial data collection completed")
    except Exception as e:
        logger.warning(f"⚠️ Error in initial data collection: {e}")
        # Не падаем, продолжаем запуск

async def start_ml_background_training():
    """Фоновое обучение ML"""
    logger.info("🤖 Scheduling ML background training")
    try:
        # Задержка 60 секунд перед началом обучения
        await asyncio.sleep(60)
        
        from ml_models import ml_models
        await ml_models.train_models()
        
        logger.info("✅ ML background training completed")
    except Exception as e:
        logger.warning(f"⚠️ Error in ML background training: {e}")
        # Не падаем, продолжаем работу

async def start_system_service():
    """Запуск системного сервиса"""
    try:
        from system_service import system_service
        await system_service.start()
        logger.info("🚀 System service started successfully")
    except Exception as e:
        logger.error(f"Error starting system service: {e}")

async def start_match_scheduler():
    """Запуск планировщика матчей"""
    try:
        from match_scheduler import match_scheduler
        await match_scheduler.start()
        logger.info("📊 Match scheduler started successfully")
    except Exception as e:
        logger.error(f"Error starting match scheduler: {e}")

async def main():
    """Главная функция запуска"""
    logger.info("🚀 Starting AIBET Analytics Platform")
    
    # Определение типа сервиса
    service_type = os.getenv('SERVICE_TYPE', 'web')
    
    try:
        # 1. Инициализируем базу данных (общая для всех сервисов)
        db_manager = await initialize_database()
        
        # 2. Начальный сбор данных (не блокирующий)
        asyncio.create_task(start_initial_data_collection(db_manager))
        
        # 3. Фоновое обучение ML (не блокирующее)
        asyncio.create_task(start_ml_background_training())
        
        if service_type == 'web':
            logger.info("📊 Starting AIBET Mini App Web Service")
            from mini_app import main as web_main
            await web_main()
            
        elif service_type == 'bot':
            logger.info("🤖 Starting AIBOT Telegram Bot Web Service")
            from telegram_bot import main as bot_main
            
            # Запускаем все сервисы параллельно
            await asyncio.gather(
                bot_main(),
                health_server(),
                start_system_service(),
                start_match_scheduler()
            )
            
        else:
            logger.error(f"❌ Unknown service type: {service_type}")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"❌ Critical error in main startup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Запуск
    asyncio.run(main())
