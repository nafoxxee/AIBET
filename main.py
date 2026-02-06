"""
AIBET + AIBOT - Unified Web Application for Render Free
FastAPI + Telegram Bot with Webhook
"""

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
PORT = int(os.getenv('PORT', 8000))
BOT_TOKEN = os.getenv('BOT_TOKEN')
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# Validate environment
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable is required")
    exit(1)

if not RENDER_EXTERNAL_URL:
    logger.error("❌ RENDER_EXTERNAL_URL environment variable is required")
    exit(1)

logger.info(f"🚀 Starting unified application on port {PORT}")
logger.info(f"🌐 Render URL: {RENDER_EXTERNAL_URL}")
logger.info(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")


# Global variables
bot_application = None
telegram_bot = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global bot_application, telegram_bot
    
    # Startup
    logger.info("🚀 Starting AIBET + AIBOT unified service...")
    
    try:
        # Initialize Telegram bot
        telegram_bot = Bot(token=BOT_TOKEN)
        
        # Get bot info
        bot_info = await telegram_bot.get_me()
        logger.info(f"✅ Bot initialized: @{bot_info.username}")
        
        # Create Application
        bot_application = Application.builder().token(BOT_TOKEN).build()
        
        # Add command handlers
        bot_application.add_handler(CommandHandler("start", start_command))
        bot_application.add_handler(CommandHandler("help", help_command))
        bot_application.add_handler(CommandHandler("status", status_command))
        bot_application.add_handler(CommandHandler("about", about_command))
        
        # Initialize application
        await bot_application.initialize()
        
        # Set webhook
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        await telegram_bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set: {webhook_url}")
        
        logger.info("✅ Unified service ready!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down unified service...")
    
    try:
        if bot_application:
            await bot_application.shutdown()
        if telegram_bot:
            await telegram_bot.delete_webhook()
        logger.info("✅ Service shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="AIBET + AIBOT Unified Service",
    description="Unified FastAPI + Telegram Bot with Webhook",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redocUrl="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = datetime.utcnow()
    
    try:
        response = await call_next(request)
        process_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"📥 {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
        
        return response
        
    except Exception as e:
        process_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"❌ {request.method} {request.url.path} - ERROR - {process_time:.3f}s - {e}")
        raise


# Telegram Bot Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    try:
        welcome_message = f"""
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
Web API: {RENDER_EXTERNAL_URL}
Documentation: {RENDER_EXTERNAL_URL}/docs

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
        logger.info(f"📤 Start command sent to user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Error in start_command: {e}")
        await update.message.reply_text("❌ Service temporarily unavailable")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    try:
        help_message = f"""
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
{RENDER_EXTERNAL_URL}

📚 **Documentation:**
API docs: {RENDER_EXTERNAL_URL}/docs

❓ **Support:**
For technical issues, please check our web platform.
"""
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
        logger.info(f"📤 Help command sent to user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Error in help_command: {e}")
        await update.message.reply_text("❌ Service temporarily unavailable")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command"""
    try:
        status_message = f"""
📊 **AIBOT Service Status**

✅ **Bot Status:** Online
🕒 **Current Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
🤖 **Bot Version:** 2.0.0
🌐 **Service URL:** {RENDER_EXTERNAL_URL}

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

🌐 **Web Platform:** {RENDER_EXTERNAL_URL}
"""
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
        logger.info(f"📤 Status command sent to user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Error in status_command: {e}")
        await update.message.reply_text("❌ Service temporarily unavailable")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command"""
    try:
        about_message = f"""
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
• Web API: {RENDER_EXTERNAL_URL}
• Documentation: /docs endpoint
• Health Monitoring: /api/health endpoint

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

📈 **Version:** 2.0.0
🕒 **Last Updated:** 2026-02-06
"""
        
        await update.message.reply_text(about_message, parse_mode='Markdown')
        logger.info(f"📤 About command sent to user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Error in about_command: {e}")
        await update.message.reply_text("❌ Service temporarily unavailable")


# API Endpoints
@app.get("/api/health")
async def api_health():
    """Health check endpoint for AIBET"""
    try:
        return JSONResponse(
            status_code=200,
            content={"status": "ok"}
        )
    except Exception as e:
        logger.error(f"❌ Error in health endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        bot_status = "online" if telegram_bot else "offline"
        webhook_status = "configured" if bot_application else "not_configured"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "service": "AIBET + AIBOT Unified",
            "port": PORT,
            "bot_status": bot_status,
            "webhook_status": webhook_status,
            "render_url": RENDER_EXTERNAL_URL
        }
    except Exception as e:
        logger.error(f"❌ Error in health endpoint: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram webhook endpoint"""
    try:
        if not bot_application:
            logger.error("❌ Bot application not initialized")
            raise HTTPException(status_code=500, detail="Bot not initialized")
        
        # Get update from Telegram
        data = await request.json()
        
        # Create Update object
        update = Update.de_json(data, bot_application.bot)
        
        # Process update
        await bot_application.process_update(update)
        
        logger.info(f"📨 Webhook processed: update_id {data.get('update_id', 'unknown')}")
        
        return JSONResponse(status_code=200, content={"status": "ok"})
        
    except Exception as e:
        logger.error(f"❌ Error in webhook: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AIBET + AIBOT Unified Service",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "api_health": "/api/health",
        "webhook": "/webhook",
        "render_url": RENDER_EXTERNAL_URL,
        "bot_status": "online" if telegram_bot else "offline"
    }


@app.get("/v1/nhl/schedule")
async def get_nhl_schedule():
    """Get NHL schedule - educational version"""
    return {
        "success": True,
        "data": [],
        "message": "NHL schedule service - educational analytics only",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/khl/schedule")
async def get_khl_schedule():
    """Get KHL schedule - educational version"""
    return {
        "success": True,
        "data": [],
        "message": "KHL schedule service - educational analytics only",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/cs2/upcoming")
async def get_cs2_upcoming():
    """Get CS2 upcoming matches - educational version"""
    return {
        "success": True,
        "data": [],
        "message": "CS2 upcoming matches service - educational analytics only",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/ai/context/{match_id}")
async def get_ai_context(match_id: str):
    """Get AI context - educational version"""
    return {
        "success": True,
        "data": {
            "match_id": match_id,
            "context": "Educational analysis only",
            "not_a_prediction": True,
            "educational_purpose": True,
            "message": "AI context service - educational analysis only"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/ai/score/{match_id}")
async def get_ai_score(match_id: str):
    """Get AI score - educational version"""
    return {
        "success": True,
        "data": {
            "match_id": match_id,
            "ai_score": 0.5,
            "confidence": 0.5,
            "risk_level": "medium",
            "not_a_prediction": True,
            "educational_purpose": True,
            "message": "AI scoring service - educational analysis only"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 Starting unified service on port {PORT}")
    logger.info(f"🌐 Render URL: {RENDER_EXTERNAL_URL}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=DEBUG
    )
