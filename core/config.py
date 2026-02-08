"""
AIBET Core Configuration
"""

import os
from typing import Optional


class Config:
    """Application configuration"""
    
    # Bot configuration
    BOT_TOKEN: Optional[str] = os.getenv("BOT_TOKEN")
    
    # API configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Debug mode
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")
        
        print(f"✅ Configuration validated")
        print(f"🤖 Bot Token: {cls.BOT_TOKEN[:10]}...")
        print(f"🌐 API: {cls.API_HOST}:{cls.API_PORT}")
        print(f"🐛 Debug: {cls.DEBUG}")


# Global configuration instance
config = Config()
