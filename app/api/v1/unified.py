"""
AIBET Analytics Platform - Unified API v1
Combined data from all leagues
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from app.services import nhl_service, khl_service, cs2_service
from app.schemas import UnifiedResponse, LeagueMatch
from app.metrics import metrics
from app.quality import quality_assessor
from app.logging import setup_logging

logger = setup_logging(__name__)

router = APIRouter()


@router.get("/matches", response_model=UnifiedResponse)
async def get_unified_matches(
    league: Optional[str] = Query(default=None, description="Filter by league (NHL, KHL, CS2)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=100, ge=1, le=200, description="Limit number of matches")
):
    """Get unified matches from all leagues"""
    try:
        await metrics.increment_requests("unified_matches")
        
        all_matches = []
        
        # Get matches from all enabled services
        from app.config import settings
        
        if settings.ENABLE_NHL and (league is None or league.upper() == "NHL"):
            nhl_matches = await nhl_service.get_schedule(limit=limit//3)
            all_matches.extend(nhl_matches)
        
        if settings.ENABLE_KHL and (league is None or league.upper() == "KHL"):
            khl_matches = await khl_service.get_schedule(limit=limit//3)
            all_matches.extend(khl_matches)
        
        if settings.ENABLE_CS2 and (league is None or league.upper() == "CS2"):
            cs2_upcoming = await cs2_service.get_upcoming(limit=limit//3)
            cs2_results = await cs2_service.get_results(limit=limit//3)
            all_matches.extend(cs2_upcoming)
            all_matches.extend(cs2_results)
        
        # Filter by status if provided
        if status:
            all_matches = [match for match in all_matches if match.status == status]
        
        # Assess data quality
        filtered_matches = await quality_assessor.filter_bad_data(all_matches)
        
        # Sort by start time
        filtered_matches.sort(key=lambda x: x.start_time, reverse=True)
        
        # Apply limit
        filtered_matches = filtered_matches[:limit]
        
        return UnifiedResponse(
            success=True,
            data=filtered_matches,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in unified matches endpoint: {e}")
        await metrics.record_error("unified_matches_error")
        
        # FAILSAFE: Return empty array instead of error
        return UnifiedResponse(
            success=True,
            data=[],
            timestamp=datetime.utcnow(),
            message="Service temporarily unavailable, showing cached data"
        )


@router.get("/leagues", response_model=UnifiedResponse)
async def get_available_leagues():
    """Get available leagues and their status"""
    try:
        await metrics.increment_requests("unified_leagues")
        
        from app.config import settings
        
        leagues = {
            "NHL": {
                "enabled": settings.ENABLE_NHL,
                "description": "National Hockey League",
                "data_sources": ["api-web.nhle.com"],
                "features": ["schedule", "games", "standings", "odds"]
            },
            "KHL": {
                "enabled": settings.ENABLE_KHL,
                "description": "Kontinental Hockey League",
                "data_sources": ["khl.ru"],
                "features": ["schedule", "games", "standings", "odds"]
            },
            "CS2": {
                "enabled": settings.ENABLE_CS2,
                "description": "Counter-Strike 2 Esports",
                "data_sources": ["hltv.org", "faceit.com", "esea.net"],
                "features": ["upcoming", "results", "matches", "tournaments", "odds"]
            }
        }
        
        return UnifiedResponse(
            success=True,
            data=leagues,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in unified leagues endpoint: {e}")
        await metrics.record_error("unified_leagues_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/summary", response_model=UnifiedResponse)
async def get_unified_summary():
    """Get unified summary of all data"""
    try:
        await metrics.increment_requests("unified_summary")
        
        from app.config import settings
        
        summary = {
            "total_matches": 0,
            "leagues_status": {},
            "data_quality": {},
            "last_updated": {}
        }
        
        # Get data from each league
        if settings.ENABLE_NHL:
            nhl_matches = await nhl_service.get_schedule(limit=10)
            summary["leagues_status"]["NHL"] = {
                "enabled": True,
                "matches_count": len(nhl_matches),
                "last_check": datetime.utcnow().isoformat()
            }
            summary["total_matches"] += len(nhl_matches)
        
        if settings.ENABLE_KHL:
            khl_matches = await khl_service.get_schedule(limit=10)
            summary["leagues_status"]["KHL"] = {
                "enabled": True,
                "matches_count": len(khl_matches),
                "last_check": datetime.utcnow().isoformat()
            }
            summary["total_matches"] += len(khl_matches)
        
        if settings.ENABLE_CS2:
            cs2_upcoming = await cs2_service.get_upcoming(limit=5)
            cs2_results = await cs2_service.get_results(limit=5)
            cs2_total = len(cs2_upcoming) + len(cs2_results)
            summary["leagues_status"]["CS2"] = {
                "enabled": True,
                "matches_count": cs2_total,
                "last_check": datetime.utcnow().isoformat()
            }
            summary["total_matches"] += cs2_total
        
        summary["last_updated"] = datetime.utcnow().isoformat()
        
        return UnifiedResponse(
            success=True,
            data=summary,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in unified summary endpoint: {e}")
        await metrics.record_error("unified_summary_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/search", response_model=UnifiedResponse)
async def search_matches(
    query: str = Query(..., description="Search query for teams"),
    league: Optional[str] = Query(default=None, description="Filter by league"),
    limit: int = Query(default=20, ge=1, le=50, description="Limit search results")
):
    """Search matches by team names"""
    try:
        await metrics.increment_requests("unified_search")
        
        # Get all matches
        all_matches_response = await get_unified_matches(league=league, limit=200)
        all_matches = all_matches_response.data or []
        
        # Search by team names
        query_lower = query.lower()
        search_results = []
        
        for match in all_matches:
            if any(query_lower in team.lower() for team in match.teams):
                search_results.append(match)
        
        # Limit results
        search_results = search_results[:limit]
        
        return UnifiedResponse(
            success=True,
            data=search_results,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in unified search endpoint: {e}")
        await metrics.record_error("unified_search_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )
