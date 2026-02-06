"""
AIBET Analytics Platform - AI Analytics API v1
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from datetime import datetime

from app.ai.context import ai_context_builder
from app.ai.features import ai_feature_engineer
from app.ai.scoring import ai_scoring_engine
from app.ai.explanation import ai_explanation_generator
from app.services import nhl_service, khl_service, cs2_service
from app.schemas import UnifiedResponse, LeagueMatch, AIExplanation, AIScore, AIContext
from app.metrics import metrics
from app.logging import setup_logging

logger = setup_logging(__name__)

router = APIRouter()


@router.get("/context/{global_match_id}", response_model=UnifiedResponse)
async def get_ai_context(
    global_match_id: str = Path(..., description="Global match ID")
):
    """Get AI context for specific match"""
    try:
        await metrics.increment_requests("ai_context")
        
        # Build AI context
        context = await ai_context_builder.build_match_context(global_match_id)
        
        return UnifiedResponse(
            success=True,
            data=context.dict(),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in AI context endpoint: {e}")
        await metrics.record_error("ai_context_error")
        
        # FAILSAFE: Return educational fallback
        return UnifiedResponse(
            success=True,
            data={
                "global_match_id": global_match_id,
                "context": "Context temporarily unavailable",
                "not_a_prediction": True,
                "educational_purpose": True,
                "message": "AI context service temporarily unavailable"
            },
            timestamp=datetime.utcnow(),
            message="Educational analysis only"
        )


@router.get("/score/{global_match_id}", response_model=UnifiedResponse)
async def get_ai_score(
    global_match_id: str = Path(..., description="Global match ID")
):
    """Get AI scoring for specific match"""
    try:
        await metrics.increment_requests("ai_score")
        
        # Build context first
        context = await ai_context_builder.build_match_context(global_match_id)
        
        # Extract features
        features = await ai_feature_engineer.extract_features(
            match=None,  # We'll extract from context
            context=context.context_data
        )
        
        # Find the match
        match = await ai_context_builder._find_match_by_id(global_match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Calculate AI score
        ai_score = await ai_scoring_engine.calculate_ai_score(match, features)
        
        return UnifiedResponse(
            success=True,
            data=ai_score.dict(),
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI score endpoint: {e}")
        await metrics.record_error("ai_score_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/explain/{global_match_id}", response_model=UnifiedResponse)
async def get_ai_explanation(
    global_match_id: str = Path(..., description="Global match ID")
):
    """Get AI explanation for specific match"""
    try:
        await metrics.increment_requests("ai_explain")
        
        # Build context
        context = await ai_context_builder.build_match_context(global_match_id)
        
        # Extract features
        features = await ai_feature_engineer.extract_features(
            match=None,
            context=context.context_data
        )
        
        # Find the match
        match = await ai_context_builder._find_match_by_id(global_match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Calculate AI score
        ai_score = await ai_scoring_engine.calculate_ai_score(match, features)
        
        # Generate explanation
        explanation = await ai_explanation_generator.generate_explanation(match, features, ai_score)
        
        return UnifiedResponse(
            success=True,
            data=explanation.dict(),
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI explain endpoint: {e}")
        await metrics.record_error("ai_explain_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/value", response_model=UnifiedResponse)
async def get_value_signals(
    league: Optional[str] = Query(default=None, description="Filter by league"),
    min_value_score: float = Query(default=0.6, ge=0.0, le=1.0, description="Minimum value score"),
    limit: int = Query(default=20, ge=1, le=50, description="Limit number of signals")
):
    """Get AI value betting signals"""
    try:
        await metrics.increment_requests("ai_value")
        
        # Get matches from all leagues
        all_matches = []
        
        from app.config import settings
        
        if settings.ENABLE_NHL and (league is None or league.upper() == "NHL"):
            nhl_matches = await nhl_service.get_schedule(limit=50)
            all_matches.extend(nhl_matches)
        
        if settings.ENABLE_KHL and (league is None or league.upper() == "KHL"):
            khl_matches = await khl_service.get_schedule(limit=50)
            all_matches.extend(khl_matches)
        
        if settings.ENABLE_CS2 and (league is None or league.upper() == "CS2"):
            cs2_matches = await cs2_service.get_matches()
            all_matches.extend(cs2_matches)
        
        # Filter for upcoming matches only
        upcoming_matches = [m for m in all_matches if m.status in ["scheduled", "upcoming"]]
        
        # Analyze each match for value
        value_signals = []
        
        for match in upcoming_matches[:limit]:
            try:
                # Build context
                context = await ai_context_builder.build_match_context(match.global_match_id)
                
                # Extract features
                features = await ai_feature_engineer.extract_features(match, context.context_data)
                
                # Calculate AI score
                ai_score = await ai_scoring_engine.calculate_ai_score(match, features)
                
                # Check if meets value threshold
                if ai_score.value_score >= min_value_score:
                    value_signals.append({
                        "global_match_id": match.global_match_id,
                        "league": match.league,
                        "teams": match.teams,
                        "start_time": match.start_time.isoformat(),
                        "signal_type": "value",
                        "strength": ai_score.value_score,
                        "ai_score": ai_score.ai_score,
                        "confidence": ai_score.confidence,
                        "risk_level": ai_score.risk_level,
                        "reasoning": f"Value score {ai_score.value_score:.2f} exceeds threshold {min_value_score}",
                        "signal_timestamp": datetime.utcnow().isoformat()
                    })
                
            except Exception as e:
                logger.error(f"Error analyzing match {match.global_match_id}: {e}")
                continue
        
        # Sort by value score
        value_signals.sort(key=lambda x: x["strength"], reverse=True)
        
        return UnifiedResponse(
            success=True,
            data={
                "signals": value_signals,
                "total_signals": len(value_signals),
                "min_value_threshold": min_value_score,
                "league_filter": league,
                "analysis_timestamp": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in AI value endpoint: {e}")
        await metrics.record_error("ai_value_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/features/{global_match_id}", response_model=UnifiedResponse)
async def get_ai_features(
    global_match_id: str = Path(..., description="Global match ID")
):
    """Get AI features for specific match"""
    try:
        await metrics.increment_requests("ai_features")
        
        # Build context
        context = await ai_context_builder.build_match_context(global_match_id)
        
        # Extract features
        features = await ai_feature_engineer.extract_features(
            match=None,
            context=context.context_data
        )
        
        return UnifiedResponse(
            success=True,
            data=features,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in AI features endpoint: {e}")
        await metrics.record_error("ai_features_error")
        
        return UnifiedResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow()
        )


@router.get("/health")
async def ai_health():
    """AI service health check"""
    try:
        # Test AI components
        test_context = await ai_context_builder.build_match_context("test_id")
        test_features = await ai_feature_engineer.extract_features(None, test_context.context_data)
        test_score = await ai_scoring_engine.calculate_ai_score(None, test_features)
        test_explanation = await ai_explanation_generator.generate_explanation(None, test_features, test_score)
        
        return {
            "service": "ai",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "context_builder": "operational",
                "feature_engineer": "operational",
                "scoring_engine": "operational",
                "explanation_generator": "operational"
            },
            "test_results": {
                "context_generated": bool(test_context.context_data),
                "features_extracted": "form" in test_features,
                "score_calculated": test_score.ai_score > 0,
                "explanation_generated": len(test_explanation.summary) > 0
            }
        }
    except Exception as e:
        logger.error(f"AI health check error: {e}")
        return {
            "service": "ai",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
