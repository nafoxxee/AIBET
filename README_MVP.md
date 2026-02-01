# 🎯 AIBET MVP - Analytical Betting Platform

## 📋 **Senior Full-Stack Implementation**

### **Концепция:**
- Аналитический ИИ-движок на исторических данных
- Сигналы ДО начала матчей (pre-match)
- Value ставки (probability > implied odds)
- Полностью бесплатная система

### **Архитектура:**
```
aibet-mvp/
├── database/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy модели
│   ├── migrations.py       # Миграции БД
│   └── connection.py       # SQLite connection
├── data/
│   ├── cs2_historical.csv # Исторические CS2 матчи
│   ├── khl_historical.csv # Исторические КХЛ матчи
│   └── team_stats.csv     # Статистика команд
├── ml/
│   ├── __init__.py
│   ├── feature_engineer.py # Feature engineering
│   ├── models.py          # ML модели
│   └── predictor.py       # Предиктор
├── api/
│   ├── __init__.py
│   ├── main.py            # FastAPI приложение
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── matches.py     # Эндпоинты матчей
│   │   ├── signals.py     # Эндпоинты сигналов
│   │   └── statistics.py  # Статистика
│   └── dependencies.py    # Зависимости
├── bot/
│   ├── __init__.py
│   ├── main.py            # Telegram бот
│   ├── handlers.py        # Хендлеры
│   └── keyboards.py       # Клавиатуры
├── mini_app/
│   ├── index.html         # Mini App HTML
│   ├── style.css          # Стили
│   └── script.js          # JavaScript
├── utils/
│   ├── __init__.py
│   ├── logger.py          # Логирование
│   └── cache.py           # Кеширование
├── main.py                # Главный entry point
├── requirements.txt       # Зависимости
├── Dockerfile             # Docker конфиг
└── render.yaml            # Render деплой
```

### **Технологии:**
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **ML**: scikit-learn + pandas + numpy
- **Frontend**: HTML/CSS/JS (Telegram Mini App)
- **Bot**: aiogram 3
- **Deploy**: Render Free Tier
- **Data**: CSV datasets (Kaggle/GitHub)

### **Особенности:**
- Никаких live-парсеров
- Никаких букмекеров
- Только бесплатные источники
- Graceful fallbacks
- Масштабируемая архитектура
