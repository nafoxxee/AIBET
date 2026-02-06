"""
AIBET Analytics Platform - Metrics Collection
"""

import time
import asyncio
from typing import Dict, Any
from collections import defaultdict, deque
from datetime import datetime

from app.logging import setup_logging

logger = setup_logging(__name__)


class MetricsCollector:
    """Metrics collector for application monitoring"""
    
    def __init__(self):
        self._metrics = {
            "uptime": time.time(),
            "requests_total": 0,
            "requests_by_endpoint": defaultdict(int),
            "response_times": deque(maxlen=1000),
            "cache_hits": 0,
            "cache_misses": 0,
            "source_failures": defaultdict(int),
            "errors": defaultdict(int)
        }
        self._lock = asyncio.Lock()
    
    async def increment_requests(self, endpoint: str = "unknown"):
        """Increment request counter"""
        async with self._lock:
            self._metrics["requests_total"] += 1
            self._metrics["requests_by_endpoint"][endpoint] += 1
    
    async def record_response_time(self, duration: float):
        """Record response time"""
        async with self._lock:
            self._metrics["response_times"].append(duration)
    
    async def increment_cache_hits(self):
        """Increment cache hit counter"""
        async with self._lock:
            self._metrics["cache_hits"] += 1
    
    async def increment_cache_misses(self):
        """Increment cache miss counter"""
        async with self._lock:
            self._metrics["cache_misses"] += 1
    
    async def record_source_failure(self, source: str):
        """Record source failure"""
        async with self._lock:
            self._metrics["source_failures"][source] += 1
    
    async def record_error(self, error_type: str):
        """Record error"""
        async with self._lock:
            self._metrics["errors"][error_type] += 1
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        async with self._lock:
            response_times = list(self._metrics["response_times"])
            
            return {
                "uptime_seconds": int(time.time() - self._metrics["uptime"]),
                "requests_total": self._metrics["requests_total"],
                "requests_by_endpoint": dict(self._metrics["requests_by_endpoint"]),
                "response_time_stats": {
                    "avg": sum(response_times) / len(response_times) if response_times else 0,
                    "min": min(response_times) if response_times else 0,
                    "max": max(response_times) if response_times else 0,
                    "p95": self._percentile(response_times, 0.95) if response_times else 0
                },
                "cache_stats": {
                    "hits": self._metrics["cache_hits"],
                    "misses": self._metrics["cache_misses"],
                    "hit_ratio": (
                        self._metrics["cache_hits"] / 
                        max(self._metrics["cache_hits"] + self._metrics["cache_misses"], 1)
                    )
                },
                "source_failures": dict(self._metrics["source_failures"]),
                "errors": dict(self._metrics["errors"]),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _percentile(self, data: list, percentile: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def startup(self):
        """Record startup"""
        logger.info("Metrics collector started")
    
    def shutdown(self):
        """Record shutdown"""
        logger.info("Metrics collector stopped")


# Global metrics instance
metrics = MetricsCollector()
