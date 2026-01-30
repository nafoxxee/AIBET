import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class TelegramConfig:
    bot_token: Optional[str] = None
    cs2_channel_id: Optional[str] = None
    khl_channel_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.bot_token:
            print("⚠️  TELEGRAM_BOT_TOKEN not set. Please set environment variable or update config.")
        if not self.cs2_channel_id:
            print("⚠️  CS2_CHANNEL_ID not set. Please set environment variable or update config.")
        if not self.khl_channel_id:
            print("⚠️  KHL_CHANNEL_ID not set. Please set environment variable or update config.")


@dataclass
class DatabaseConfig:
    path: str = "storage/database.db"
    
    def __post_init__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)


@dataclass
class SchedulerConfig:
    cs2_check_interval: int = 300  # 5 minutes
    khl_check_interval: int = 300  # 5 minutes
    ml_retrain_interval: int = 86400  # 24 hours
    heartbeat_interval: int = 3600  # 1 hour


@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    enable_cors: bool = True
    max_connections: int = 1000
    websocket_ping_interval: int = 30


@dataclass
class AppConfig:
    telegram: TelegramConfig
    database: DatabaseConfig
    scheduler: SchedulerConfig
    api: APIConfig
    admin_telegram_ids: list
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        # Загрузка админских ID из переменных окружения
        admin_ids_str = os.getenv('ADMIN_TELEGRAM_IDS', '')
        admin_ids = []
        if admin_ids_str:
            try:
                admin_ids = [int(id.strip()) for id in admin_ids_str.split(',')]
            except ValueError:
                print("⚠️  Invalid ADMIN_TELEGRAM_IDS format. Use comma-separated integers.")
        
        return cls(
            telegram=TelegramConfig(
                bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
                cs2_channel_id=os.getenv('CS2_CHANNEL_ID'),
                khl_channel_id=os.getenv('KHL_CHANNEL_ID')
            ),
            database=DatabaseConfig(),
            scheduler=SchedulerConfig(),
            api=APIConfig(
                host=os.getenv('API_HOST', '0.0.0.0'),
                port=int(os.getenv('API_PORT', 8080)),
                enable_cors=os.getenv('ENABLE_CORS', 'true').lower() == 'true',
                max_connections=int(os.getenv('MAX_CONNECTIONS', 1000)),
                websocket_ping_interval=int(os.getenv('WEBSOCKET_PING_INTERVAL', 30))
            ),
            admin_telegram_ids=admin_ids
        )


# Global config instance
config = AppConfig.from_env()
