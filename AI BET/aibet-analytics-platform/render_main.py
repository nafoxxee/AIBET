#!/usr/bin/env python3
"""
Render deployment entry point for AI BET Analytics Platform
Runs both health check server and Telegram bot
"""

import asyncio
import logging
import threading
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_health_server():
    """Run health check server in separate thread"""
    import uvicorn
    from health_server import app
    
    logger.info("Starting health check server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

async def run_telegram_bot():
    """Run Telegram bot"""
    try:
        # Import and run the main application
        from app.main import main as telegram_main
        
        logger.info("Starting Telegram bot...")
        await telegram_main()
        
    except Exception as e:
        logger.error(f"Error in Telegram bot: {e}")
        # Keep the process alive even if bot fails
        while True:
            logger.info("Bot process alive, waiting...")
            await asyncio.sleep(300)  # Wait 5 minutes

def main():
    """Main entry point for Render deployment"""
    logger.info("🚀 Starting AI BET Analytics Platform on Render")
    logger.info(f"⏰ Started at: {datetime.now().isoformat()}")
    
    # Start health server in background thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Give health server time to start
    time.sleep(3)
    
    # Run Telegram bot in main thread
    try:
        asyncio.run(run_telegram_bot())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        # Keep process alive for Render
        while True:
            time.sleep(60)

if __name__ == "__main__":
    main()
