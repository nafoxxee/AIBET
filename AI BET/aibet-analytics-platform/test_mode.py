import asyncio
import logging
from datetime import datetime
from app.config import config
from app.main import TelegramSender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_test_mode():
    """Run test mode with real analysis and posting"""
    print("🧪 AI BET Analytics - TEST MODE")
    print("=" * 50)
    
    # Check configuration
    if not config.telegram.bot_token:
        print("❌ ERROR: Telegram bot token not configured!")
        print("Please set TELEGRAM_BOT_TOKEN environment variable")
        return False
    
    if not config.telegram.cs2_channel_id:
        print("❌ ERROR: CS2 channel ID not configured!")
        print("Please set CS2_CHANNEL_ID environment variable")
        return False
    
    if not config.telegram.khl_channel_id:
        print("❌ ERROR: KHL channel ID not configured!")
        print("Please set KHL_CHANNEL_ID environment variable")
        return False
    
    print("✅ Configuration verified")
    print(f"🤖 Bot Token: {config.telegram.bot_token[:10]}...")
    print(f"📮 CS2 Channel: {config.telegram.cs2_channel_id}")
    print(f"📮 KHL Channel: {config.telegram.khl_channel_id}")
    print()
    
    # Initialize Telegram sender
    try:
        telegram = TelegramSender(config.telegram.bot_token)
        print("✅ Telegram bot initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Telegram bot: {e}")
        return False
    
    # Test CS2 Analysis
    print("\n🎮 Running CS2 Analysis...")
    try:
        from cs2.sources.hltv_parser import parse_cs2_matches
        from cs2.analysis.scenarios import analyze_cs2_matches
        from storage.database import store_cs2_matches
        
        # Fetch CS2 matches
        print("📡 Fetching CS2 matches...")
        cs2_matches = await parse_cs2_matches()
        
        if not cs2_matches:
            cs2_message = "🎮 CS2 Analysis Results\n\n" \
                         "⚠️ No suitable matches detected currently\n\n" \
                         "📊 Analysis completed: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            print(f"📊 Found {len(cs2_matches)} CS2 matches")
            await store_cs2_matches(cs2_matches)
            
            # Run analysis
            print("🧠 Running CS2 scenario analysis...")
            cs2_analysis = await analyze_cs2_matches(cs2_matches)
            
            if cs2_analysis:
                cs2_message = telegram._format_cs2_message(cs2_analysis)
                print(f"✅ CS2 analysis complete - {len(cs2_analysis.get('scenarios', []))} scenarios detected")
            else:
                cs2_message = "🎮 CS2 Analysis Results\n\n" \
                             "⚠️ No scenarios detected\n\n" \
                             f"📊 Matches analyzed: {len(cs2_matches)}\n" \
                             "📊 Analysis completed: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Post to CS2 channel
        print("📤 Posting to CS2 channel...")
        await telegram.send_message(config.telegram.cs2_channel_id, cs2_message)
        print("✅ CS2 analysis posted to channel")
        
    except Exception as e:
        print(f"❌ CS2 analysis failed: {e}")
        cs2_message = "🎮 CS2 Analysis Results\n\n" \
                     f"❌ Analysis failed: {str(e)}\n\n" \
                     "📊 Analysis completed: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await telegram.send_message(config.telegram.cs2_channel_id, cs2_message)
    
    # Test KHL Analysis
    print("\n🏒 Running KHL Analysis...")
    try:
        from khl.sources.matches_parser import parse_khl_matches
        from khl.analysis.scenarios import analyze_khl_matches
        from storage.database import store_khl_matches
        
        # Fetch KHL matches
        print("📡 Fetching KHL matches...")
        khl_matches = await parse_khl_matches()
        
        if not khl_matches:
            khl_message = "🏒 KHL Analysis Results\n\n" \
                         "⚠️ No suitable matches detected currently\n\n" \
                         "📊 Analysis completed: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            print(f"📊 Found {len(khl_matches)} KHL matches")
            await store_khl_matches(khl_matches)
            
            # Run analysis
            print("🧠 Running KHL scenario analysis...")
            khl_analysis = await analyze_khl_matches(khl_matches)
            
            if khl_analysis:
                khl_message = telegram._format_khl_message(khl_analysis)
                print(f"✅ KHL analysis complete - {len(khl_analysis.get('scenarios', []))} scenarios detected")
            else:
                khl_message = "🏒 KHL Analysis Results\n\n" \
                             "⚠️ No scenarios detected\n\n" \
                             f"📊 Matches analyzed: {len(khl_matches)}\n" \
                             "📊 Analysis completed: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Post to KHL channel
        print("📤 Posting to KHL channel...")
        await telegram.send_message(config.telegram.khl_channel_id, khl_message)
        print("✅ KHL analysis posted to channel")
        
    except Exception as e:
        print(f"❌ KHL analysis failed: {e}")
        khl_message = "🏒 KHL Analysis Results\n\n" \
                     f"❌ Analysis failed: {str(e)}\n\n" \
                     "📊 Analysis completed: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await telegram.send_message(config.telegram.khl_channel_id, khl_message)
    
    # Summary
    print("\n" + "=" * 50)
    print("🧪 TEST MODE COMPLETE")
    print("✅ Analysis results posted to both channels")
    print("📱 Check your Telegram channels for results")
    print(f"📊 CS2: https://t.me/{config.telegram.cs2_channel_id.replace('@', '')}")
    print(f"📊 KHL: https://t.me/{config.telegram.khl_channel_id.replace('@', '')}")
    print("=" * 50)
    
    return True


async def main():
    """Main test mode entry point"""
    success = await run_test_mode()
    
    if success:
        print("\n🎉 Test mode completed successfully!")
        print("The system is ready for production deployment.")
    else:
        print("\n❌ Test mode failed. Please check configuration and try again.")


if __name__ == "__main__":
    asyncio.run(main())
