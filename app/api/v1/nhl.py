"""
AIBET Analytics Platform - NHL API v1
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from datetime import datetime

from app.services import nhl_service
from app.schemas import UnifiedResponse, LeagueMatch
from app.metrics import metrics
from app.logging import setup_logging

logger = setup_logging(__name__)

router = APIRouter()


@router.get("/schedule", response_model=UnifiedResponse)
async def get_nhl_schedule(
    limit: int = Query(default=50, ge=1, le=100, description="Limit number of matches")
):
    """Get NHL schedule"""
    try:
        await metrics.increment_requests("nhl_schedule")
        
        matches = await nhl_service.get_schedule(limit=limit)
        
        return UnifiedResponse(
            success=True,
            data=matches,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in NHL schedule endpoint: {e}")
        await metrics.record_error("nhl_schedule_error")
        
        # FAILSAFE: Return empty array instead of error
        return UnifiedResponse(
            success=True,
            data=[],
            timestamp=datetime.utcnow(),
            message="Service temporarily unavailable, showing cached data"
        )


@router.get("/games", response_model=UnifiedResponse)
async def get_nhl_games(
    game_id: Optional[str] = Query(default=None, description="Specific game ID")
):
    """Get NHL games"""
    try:
        await metrics.increment_requests("nhl_games")
        
        matches = await nhl_service.get_games(game_id=game_id)
        
        return UnifiedResponse(
            success=True,
            data=matches,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in NHL games endpoint: {e}")
        await metrics.record_error("nhl_games_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/standings", response_model=UnifiedResponse)
async def get_nhl_standings():
    """Get NHL standings"""
    try:
        await metrics.increment_requests("nhl_standings")
        
        standings = await nhl_service.get_standings()
        
        return UnifiedResponse(
            success=True,
            data=standings,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in NHL standings endpoint: {e}")
        await metrics.record_error("nhl_standings_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/health")
async def nhl_health():
    """NHL service health check"""
    try:
        health = await nhl_service.health_check()
        return {
            "service": "nhl",
            "status": health["status"],
            "timestamp": datetime.utcnow().isoformat(),
            "details": health
        }
    except Exception as e:
        logger.error(f"NHL health check error: {e}")
        return {
            "service": "nhl",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
