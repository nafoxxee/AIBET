# 🚨 EMERGENCY DEPLOYMENT FIX

## Проблема
Render все еще использует старую конфигурацию из веб-интерфейса:
- `Start Command:python main_web_analytics.py` (неправильно)
- Вместо `python main_dual.py` (правильно)

## Решение: Создать новые сервисы

### 1. Удалить старые сервисы в Render Dashboard
1. Зайти в [Render Dashboard](https://dashboard.render.com)
2. Удалить `aibet-mini-app` 
3. Удалить `aibot-telegram-bot`

### 2. Создать новые сервисы с правильной конфигурацией

#### AIBET Mini App (Web Service)
1. **New** → **Web Service**
2. **Connect Repository**: `nafoxxee/AIBET`
3. **Name**: `aibet-mini-app-v2`
4. **Environment**: `Docker`
5. **Root Directory**: `./`
6. **Dockerfile Path**: `./Dockerfile.web`
7. **Build Command**: `pip install -r requirements_full.txt`
8. **Start Command**: `python main_dual.py`
9. **Instance Type**: `Free`
10. **Add Environment Variables**:
    - `PORT=10000`
    - `SERVICE_TYPE=web`
    - `PYTHON_VERSION=3.9.0`

#### AIBOT Telegram Bot (Worker Service)
1. **New** → **Worker** 
2. **Connect Repository**: `nafoxxee/AIBET`
3. **Name**: `aibot-telegram-bot-v2`
4. **Environment**: `Docker`
5. **Root Directory**: `./`
6. **Dockerfile Path**: `./Dockerfile.bot`
7. **Build Command**: `pip install -r requirements_full.txt`
8. **Start Command**: `python main_dual.py`
9. **Instance Type**: `Free`
10. **Add Environment Variables**:
    - `SERVICE_TYPE=bot`
    - `TELEGRAM_BOT_TOKEN=8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4`
    - `ADMIN_ID=379036860`
    - `CS2_CHANNEL=@aibetcsgo`
    - `KHL_CHANNEL=@aibetkhl`
    - `AIBET_WEB_URL=https://aibet-mini-app-v2.onrender.com`
    - `PYTHON_VERSION=3.9.0`

## Почему это нужно
- Render кэширует конфигурацию из веб-интерфейса
- YAML файл не перезаписывает существующие настройки
- Только новые сервисы используют правильную конфигурацию

## Результат
После создания новых сервисов:
- ✅ Mini App: `https://aibet-mini-app-v2.onrender.com`
- ✅ Telegram Bot: автоматически начнет работу
- ✅ Все зависимости установлены
- ✅ Правильные команды запуска
