"""
AIBET Analytics Platform - Rate Limiting
"""

import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict, deque

from app.logging import setup_logging

logger = setup_logging(__name__)


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, requests: int = 100, window: int = 60):
        self.max_requests = requests
        self.window_seconds = window
        self._requests: Dict[str, deque] = defaultdict(lambda: deque())
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        async with self._lock:
            now = time.time()
            request_times = self._requests[identifier]
            
            # Remove old requests outside the window
            while request_times and request_times[0] <= now - self.window_seconds:
                request_times.popleft()
            
            # Check if under limit
            if len(request_times) < self.max_requests:
                request_times.append(now)
                return True
            
            logger.warning(f"Rate limit exceeded for {identifier}: {len(request_times)}/{self.max_requests}")
            return False
    
    async def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        async with self._lock:
            now = time.time()
            request_times = self._requests[identifier]
            
            # Remove old requests
            while request_times and request_times[0] <= now - self.window_seconds:
                request_times.popleft()
            
            return max(0, self.max_requests - len(request_times))
    
    async def get_reset_time(self, identifier: str) -> Optional[float]:
        """Get reset time for identifier"""
        async with self._lock:
            request_times = self._requests[identifier]
            
            if not request_times:
                return None
            
            # Reset time is when the oldest request expires
            return request_times[0] + self.window_seconds


class IPRateLimiter(RateLimiter):
    """IP-based rate limiter"""
    
    def __init__(self, requests: int = 100, window: int = 60):
        super().__init__(requests, window)
    
    async def is_allowed_ip(self, ip_address: str) -> bool:
        """Check if IP is allowed"""
        return await self.is_allowed(ip_address)


class UserAgentValidator:
    """User-Agent validation for security"""
    
    def __init__(self):
        self.blocked_patterns = [
            "bot",
            "crawler",
            "scraper",
            "spider",
            "curl",
            "wget"
        ]
    
    def is_valid_user_agent(self, user_agent: str) -> bool:
        """Validate User-Agent string"""
        if not user_agent:
            return False
        
        user_agent_lower = user_agent.lower()
        
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if pattern in user_agent_lower:
                logger.warning(f"Blocked User-Agent: {user_agent}")
                return False
        
        # Check minimum length
        if len(user_agent) < 10:
            return False
        
        return True


class LoopProtection:
    """Protection against request loops"""
    
    def __init__(self, max_requests_per_second: int = 10):
        self.max_rps = max_requests_per_second
        self._request_times: deque = deque()
        self._lock = asyncio.Lock()
    
    async def check_loop(self, identifier: str) -> bool:
        """Check for request loops"""
        async with self._lock:
            now = time.time()
            self._request_times.append(now)
            
            # Keep only last second of requests
            while self._request_times and self._request_times[0] <= now - 1.0:
                self._request_times.popleft()
            
            # Check if too many requests in last second
            if len(self._request_times) > self.max_rps:
                logger.warning(f"Loop protection triggered for {identifier}: {len(self._request_times)} RPS")
                return False
            
            return True


# Global instances
ip_rate_limiter = IPRateLimiter()
user_agent_validator = UserAgentValidator()
loop_protection = LoopProtection()
