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

if __name__ == "__main__":
    # Запуск
    asyncio.run(main())
