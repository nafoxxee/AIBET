import os
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class TelegramConfig:
    bot_token: Optional[str] = None
    cs2_channel_id: Optional[str] = None
    khl_channel_id: Optional[str] = None
    admin_ids: List[int] = None
    cs2_channel: Optional[str] = None  # @aibetcsgo
    khl_channel: Optional[str] = None  # @aibetkhl
    admin_id: Optional[int] = None
    web_app_url: Optional[str] = None
    
    def __post_init__(self):
        if self.admin_ids is None:
            admin_ids_str = os.getenv('ADMIN_TELEGRAM_IDS', '')
            self.admin_ids = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()] if admin_ids_str else []


@dataclass
class DatabaseConfig:
    path: str = "database.db"
    
    def __post_init__(self):
        os.makedirs(os.path.dirname(self.path) if os.path.dirname(self.path) else '.', exist_ok=True)


@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    webhook_url: Optional[str] = None
    render_port: int = 10000  # Render default port


@dataclass
class MLConfig:
    model_retrain_interval: int = 86400  # 24 hours
    min_training_samples: int = 100
    confidence_threshold: float = 0.6


@dataclass
class SchedulerConfig:
    cs2_check_interval: int = 300  # 5 minutes
    khl_check_interval: int = 600  # 10 minutes


@dataclass
class AppConfig:
    telegram: TelegramConfig
    database: DatabaseConfig
    api: APIConfig
    ml: MLConfig
    scheduler: SchedulerConfig
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        return cls(
            telegram=TelegramConfig(
                bot_token=os.getenv('TELEGRAM_BOT_TOKEN', '8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4'),
                cs2_channel_id=os.getenv('CS2_CHANNEL_ID'),
                khl_channel_id=os.getenv('KHL_CHANNEL_ID'),
                cs2_channel=os.getenv('CS2_CHANNEL', '@aibetcsgo'),
                khl_channel=os.getenv('KHL_CHANNEL', '@aibetkhl'),
                admin_id=int(os.getenv('ADMIN_ID', '379036860')),
                web_app_url=os.getenv('AIBET_WEB_URL', 'https://aibet-mini-app.onrender.com')
            ),
            database=DatabaseConfig(
                path=os.getenv('DATABASE_PATH', 'database.db')
            ),
            api=APIConfig(
                host=os.getenv('API_HOST', '0.0.0.0'),
                port=int(os.getenv('API_PORT', 8080)),
                webhook_url=os.getenv('WEBHOOK_URL'),
                render_port=int(os.getenv('PORT', 10000))
            ),
            ml=MLConfig(
                model_retrain_interval=int(os.getenv('ML_RETRAIN_INTERVAL', 86400)),
                min_training_samples=int(os.getenv('ML_MIN_TRAINING_SAMPLES', 100)),
                confidence_threshold=float(os.getenv('ML_CONFIDENCE_THRESHOLD', 0.6))
            ),
            scheduler=SchedulerConfig(
                cs2_check_interval=int(os.getenv('CS2_CHECK_INTERVAL', 300)),
                khl_check_interval=int(os.getenv('KHL_CHECK_INTERVAL', 600))
            )
        )


# Global config instance
config = AppConfig.from_env()
