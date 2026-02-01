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

async def initialize_components(db_manager):
    """Инициализация всех компонентов с правильным порядком"""
    logger.info("🔧 Initializing components")
    
    service_type = os.getenv('SERVICE_TYPE', 'web')
    logger.info(f"🔧 Service type: {service_type}")
    
    try:
        # 1. Инициализируем ML модели с db_manager (для обоих сервисов)
        from ml_models import AdvancedMLModels
        global ml_models
        ml_models = AdvancedMLModels(db_manager_instance=db_manager)
        await ml_models.initialize()
        logger.info("✅ ML Models initialized")
        
        if service_type == 'bot':
            # ТОЛЬКО для Bot сервиса: инициализируем Telegram Bot
            from telegram_bot import AIBOTTelegramBot
            global telegram_bot
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                raise ValueError("TELEGRAM_BOT_TOKEN is required for bot service")
            admin_id = int(os.getenv("ADMIN_ID", "379036860"))
            telegram_bot = AIBOTTelegramBot(bot_token, admin_id, db_manager)
            logger.info("✅ Telegram Bot initialized")
            
        elif service_type == 'web':
            # ТОЛЬКО для Web сервиса: инициализируем Mini App
            from mini_app import AIBETMiniApp
            global mini_app
            mini_app = AIBETMiniApp(db_manager, ml_models)
            logger.info("✅ Mini App initialized")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ Error initializing components: {e}")
        return False

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

async def start_background_services():
    """Запуск фоновых сервисов"""
    logger.info("🔄 Starting background services")
    
    try:
        # 1. Запускаем updater матчей
        from match_updater import match_updater
        asyncio.create_task(match_updater.start())
        logger.info("✅ Match updater started")
        
        # 2. Запускаем фоновое обучение ML
        asyncio.create_task(start_ml_background_training())
        logger.info("✅ ML background training scheduled")
        
        # 3. Запускаем системный сервис
        asyncio.create_task(start_system_service())
        logger.info("✅ System service started")
        
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ Error starting background services: {e}")
        return False

async def main():
    """Главная функция запуска"""
    logger.info("🚀 Starting AIBET Analytics Platform")
    
    # Определение типа сервиса
    service_type = os.getenv('SERVICE_TYPE', 'web')
    
    try:
        # 1. Инициализируем базу данных (общая для всех сервисов)
        db_manager = await initialize_database()
        
        # 2. Инициализируем компоненты
        components_ready = await initialize_components(db_manager)
        if not components_ready:
            logger.error("❌ Failed to initialize components")
            sys.exit(1)
        
        # 3. Запускаем фоновые сервисы
        await start_background_services()
        
        # 4. Начальный сбор данных (не блокирующий)
        asyncio.create_task(start_initial_data_collection(db_manager))
        
        if service_type == 'web':
            logger.info("📊 Starting AIBET Mini App Web Service")
            # Запускаем Mini App с health сервером
            await asyncio.gather(
                mini_app.run(),
                health_server()
            )
            
        elif service_type == 'bot':
            logger.info("🤖 Starting AIBOT Telegram Bot Web Service")
            from telegram_bot import main as bot_main
            
            # Запускаем все сервисы параллельно
            await asyncio.gather(
                bot_main(),
                health_server()
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
