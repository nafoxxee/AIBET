"""
AIBET Analytics Platform - Time Utilities
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Union


class TimeUtils:
    """Time utilities for the platform"""
    
    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC time"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def parse_datetime(datetime_str: str, default: Optional[datetime] = None) -> datetime:
        """Parse datetime string with fallback"""
        if not datetime_str:
            return default or TimeUtils.utc_now()
        
        # Common datetime formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d.%m.%Y %H:%M:%S",
            "%d.%m.%Y",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(datetime_str, fmt)
                # Ensure timezone is UTC if not specified
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        # Return default if parsing fails
        return default or TimeUtils.utc_now()
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
        """Format datetime to string"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        
        return dt.strftime(format_str)
    
    @staticmethod
    def is_future(dt: datetime) -> bool:
        """Check if datetime is in the future"""
        return dt > TimeUtils.utc_now()
    
    @staticmethod
    def is_past(dt: datetime, hours: int = 24) -> bool:
        """Check if datetime is in the past by specified hours"""
        cutoff = TimeUtils.utc_now() - timedelta(hours=hours)
        return dt < cutoff
    
    @staticmethod
    def time_until(dt: datetime) -> timedelta:
        """Get time until datetime"""
        now = TimeUtils.utc_now()
        return dt - now if dt > now else timedelta(0)
    
    @staticmethod
    def time_since(dt: datetime) -> timedelta:
        """Get time since datetime"""
        now = TimeUtils.utc_now()
        return now - dt if dt < now else timedelta(0)
    
    @staticmethod
    def seconds_to_human(seconds: float) -> str:
        """Convert seconds to human readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}h"
        else:
            days = seconds / 86400
            return f"{days:.1f}d"
    
    @staticmethod
    def get_time_window(start_time: datetime, window_hours: int = 24) -> tuple:
        """Get time window around start time"""
        start = start_time - timedelta(hours=window_hours)
        end = start_time + timedelta(hours=window_hours)
        return start, end
    
    @staticmethod
    def is_business_hours(dt: datetime) -> bool:
        """Check if datetime is during business hours (9-17 UTC)"""
        return 9 <= dt.hour <= 17
    
    @staticmethod
    def get_cache_ttl(league: str, default_ttl: int = 300) -> int:
        """Get cache TTL for league"""
        from app.config import SERVICE_CONFIG
        
        if league.lower() in SERVICE_CONFIG:
            return SERVICE_CONFIG[league.lower()]["ttl"]
        
        return default_ttl
    
    @staticmethod
    def timestamp_ms() -> int:
        """Get current timestamp in milliseconds"""
        return int(time.time() * 1000)
    
    @staticmethod
    def from_timestamp_ms(timestamp_ms: int) -> datetime:
        """Convert timestamp from milliseconds to datetime"""
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)


# Global instance
time_utils = TimeUtils()
