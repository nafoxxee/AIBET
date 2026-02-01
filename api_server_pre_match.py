#!/usr/bin/env python3
"""
AIBET Analytics Platform - Pre-Match API Server
FastAPI сервер для pre-match режима без live данных
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
    title="AIBET Pre-Match Analytics API",
    description="Pre-Match sports analytics and predictions API",
    version="3.0.0"
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
class PreMatchMatchResponse(BaseModel):
    id: int
    sport: str
    team1: str
    team2: str
    tournament: str
    date: str
    status: str
    format: Optional[str] = None
    source: str
    match_type: str = "pre_match"
    features: Optional[Dict] = None

class PreMatchSignalResponse(BaseModel):
    id: int
    sport: str
    team1: str
    team2: str
    tournament: str
    date: str
    prediction: str
    probability: float
    confidence: str
    facts: Optional[str] = None
    recommendation: Optional[str] = None
    published: bool
    created_at: str

class PreMatchHealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    mode: str
    database: str
    matches_count: int
    historical_matches_count: int
    signals_count: int

# Глобальные переменные
db_manager = None
signal_generator = None

async def init_services():
    """Инициализация сервисов"""
    global db_manager, signal_generator
    
    try:
        from database_pre_match import pre_match_db
        from signal_generator_pre_match import PreMatchSignalGenerator
        
        db_manager = pre_match_db
        await db_manager.initialize()
        
        # Инициализация тестовых данных
        await db_manager.initialize_test_data()
        
        signal_generator = PreMatchSignalGenerator(db_manager)
        
        logger.info("✅ Pre-Match services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Error initializing pre-match services: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Событие запуска"""
    await init_services()

@app.get("/", response_model=Dict)
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "AIBET Pre-Match Analytics API",
        "version": "3.0.0",
        "status": "running",
        "mode": "pre_match",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health", response_model=PreMatchHealthResponse)
async def health_check():
    """Проверка здоровья pre-match системы"""
    try:
        if not db_manager:
            await init_services()
        
        matches_count = await db_manager.get_match_count()
        historical_matches_count = await db_manager.get_historical_match_count()
        signals_count = len(await db_manager.get_signals())
        
        return PreMatchHealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            service="pre_match_api",
            mode="pre_match",
            database="connected",
            matches_count=matches_count,
            historical_matches_count=historical_matches_count,
            signals_count=signals_count
        )
        
    except Exception as e:
        logger.error(f"❌ Pre-Match health check failed: {e}")
        raise HTTPException(status_code=500, detail="Pre-Match health check failed")

@app.get("/api/matches", response_model=List[PreMatchMatchResponse])
async def get_matches(sport: Optional[str] = None, status: Optional[str] = None, limit: int = 50):
    """Получить pre-match матчи"""
    try:
        if not db_manager:
            await init_services()
        
        matches = await db_manager.get_matches(sport=sport, status=status, limit=limit)
        
        if not matches:
            return []
        
        return [PreMatchMatchResponse(**match) for match in matches]
        
    except Exception as e:
        logger.error(f"❌ Error getting pre-match matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pre-match matches")

@app.get("/api/matches/upcoming", response_model=List[PreMatchMatchResponse])
async def get_upcoming_matches(sport: Optional[str] = None, limit: int = 30):
    """Получить предстоящие pre-match матчи"""
    try:
        if not db_manager:
            await init_services()
        
        matches = await db_manager.get_upcoming_matches(sport=sport)
        
        if not matches:
            return []
        
        return [PreMatchMatchResponse(**match) for match in matches[:limit]]
        
    except Exception as e:
        logger.error(f"❌ Error getting upcoming pre-match matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to get upcoming pre-match matches")

@app.get("/api/matches/finished", response_model=List[PreMatchMatchResponse])
async def get_finished_matches(sport: Optional[str] = None, limit: int = 100):
    """Получить завершенные матчи"""
    try:
        if not db_manager:
            await init_services()
        
        matches = await db_manager.get_finished_matches(sport=sport)
        
        if not matches:
            return []
        
        return [PreMatchMatchResponse(**match) for match in matches[:limit]]
        
    except Exception as e:
        logger.error(f"❌ Error getting finished matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to get finished matches")

@app.get("/api/matches/historical", response_model=List[PreMatchMatchResponse])
async def get_historical_matches(sport: Optional[str] = None, limit: int = 200):
    """Получить исторические матчи для ML"""
    try:
        if not db_manager:
            await init_services()
        
        matches = await db_manager.get_historical_matches(sport=sport, limit=limit)
        
        if not matches:
            return []
        
        return [PreMatchMatchResponse(**match) for match in matches]
        
    except Exception as e:
        logger.error(f"❌ Error getting historical matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to get historical matches")

@app.get("/api/signals", response_model=List[PreMatchSignalResponse])
async def get_signals(sport: Optional[str] = None, published: Optional[bool] = None):
    """Получить pre-match сигналы"""
    try:
        if not db_manager:
            await init_services()
        
        signals = await db_manager.get_signals(sport=sport, published=published)
        
        if not signals:
            return []
        
        return [PreMatchSignalResponse(**signal) for signal in signals]
        
    except Exception as e:
        logger.error(f"❌ Error getting pre-match signals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pre-match signals")

@app.get("/api/signals/active", response_model=List[PreMatchSignalResponse])
async def get_active_signals(sport: Optional[str] = None):
    """Получить активные pre-match сигналы"""
    try:
        if not signal_generator:
            await init_services()
        
        signals = await signal_generator.get_active_signals(sport=sport)
        
        if not signals:
            return []
        
        return [PreMatchSignalResponse(**signal) for signal in signals]
        
    except Exception as e:
        logger.error(f"❌ Error getting active pre-match signals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active pre-match signals")

@app.get("/api/statistics")
async def get_statistics():
    """Получить статистику pre-match системы"""
    try:
        if not db_manager:
            await init_services()
        
        total_matches = await db_manager.get_match_count()
        historical_matches = await db_manager.get_historical_match_count()
        cs2_matches = len(await db_manager.get_matches(sport='cs2'))
        khl_matches = len(await db_manager.get_matches(sport='khl'))
        total_signals = len(await db_manager.get_signals())
        published_signals = len(await db_manager.get_signals(published=True))
        
        return {
            "mode": "pre_match",
            "matches": {
                "total": total_matches,
                "upcoming": total_matches,
                "historical": historical_matches,
                "cs2": cs2_matches,
                "khl": khl_matches
            },
            "signals": {
                "total": total_signals,
                "published": published_signals,
                "unpublished": total_signals - published_signals,
                "active": len(await signal_generator.get_active_signals()) if signal_generator else 0
            },
            "ml_models": {
                "training_data": historical_matches,
                "status": "trained" if historical_matches >= 30 else "insufficient_data"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting pre-match statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pre-match statistics")

@app.get("/api/predict/{match_id}")
async def predict_match(match_id: int):
    """Pre-Match прогноз матча"""
    try:
        if not db_manager:
            await init_services()
        
        # Получаем матч
        matches = await db_manager.get_matches()
        match = next((m for m in matches if m['id'] == match_id), None)
        
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Получаем pre-match прогноз
        from ml_models_pre_match import PreMatchMLModels
        ml_models = PreMatchMLModels(db_manager)
        prediction = await ml_models.predict_match(match, match['sport'])
        
        return {
            "match_id": match_id,
            "mode": "pre_match",
            "prediction": prediction,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in pre-match prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict pre-match match")

@app.post("/api/update", response_model=Dict)
async def update_data(background_tasks: BackgroundTasks):
    """Обновить pre-match данные"""
    try:
        # Запускаем обновление в фоне
        background_tasks.add_task(run_pre_match_data_update)
        
        return {
            "message": "Pre-Match data update started",
            "mode": "pre_match",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting pre-match data update: {e}")
        raise HTTPException(status_code=500, detail="Failed to start pre-match data update")

@app.post("/api/generate-signals", response_model=Dict)
async def generate_signals(background_tasks: BackgroundTasks):
    """Генерировать pre-match сигналы"""
    try:
        # Запускаем генерацию в фоне
        background_tasks.add_task(run_pre_match_signal_generation)
        
        return {
            "message": "Pre-Match signal generation started",
            "mode": "pre_match",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting pre-match signal generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start pre-match signal generation")

@app.post("/api/train-models", response_model=Dict)
async def train_models(background_tasks: BackgroundTasks):
    """Обучить ML модели на исторических данных"""
    try:
        # Запускаем обучение в фоне
        background_tasks.add_task(run_ml_training)
        
        return {
            "message": "Pre-Match ML models training started",
            "mode": "pre_match",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting ML training: {e}")
        raise HTTPException(status_code=500, detail="Failed to start ML training")

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
        logger.error(f"❌ Error getting pre-match team stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pre-match team stats")

# Фоновые задачи
async def run_pre_match_data_update():
    """Фоновое обновление pre-match данных"""
    try:
        logger.info("🔄 Starting background pre-match data update")
        
        # Обновление CS2 pre-match матчей
        from data_sources.pre_match.cs2_pre_match import cs2_pre_match_source
        cs2_matches = await cs2_pre_match_source.get_pre_match_matches()
        
        for match in cs2_matches:
            await db_manager.add_match(match)
        
        # Обновление КХЛ pre-match матчей
        from data_sources.pre_match.khl_pre_match import khl_pre_match_source
        khl_matches = await khl_pre_match_source.get_pre_match_matches()
        
        for match in khl_matches:
            await db_manager.add_match(match)
        
        logger.info(f"✅ Pre-Match data update completed: {len(cs2_matches)} CS2, {len(khl_matches)} KHL")
        
    except Exception as e:
        logger.error(f"❌ Background pre-match data update failed: {e}")

async def run_pre_match_signal_generation():
    """Фоновая генерация pre-match сигналов"""
    try:
        logger.info("🎯 Starting background pre-match signal generation")
        
        if not signal_generator:
            await init_services()
        
        signals = await signal_generator.generate_signals()
        
        # Публикация сигналов
        for signal in signals:
            await signal_generator.publish_signal_to_channel(signal)
        
        logger.info(f"✅ Pre-Match signal generation completed: {len(signals)} signals")
        
    except Exception as e:
        logger.error(f"❌ Background pre-match signal generation failed: {e}")

async def run_ml_training():
    """Фоновое обучение ML моделей"""
    try:
        logger.info("🤖 Starting background ML training")
        
        from ml_models_pre_match import PreMatchMLModels
        ml_models = PreMatchMLModels(db_manager)
        
        # Обучаем модели для обоих видов спорта
        await ml_models.train_models('cs2')
        await ml_models.train_models('khl')
        
        logger.info("✅ ML models training completed")
        
    except Exception as e:
        logger.error(f"❌ Background ML training failed: {e}")

# Обработка ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик ошибок"""
    logger.error(f"❌ Global pre-match error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Pre-Match internal server error",
            "message": str(exc),
            "mode": "pre_match",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api_server_pre_match:app",
        host="0.0.0.0",
        port=1000,
        reload=True,
        log_level="info"
    )
