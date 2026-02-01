#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real API Server
FastAPI endpoints with real data, ML predictions, and proper error handling
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import config
from database import DatabaseManager, Match, Signal, db_manager
from parsers.cs2_parser import CS2Parser
from parsers.khl_parser import KHLParser
from parsers.odds_parser import odds_parser
from feature_engineering_real import feature_engineering
from ml_models_real import ml_models

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AIBET Analytics API",
    description="Real-time sports betting analytics API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
cs2_parser = CS2Parser()
khl_parser = KHLParser()

# Background task status
background_tasks_status = {
    "last_data_update": None,
    "last_ml_training": None,
    "is_updating": False,
    "is_training": False
}

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "background_tasks": background_tasks_status
    }

# Matches endpoints
@app.get("/api/matches")
async def get_matches(
    sport: Optional[str] = Query(None, description="Filter by sport (cs2, khl)"),
    status: Optional[str] = Query(None, description="Filter by status (upcoming, live, finished)"),
    limit: int = Query(50, ge=1, le=100, description="Number of matches to return")
):
    """Get real matches from database"""
    try:
        matches = await db_manager.get_matches(
            sport=sport,
            status=status,
            limit=limit
        )
        
        # Convert to dict format
        matches_data = []
        for match in matches:
            match_dict = {
                "id": str(match.id),
                "sport": match.sport,
                "team1": match.team1,
                "team2": match.team2,
                "score": match.score,
                "status": match.status,
                "start_time": match.start_time.isoformat() if match.start_time else None,
                "features": match.features or {}
            }
            matches_data.append(match_dict)
        
        return {
            "success": True,
            "data": matches_data,
            "count": len(matches_data),
            "filters": {
                "sport": sport,
                "status": status,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/matches/refresh")
async def refresh_matches(background_tasks: BackgroundTasks):
    """Refresh matches from real sources"""
    try:
        if background_tasks_status["is_updating"]:
            return {
                "success": False,
                "message": "Update already in progress",
                "status": background_tasks_status
            }
        
        background_tasks.add_task(update_matches_task)
        
        return {
            "success": True,
            "message": "Match update started",
            "status": background_tasks_status
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting match refresh: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Odds endpoints
@app.get("/api/odds")
async def get_odds(
    sport: Optional[str] = Query(None, description="Filter by sport (cs2, khl)"),
    bookmaker: Optional[str] = Query(None, description="Filter by bookmaker"),
    limit: int = Query(50, ge=1, le=100, description="Number of odds to return")
):
    """Get real odds from bookmakers"""
    try:
        # Get fresh odds
        if sport:
            odds_data = await odds_parser.get_all_odds(sport)
        else:
            # Get odds for both sports
            cs2_odds = await odds_parser.get_all_odds('cs2')
            khl_odds = await odds_parser.get_all_odds('khl')
            odds_data = cs2_odds + khl_odds
        
        # Filter by bookmaker if specified
        if bookmaker:
            odds_data = [o for o in odds_data if o.bookmaker == bookmaker]
        
        # Convert to dict format
        odds_list = []
        for odds in odds_data[:limit]:
            odds_dict = {
                "match_id": odds.match_id,
                "sport": odds.sport,
                "bookmaker": odds.bookmaker,
                "team1": odds.team1,
                "team2": odds.team2,
                "odds1": odds.odds1,
                "odds2": odds.odds2,
                "odds_draw": odds.odds_draw,
                "total_over": odds.total_over,
                "total_under": odds.total_under,
                "handicap1": odds.handicap1,
                "handicap2": odds.handicap2,
                "updated_at": odds.updated_at.isoformat()
            }
            odds_list.append(odds_dict)
        
        return {
            "success": True,
            "data": odds_list,
            "count": len(odds_list),
            "filters": {
                "sport": sport,
                "bookmaker": bookmaker,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting odds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/odds/average")
async def get_average_odds(
    sport: Optional[str] = Query(None, description="Filter by sport (cs2, khl)"),
    limit: int = Query(20, ge=1, le=50, description="Number of average odds to return")
):
    """Get average odds across bookmakers"""
    try:
        if sport:
            avg_odds = await odds_parser.get_average_odds(sport)
        else:
            cs2_avg = await odds_parser.get_average_odds('cs2')
            khl_avg = await odds_parser.get_average_odds('khl')
            avg_odds = cs2_avg + khl_avg
        
        return {
            "success": True,
            "data": avg_odds[:limit],
            "count": len(avg_odds[:limit]),
            "filters": {
                "sport": sport,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting average odds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ML Predictions endpoints
@app.get("/api/ml_predictions")
async def get_ml_predictions(
    sport: Optional[str] = Query(None, description="Filter by sport (cs2, khl)"),
    confidence_min: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence"),
    limit: int = Query(20, ge=1, le=50, description="Number of predictions to return")
):
    """Get ML predictions for upcoming matches"""
    try:
        predictions = await ml_models.predict_upcoming_matches(sport=sport, limit=limit)
        
        # Filter by confidence
        filtered_predictions = [
            p for p in predictions 
            if p.confidence >= confidence_min
        ]
        
        # Convert to dict format
        predictions_data = []
        for pred in filtered_predictions:
            pred_dict = {
                "match_id": pred.match_id,
                "team1": pred.team1,
                "team2": pred.team2,
                "sport": pred.sport,
                "prediction": pred.team1 if pred.prediction == 1 else pred.team2,
                "confidence": round(pred.confidence, 3),
                "probabilities": {
                    "team1": round(pred.probabilities[pred.team1], 3),
                    "team2": round(pred.probabilities[pred.team2], 3)
                },
                "model_used": pred.model_used,
                "features_used": pred.features_used,
                "timestamp": pred.timestamp.isoformat()
            }
            predictions_data.append(pred_dict)
        
        return {
            "success": True,
            "data": predictions_data,
            "count": len(predictions_data),
            "filters": {
                "sport": sport,
                "confidence_min": confidence_min,
                "limit": limit
            },
            "model_status": await ml_models.get_model_status()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting ML predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ml_models/train")
async def train_ml_models(
    background_tasks: BackgroundTasks,
    sport: Optional[str] = Query(None, description="Train on specific sport"),
    force_retrain: bool = Query(False, description="Force retraining")
):
    """Train ML models"""
    try:
        if background_tasks_status["is_training"]:
            return {
                "success": False,
                "message": "Training already in progress",
                "status": background_tasks_status
            }
        
        background_tasks.add_task(train_models_task, sport, force_retrain)
        
        return {
            "success": True,
            "message": "ML model training started",
            "status": background_tasks_status
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting ML training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml_models/status")
async def get_ml_models_status():
    """Get ML models status and metrics"""
    try:
        status = await ml_models.get_model_status()
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting ML status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Signals endpoints
@app.get("/api/signals")
async def get_signals(
    sport: Optional[str] = Query(None, description="Filter by sport (cs2, khl)"),
    confidence_min: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence"),
    limit: int = Query(10, ge=1, le=20, description="Number of signals to return")
):
    """Get betting signals (high-confidence predictions)"""
    try:
        # Get high-confidence predictions as signals
        predictions = await ml_models.predict_upcoming_matches(sport=sport, limit=limit*2)
        
        # Filter for high confidence
        signals = [
            p for p in predictions 
            if p.confidence >= confidence_min
        ][:limit]
        
        # Convert to signal format
        signals_data = []
        for signal in signals:
            signal_dict = {
                "id": f"signal_{signal.match_id}",
                "match_id": signal.match_id,
                "team1": signal.team1,
                "team2": signal.team2,
                "sport": signal.sport,
                "prediction": signal.team1 if signal.prediction == 1 else signal.team2,
                "confidence": round(signal.confidence, 3),
                "odds_suggested": round(1.0 / signal.confidence, 2),  # Suggested odds
                "value_score": round((signal.confidence * 2.0 - 1.0) * 100, 1),  # Value percentage
                "model_used": signal.model_used,
                "created_at": signal.timestamp.isoformat(),
                "status": "active"
            }
            signals_data.append(signal_dict)
        
        return {
            "success": True,
            "data": signals_data,
            "count": len(signals_data),
            "filters": {
                "sport": sport,
                "confidence_min": confidence_min,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Statistics endpoints
@app.get("/api/stats/teams/{team_name}")
async def get_team_stats(
    team_name: str,
    sport: str = Query(..., description="Sport (cs2, khl)")
):
    """Get detailed team statistics"""
    try:
        features = await feature_engineering.get_team_features(team_name, sport)
        features_dict = feature_engineering.features_to_dict(features)
        
        return {
            "success": True,
            "data": {
                "team_name": features.team_name,
                "sport": features.sport,
                "features": features_dict,
                "metadata": {
                    "total_matches": features.total_matches,
                    "last_updated": features.last_updated.isoformat()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting team stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def update_matches_task():
    """Background task to update matches"""
    try:
        background_tasks_status["is_updating"] = True
        logger.info("🔄 Starting match update task")
        
        # Update CS2 matches
        cs2_matches = await cs2_parser.parse_matches()
        for match in cs2_matches:
            try:
                await db_manager.add_match(match)
            except Exception as e:
                logger.warning(f"⚠️ Error saving CS2 match: {e}")
        
        # Update KHL matches
        khl_matches = await khl_parser.parse_matches()
        for match in khl_matches:
            try:
                await db_manager.add_match(match)
            except Exception as e:
                logger.warning(f"⚠️ Error saving KHL match: {e}")
        
        background_tasks_status["last_data_update"] = datetime.now().isoformat()
        logger.info(f"✅ Match update completed: {len(cs2_matches)} CS2, {len(khl_matches)} KHL")
        
    except Exception as e:
        logger.error(f"❌ Error in match update task: {e}")
    finally:
        background_tasks_status["is_updating"] = False

async def train_models_task(sport: Optional[str], force_retrain: bool):
    """Background task to train ML models"""
    try:
        background_tasks_status["is_training"] = True
        logger.info("🤖 Starting ML training task")
        
        success = await ml_models.train_models(sport=sport, force_retrain=force_retrain)
        
        if success:
            background_tasks_status["last_ml_training"] = datetime.now().isoformat()
            logger.info("✅ ML training completed successfully")
        else:
            logger.warning("⚠️ ML training failed")
        
    except Exception as e:
        logger.error(f"❌ Error in ML training task: {e}")
    finally:
        background_tasks_status["is_training"] = False

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now().isoformat()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("🚀 AIBET Analytics API starting up")
    
    # Initialize database
    try:
        await db_manager.initialize()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Check if models need training
    try:
        await ml_models.retrain_if_needed(days_threshold=7)
    except Exception as e:
        logger.warning(f"⚠️ ML model check failed: {e}")
    
    logger.info("✅ AIBET Analytics API ready")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 AIBET Analytics API shutting down")
    
    # Close database connections
    try:
        await db_manager.close()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "api_server_real:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
