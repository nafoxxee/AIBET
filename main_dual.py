#!/usr/bin/env python3
"""
AIBET Analytics Platform - Main Entry Point
Запуск двух сервисов: Mini App и Telegram Bot
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

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
        logger.info("🤖 Starting AIBOT Telegram Bot Service")
        from telegram_bot import main as bot_main
        await bot_main()
    else:
        logger.error(f"❌ Unknown service type: {service_type}")
        sys.exit(1)

if __name__ == "__main__":
    # Создание директории для логов
    os.makedirs("logs", exist_ok=True)
    
    # Запуск
    asyncio.run(main())
