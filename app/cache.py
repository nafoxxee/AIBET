"""
AIBET Analytics Platform - In-memory TTL Cache
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CacheItem:
    """Cache item with TTL"""
    data: Any
    timestamp: float
    ttl: int
    
    @property
    def is_expired(self) -> bool:
        """Check if cache item is expired"""
        return time.time() > (self.timestamp + self.ttl)


class InMemoryCache:
    """In-memory TTL cache implementation"""
    
    def __init__(self, max_items: int = 1000):
        self.max_items = max_items
        self._cache: Dict[str, CacheItem] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        async with self._lock:
            item = self._cache.get(key)
            if item is None:
                return None
            
            if item.is_expired:
                del self._cache[key]
                logger.debug(f"Cache expired for key: {key}")
                return None
            
            logger.debug(f"Cache hit for key: {key}")
            return item.data
    
    async def set(self, key: str, data: Any, ttl: int = 300) -> None:
        """Set item in cache with TTL"""
        async with self._lock:
            # Remove oldest items if cache is full
            if len(self._cache) >= self.max_items:
                oldest_key = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].timestamp
                )
                del self._cache[oldest_key]
                logger.debug(f"Cache evicted oldest key: {oldest_key}")
            
            self._cache[key] = CacheItem(
                data=data,
                timestamp=time.time(),
                ttl=ttl
            )
            logger.debug(f"Cache set for key: {key} (TTL: {ttl}s)")
    
    async def delete(self, key: str) -> bool:
        """Delete item from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted for key: {key}")
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache"""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    async def cleanup_expired(self) -> int:
        """Clean up expired items"""
        async with self._lock:
            expired_keys = [
                key for key, item in self._cache.items()
                if item.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache items")
            
            return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            total_items = len(self._cache)
            expired_items = sum(
                1 for item in self._cache.values()
                if item.is_expired
            )
            
            return {
                "total_items": total_items,
                "expired_items": expired_items,
                "max_items": self.max_items,
                "hit_ratio": getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for cache"""
        stats = await self.get_stats()
        return {
            "status": "healthy" if stats["total_items"] < self.max_items else "warning",
            "stats": stats
        }


class CacheManager:
    """Cache manager for different data types"""
    
    def __init__(self):
        self.caches = {}
    
    async def initialize(self):
        """Initialize all caches"""
        from app.config import settings
        
        self.caches = {
            "nhl": InMemoryCache(max_items=settings.CACHE_MAX_ITEMS),
            "khl": InMemoryCache(max_items=settings.CACHE_MAX_ITEMS),
            "cs2": InMemoryCache(max_items=settings.CACHE_MAX_ITEMS),
            "odds": InMemoryCache(max_items=settings.CACHE_MAX_ITEMS),
            "ai": InMemoryCache(max_items=settings.CACHE_MAX_ITEMS // 2)
        }
        logger.info("Cache manager initialized")
    
    async def get_cache(self, cache_type: str) -> InMemoryCache:
        """Get cache by type"""
        return self.caches.get(cache_type)
    
    async def cleanup(self):
        """Cleanup all caches"""
        for cache in self.caches.values():
            await cache.clear()
        logger.info("All caches cleaned up")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for all caches"""
        return {
            cache_type: await cache.health_check()
            for cache_type, cache in self.caches.items()
        }


# Global cache manager
cache_manager = CacheManager()
