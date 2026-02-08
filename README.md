# AIBET - Timeweb VPS Deployment

Educational sports analytics platform with Telegram bot and FastAPI API.

## 🚀 Quick Start

### Timeweb VPS Deployment

```bash
# Clone repository
git clone https://github.com/nafoxxee/AIBET.git
cd AIBET

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your BOT_TOKEN

# Run Telegram bot (recommended)
python run.py bot
```

## 📁 Project Structure

```
AIBET/
├── bot/
│   ├── __init__.py
│   └── bot.py         # Telegram bot entrypoint
├── api/
│   ├── __init__.py
│   └── main.py        # FastAPI entrypoint
├── core/
│   ├── __init__.py
│   ├── config.py       # Configuration management
│   └── storage.py      # Simple storage
├── run.py              # Unified entrypoint
├── requirements.txt     # Dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## 🤖 Telegram Bot Features

### Commands
- `/start` - Главное меню с inline-кнопками
- `/help` - Справка по боту
- `/status` - Статус бота и статистика
- `/about` - Информация о проекте

### Inline Buttons
- **🏒 NHL** - Информация о NHL
- **🏒 KHL** - Информация о KHL
- **🎮 CS2** - Информация о CS2
- **📊 О проекте** - О проекте AIBET

## 📦 Dependencies

```txt
# Telegram Bot
python-telegram-bot==20.7

# FastAPI Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Environment Management
python-dotenv==1.0.1
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here

# API Configuration (optional)
API_HOST=0.0.0.0
API_PORT=8000

# Debug Mode
DEBUG=false
```

## 🚀 Deployment

### Run Telegram Bot

```bash
python run.py bot
```

### Run API

```bash
python run.py api
```

## ⚠️ Educational Purpose Only

All analytics and information provided are for educational purposes only.
No betting advice, financial recommendations, or predictions are provided.

---

**Built with ❤️ for Timeweb VPS deployment**
