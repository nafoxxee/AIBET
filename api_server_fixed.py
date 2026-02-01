#!/usr/bin/env python3
"""
AIBET Analytics Platform - Fixed API Server
Исправленный FastAPI сервер с реальными данными
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os

logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(
    title="AIBET Analytics API",
    description="Sports analytics and predictions API",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic модели
class MatchResponse(BaseModel):
    id: int
    sport: str
    team1: str
    team2: str
    tournament: str
    date: str
    status: str
    score: Optional[str] = None
    format: Optional[str] = None
    link: Optional[str] = None
    source: str
    features: Optional[Dict] = None

class SignalResponse(BaseModel):
    id: int
    sport: str
    team1: str
    team2: str
    tournament: str
    date: str
    prediction: str
    probability: float
    facts: Optional[str] = None
    recommendation: Optional[str] = None
    published: bool
    created_at: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    database: str
    matches_count: int
    signals_count: int

# Глобальные переменные
db_manager = None
signal_generator = None

async def init_services():
    """Инициализация сервисов"""
    global db_manager, signal_generator
    
    try:
        from database_fixed import DatabaseManager
        from signal_generator_fixed import SignalGeneratorFixed
        
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        signal_generator = SignalGeneratorFixed(db_manager)
        
        logger.info("✅ Services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Error initializing services: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Событие запуска"""
    await init_services()

@app.get("/", response_model=Dict)
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "AIBET Analytics API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья системы"""
    try:
        if not db_manager:
            await init_services()
        
        matches_count = await db_manager.get_match_count()
        signals_count = len(await db_manager.get_signals())
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            service="api",
            database="connected",
            matches_count=matches_count,
            signals_count=signals_count
        )
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/api/matches", response_model=List[MatchResponse])
async def get_matches(sport: Optional[str] = None, status: Optional[str] = None, limit: int = 50):
    """Получить матчи"""
    try:
        if not db_manager:
            await init_services()
        
        matches = await db_manager.get_matches(sport=sport, status=status, limit=limit)
        
        if not matches:
            return []
        
        return [MatchResponse(**match) for match in matches]
        
    except Exception as e:
        logger.error(f"❌ Error getting matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to get matches")

@app.get("/api/matches/upcoming", response_model=List[MatchResponse])
async def get_upcoming_matches(sport: Optional[str] = None, limit: int = 20):
    """Получить предстоящие матчи"""
    try:
        if not db_manager:
            await init_services()
        
        matches = await db_manager.get_upcoming_matches(sport=sport)
        
        if not matches:
            return []
        
        return [MatchResponse(**match) for match in matches[:limit]]
        
    except Exception as e:
        logger.error(f"❌ Error getting upcoming matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to get upcoming matches")

@app.get("/api/signals", response_model=List[SignalResponse])
async def get_signals(sport: Optional[str] = None, published: Optional[bool] = None):
    """Получить сигналы"""
    try:
        if not db_manager:
            await init_services()
        
        signals = await db_manager.get_signals(sport=sport, published=published)
        
        if not signals:
            return []
        
        return [SignalResponse(**signal) for signal in signals]
        
    except Exception as e:
        logger.error(f"❌ Error getting signals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get signals")

@app.get("/api/signals/active", response_model=List[SignalResponse])
async def get_active_signals(sport: Optional[str] = None):
    """Получить активные сигналы"""
    try:
        if not signal_generator:
            await init_services()
        
        signals = await signal_generator.get_active_signals(sport=sport)
        
        if not signals:
            return []
        
        return [SignalResponse(**signal) for signal in signals]
        
    except Exception as e:
        logger.error(f"❌ Error getting active signals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active signals")

@app.get("/api/stats")
async def get_stats():
    """Получить статистику"""
    try:
        if not db_manager:
            await init_services()
        
        total_matches = await db_manager.get_match_count()
        cs2_matches = len(await db_manager.get_matches(sport='cs2'))
        khl_matches = len(await db_manager.get_matches(sport='khl'))
        total_signals = len(await db_manager.get_signals())
        published_signals = len(await db_manager.get_signals(published=True))
        
        return {
            "matches": {
                "total": total_matches,
                "cs2": cs2_matches,
                "khl": khl_matches
            },
            "signals": {
                "total": total_signals,
                "published": published_signals,
                "unpublished": total_signals - published_signals
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")

@app.get("/api/predict/{match_id}")
async def predict_match(match_id: int):
    """Прогноз матча"""
    try:
        if not db_manager:
            await init_services()
        
        # Получаем матч
        matches = await db_manager.get_matches()
        match = next((m for m in matches if m['id'] == match_id), None)
        
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Получаем прогноз
        from ml_models_fixed import MLModelsFixed
        ml_models = MLModelsFixed(db_manager)
        prediction = await ml_models.predict_match(match, match['sport'])
        
        return {
            "match_id": match_id,
            "prediction": prediction,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error predicting match: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict match")

@app.post("/api/update", response_model=Dict)
async def update_data(background_tasks: BackgroundTasks):
    """Обновить данные"""
    try:
        # Запускаем обновление в фоне
        background_tasks.add_task(run_data_update)
        
        return {
            "message": "Data update started",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting data update: {e}")
        raise HTTPException(status_code=500, detail="Failed to start data update")

@app.post("/api/generate-signals", response_model=Dict)
async def generate_signals(background_tasks: BackgroundTasks):
    """Генерировать сигналы"""
    try:
        # Запускаем генерацию в фоне
        background_tasks.add_task(run_signal_generation)
        
        return {
            "message": "Signal generation started",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting signal generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start signal generation")

@app.get("/api/team-stats/{team_name}")
async def get_team_stats(team_name: str, sport: str):
    """Получить статистику команды"""
    try:
        if not db_manager:
            await init_services()
        
        stats = await db_manager.get_team_stats(team_name, sport)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Team stats not found")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting team stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get team stats")

# Фоновые задачи
async def run_data_update():
    """Фоновое обновление данных"""
    try:
        logger.info("🔄 Starting background data update")
        
        # Обновление CS2 матчей
        from parsers.cs2_parser_fixed import CS2ParserFixed
        cs2_parser = CS2ParserFixed()
        cs2_matches = await cs2_parser.parse_matches()
        
        for match in cs2_matches:
            await db_manager.add_match(match)
        
        # Обновление КХЛ матчей
        from parsers.khl_parser_fixed import KHLParserFixed
        khl_parser = KHLParserFixed()
        khl_matches = await khl_parser.parse_matches()
        
        for match in khl_matches:
            await db_manager.add_match(match)
        
        logger.info(f"✅ Data update completed: {len(cs2_matches)} CS2, {len(khl_matches)} KHL")
        
    except Exception as e:
        logger.error(f"❌ Background data update failed: {e}")

async def run_signal_generation():
    """Фоновая генерация сигналов"""
    try:
        logger.info("🎯 Starting background signal generation")
        
        if not signal_generator:
            await init_services()
        
        signals = await signal_generator.generate_signals()
        
        # Публикация сигналов
        for signal in signals:
            await signal_generator.publish_signal_to_channel(signal)
        
        logger.info(f"✅ Signal generation completed: {len(signals)} signals")
        
    except Exception as e:
        logger.error(f"❌ Background signal generation failed: {e}")

# Обработка ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик ошибок"""
    logger.error(f"❌ Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api_server_fixed:app",
        host="0.0.0.0",
        port=1000,
        reload=True,
        log_level="info"
    )
