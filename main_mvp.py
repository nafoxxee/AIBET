#!/usr/bin/env python3
"""
AIBET MVP - Main Entry Point
Senior Full-Stack Implementation
"""

import asyncio
import logging
import os
import sys
import signal
from typing import Optional

# Создание директории для логов
os.makedirs("logs", exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mvp.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class AIBETMVP:
    """AIBET MVP Application"""
    
    def __init__(self):
        self.service_type = os.getenv("SERVICE_TYPE", "api")
        self.api_server = None
        self.telegram_bot = None
        self.running = False
        
    async def initialize(self):
        """Initialize application components"""
        try:
            logger.info("🚀 Initializing AIBET MVP...")
            
            # Initialize database
            from database.connection import init_database
            db_success = await init_database()
            
            if not db_success:
                logger.error("❌ Database initialization failed")
                return False
            
            logger.info("✅ Database initialized")
            
            # Initialize ML models
            from database.connection import get_db_context
            from ml.predictor import Predictor
            
            with get_db_context() as db:
                predictor = Predictor(db)
                predictor.initialize_models('cs2')
                predictor.initialize_models('khl')
            
            logger.info("✅ ML models initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def start_api_server(self):
        """Start FastAPI server"""
        try:
            logger.info("🌐 Starting FastAPI server...")
            
            import uvicorn
            from api.main import app
            
            # Use PORT from environment (Render sets this)
            port = int(os.getenv("PORT", 1000))
            
            config = uvicorn.Config(
                app,
                host="0.0.0.0",
                port=port,
                log_level="info",
                access_log=True
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"❌ API server error: {e}")
            raise
    
    async def start_telegram_bot(self):
        """Start Telegram bot"""
        try:
            logger.info("🤖 Starting Telegram bot...")
            
            from bot.main import create_bot
            
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            admin_id = int(os.getenv("ADMIN_ID", "379036860"))
            
            if not bot_token:
                raise ValueError("TELEGRAM_BOT_TOKEN not found")
            
            bot = await create_bot(bot_token, admin_id)
            await bot.start()
            
        except Exception as e:
            logger.error(f"❌ Telegram bot error: {e}")
            raise
    
    async def run(self):
        """Run the application"""
        try:
            logger.info(f"🚀 Starting AIBET MVP (Service: {self.service_type})")
            
            # Initialize
            if not await self.initialize():
                return
            
            self.running = True
            
            # Start based on service type
            if self.service_type == "api":
                await self.start_api_server()
            elif self.service_type == "bot":
                await self.start_telegram_bot()
            else:
                logger.error(f"❌ Unknown service type: {self.service_type}")
                return
            
        except KeyboardInterrupt:
            logger.info("⏹️ Received shutdown signal")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
        finally:
            self.running = False
            logger.info("🏁 AIBET MVP stopped")

async def main():
    """Main entry point"""
    app = AIBETMVP()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())
