#!/usr/bin/env python3
"""
AIBET Analytics Platform - Simple Test
Проверка базового функционала
"""

import asyncio
import os
from datetime import datetime

# Устанавливаем переменные окружения
os.environ['SERVICE_TYPE'] = 'web'
os.environ['TELEGRAM_BOT_TOKEN'] = '8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4'
os.environ['ADMIN_ID'] = '379036860'

async def test_database():
    """Тест базы данных"""
    print("🗄️ Testing database...")
    try:
        from database import db_manager
        await db_manager.initialize()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

async def test_ml_models():
    """Тест ML моделей"""
    print("🤖 Testing ML models...")
    try:
        from ml_models import ml_models
        await ml_models.initialize()
        print("✅ ML models initialized successfully")
        return True
    except Exception as e:
        print(f"❌ ML models error: {e}")
        return False

async def test_parsers():
    """Тест парсеров"""
    print("📊 Testing parsers...")
    try:
        from parsers.cs2_parser import cs2_parser
        from parsers.khl_parser import khl_parser
        
        # Тест CS2 парсера
        cs2_matches = await cs2_parser.get_fallback_matches()
        print(f"✅ CS2 parser: {len(cs2_matches)} matches")
        
        # Тест KHL парсера
        khl_matches = await khl_parser.get_fallback_matches()
        print(f"✅ KHL parser: {len(khl_matches)} matches")
        
        return True
    except Exception as e:
        print(f"❌ Parsers error: {e}")
        return False

async def test_telegram_bot():
    """Тест Telegram бота"""
    print("🤖 Testing Telegram bot...")
    try:
        from telegram_bot import create_bot
        bot = create_bot()
        print("✅ Telegram bot created successfully")
        return True
    except Exception as e:
        print(f"❌ Telegram bot error: {e}")
        return False

async def test_mini_app():
    """Тест Mini App"""
    print("📱 Testing Mini App...")
    try:
        from mini_app import AIBETMiniApp
        app = AIBETMiniApp()
        print("✅ Mini App created successfully")
        return True
    except Exception as e:
        print(f"❌ Mini App error: {e}")
        return False

async def main():
    """Основной тест"""
    print("🚀 Starting AIBET Platform Test")
    print("=" * 50)
    
    tests = [
        ("Database", test_database),
        ("ML Models", test_ml_models),
        ("Parsers", test_parsers),
        ("Telegram Bot", test_telegram_bot),
        ("Mini App", test_mini_app)
    ]
    
    results = []
    
    for name, test_func in tests:
        print(f"\n🧪 Running {name} test...")
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test failed: {e}")
            results.append((name, False))
    
    # Итоги
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 ALL TESTS PASSED! System is ready!")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
