#!/usr/bin/env python3
"""
AI BET Analytics - Scheduler Worker
Background worker for scheduled tasks on Render
"""

import asyncio
import logging
import signal
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import config
from app.scheduler import scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GracefulExit:
    shutdown = False
    
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
    
    def exit_gracefully(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown = True
        scheduler.stop()

async def main():
    """Main worker function"""
    logger.info("🚀 AI BET Analytics Scheduler Worker Starting...")
    
    # Initialize graceful exit handler
    graceful_exit = GracefulExit()
    
    # Import and setup sport modules
    try:
        from cs2.sources.hltv_parser import setup_cs2_tasks
        from khl.sources.matches_parser import setup_khl_tasks
        
        # Setup tasks for each sport
        setup_cs2_tasks(scheduler)
        setup_khl_tasks(scheduler)
        
        logger.info("✅ All sport modules loaded successfully")
        
    except ImportError as e:
        logger.error(f"❌ Failed to import sport modules: {e}")
        return
    
    # Start scheduler
    try:
        logger.info("🔄 Starting scheduler...")
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("⏹️ Scheduler stopped by user")
    except Exception as e:
        logger.error(f"💥 Scheduler failed: {e}")
    finally:
        logger.info("🛑 Scheduler worker stopped")

if __name__ == "__main__":
    asyncio.run(main())
