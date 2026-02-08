"""
AIBET - Unified Entry Point
Timeweb deployment ready
"""

import asyncio
import sys
from datetime import datetime

from core.config import config


def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🚀 AIBET - Educational Analytics              ║
║                                                              ║
║  🤖 Telegram Bot + 🌐 FastAPI API                          ║
║  Timeweb VPS Deployment Ready                                   ║
║                                                              ║
║  Version: 1.0.0                                             ║
║  Mode: Production                                             ║
╚════════════════════════════════════════════════════════════════╝
"""
    print(banner)


async def run_bot():
    """Run Telegram bot"""
    try:
        print("🤖 Запуск Telegram бота...")
        from bot.bot import bot
        await bot.run()
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        return False
    return True


async def run_api():
    """Run FastAPI API"""
    try:
        print("🌐 Запуск FastAPI...")
        import uvicorn
        from api.main import app
        
        uvicorn.run(
            "api.main:app",
            host=config.API_HOST,
            port=config.API_PORT,
            reload=config.DEBUG
        )
    except Exception as e:
        print(f"❌ Ошибка запуска API: {e}")
        return False
    return True


async def main():
    """Main entry point"""
    print_banner()
    
    try:
        # Validate configuration
        config.validate()
        
        print("📋 Доступные режимы:")
        print("1. 🤖 Telegram Bot (рекомендуется)")
        print("2. 🌐 FastAPI API")
        print("3. 🚀 Оба сервиса")
        print()
        
        # Check command line arguments
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
        else:
            # Default to bot mode
            mode = "bot"
        
        print(f"🎯 Режим запуска: {mode}")
        print("=" * 60)
        
        if mode == "bot":
            success = await run_bot()
        elif mode == "api":
            success = await run_api()
        elif mode == "both":
            print("⚠️ Режим 'both' временно отключен для стабильности")
            print("🤖 Запуск только Telegram бота...")
            success = await run_bot()
        else:
            print(f"❌ Неизвестный режим: {mode}")
            print("Доступные режимы: bot, api, both")
            success = False
        
        if success:
            print("✅ Сервис успешно завершен")
        else:
            print("❌ Сервис завершился с ошибкой")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Получен KeyboardInterrupt, завершение...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
