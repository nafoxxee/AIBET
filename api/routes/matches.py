"""
AIBET MVP API Routes - Matches
Endpoints for match data and predictions
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.connection import get_db
from database.models import Match, Team
from ml.predictor import Predictor

router = APIRouter()

# Pydantic models
class MatchResponse(BaseModel):
    id: int
    team1: str
    team2: str
    sport: str
    date: str
    tournament: Optional[str] = None
    result: Optional[str] = None
    score: Optional[str] = None
    is_upcoming: bool = False

class PredictionResponse(BaseModel):
    match_id: int
    team1: str
    team2: str
    sport: str
    prediction: str
    probabilities: dict
    confidence: float
    explanation: str
    value_score: float

@router.get("/matches", response_model=List[MatchResponse])
async def get_matches(
    sport: Optional[str] = Query(None, description="Filter by sport (cs2, khl)"),
    upcoming: Optional[bool] = Query(None, description="Filter upcoming matches only"),
    limit: int = Query(50, le=100, description="Maximum number of matches"),
    db: Session = Depends(get_db)
):
    """Get matches with optional filters"""
    try:
        query = db.query(Match).join(Team, Match.team1_id == Team.id)
        
        if sport:
            query = query.filter(Match.sport == sport)
        
        if upcoming is not None:
            query = query.filter(Match.is_upcoming == upcoming)
        
        matches = query.order_by(Match.date.desc()).limit(limit).all()
        
        result = []
        for match in matches:
            result.append(MatchResponse(
                id=match.id,
                team1=match.team1.name if match.team1 else "Unknown",
                team2=match.team2.name if match.team2 else "Unknown",
                sport=match.sport,
                date=match.date.isoformat() if match.date else None,
                tournament=match.tournament,
                result=match.result,
                score=match.score,
                is_upcoming=match.is_upcoming
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matches/upcoming", response_model=List[MatchResponse])
async def get_upcoming_matches(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    limit: int = Query(20, le=50, description="Maximum number of matches"),
    db: Session = Depends(get_db)
):
    """Get upcoming matches only"""
    return await get_matches(sport=sport, upcoming=True, limit=limit, db=db)

@router.get("/matches/{match_id}", response_model=MatchResponse)
async def get_match(match_id: int, db: Session = Depends(get_db)):
    """Get specific match by ID"""
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        return MatchResponse(
            id=match.id,
            team1=match.team1.name if match.team1 else "Unknown",
            team2=match.team2.name if match.team2 else "Unknown",
            sport=match.sport,
            date=match.date.isoformat() if match.date else None,
            tournament=match.tournament,
            result=match.result,
            score=match.score,
            is_upcoming=match.is_upcoming
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/matches/{match_id}/predict", response_model=PredictionResponse)
async def predict_match(match_id: int, db: Session = Depends(get_db)):
    """Get prediction for a specific match"""
    try:
        # Check if match exists
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Get prediction
        predictor = Predictor(db)
        prediction = predictor.predict_match(match_id)
        
        if 'error' in prediction:
            raise HTTPException(status_code=500, detail=prediction['error'])
        
        return PredictionResponse(
            match_id=match_id,
            team1=match.team1.name if match.team1 else "Unknown",
            team2=match.team2.name if match.team2 else "Unknown",
            sport=match.sport,
            prediction=prediction['prediction'],
            probabilities=prediction['probabilities'],
            confidence=prediction['confidence'],
            explanation=prediction['explanation'],
            value_score=prediction['value_score']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matches/{match_id}/features")
async def get_match_features(match_id: int, db: Session = Depends(get_db)):
    """Get features used for prediction"""
    try:
        # Check if match exists
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Get features
        predictor = Predictor(db)
        features = predictor.feature_engineer.extract_features(match_id)
        
        if not features:
            return {"features": {}, "count": 0}
        
        return {
            "features": features,
            "count": len(features),
            "match_id": match_id,
            "sport": match.sport
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
