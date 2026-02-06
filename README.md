# AIBET + AIBOT - Unified Web Service

Production-ready unified FastAPI + Telegram bot with webhook for Render Free deployment.

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your BOT_TOKEN and RENDER_EXTERNAL_URL

# Run unified service
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Deployment

```bash
# Deploy to Render
git clone https://github.com/nafoxxee/AIBET.git
# Connect to Render - auto-detects render.yaml
# Single unified service: API + Bot with Webhook
```

## 📁 Project Structure

```
AIBET/
├── main.py              # Unified FastAPI + Bot entrypoint
├── app/                 # Legacy API modules (optional)
├── bot/                 # Legacy bot modules (optional)
├── .env.example         # Environment template
├── Dockerfile           # Docker configuration
├── render.yaml          # Render deployment
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## 🌐 Unified Service Features

### AIBET Analytics API
- **URL**: `https://aibet-unified.onrender.com`
- **Health**: `/api/health` (returns `{"status": "ok"}`)
- **Docs**: `/docs`
- **Endpoints**: `/v1/nhl/*`, `/v1/khl/*`, `/v1/cs2/*`, `/v1/ai/*`

### AIBOT Telegram Bot
- **Webhook**: `/webhook` endpoint
- **Commands**: `/start`, `/help`, `/status`, `/about`
- **Purpose**: Educational sports analytics
- **No polling**: Uses webhook only (no getUpdates conflicts)

## 📦 Dependencies

```txt
# Core Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Telegram Bot with Webhook Support
python-telegram-bot==20.7

# HTTP Client for Webhook
httpx==0.25.2

# Data Validation
pydantic==2.7.4

# Environment Management
python-dotenv==1.0.1
```

## 🔧 Configuration

### Environment Variables

```bash
# Service Configuration
PORT=8000
DEBUG=false

# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here

# Render Configuration
RENDER_EXTERNAL_URL=https://your-service.onrender.com
```

## 🚀 Render Deployment

### Single Web Service
- **Type**: `web`
- **Port**: `8000` (from `PORT` env var)
- **Health Check**: `/api/health`
- **Webhook**: `/webhook`

### Build Command
```bash
docker build -t aibet-unified .
```

### Start Command
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Environment Variables (Render)
- `PORT=8000`
- `BOT_TOKEN=your_token` (sync: false)
- `RENDER_EXTERNAL_URL=https://aibet-unified.onrender.com`
- `DEBUG=false`

## ⚠️ Educational Purpose Only

All analytics and information provided are for educational purposes only.
No betting advice, financial recommendations, or predictions are provided.

## 📊 API Endpoints

### Health & Status
- `/api/health` - Health check (returns `{"status": "ok"}`)
- `/health` - Detailed health status
- `/` - Root endpoint with service info

### Analytics (Educational)
- `/v1/nhl/schedule` - NHL schedule
- `/v1/khl/schedule` - KHL schedule
- `/v1/cs2/upcoming` - CS2 matches
- `/v1/ai/context/{match_id}` - AI context
- `/v1/ai/score/{match_id}` - AI scoring

### Telegram Bot
- `/webhook` - Telegram webhook endpoint
- Commands: `/start`, `/help`, `/status`, `/about`

## 🛠️ Development

### Testing
```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Test webhook (requires bot token)
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"update_id": 123, "message": {"message_id": 123, "from": {"id": 123}, "chat": {"id": 123}, "text": "/start"}}'
```

### Docker
```bash
# Build
docker build -t aibet-unified .

# Run
docker run -p 8000:8000 \
  -e BOT_TOKEN=your_token \
  -e RENDER_EXTERNAL_URL=http://localhost:8000 \
  aibet-unified
```

## 📈 Monitoring

### Health Checks
- **API**: `/api/health` (simple status)
- **Service**: `/health` (detailed status)
- **Bot**: Webhook logging

### Logging
- **Request logging**: All HTTP requests logged
- **Bot logging**: All bot interactions logged
- **Error logging**: Detailed error tracking

## 🔒 Security

- **API**: CORS enabled, educational responses only
- **Bot**: Webhook only (no polling), token authentication
- **Data**: Public sources only, no sensitive information

## 🚀 Webhook Configuration

### Automatic Setup
The service automatically:
1. Sets up Telegram webhook on startup
2. Uses `RENDER_EXTERNAL_URL` for webhook URL
3. Validates bot token and connectivity
4. Logs webhook status

### Webhook URL
```
https://your-service.onrender.com/webhook
```

### No Polling
- **No getUpdates conflicts**
- **No polling loops**
- **Webhook only** (Render compatible)

## 📞 Support

For technical issues:
1. Check `/api/health` endpoint
2. Review environment variables
3. Verify bot token configuration
4. Check Render service logs

## 🔄 Auto-Deployment

The service automatically:
- Deploys on push to `main` branch
- Restarts on errors
- Updates webhook on redeploy
- Logs all deployment events

---

**Built with ❤️ for educational sports analytics and Render Free deployment**
