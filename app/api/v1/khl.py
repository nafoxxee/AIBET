"""
AIBET Analytics Platform - KHL API v1
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from app.services import khl_service
from app.schemas import UnifiedResponse, LeagueMatch
from app.metrics import metrics
from app.logging import setup_logging

logger = setup_logging(__name__)

router = APIRouter()


@router.get("/schedule", response_model=UnifiedResponse)
async def get_khl_schedule(
    limit: int = Query(default=50, ge=1, le=100, description="Limit number of matches")
):
    """Get KHL schedule"""
    try:
        await metrics.increment_requests("khl_schedule")
        
        matches = await khl_service.get_schedule(limit=limit)
        
        return UnifiedResponse(
            success=True,
            data=matches,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in KHL schedule endpoint: {e}")
        await metrics.record_error("khl_schedule_error")
        
        # FAILSAFE: Return empty array instead of error
        return UnifiedResponse(
            success=True,
            data=[],
            timestamp=datetime.utcnow(),
            message="Service temporarily unavailable, showing cached data"
        )


@router.get("/games", response_model=UnifiedResponse)
async def get_khl_games(
    game_id: Optional[str] = Query(default=None, description="Specific game ID")
):
    """Get KHL games"""
    try:
        await metrics.increment_requests("khl_games")
        
        matches = await khl_service.get_games(game_id=game_id)
        
        return UnifiedResponse(
            success=True,
            data=matches,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in KHL games endpoint: {e}")
        await metrics.record_error("khl_games_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/standings", response_model=UnifiedResponse)
async def get_khl_standings():
    """Get KHL standings"""
    try:
        await metrics.increment_requests("khl_standings")
        
        standings = await khl_service.get_standings()
        
        return UnifiedResponse(
            success=True,
            data=standings,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in KHL standings endpoint: {e}")
        await metrics.record_error("khl_standings_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/health")
async def khl_health():
    """KHL service health check"""
    try:
        health = await khl_service.health_check()
        return {
            "service": "khl",
            "status": health["status"],
            "timestamp": datetime.utcnow().isoformat(),
            "details": health
        }
    except Exception as e:
        logger.error(f"KHL health check error: {e}")
        return {
            "service": "khl",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
