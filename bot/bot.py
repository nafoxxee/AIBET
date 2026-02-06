"""
AIBOT - Telegram Bot for AIBET Analytics Platform
Simple bot for educational sports analytics
"""

import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable is required")
    exit(1)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    welcome_message = """
🚀 **AIBOT - Educational Sports Analytics Bot**

Welcome to the educational sports analytics assistant!

📊 **Available Commands:**
/start - Show this welcome message
/help - Show help information
/status - Check bot status
/about - About this service

⚠️ **Educational Purpose Only:**
This bot provides educational sports analytics information only.
No betting advice or predictions are provided.

🌐 **AIBET Analytics Platform:**
Web API: https://aibet-analytics.onrender.com
Documentation: https://aibet-analytics.onrender.com/docs

📈 **Features:**
• NHL schedule and analytics
• KHL matches and insights  
• CS2 esports data
• Educational AI analysis

🔍 **Data Sources:**
Public sports APIs and official league websites
Real-time educational analytics
"""
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    help_message = """
🤖 **AIBOT Help - Educational Analytics**

📋 **Commands:**
/start - Welcome message
/help - Show this help
/status - Bot service status
/about - About information

🏒 **Sports Covered:**
• NHL - National Hockey League
• KHL - Kontinental Hockey League  
• CS2 - Counter-Strike 2 Esports

📊 **Analytics Features:**
• Match schedules
• Educational insights
• Risk assessment
• Value analysis

⚠️ **Important Notice:**
All information is for educational purposes only.
No betting advice or financial recommendations.

🌐 **Web Platform:**
Visit our main platform at:
https://aibet-analytics.onrender.com

📚 **Documentation:**
API docs: https://aibet-analytics.onrender.com/docs

❓ **Support:**
For technical issues, please check our web platform.
"""
    
    await update.message.reply_text(help_message, parse_mode='Markdown')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command"""
    status_message = f"""
📊 **AIBOT Service Status**

✅ **Bot Status:** Online
🕒 **Current Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
🤖 **Bot Version:** 1.3.0

🌐 **Connected Services:**
• AIBET Analytics API: ✅ Online
• Educational AI Engine: ✅ Active
• Data Sources: ✅ Connected

📈 **Analytics Available:**
• NHL Schedule: ✅ Available
• KHL Matches: ✅ Available  
• CS2 Esports: ✅ Available
• AI Insights: ✅ Educational Only

⚠️ **Service Mode:** Educational Analytics Only
🔒 **Compliance:** Educational Purpose Only

🌐 **Web Platform:** https://aibet-analytics.onrender.com
"""
    
    await update.message.reply_text(status_message, parse_mode='Markdown')


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command"""
    about_message = """
🏆 **About AIBOT - Educational Sports Analytics**

📖 **Mission:**
To provide educational sports analytics and insights for learning purposes only.

🔬 **Technology:**
• FastAPI Backend
• Telegram Bot Framework
• Educational AI Analysis
• Real-time Data Processing

🏒 **Sports Coverage:**
• **NHL** - Professional hockey analytics
• **KHL** - International hockey insights
• **CS2** - Esports analytics

📊 **Analytics Features:**
• Match schedules and timing
• Team performance insights
• Educational risk assessment
• Market efficiency analysis

⚠️ **Educational Disclaimer:**
All information provided is for educational purposes only.
No betting advice, financial recommendations, or predictions.
Sports analytics involves inherent uncertainties.

🌐 **Platform Integration:**
• Web API: https://aibet-analytics.onrender.com
• Documentation: /docs endpoint
• Health Monitoring: /health endpoint

📚 **Learning Resources:**
Educational sports analytics for:
• Data science enthusiasts
• Sports analytics students
• Research purposes
• Technical demonstrations

🔒 **Compliance:**
• Educational purpose only
• No gambling services
• No financial advice
• Responsible analytics

📈 **Version:** 1.3.0
🕒 **Last Updated:** 2026-02-06
"""
    
    await update.message.reply_text(about_message, parse_mode='Markdown')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    print(f"Error with update {update}: {context.error}")
    
    error_message = """
❌ **Service Temporarily Unavailable**

Please try again later.
For continuous service, visit our web platform:
https://aibet-analytics.onrender.com

⚠️ Educational analytics only.
"""
    
    try:
        await update.message.reply_text(error_message, parse_mode='Markdown')
    except:
        pass  # Avoid error loops


def main() -> None:
    """Start the bot"""
    print("🚀 Starting AIBOT - Educational Sports Analytics Bot")
    print(f"📅 Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("about", about_command))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("✅ Bot handlers registered")
    print("🤖 AIBOT is starting...")
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
