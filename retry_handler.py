#!/usr/bin/env python3
"""
AIBET Analytics Platform - Comprehensive Retry Handler
Универсальная обработка ошибок и повторных попыток с логированием
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, Dict, List, Union
from functools import wraps
from enum import Enum
import json

logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    """Стратегии повторных попыток"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    JITTER = "jitter"

class RetryError(Exception):
    """Исключение для ошибок повторных попыток"""
    def __init__(self, message: str, attempts: int, last_exception: Exception):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception

class RetryHandler:
    def __init__(self):
        self.default_config = {
            "max_attempts": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "backoff_multiplier": 2.0,
            "jitter_factor": 0.1,
            "strategy": RetryStrategy.EXPONENTIAL_BACKOFF,
            "retry_on": [Exception],  # По умолчанию retry на все исключения
            "log_level": logging.WARNING
        }
        
        # Статистика попыток
        self.attempt_stats = {
            "total_attempts": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "errors_by_type": {},
            "last_update": datetime.now()
        }
    
    def calculate_delay(self, attempt: int, strategy: RetryStrategy, config: Dict[str, Any]) -> float:
        """Рассчитать задержку между попытками"""
        if strategy == RetryStrategy.FIXED_DELAY:
            delay = config["base_delay"]
        
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config["base_delay"] * attempt
        
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config["base_delay"] * (config["backoff_multiplier"] ** (attempt - 1))
        
        elif strategy == RetryStrategy.JITTER:
            base = config["base_delay"] * (config["backoff_multiplier"] ** (attempt - 1))
            jitter = base * config["jitter_factor"] * random.uniform(-1, 1)
            delay = max(0, base + jitter)
        
        else:
            delay = config["base_delay"]
        
        # Ограничиваем максимальную задержку
        return min(delay, config["max_delay"])
    
    def should_retry(self, exception: Exception, retry_on: List[type]) -> bool:
        """Определить, нужно ли повторять попытку"""
        return any(isinstance(exception, exc_type) for exc_type in retry_on)
    
    def log_attempt(self, attempt: int, max_attempts: int, delay: float, 
                   exception: Exception, operation: str, config: Dict[str, Any]):
        """Логировать попытку"""
        log_level = config.get("log_level", logging.WARNING)
        
        # Обновляем статистику
        self.attempt_stats["total_attempts"] += 1
        exc_type = type(exception).__name__
        self.attempt_stats["errors_by_type"][exc_type] = self.attempt_stats["errors_by_type"].get(exc_type, 0) + 1
        
        if attempt == 1:
            logger.log(log_level, f"⚠️ {operation} failed (attempt {attempt}/{max_attempts}): {exception}")
            logger.log(log_level, f"⏱️ Retrying in {delay:.2f}s...")
        else:
            logger.log(log_level, f"⚠️ {operation} failed again (attempt {attempt}/{max_attempts}): {exception}")
            logger.log(log_level, f"⏱️ Retrying in {delay:.2f}s...")
    
    def log_success(self, attempt: int, operation: str):
        """Логировать успешное выполнение"""
        if attempt > 1:
            self.attempt_stats["successful_retries"] += 1
            logger.info(f"✅ {operation} succeeded after {attempt} attempts")
        else:
            logger.debug(f"✅ {operation} succeeded on first attempt")
    
    def log_failure(self, attempt: int, max_attempts: int, operation: str, last_exception: Exception):
        """Логировать окончательную неудачу"""
        self.attempt_stats["failed_retries"] += 1
        logger.error(f"❌ {operation} failed after {max_attempts} attempts")
        logger.error(f"❌ Final error: {last_exception}")
    
    async def retry_async(self, func: Callable, *args, **kwargs) -> Any:
        """Асинхронная функция с retry"""
        config = kwargs.pop("retry_config", self.default_config.copy())
        operation_name = kwargs.pop("operation", func.__name__)
        
        max_attempts = config["max_attempts"]
        strategy = config["strategy"]
        retry_on = config["retry_on"]
        
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                
                if attempt > 1:
                    self.log_success(attempt, operation_name)
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt == max_attempts or not self.should_retry(e, retry_on):
                    self.log_failure(attempt, max_attempts, operation_name, e)
                    raise RetryError(
                        f"{operation_name} failed after {attempt} attempts",
                        attempt,
                        e
                    )
                
                delay = self.calculate_delay(attempt, strategy, config)
                self.log_attempt(attempt, max_attempts, delay, e, operation_name, config)
                
                await asyncio.sleep(delay)
    
    def retry_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Синхронная функция с retry"""
        config = kwargs.pop("retry_config", self.default_config.copy())
        operation_name = kwargs.pop("operation", func.__name__)
        
        max_attempts = config["max_attempts"]
        strategy = config["strategy"]
        retry_on = config["retry_on"]
        
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                
                if attempt > 1:
                    self.log_success(attempt, operation_name)
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt == max_attempts or not self.should_retry(e, retry_on):
                    self.log_failure(attempt, max_attempts, operation_name, e)
                    raise RetryError(
                        f"{operation_name} failed after {attempt} attempts",
                        attempt,
                        e
                    )
                
                delay = self.calculate_delay(attempt, strategy, config)
                self.log_attempt(attempt, max_attempts, delay, e, operation_name, config)
                
                time.sleep(delay)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику попыток"""
        return {
            **self.attempt_stats,
            "success_rate": (
                self.attempt_stats["successful_retries"] / 
                max(1, self.attempt_stats["total_attempts"])
            ) * 100
        }
    
    def reset_stats(self):
        """Сбросить статистику"""
        self.attempt_stats = {
            "total_attempts": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "errors_by_type": {},
            "last_update": datetime.now()
        }

