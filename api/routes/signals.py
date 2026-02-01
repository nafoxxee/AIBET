"""
AIBET MVP API Routes - Signals
Endpoints for betting signals
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.connection import get_db
from database.models import Signal, Match, Team

router = APIRouter()

# Pydantic models
class SignalResponse(BaseModel):
    id: int
    match_id: int
    team1: str
    team2: str
    sport: str
    prediction: str
    probability: float
    confidence: float
    value_score: float
    explanation: str
    is_active: bool
    created_at: str

class SignalStats(BaseModel):
    total_signals: int
    active_signals: int
    cs2_signals: int
    khl_signals: int
    avg_confidence: float
    avg_value_score: float

@router.get("/signals", response_model=List[SignalResponse])
async def get_signals(
    sport: Optional[str] = Query(None, description="Filter by sport (cs2, khl)"),
    active: Optional[bool] = Query(None, description="Filter active signals only"),
    limit: int = Query(50, le=100, description="Maximum number of signals"),
    db: Session = Depends(get_db)
):
    """Get betting signals with optional filters"""
    try:
        query = db.query(Signal).join(Match).join(Team, Match.team1_id == Team.id)
        
        if sport:
            query = query.filter(Signal.sport == sport)
        
        if active is not None:
            query = query.filter(Signal.is_active == active)
        
        signals = query.order_by(Signal.created_at.desc()).limit(limit).all()
        
        result = []
        for signal in signals:
            result.append(SignalResponse(
                id=signal.id,
                match_id=signal.match_id,
                team1=signal.match.team1.name if signal.match and signal.match.team1 else "Unknown",
                team2=signal.match.team2.name if signal.match and signal.match.team2 else "Unknown",
                sport=signal.sport,
                prediction=signal.prediction,
                probability=signal.probability,
                confidence=signal.confidence,
                value_score=signal.value_score or 0.0,
                explanation=signal.explanation or "",
                is_active=signal.is_active,
                created_at=signal.created_at.isoformat() if signal.created_at else None
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals/active", response_model=List[SignalResponse])
async def get_active_signals(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    limit: int = Query(20, le=50, description="Maximum number of signals"),
    db: Session = Depends(get_db)
):
    """Get active signals only"""
    return await get_signals(sport=sport, active=True, limit=limit, db=db)

@router.get("/signals/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: int, db: Session = Depends(get_db)):
    """Get specific signal by ID"""
    try:
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        return SignalResponse(
            id=signal.id,
            match_id=signal.match_id,
            team1=signal.match.team1.name if signal.match and signal.match.team1 else "Unknown",
            team2=signal.match.team2.name if signal.match and signal.match.team2 else "Unknown",
            sport=signal.sport,
            prediction=signal.prediction,
            probability=signal.probability,
            confidence=signal.confidence,
            value_score=signal.value_score or 0.0,
            explanation=signal.explanation or "",
            is_active=signal.is_active,
            created_at=signal.created_at.isoformat() if signal.created_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals/statistics", response_model=SignalStats)
async def get_signal_statistics(db: Session = Depends(get_db)):
    """Get signal statistics"""
    try:
        # Total signals
        total_signals = db.query(Signal).count()
        
        # Active signals
        active_signals = db.query(Signal).filter(Signal.is_active == True).count()
        
        # Sport-specific signals
        cs2_signals = db.query(Signal).filter(Signal.sport == 'cs2').count()
        khl_signals = db.query(Signal).filter(Signal.sport == 'khl').count()
        
        # Average metrics
        signals = db.query(Signal).all()
        
        if signals:
            avg_confidence = sum(s.confidence for s in signals) / len(signals)
            avg_value_score = sum(s.value_score or 0 for s in signals) / len(signals)
        else:
            avg_confidence = 0.0
            avg_value_score = 0.0
        
        return SignalStats(
            total_signals=total_signals,
            active_signals=active_signals,
            cs2_signals=cs2_signals,
            khl_signals=khl_signals,
            avg_confidence=avg_confidence,
            avg_value_score=avg_value_score
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signals/{signal_id}/deactivate")
async def deactivate_signal(signal_id: int, db: Session = Depends(get_db)):
    """Deactivate a signal"""
    try:
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        signal.is_active = False
        signal.updated_at = datetime.now()
        db.commit()
        
        return {"message": "Signal deactivated successfully", "signal_id": signal_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals/performance")
async def get_signal_performance(
    days: int = Query(30, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get signal performance metrics"""
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get signals with results
        signals = db.query(Signal).filter(
            Signal.created_at >= cutoff_date,
            Signal.result.isnot(None)
        ).all()
        
        if not signals:
            return {
                "period_days": days,
                "total_signals": 0,
                "win_rate": 0.0,
                "avg_confidence": 0.0,
                "profit_loss": 0.0
            }
        
        # Calculate metrics
        wins = sum(1 for s in signals if s.result == 'win')
        losses = sum(1 for s in signals if s.result == 'loss')
        total = len(signals)
        
        win_rate = wins / total if total > 0 else 0.0
        avg_confidence = sum(s.confidence for s in signals) / total if total > 0 else 0.0
        
        # Simplified P&L calculation (would use actual odds in real implementation)
        profit_loss = (wins * 1.0) - (losses * 1.0)  # Assuming even odds
        
        return {
            "period_days": days,
            "total_signals": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "avg_confidence": avg_confidence,
            "profit_loss": profit_loss
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
