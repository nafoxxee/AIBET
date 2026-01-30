#!/usr/bin/env python3
"""
AI BET Analytics Platform - Web Service for Mini App
FastAPI server for web interface and API endpoints
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Создание директории для логов (ДО любого импорта модулей)
os.makedirs("logs", exist_ok=True)

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="AI BET Analytics Platform",
    description="Sports betting analytics platform",
    version="1.0.0"
)

# HTML для Mini App
MINI_APP_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI BET Analytics</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .matches-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .match-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .btn:hover {
            background: #45a049;
        }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
        .status.active { background: #4CAF50; }
        .status.pending { background: #FF9800; }
        .status.completed { background: #2196F3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 AI BET Analytics Platform</h1>
            <p>Аналитика спортивных ставок на основе ИИ</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">247</div>
                <div>Проанализировано матчей</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">73%</div>
                <div>Точность прогнозов</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">12</div>
                <div>Активных сигналов</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">+45%</div>
                <div>Прибыль за месяц</div>
            </div>
        </div>

        <div class="matches-section">
            <h2>🎮 CS2 Матчи</h2>
            <div class="match-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>NAVI vs G2</strong>
                        <div style="color: #ccc; font-size: 14px;">BLAST Premier • 18:00</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="status active">LIVE</div>
                        <div style="margin-top: 5px;">
                            <span style="color: #4CAF50;">1.85</span> — 
                            <span style="color: #4CAF50;">1.95</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="match-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>FaZe vs Vitality</strong>
                        <div style="color: #ccc; font-size: 14px;">IEM Katowice • 20:00</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="status pending">Скоро</div>
                        <div style="margin-top: 5px;">
                            <span>1.75</span> — 
                            <span>2.10</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="matches-section">
            <h2>🏒 КХЛ Матчи</h2>
            <div class="match-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>ЦСКА vs СКА</strong>
                        <div style="color: #ccc; font-size: 14px;">КХЛ • 19:30</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="status active">LIVE</div>
                        <div style="margin-top: 5px;">
                            <span style="color: #4CAF50;">2.10</span> — 
                            <span style="color: #4CAF50;">1.80</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div style="text-align: center; margin-top: 40px;">
            <button class="btn" onclick="refreshData()">🔄 Обновить данные</button>
        </div>
    </div>

    <script>
        function refreshData() {
            location.reload();
        }
        
        // Автообновление каждые 30 секунд
        setInterval(refreshData, 30000);
        
        // Проверка статуса сервера
        fetch('/api/health')
            .then(response => response.json())
            .then(data => {
                console.log('Server status:', data);
            })
            .catch(error => {
                console.error('Health check failed:', error);
            });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    """Главная страница Mini App"""
    return MINI_APP_HTML

@app.get("/api/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "web",
        "timestamp": "2026-01-30T20:00:00Z",
        "version": "1.0.0"
    }

@app.get("/api/stats")
async def get_stats():
    """Получение статистики"""
    return {
        "matches_analyzed": 247,
        "accuracy": 73,
        "active_signals": 12,
        "monthly_profit": 45,
        "cs2_matches": 15,
        "khl_matches": 8
    }

@app.get("/api/matches")
async def get_matches():
    """Получение списка матчей"""
    return {
        "cs2": [
            {
                "id": "navi_vs_g2",
                "team1": "NAVI",
                "team2": "G2",
                "tournament": "BLAST Premier",
                "time": "18:00",
                "status": "live",
                "odds1": 1.85,
                "odds2": 1.95
            },
            {
                "id": "faze_vs_vitality",
                "team1": "FaZe",
                "team2": "Vitality",
                "tournament": "IEM Katowice",
                "time": "20:00",
                "status": "upcoming",
                "odds1": 1.75,
                "odds2": 2.10
            }
        ],
        "khl": [
            {
                "id": "cska_vs_ska",
                "team1": "ЦСКА",
                "team2": "СКА",
                "tournament": "КХЛ",
                "time": "19:30",
                "status": "live",
                "odds1": 2.10,
                "odds2": 1.80
            }
        ]
    }

@app.get("/api/signals")
async def get_signals():
    """Получение сигналов"""
    return {
        "signals": [
            {
                "id": "cs2_1",
                "match": "NAVI vs G2",
                "sport": "cs2",
                "scenario": "Победа NAVI",
                "confidence": "HIGH",
                "probability": 0.78,
                "odds": 1.85
            },
            {
                "id": "khl_1",
                "match": "ЦСКА vs СКА",
                "sport": "khl",
                "scenario": "Тотал больше 4.5",
                "confidence": "MEDIUM",
                "probability": 0.65,
                "odds": 1.95
            }
        ]
    }

# Pinger для поддержания сервиса активным
@app.get("/ping")
async def ping():
    """Pinger endpoint для Render"""
    return {"status": "pong", "timestamp": "2026-01-30T20:00:00Z"}

async def main():
    """Основная функция запуска"""
    try:
        # Получаем порт из переменных окружения Render
        PORT = int(os.environ.get('PORT', 10000))
        HOST = "0.0.0.0"
        
        logger.info(f"🚀 Запуск AI BET Web Service на {HOST}:{PORT}")
        logger.info("📱 Mini App доступна по адресу: /")
        logger.info("🔗 API документация: /docs")
        
        # Запуск сервера
        config = uvicorn.Config(
            app=app,
            host=HOST,
            port=PORT,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска веб-сервиса: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
