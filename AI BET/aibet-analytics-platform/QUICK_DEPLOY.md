# 🚀 БЫСТРЫЙ ДЕПЛОЙ НА RENDER - ИНСТРУКЦИЯ

## ⚡ Готово к деплою! Все файлы настроены.

### 1. 🔗 Перейдите на Render:
https://render.com/

### 2. 📁 Подключите GitHub:
- Зарегистрируйтесь через GitHub
- Выберите репозиторий: `nafoxxee/AIBET`
- Укажите путь: `AI BET/aibet-analytics-platform`

### 3. ⚙️ Настройки (Render найдет автоматически из render.yaml):
- **Name**: `aibet-analytics`
- **Runtime**: Python 3.9
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python render_main.py`
- **Health Check**: `/health`

### 4. 🔑 Environment Variables (уже в render.yaml):
```
TELEGRAM_BOT_TOKEN=8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4
CS2_CHANNEL_ID=@aibetcsgo
KHL_CHANNEL_ID=@aibetkhl
PYTHON_VERSION=3.9
```

### 5. 🚀 Нажмите "Create Web Service"

---

## ✅ Что будет работать после деплоя:

### 🤖 Telegram Bot:
- **Main Entry**: `render_main.py` (запускает и health server, и бота)
- **Health Check**: `/health` endpoint на порту 8000
- **Bot Commands**: `/start`, меню, статус системы

### 📊 Сервисы:
- **Health Server**: FastAPI + Uvicorn (порт 8000)
- **Telegram Bot**: Aiogram (фоновый процесс)
- **Auto-restart**: если бот упадет, перезапустится

### 📈 Мониторинг:
- Render Dashboard → Logs
- Health Check: `https://your-app.onrender.com/health`
- Telegram: `/start` → "📊 System Status"

---

## 🔧 Проверка после деплоя:

### 1. Health Check:
```bash
curl https://your-app-name.onrender.com/health
```
Ответ:
```json
{"status": "healthy", "timestamp": "...", "service": "aibet-analytics"}
```

### 2. Telegram Bot:
- Найдите вашего бота по токену
- Отправьте `/start`
- Проверьте меню и кнопки

### 3. Каналы:
- Убедитесь что бот админ @aibetcsgo и @aibetkhl
- Проверьте что постится аналитика

---

## 🎯 Готово! 

**Платформа будет работать 24/7 на Render Free Plan!**

- ✅ Автоматический анализ матчей
- ✅ Публикация в Telegram каналы  
- ✅ ML модели и прогнозы
- ✅ Система мониторинга
- ✅ Health checks и авто-перезапуск

---

**🔗 Ссылки после деплоя:**
- Render Dashboard: https://dashboard.render.com/
- Ваше приложение: `https://aibet-analytics.onrender.com`
- Health Check: `https://aibet-analytics.onrender.com/health`

**📱 Каналы:**
- CS2: @aibetcsgo  
- KHL: @aibetkhl

**🚀 Деплой готов! Жду ваших результатов!**
