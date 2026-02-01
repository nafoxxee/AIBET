#!/usr/bin/env python3
"""
AIBET Analytics Platform - Import Test
Простая проверка импортов
"""

print("🚀 Testing AIBET Platform Imports...")

try:
    import os
    os.environ['SERVICE_TYPE'] = 'web'
    os.environ['TELEGRAM_BOT_TOKEN'] = '8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4'
    os.environ['ADMIN_ID'] = '379036860'
    print("✅ Environment variables set")
except Exception as e:
    print(f"❌ Environment error: {e}")

try:
    from database import db_manager
    print("✅ Database import successful")
except Exception as e:
    print(f"❌ Database import error: {e}")

try:
    from ml_models import ml_models
    print("✅ ML models import successful")
except Exception as e:
    print(f"❌ ML models import error: {e}")

try:
    from signal_generator import signal_generator
    print("✅ Signal generator import successful")
except Exception as e:
    print(f"❌ Signal generator import error: {e}")

try:
    from telegram_publisher import create_telegram_publisher
    print("✅ Telegram publisher import successful")
except Exception as e:
    print(f"❌ Telegram publisher import error: {e}")

try:
    from parsers.cs2_parser import cs2_parser
    print("✅ CS2 parser import successful")
except Exception as e:
    print(f"❌ CS2 parser import error: {e}")

try:
    from parsers.khl_parser import khl_parser
    print("✅ KHL parser import successful")
except Exception as e:
    print(f"❌ KHL parser import error: {e}")

try:
    from telegram_bot import create_bot
    print("✅ Telegram bot import successful")
except Exception as e:
    print(f"❌ Telegram bot import error: {e}")

try:
    from mini_app import AIBETMiniApp
    print("✅ Mini app import successful")
except Exception as e:
    print(f"❌ Mini app import error: {e}")

try:
    from system_service import system_service
    print("✅ System service import successful")
except Exception as e:
    print(f"❌ System service import error: {e}")

try:
    from main_dual import main
    print("✅ Main dual import successful")
except Exception as e:
    print(f"❌ Main dual import error: {e}")

print("\n🎯 Import test completed!")
print("📊 If all imports are successful, the system is ready!")
