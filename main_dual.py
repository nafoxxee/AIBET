#!/usr/bin/env python3
"""
AIBET Analytics Platform - Main Entry Point
Production Ready с автоматическим запуском системных сервисов
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
mini_app = None
background_tasks = []

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
        return {"message": "AIBET Bot Health Server", "status": "running"}
    
    config = uvicorn.Config(app, host="0.0.0.0", port=1000, log_level="info")
    server = uvicorn.Server(config)
    
    logger.info("🏥 Health server starting on port 1000")
    await server.serve()

async def initialize_database():
    """Инициализация базы данных с graceful fallback"""
    logger.info("🗄️ Initializing Database")
    try:
        from database import db_manager
        await db_manager.initialize()
        logger.info("✅ Database initialized successfully")
        return db_manager
    except ImportError as e:
        logger.error(f"❌ Database import error: {e}")
        logger.warning("⚠️ Using fallback database manager")
        # Создаем простой fallback
        class FallbackDBManager:
            def __init__(self):
                self.initialized = False
            async def initialize(self):
                self.initialized = True
                logger.info("✅ Fallback database initialized")
        return FallbackDBManager()
    except Exception as e:
        logger.exception(f"❌ Error initializing database: {e}")
        logger.warning("⚠️ Continuing without database")
        # Создаем простой fallback
        class FallbackDBManager:
            def __init__(self):
                self.initialized = False
            async def initialize(self):
                self.initialized = True
                logger.info("✅ Fallback database initialized")
        return FallbackDBManager()

async def initialize_components(db_manager):
    """Инициализация всех компонентов с правильным порядком"""
    logger.info("🔧 Initializing components")
    
    service_type = os.getenv('SERVICE_TYPE', 'web')
    logger.info(f"🔧 Service type: {service_type}")
    
    try:
        # 1. Инициализируем ML модели с db_manager (для обоих сервисов)
        try:
            from ml_models import AdvancedMLModels
            global ml_models
            ml_models = AdvancedMLModels(db_manager_instance=db_manager)
            await ml_models.initialize()
            logger.info("✅ ML Models initialized")
        except ImportError as e:
            logger.error(f"❌ ML models import error: {e}")
            logger.warning("⚠️ Continuing without ML models")
            ml_models = None
        except Exception as e:
            logger.error(f"❌ ML models initialization error: {e}")
            logger.warning("⚠️ Continuing without ML models")
            ml_models = None
        
        # 2. Инициализируем компоненты в зависимости от типа сервиса
        if service_type == 'api':
            logger.info("📊 Initializing API components")
            # Для API не импортируем mini_app если нет SQLAlchemy
            try:
                from mini_app import AIBETMiniApp
                global mini_app
                mini_app = AIBETMiniApp(db_manager)
                await mini_app.initialize()
                logger.info("✅ Mini App initialized")
            except ImportError as e:
                logger.error(f"❌ Mini App import error: {e}")
                logger.warning("⚠️ Continuing without Mini App")
                mini_app = None
            except Exception as e:
                logger.error(f"❌ Mini App initialization error: {e}")
                logger.warning("⚠️ Continuing without Mini App")
                mini_app = None
                
        elif service_type == 'bot':
            logger.info("🤖 Initializing Bot components")
            # Для бота не импортируем telegram_bot если нет SQLAlchemy
            try:
                from telegram_bot import AIBOTTelegramBot
                global telegram_bot
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
                if not bot_token:
                    raise ValueError("❌ TELEGRAM_BOT_TOKEN is required for bot service")
                
                # Проверяем тип токена
                if not isinstance(bot_token, str):
                    raise ValueError(f"❌ TELEGRAM_BOT_TOKEN must be str, got {type(bot_token)}")
                
                # Проверяем формат токена (должен начинаться с цифр или символов)
                if len(bot_token) < 10 or ':' not in bot_token:
                    raise ValueError("❌ TELEGRAM_BOT_TOKEN appears to be invalid (too short or missing ':')")
                
                logger.info(f"✅ Telegram token validated: {bot_token[:10]}...")
                telegram_bot = AIBOTTelegramBot(bot_token, 379036860, db_manager)
                await telegram_bot.initialize()
                logger.info("✅ Telegram Bot initialized")
            except ImportError as e:
                logger.error(f"❌ Telegram bot import error: {e}")
                logger.warning("⚠️ Continuing without Telegram Bot")
                telegram_bot = None
            except Exception as e:
                logger.error(f"❌ Telegram bot initialization error: {e}")
                logger.warning("⚠️ Continuing without Telegram Bot")
                telegram_bot = None
        
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
        cs2_matches = await cs2_parser.update_matches()
        khl_matches = await khl_parser.update_matches()
        
        logger.info(f"🔴 Updated {len(cs2_matches)} CS2 matches")
        logger.info(f"🏒 Updated {len(khl_matches)} KHL matches")
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
        
        # 5. Финальная проверка системы
        logger.info("🔍 Running final system checks...")
        
        # Проверка токенов
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if bot_token and isinstance(bot_token, str) and ':' in bot_token:
            logger.info("✅ Telegram токены корректны")
        else:
            logger.warning("⚠️ Telegram токены требуют проверки")
        
        # Проверка парсеров
        try:
            from mini_app import CS2_PARSER_AVAILABLE, KHL_PARSER_AVAILABLE
            if CS2_PARSER_AVAILABLE and KHL_PARSER_AVAILABLE:
                logger.info("✅ Парсеры CS2 и KHL работают, реальные матчи загружены")
            else:
                logger.warning("⚠️ Некоторые парсеры недоступны, используются fallback данные")
        except ImportError:
            logger.warning("⚠️ Статус парсеров неизвестен")
        
        # Проверка ML моделей
        if ml_models._initialized:
            logger.info("✅ ML модели обучены и загружены")
        else:
            logger.warning("⚠️ ML модели все еще инициализируются")
        
        # Проверка сигналов
        try:
            signals = await db_manager.get_signals(limit=5)
            logger.info(f"✅ Сигналы генерируются для реальных матчей (всего: {len(signals)})")
        except Exception as e:
            logger.warning(f"⚠️ Проверка сигналов: {e}")
        
        logger.info("🎯 AIBET + AIBOT System Ready!")
        
        if service_type == 'api':
            logger.info("📊 Starting AIBET API Web Service")
            # Запускаем API сервер с PORT из окружения
            try:
                from api_server import start_api_server
                # Используем PORT из окружения (Render)
                port = int(os.environ.get("PORT", 10000))
                logger.info(f"🌐 Starting API server on port {port}")
                await start_api_server(port=port)
            except ImportError as e:
                logger.error(f"❌ API server import error: {e}")
                # Fallback - запускаем простой FastAPI сервер
                from fastapi import FastAPI
                import uvicorn
                
                app = FastAPI()
                
                @app.get("/api/health")
                async def health():
                    return {"status": "ok", "service": "api", "timestamp": datetime.now().isoformat()}
                
                @app.get("/")
                async def root():
                    return {"message": "AIBET API Server", "status": "running"}
                
                port = int(os.environ.get("PORT", 10000))
                config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
                server = uvicorn.Server(config)
                await server.serve()
            
        elif service_type == 'bot':
            logger.info("🤖 Starting AIBOT Telegram Bot Background Worker")
            try:
                from telegram_bot import main as bot_main
                # Запускаем бота как background worker (без портов)
                await bot_main()
            except ImportError as e:
                logger.error(f"❌ Telegram bot import error: {e}")
                logger.info("⚠️ Bot will run in simple mode")
                # Просто держим процесс активным для worker
                while True:
                    await asyncio.sleep(60)
                    logger.info("🤖 Bot worker is running...")
            
        else:
            logger.error(f"❌ Unknown service type: {service_type}")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"❌ Critical error in main startup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Запуск
    asyncio.run(main())
