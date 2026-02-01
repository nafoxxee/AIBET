#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real Main Entry Point
Полностью переработанный запуск с реальными данными
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
        return {"message": "AIBET Real Bot Health Server", "status": "running"}
    
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
    """Инициализация всех компонентов с реальными данными"""
    logger.info("🔧 Initializing real components")
    
    service_type = os.getenv('SERVICE_TYPE', 'web')
    logger.info(f"🔧 Service type: {service_type}")
    
    try:
        # Инициализируем ML модели с реальными данными
        from ml_real import real_ml_models
        global ml_models
        ml_models = real_ml_models
        await ml_models.initialize()
        logger.info("✅ Real ML Models initialized")
        
        if service_type == 'bot':
            # ТОЛЬКО для Bot сервиса: инициализируем Telegram Bot
            from telegram_bot_real import RealTelegramBot
            global telegram_bot
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                raise ValueError("❌ TELEGRAM_BOT_TOKEN is required for bot service")
            
            # Проверяем тип токена
            if not isinstance(bot_token, str):
                raise ValueError(f"❌ TELEGRAM_BOT_TOKEN must be str, got {type(bot_token)}")
            
            # Проверяем формат токена
            if len(bot_token) < 10 or ':' not in bot_token:
                raise ValueError("❌ TELEGRAM_BOT_TOKEN appears to be invalid (too short or missing ':')")
            
            logger.info(f"✅ Telegram token validated: {bot_token[:10]}...")
            admin_id = int(os.getenv("ADMIN_ID", "379036860"))
            telegram_bot = RealTelegramBot(bot_token, admin_id, db_manager)
            await telegram_bot.initialize()
            logger.info("✅ Real Telegram Bot initialized")
            
        elif service_type == 'web':
            # ТОЛЬКО для Web сервиса: инициализируем Mini App
            from mini_app_real import RealMiniApp
            global mini_app
            mini_app = RealMiniApp(db_manager, ml_models)
            logger.info("✅ Real Mini App initialized")
        
        return True
        
    except Exception as e:
        logger.exception(f"❌ Error initializing components: {e}")
        return False

async def start_real_data_collection(db_manager):
    """Сбор реальных данных"""
    logger.info("📊 Starting real data collection")
    try:
        from data_sources.cs2_real import cs2_real_source
        from data_sources.khl_real import khl_real_source
        
        # Запускаем сбор данных
        cs2_count = await cs2_real_source.update_database()
        khl_count = await khl_real_source.update_database()
        
        logger.info(f"✅ Real data collection completed: CS2={cs2_count}, KHL={khl_count}")
    except Exception as e:
        logger.warning(f"⚠️ Error in real data collection: {e}")
        # Не падаем, продолжаем запуск

async def start_feature_engineering():
    """Запуск feature engineering"""
    logger.info("🔧 Starting feature engineering")
    try:
        from feature_engineering import feature_engineering
        updated_count = await feature_engineering.update_all_matches_features()
        logger.info(f"✅ Feature engineering completed: {updated_count} matches updated")
    except Exception as e:
        logger.warning(f"⚠️ Error in feature engineering: {e}")

async def start_ml_training():
    """Запуск обучения ML"""
    logger.info("🤖 Starting ML training")
    try:
        from ml_real import real_ml_models
        success = await real_ml_models.train_models()
        if success:
            logger.info("✅ ML training completed successfully")
        else:
            logger.info("⚠️ ML training skipped (insufficient data)")
    except Exception as e:
        logger.warning(f"⚠️ Error in ML training: {e}")

async def start_signal_generation():
    """Запуск генерации сигналов"""
    logger.info("🎯 Starting signal generation")
    try:
        from signal_generator_real import real_signal_generator
        signals = await real_signal_generator.generate_signals()
        logger.info(f"✅ Signal generation completed: {len(signals)} signals generated")
    except Exception as e:
        logger.warning(f"⚠️ Error in signal generation: {e}")

async def start_background_services():
    """Запуск фоновых сервисов"""
    logger.info("🔄 Starting background services")
    
    try:
        # 1. Сбор реальных данных
        asyncio.create_task(start_real_data_collection(None))
        
        # 2. Feature engineering
        asyncio.create_task(start_feature_engineering())
        
        # 3. Обучение ML
        asyncio.create_task(start_ml_training())
        
        # 4. Генерация сигналов
        asyncio.create_task(start_signal_generation())
        
        # 5. Авто-публикация (только для бота)
        service_type = os.getenv('SERVICE_TYPE', 'web')
        if service_type == 'bot':
            from auto_publisher_real import create_real_auto_publisher
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if bot_token:
                auto_publisher = create_real_auto_publisher(bot_token)
                await auto_publisher.initialize()
                asyncio.create_task(auto_publisher.start_auto_publishing())
                logger.info("✅ Auto publisher started")
        
        logger.info("✅ All background services started")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ Error starting background services: {e}")
        return False

async def main():
    """Главная функция запуска"""
    logger.info("🚀 Starting AIBET Real Analytics Platform")
    
    # Определение типа сервиса
    service_type = os.getenv('SERVICE_TYPE', 'web')
    
    try:
        # 1. Инициализируем базу данных
        db_manager = await initialize_database()
        
        # 2. Инициализируем компоненты
        components_ready = await initialize_components(db_manager)
        if not components_ready:
            logger.error("❌ Failed to initialize components")
            sys.exit(1)
        
        # 3. Запускаем фоновые сервисы
        await start_background_services()
        
        # 4. Финальная проверка системы
        logger.info("🔍 Running final system checks...")
        
        # Проверка токенов
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if bot_token and isinstance(bot_token, str) and ':' in bot_token:
            logger.info("✅ Telegram токены корректны")
        else:
            logger.warning("⚠️ Telegram токены требуют проверки")
        
        # Проверка ML моделей
        if ml_models._trained:
            logger.info("✅ ML модели обучены и загружены")
        else:
            logger.info("⚠️ ML модели в процессе обучения")
        
        # Проверка данных
        try:
            matches = await db_manager.get_matches(limit=10)
            logger.info(f"✅ В базе данных {len(matches)} матчей")
        except Exception as e:
            logger.warning(f"⚠️ Проверка данных: {e}")
        
        logger.info("🎯 AIBET Real System Ready!")
        
        if service_type == 'web':
            logger.info("📊 Starting AIBET Real Mini App Web Service")
            # Запускаем Mini App с health сервером
            await asyncio.gather(
                mini_app.run(),
                health_server()
            )
            
        elif service_type == 'bot':
            logger.info("🤖 Starting AIBOT Real Telegram Bot Web Service")
            from telegram_bot_real import main as bot_main
            
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
