"""
AIBET Analytics Platform - CS2 API v1
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from app.services import cs2_service
from app.schemas import UnifiedResponse, LeagueMatch
from app.metrics import metrics
from app.logging import setup_logging

logger = setup_logging(__name__)

router = APIRouter()


@router.get("/upcoming", response_model=UnifiedResponse)
async def get_cs2_upcoming(
    limit: int = Query(default=50, ge=1, le=100, description="Limit number of matches")
):
    """Get CS2 upcoming matches"""
    try:
        await metrics.increment_requests("cs2_upcoming")
        
        matches = await cs2_service.get_upcoming(limit=limit)
        
        return UnifiedResponse(
            success=True,
            data=matches,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in CS2 upcoming endpoint: {e}")
        await metrics.record_error("cs2_upcoming_error")
        
        # FAILSAFE: Return empty array instead of error
        return UnifiedResponse(
            success=True,
            data=[],
            timestamp=datetime.utcnow(),
            message="Service temporarily unavailable, showing cached data"
        )


@router.get("/results", response_model=UnifiedResponse)
async def get_cs2_results(
    limit: int = Query(default=50, ge=1, le=100, description="Limit number of results")
):
    """Get CS2 match results"""
    try:
        await metrics.increment_requests("cs2_results")
        
        matches = await cs2_service.get_results(limit=limit)
        
        return UnifiedResponse(
            success=True,
            data=matches,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in CS2 results endpoint: {e}")
        await metrics.record_error("cs2_results_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/matches", response_model=UnifiedResponse)
async def get_cs2_matches(
    match_id: Optional[str] = Query(default=None, description="Specific match ID")
):
    """Get CS2 matches (upcoming + results)"""
    try:
        await metrics.increment_requests("cs2_matches")
        
        matches = await cs2_service.get_matches(match_id=match_id)
        
        return UnifiedResponse(
            success=True,
            data=matches,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in CS2 matches endpoint: {e}")
        await metrics.record_error("cs2_matches_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/tournaments", response_model=UnifiedResponse)
async def get_cs2_tournaments():
    """Get CS2 tournaments"""
    try:
        await metrics.increment_requests("cs2_tournaments")
        
        tournaments = await cs2_service.get_tournaments()
        
        return UnifiedResponse(
            success=True,
            data=tournaments,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in CS2 tournaments endpoint: {e}")
        await metrics.record_error("cs2_tournaments_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/health")
async def cs2_health():
    """CS2 service health check"""
    try:
        health = await cs2_service.health_check()
        return {
            "service": "cs2",
            "status": health["status"],
            "timestamp": datetime.utcnow().isoformat(),
            "details": health
        }
    except Exception as e:
        logger.error(f"CS2 health check error: {e}")
        return {
            "service": "cs2",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