# Глобальный экземпляр
retry_handler = RetryHandler()

# Декораторы для удобного использования
def retry_async(**retry_kwargs):
    """Декоратор для асинхронных функций"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_handler.retry_async(func, *args, **kwargs, **retry_kwargs)
        return wrapper
    return decorator

def retry_sync(**retry_kwargs):
    """Декоратор для синхронных функций"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_handler.retry_sync(func, *args, **kwargs, **retry_kwargs)
        return wrapper
    return decorator

# Преднастроенные конфигурации для разных типов операций
NETWORK_CONFIG = {
    "max_attempts": 5,
    "base_delay": 2.0,
    "max_delay": 30.0,
    "strategy": RetryStrategy.EXPONENTIAL_BACKOFF,
    "retry_on": [ConnectionError, TimeoutError, OSError],
    "log_level": logging.WARNING
}

DATABASE_CONFIG = {
    "max_attempts": 3,
    "base_delay": 1.0,
    "max_delay": 10.0,
    "strategy": RetryStrategy.LINEAR_BACKOFF,
    "retry_on": [ConnectionError, TimeoutError],
    "log_level": logging.WARNING
}

PARSING_CONFIG = {
    "max_attempts": 3,
    "base_delay": 5.0,
    "max_delay": 60.0,
    "strategy": RetryStrategy.EXPONENTIAL_BACKOFF,
    "retry_on": [ConnectionError, TimeoutError, HTTPError, ValueError],
    "log_level": logging.WARNING
}

ML_CONFIG = {
    "max_attempts": 2,
    "base_delay": 1.0,
    "max_delay": 5.0,
    "strategy": RetryStrategy.FIXED_DELAY,
    "retry_on": [ValueError, RuntimeError],
    "log_level": logging.ERROR
}

# Контекстный менеджер для операций с retry
class RetryContext:
    def __init__(self, operation: str, config: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.config = config or retry_handler.default_config.copy()
        self.start_time = None
        self.attempts = 0
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.attempts += 1
            duration = time.time() - self.start_time
            logger.error(f"❌ {self.operation} failed after {duration:.2f}s ({self.attempts} attempts)")
        else:
            duration = time.time() - self.start_time
            logger.debug(f"✅ {self.operation} completed in {duration:.2f}s")
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Выполнить функцию с retry"""
        return await retry_handler.retry_async(
            func, *args, 
            operation=self.operation,
            retry_config=self.config,
            **kwargs
        )

# Утилиты для мониторинга и отчетности
class RetryMonitor:
    def __init__(self):
        self.alert_threshold = 0.5  # 50% failure rate threshold
        self.check_interval = 300  # 5 minutes
    
    async def start_monitoring(self):
        """Запустить мониторинг retry статистики"""
        logger.info("🔍 Starting retry monitoring")
        
        while True:
            try:
                stats = retry_handler.get_stats()
                
                # Проверяем порог сбоев
                failure_rate = 100 - stats["success_rate"]
                if failure_rate > self.alert_threshold * 100:
                    logger.warning(f"🚨 High failure rate detected: {failure_rate:.1f}%")
                    await self.send_alert(stats)
                
                # Логируем статистику
                logger.info(f"📊 Retry stats: {stats['total_attempts']} attempts, "
                           f"{stats['success_rate']:.1f}% success rate")
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in retry monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def send_alert(self, stats: Dict[str, Any]):
        """Отправить алерт о высоком уровне сбоев"""
        # Здесь можно добавить отправку в Telegram, email и т.д.
        alert_message = f"""
🚨 **High Failure Rate Alert**

**Stats:**
- Total attempts: {stats['total_attempts']}
- Success rate: {stats['success_rate']:.1f}%
- Failed retries: {stats['failed_retries']}

**Top Errors:**
{self._format_errors(stats['errors_by_type'])}

**Time:** {datetime.now().isoformat()}
        """
        
        logger.error(alert_message)
    
    def _format_errors(self, errors: Dict[str, int]) -> str:
        """Форматировать ошибки для алерта"""
        sorted_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)
        return "\n".join([f"- {err_type}: {count}" for err_type, count in sorted_errors[:5]])

# Глобальный монитор
retry_monitor = RetryMonitor()

# Примеры использования
if __name__ == "__main__":
    # Асинхронная функция с retry
    @retry_async(max_attempts=3, base_delay=1.0, operation="test_operation")
    async def test_async_function():
        # Симуляция случайной ошибки
        if random.random() < 0.7:
            raise ConnectionError("Random connection error")
        return "Success!"
    
    # Синхронная функция с retry
    @retry_sync(max_attempts=2, operation="test_sync")
    def test_sync_function():
        if random.random() < 0.5:
            raise ValueError("Random value error")
        return "Sync success!"
    
    async def main():
        # Тест асинхронной функции
        try:
            result = await test_async_function()
            print(f"Async result: {result}")
        except RetryError as e:
            print(f"Async failed: {e}")
        
        # Тест синхронной функции
        try:
            result = test_sync_function()
            print(f"Sync result: {result}")
        except RetryError as e:
            print(f"Sync failed: {e}")
        
        # Тест контекстного менеджера
        async with RetryContext("context_test", NETWORK_CONFIG) as ctx:
            try:
                result = await ctx.execute(test_async_function)
                print(f"Context result: {result}")
            except RetryError as e:
                print(f"Context failed: {e}")
    
    asyncio.run(main())
