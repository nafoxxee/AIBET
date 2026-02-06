"""
AIBET Analytics Platform - Odds API v1
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from app.services import odds_service
from app.schemas import UnifiedResponse, OddsInfo
from app.metrics import metrics
from app.logging import setup_logging

logger = setup_logging(__name__)

router = APIRouter()


@router.get("/nhl", response_model=UnifiedResponse)
async def get_nhl_odds(
    limit: int = Query(default=50, ge=1, le=100, description="Limit number of odds")
):
    """Get NHL pre-match odds"""
    try:
        await metrics.increment_requests("odds_nhl")
        
        odds = await odds_service.get_nhl_odds(limit=limit)
        
        return UnifiedResponse(
            success=True,
            data=odds,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in NHL odds endpoint: {e}")
        await metrics.record_error("odds_nhl_error")
        
        # FAILSAFE: Return empty array instead of error
        return UnifiedResponse(
            success=True,
            data=[],
            timestamp=datetime.utcnow(),
            message="Service temporarily unavailable, showing cached data"
        )


@router.get("/khl", response_model=UnifiedResponse)
async def get_khl_odds(
    limit: int = Query(default=50, ge=1, le=100, description="Limit number of odds")
):
    """Get KHL pre-match odds"""
    try:
        await metrics.increment_requests("odds_khl")
        
        odds = await odds_service.get_khl_odds(limit=limit)
        
        return UnifiedResponse(
            success=True,
            data=odds,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in KHL odds endpoint: {e}")
        await metrics.record_error("odds_khl_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/cs2", response_model=UnifiedResponse)
async def get_cs2_odds(
    limit: int = Query(default=50, ge=1, le=100, description="Limit number of odds")
):
    """Get CS2 pre-match odds"""
    try:
        await metrics.increment_requests("odds_cs2")
        
        odds = await odds_service.get_cs2_odds(limit=limit)
        
        return UnifiedResponse(
            success=True,
            data=odds,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in CS2 odds endpoint: {e}")
        await metrics.record_error("odds_cs2_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/analysis/{league}", response_model=UnifiedResponse)
async def get_odds_analysis(
    league: str,
    hours_back: int = Query(default=24, ge=1, le=168, description="Hours back for analysis")
):
    """Get odds movement analysis"""
    try:
        await metrics.increment_requests("odds_analysis")
        
        # Get odds snapshots
        snapshots = await odds_service.get_odds_snapshots(league, hours_back)
        
        # Analyze movement
        analysis = await odds_service.analyze_odds_movement(snapshots)
        
        return UnifiedResponse(
            success=True,
            data={
                "league": league,
                "hours_back": hours_back,
                "snapshots_count": len(snapshots),
                "analysis": analysis
            },
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in odds analysis endpoint: {e}")
        await metrics.record_error("odds_analysis_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/health")
async def odds_health():
    """Odds service health check"""
    try:
        health = await odds_service.health_check()
        return {
            "service": "odds",
            "status": health["status"],
            "timestamp": datetime.utcnow().isoformat(),
            "details": health
        }
    except Exception as e:
        logger.error(f"Odds health check error: {e}")
        return {
            "service": "odds",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
