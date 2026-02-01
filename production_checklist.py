#!/usr/bin/env python3
"""
AIBET Production Checklist
Проверка всех компонентов перед деплоем
"""

import asyncio
import logging
import sys
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionChecklist:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
    
    def check(self, name: str, condition: bool, message: str = ""):
        """Выполнить проверку"""
        self.checks.append({
            "name": name,
            "passed": condition,
            "message": message
        })
        
        if condition:
            self.passed += 1
            logger.info(f"✅ {name}")
        else:
            self.failed += 1
            logger.error(f"❌ {name} - {message}")
    
    async def check_imports(self):
        """Проверить импорты"""
        logger.info("🔍 Checking imports...")
        
        try:
            # Парсеры
            from parsers.cs2_parser import CS2Parser
            self.check("CS2 Parser import", True)
            
            from parsers.khl_parser import KHLParser
            self.check("KHL Parser import", True)
            
            from parsers.odds_parser import odds_parser
            self.check("Odds Parser import", True)
            
            # ML компоненты
            from feature_engineering_real import feature_engineering
            self.check("Feature Engineering import", True)
            
            from ml_models_real import ml_models
            self.check("ML Models import", True)
            
            # API и бот
            from api_server_real import app
            self.check("API Server import", True)
            
            from telegram_bot_real_clean import RealTelegramBot
            self.check("Telegram Bot import", True)
            
            # Сигналы
            from signal_generator_real_clean import real_signal_generator
            self.check("Signal Generator import", True)
            
        except ImportError as e:
            self.check("Import", False, str(e))
    
    async def check_parsers(self):
        """Проверить парсеры"""
        logger.info("🔍 Checking parsers...")
        
        try:
            from parsers.cs2_parser import CS2Parser
            cs2_parser = CS2Parser()
            self.check("CS2 Parser initialization", True)
            
            from parsers.khl_parser import KHLParser
            khl_parser = KHLParser()
            self.check("KHL Parser initialization", True)
            
            from parsers.odds_parser import odds_parser
            self.check("Odds Parser initialization", True)
            
        except Exception as e:
            self.check("Parser initialization", False, str(e))
    
    async def check_ml_components(self):
        """Проверить ML компоненты"""
        logger.info("🔍 Checking ML components...")
        
        try:
            from feature_engineering_real import feature_engineering
            self.check("Feature Engineering instance", hasattr(feature_engineering, 'get_team_features'))
            
            from ml_models_real import ml_models
            self.check("ML Models instance", hasattr(ml_models, 'predict_upcoming_matches'))
            
        except Exception as e:
            self.check("ML components", False, str(e))
    
    async def check_api_endpoints(self):
        """Проверить API эндпоинты"""
        logger.info("🔍 Checking API endpoints...")
        
        try:
            from api_server_real import app
            
            # Проверить роуты
            routes = [route.path for route in app.routes]
            
            required_routes = [
                "/api/health",
                "/api/matches",
                "/api/ml_predictions",
                "/api/signals",
                "/api/odds"
            ]
            
            for route in required_routes:
                self.check(f"API route {route}", route in routes)
                
        except Exception as e:
            self.check("API endpoints", False, str(e))
    
    async def check_telegram_bot(self):
        """Проверить Telegram бота"""
        logger.info("🔍 Checking Telegram bot...")
        
        try:
            from telegram_bot_real_clean import RealTelegramBot
            
            # Проверить методы
            bot_methods = [
                'cmd_start', 'cmd_live', 'cmd_signals', 
                'cmd_analysis', 'cmd_stats', 'cmd_odds'
            ]
            
            for method in bot_methods:
                self.check(f"Bot method {method}", hasattr(RealTelegramBot, method))
                
        except Exception as e:
            self.check("Telegram bot", False, str(e))
    
    async def check_database(self):
        """Проверить базу данных"""
        logger.info("🔍 Checking database...")
        
        try:
            from database import db_manager
            
            # Проверить методы
            db_methods = [
                'initialize', 'add_match', 'get_matches', 
                'add_signal', 'get_signals'
            ]
            
            for method in db_methods:
                self.check(f"DB method {method}", hasattr(db_manager, method))
                
        except Exception as e:
            self.check("Database", False, str(e))
    
    async def check_files(self):
        """Проверить файлы конфигурации"""
        logger.info("🔍 Checking configuration files...")
        
        import os
        
        required_files = [
            "render.yaml",
            "Dockerfile.web",
            "Dockerfile.bot",
            "main_production.py",
            "requirements_full.txt"
        ]
        
        for file in required_files:
            exists = os.path.exists(file)
            self.check(f"File {file}", exists)
    
    async def check_environment(self):
        """Проверить переменные окружения"""
        logger.info("🔍 Checking environment...")
        
        import os
        
        # Проверить важные переменные
        env_vars = [
            "SERVICE_TYPE"
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            self.check(f"Env var {var}", value is not None, f"Value: {value}")
    
    async def run_all_checks(self):
        """Выполнить все проверки"""
        logger.info("🚀 Starting Production Checklist")
        logger.info("=" * 50)
        
        await self.check_imports()
        await self.check_parsers()
        await self.check_ml_components()
        await self.check_api_endpoints()
        await self.check_telegram_bot()
        await self.check_database()
        await self.check_files()
        await self.check_environment()
        
        # Итоги
        logger.info("=" * 50)
        logger.info("📊 CHECKLIST RESULTS:")
        logger.info(f"✅ Passed: {self.passed}")
        logger.info(f"❌ Failed: {self.failed}")
        logger.info(f"📈 Success Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")
        
        if self.failed == 0:
            logger.info("🎉 ALL CHECKS PASSED - READY FOR DEPLOY!")
            return True
        else:
            logger.error("💥 SOME CHECKS FAILED - FIX BEFORE DEPLOY")
            
            # Показать неудачные проверки
            logger.error("\n❌ Failed checks:")
            for check in self.checks:
                if not check["passed"]:
                    logger.error(f"   - {check['name']}: {check['message']}")
            
            return False

async def main():
    """Главная функция"""
    checklist = ProductionChecklist()
    success = await checklist.run_all_checks()
    
    if success:
        logger.info("\n🚀 Ready for deployment!")
        logger.info("Run: git push origin main")
        sys.exit(0)
    else:
        logger.error("\n❌ Fix issues before deployment")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
