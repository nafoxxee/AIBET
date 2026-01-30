# 🚀 AI BET Analytics - Render Deployment Guide

## 📋 Подготовка к деплою на Render

### 🔧 Шаг 1: Загрузка кода на GitHub
1. Выполните команды из `github_upload.md`
2. Убедитесь, что код загружен в https://github.com/nafoxxee/AIBET.git

### 🌐 Шаг 2: Создание аккаунта Render
1. Перейдите на https://render.com/
2. Зарегистрируйтесь через GitHub
3. Подключите репозиторий AIBET

### ⚙️ Шаг 3: Создание Web Service
1. Нажмите "New +" → "Web Service"
2. Выберите репозиторий `nafoxxee/AIBET`
3. Настройте параметры:

**Build Settings:**
- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `python render_main.py`
- Health Check Path: `/health`

**Environment Variables:**
```
TELEGRAM_BOT_TOKEN=8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4
CS2_CHANNEL_ID=@aibetcsgo
KHL_CHANNEL_ID=@aibetkhl
PYTHON_VERSION=3.9
```

**Instance Type:**
- Free plan (для начала)

### 🔄 Шаг 4: Создание Worker Service
1. Нажмите "New +" → "Web Service" (для background задач)
2. Используйте тот же репозиторий
3. Настройте параметры:

**Build Settings:**
- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `python scheduler_worker.py`

**Environment Variables:**
```
TELEGRAM_BOT_TOKEN=8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4
CS2_CHANNEL_ID=@aibetcsgo
KHL_CHANNEL_ID=@aibetkhl
PYTHON_VERSION=3.9
```

### 📊 Шаг 5: Мониторинг
1. После деплоя проверьте логи
2. Убедитесь, что бот запущен
3. Проверьте работу планировщика

## 🎯 Результаты деплоя:
- ✅ Telegram бот работает 24/7
- ✅ Автоматический анализ матчей
- ✅ Публикация в каналы
- ✅ ML модели обучаются
- ✅ Система мониторинга активна

## 🔗 Ссылки после деплоя:
- Web Service: `https://aibet-bot.onrender.com`
- GitHub: https://github.com/nafoxxee/AIBET.git
- Каналы: @aibetcsgo, @aibetkhl
