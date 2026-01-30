#!/usr/bin/env python3
"""
AI BET Analytics - Test Runner
Run this script to test the system with real Telegram posting
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_mode import run_test_mode

def main():
    print("🚀 AI BET Analytics - Test Runner")
    print("=" * 50)
    
    # Set environment variables
    os.environ['TELEGRAM_BOT_TOKEN'] = '8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4'
    os.environ['CS2_CHANNEL_ID'] = '@aibetcsgo'
    os.environ['KHL_CHANNEL_ID'] = '@aibetkhl'
    
    print("✅ Environment variables set")
    print(f"🤖 Bot Token: {os.environ['TELEGRAM_BOT_TOKEN'][:10]}...")
    print(f"📮 CS2 Channel: {os.environ['CS2_CHANNEL_ID']}")
    print(f"📮 KHL Channel: {os.environ['KHL_CHANNEL_ID']}")
    print()
    
    # Run test mode
    try:
        success = asyncio.run(run_test_mode())
        
        if success:
            print("\n🎉 Test completed successfully!")
            print("Check your Telegram channels for results:")
            print("🎮 CS2: https://t.me/aibetcsgo")
            print("🏒 KHL: https://t.me/aibetkhl")
        else:
            print("\n❌ Test failed. Check logs for details.")
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
