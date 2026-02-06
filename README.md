# AIBET Analytics Platform

Production-ready FastAPI API and Telegram bot for educational sports analytics.

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your BOT_TOKEN

# Run API (AIBET)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run Telegram Bot (AIBOT) - in separate terminal
python bot/bot.py
```

### Production Deployment

```bash
# Deploy to Render
git clone https://github.com/nafoxxee/AIBET.git
# Connect to Render - auto-detects render.yaml
# Services: API + Bot
```

## 📁 Project Structure

```
AIBET/
├── app/
│   ├── __init__.py
│   └── main.py        # FastAPI entrypoint
├── bot/
│   ├── __init__.py
│   └── bot.py         # Telegram bot entrypoint
├── .env.example       # Environment template
├── Dockerfile         # Docker configuration
├── render.yaml        # Render deployment
├── requirements.txt   # Dependencies
└── README.md         # This file
```

## 🌐 Services

### AIBET Analytics API
- **URL**: `https://aibet-analytics.onrender.com`
- **Health**: `/health`
- **Docs**: `/docs`
- **Endpoints**: `/v1/nhl/*`, `/v1/khl/*`, `/v1/cs2/*`, `/v1/ai/*`

### AIBOT Telegram Bot
- **Commands**: `/start`, `/help`, `/status`, `/about`
- **Purpose**: Educational sports analytics
- **Token**: Required in `BOT_TOKEN` environment variable

## 📦 Dependencies

```txt
# Core Web Framework (AIBET API)
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Telegram Bot (AIBOT)
python-telegram-bot==20.7

# Essential dependencies
python-dotenv==1.0.1
```

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration (AIBET)
PORT=8000
DEBUG=false

# Telegram Bot Configuration (AIBOT)
BOT_TOKEN=your_telegram_bot_token_here
```

## 🚀 Render Deployment

### Build Commands
- **API**: Default Dockerfile command
- **Bot**: `python bot/bot.py`

### Start Commands
- **API**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Bot**: `python bot/bot.py`

### Services
1. **AIBET Analytics** (Web Service)
   - Type: `web`
   - Port: `8000`
   - Health Check: `/health`

2. **AIBOT Telegram** (Background Worker)
   - Type: `worker`
   - Command: `python bot/bot.py`
   - Token: `BOT_TOKEN` required

## ⚠️ Educational Purpose Only

All analytics and information provided are for educational purposes only.
No betting advice, financial recommendations, or predictions are provided.

## 📊 Features

### API Endpoints
- `/health` - Service health check
- `/docs` - Interactive documentation
- `/v1/nhl/schedule` - NHL schedule
- `/v1/khl/schedule` - KHL schedule
- `/v1/cs2/upcoming` - CS2 matches
- `/v1/ai/*` - Educational AI analytics

### Bot Commands
- `/start` - Welcome message
- `/help` - Help information
- `/status` - Service status
- `/about` - About information

## 🛠️ Development

### Testing
```bash
# Test API
curl http://localhost:8000/health

# Test Bot (requires BOT_TOKEN)
python bot/bot.py
```

### Docker
```bash
# Build
docker build -t aibet .

# Run API
docker run -p 8000:8000 aibet

# Run Bot
docker run -e BOT_TOKEN=your_token aibet python bot/bot.py
```

## 📈 Monitoring

### Health Checks
- **API**: `/health` endpoint
- **Bot**: Process monitoring (Render)

### Logging
- **API**: Console logging
- **Bot**: Console logging with error handling

## 🔒 Security

- **API**: CORS enabled, educational responses only
- **Bot**: Token authentication, educational disclaimers
- **Data**: Public sources only, no sensitive information

## 📞 Support

For technical issues:
1. Check `/health` endpoint
2. Review environment variables
3. Verify bot token configuration
4. Check Render service logs

---

**Built with ❤️ for educational sports analytics**
