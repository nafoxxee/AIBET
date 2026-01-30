import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Callable, Any
from dataclasses import dataclass
from app.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TaskStatus:
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_running: bool = False
    error_count: int = 0
    last_error: Optional[str] = None


class Scheduler:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self._loop = None
    
    def add_task(self, name: str, func: Callable, interval_seconds: int, enabled: bool = True):
        """Add a scheduled task"""
        self.tasks[name] = {
            'func': func,
            'interval': interval_seconds,
            'enabled': enabled,
            'status': TaskStatus()
        }
        logger.info(f"Added task '{name}' with interval {interval_seconds}s")
    
    def enable_task(self, name: str, enabled: bool = True):
        """Enable or disable a task"""
        if name in self.tasks:
            self.tasks[name]['enabled'] = enabled
            logger.info(f"Task '{name}' {'enabled' if enabled else 'disabled'}")
    
    def get_task_status(self, name: str) -> TaskStatus:
        """Get status of a specific task"""
        if name in self.tasks:
            return self.tasks[name]['status']
        return TaskStatus()
    
    async def _run_task(self, name: str):
        """Run a single task"""
        task_info = self.tasks[name]
        status = task_info['status']
        
        if status.is_running or not task_info['enabled']:
            return
        
        now = datetime.now()
        
        # Check if it's time to run
        if status.next_run and now < status.next_run:
            return
        
        status.is_running = True
        status.last_run = now
        
        try:
            logger.info(f"Running task '{name}'")
            if asyncio.iscoroutinefunction(task_info['func']):
                await task_info['func']()
            else:
                task_info['func']()
            
            status.error_count = 0
            status.last_error = None
            logger.info(f"Task '{name}' completed successfully")
            
        except Exception as e:
            status.error_count += 1
            status.last_error = str(e)
            logger.error(f"Task '{name}' failed: {e}")
            
        finally:
            status.is_running = False
            # Schedule next run
            status.next_run = now + timedelta(seconds=task_info['interval'])
    
    async def _heartbeat(self):
        """Send heartbeat to Telegram channels"""
        try:
            from app.main import telegram_sender
            
            if config.telegram.bot_token:
                heartbeat_msg = f"🤖 AI BET Analytics - Heartbeat\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n✅ System operational"
                
                # Send to CS2 channel
                if config.telegram.cs2_channel_id:
                    await telegram_sender.send_message(config.telegram.cs2_channel_id, heartbeat_msg)
                
                # Send to KHL channel  
                if config.telegram.khl_channel_id:
                    await telegram_sender.send_message(config.telegram.khl_channel_id, heartbeat_msg)
                    
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
    
    async def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self._loop = asyncio.get_event_loop()
        
        # Add heartbeat task
        self.add_task('heartbeat', self._heartbeat, config.scheduler.heartbeat_interval)
        
        logger.info("Scheduler started")
        
        # Main scheduler loop
        while self.running:
            tasks_to_run = []
            
            for name in self.tasks:
                if self.tasks[name]['enabled']:
                    tasks_to_run.append(self._run_task(name))
            
            if tasks_to_run:
                await asyncio.gather(*tasks_to_run, return_exceptions=True)
            
            # Sleep for a short time before next check
            await asyncio.sleep(10)
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Scheduler stopped")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of all tasks"""
        summary = {
            'scheduler_running': self.running,
            'total_tasks': len(self.tasks),
            'enabled_tasks': sum(1 for t in self.tasks.values() if t['enabled']),
            'tasks': {}
        }
        
        for name, task_info in self.tasks.items():
            status = task_info['status']
            summary['tasks'][name] = {
                'enabled': task_info['enabled'],
                'interval': task_info['interval'],
                'last_run': status.last_run.isoformat() if status.last_run else None,
                'next_run': status.next_run.isoformat() if status.next_run else None,
                'is_running': status.is_running,
                'error_count': status.error_count,
                'last_error': status.last_error
            }
        
        return summary


# Global scheduler instance
scheduler = Scheduler()
