"""
AIBET Analytics Platform - Configuration
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Server
    PORT: int = 8000
    DEBUG: bool = False
    
    # Service toggles
    ENABLE_NHL: bool = True
    ENABLE_KHL: bool = True
    ENABLE_CS2: bool = True
    
    # Cache TTL (seconds)
    TTL_NHL: int = 300  # 5 minutes
    TTL_KHL: int = 600  # 10 minutes
    TTL_CS2: int = 300  # 5 minutes
    TTL_ODDS: int = 180  # 3 minutes
    
    # Cache settings
    CACHE_MAX_ITEMS: int = 1000
    
    # AI settings
    AI_EXPLAIN_MODE: bool = True
    
    # Security
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Service configuration
SERVICE_CONFIG = {
    "nhl": {
        "enabled": settings.ENABLE_NHL,
        "ttl": settings.TTL_NHL,
        "base_url": "https://api-web.nhle.com"
    },
    "khl": {
        "enabled": settings.ENABLE_KHL,
        "ttl": settings.TTL_KHL,
        "base_url": "https://khl.ru"
    },
    "cs2": {
        "enabled": settings.ENABLE_CS2,
        "ttl": settings.TTL_CS2,
        "base_url": "https://hltv.org"
    },
    "odds": {
        "ttl": settings.TTL_ODDS
    }
}
