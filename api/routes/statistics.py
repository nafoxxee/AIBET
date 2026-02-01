"""
AIBET MVP API Routes - Statistics
Endpoints for system statistics and analytics
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.connection import get_db
from database.models import Match, Team, Signal, ModelMetrics

router = APIRouter()

@router.get("/statistics")
async def get_general_statistics(db: Session = Depends(get_db)):
    """Get general system statistics"""
    try:
        # Team statistics
        total_teams = db.query(Team).count()
        cs2_teams = db.query(Team).filter(Team.sport == 'cs2').count()
        khl_teams = db.query(Team).filter(Team.sport == 'khl').count()
        
        # Match statistics
        total_matches = db.query(Match).count()
        upcoming_matches = db.query(Match).filter(Match.is_upcoming == True).count()
        completed_matches = db.query(Match).filter(
            Match.is_upcoming == False,
            Match.result.isnot(None)
        ).count()
        
        cs2_matches = db.query(Match).filter(Match.sport == 'cs2').count()
        khl_matches = db.query(Match).filter(Match.sport == 'khl').count()
        
        # Signal statistics
        total_signals = db.query(Signal).count()
        active_signals = db.query(Signal).filter(Signal.is_active == True).count()
        
        return {
            "teams": {
                "total": total_teams,
                "cs2": cs2_teams,
                "khl": khl_teams
            },
            "matches": {
                "total": total_matches,
                "upcoming": upcoming_matches,
                "completed": completed_matches,
                "cs2": cs2_matches,
                "khl": khl_matches
            },
            "signals": {
                "total": total_signals,
                "active": active_signals
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/teams")
async def get_team_statistics(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    limit: int = Query(20, le=50, description="Maximum number of teams"),
    db: Session = Depends(get_db)
):
    """Get team statistics"""
    try:
        query = db.query(Team)
        
        if sport:
            query = query.filter(Team.sport == sport)
        
        teams = query.order_by(Team.rating.desc()).limit(limit).all()
        
        result = []
        for team in teams:
            # Get team match statistics
            total_matches = db.query(Match).filter(
                ((Match.team1_id == team.id) | (Match.team2_id == team.id)),
                Match.result.isnot(None)
            ).count()
            
            # Calculate wins (simplified)
            wins = db.query(Match).filter(
                Match.team1_id == team.id,
                Match.result == 'team1'
            ).count() + db.query(Match).filter(
                Match.team2_id == team.id,
                Match.result == 'team2'
            ).count()
            
            win_rate = wins / total_matches if total_matches > 0 else 0.0
            
            result.append({
                "id": team.id,
                "name": team.name,
                "sport": team.sport,
                "country": team.country,
                "rating": team.rating,
                "matches_played": total_matches,
                "wins": wins,
                "win_rate": win_rate
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/teams/{team_id}")
async def get_team_details(team_id: int, db: Session = Depends(get_db)):
    """Get detailed statistics for a specific team"""
    try:
        team = db.query(Team).filter(Team.id == team_id).first()
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get recent matches
        recent_matches = db.query(Match).filter(
            ((Match.team1_id == team_id) | (Match.team2_id == team_id)),
            Match.result.isnot(None)
        ).order_by(Match.date.desc()).limit(10).all()
        
        # Calculate form
        form = []
        for match in recent_matches:
            if match.team1_id == team_id:
                if match.result == 'team1':
                    form.append('W')
                elif match.result == 'draw':
                    form.append('D')
                else:
                    form.append('L')
            else:
                if match.result == 'team2':
                    form.append('W')
                elif match.result == 'draw':
                    form.append('D')
                else:
                    form.append('L')
        
        # Overall statistics
        total_matches = db.query(Match).filter(
            ((Match.team1_id == team_id) | (Match.team2_id == team_id)),
            Match.result.isnot(None)
        ).count()
        
        wins = db.query(Match).filter(
            Match.team1_id == team_id,
            Match.result == 'team1'
        ).count() + db.query(Match).filter(
            Match.team2_id == team_id,
            Match.result == 'team2'
        ).count()
        
        losses = db.query(Match).filter(
            ((Match.team1_id == team_id) | (Match.team2_id == team_id)),
            Match.result.in_(['team1', 'team2'])
        ).count() - wins
        
        draws = db.query(Match).filter(
            ((Match.team1_id == team_id) | (Match.team2_id == team_id)),
            Match.result == 'draw'
        ).count()
        
        return {
            "team": {
                "id": team.id,
                "name": team.name,
                "sport": team.sport,
                "country": team.country,
                "rating": team.rating
            },
            "statistics": {
                "matches_played": total_matches,
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "win_rate": wins / total_matches if total_matches > 0 else 0.0,
                "recent_form": form[:10]
            },
            "recent_matches": [
                {
                    "id": match.id,
                    "opponent": match.team2.name if match.team1_id == team_id else match.team1.name,
                    "result": 'W' if (
                        (match.team1_id == team_id and match.result == 'team1') or
                        (match.team2_id == team_id and match.result == 'team2')
                    ) else 'D' if match.result == 'draw' else 'L',
                    "score": match.score,
                    "date": match.date.isoformat() if match.date else None
                }
                for match in recent_matches[:5]
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/performance")
async def get_performance_metrics(
    days: int = Query(30, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get system performance metrics"""
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Signal performance
        signals = db.query(Signal).filter(
            Signal.created_at >= cutoff_date,
            Signal.result.isnot(None)
        ).all()
        
        if signals:
            wins = sum(1 for s in signals if s.result == 'win')
            total = len(signals)
            win_rate = wins / total
            avg_confidence = sum(s.confidence for s in signals) / total
            avg_value = sum(s.value_score or 0 for s in signals) / total
        else:
            win_rate = 0.0
            avg_confidence = 0.0
            avg_value = 0.0
            total = 0
        
        # Model metrics
        model_metrics = db.query(ModelMetrics).filter(
            ModelMetrics.last_updated >= cutoff_date
        ).all()
        
        models = {}
        for metric in model_metrics:
            if metric.sport not in models:
                models[metric.sport] = {}
            
            models[metric.sport][metric.model_name] = {
                "accuracy": metric.accuracy,
                "f1_score": metric.f1_score,
                "training_samples": metric.training_samples,
                "last_updated": metric.last_updated.isoformat()
            }
        
        return {
            "period_days": days,
            "signals": {
                "total": total,
                "win_rate": win_rate,
                "avg_confidence": avg_confidence,
                "avg_value_score": avg_value
            },
            "models": models,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/home")
async def get_home_statistics(db: Session = Depends(get_db)):
    """Get home page statistics"""
    try:
        # Quick stats for home page
        total_teams = db.query(Team).count()
        total_matches = db.query(Match).count()
        active_signals = db.query(Signal).filter(Signal.is_active == True).count()
        
        # Recent activity
        recent_signals = db.query(Signal).order_by(
            Signal.created_at.desc()
        ).limit(5).all()
        
        # Upcoming matches
        upcoming_matches = db.query(Match).filter(
            Match.is_upcoming == True
        ).order_by(Match.date).limit(5).all()
        
        return {
            "quick_stats": {
                "teams": total_teams,
                "matches": total_matches,
                "active_signals": active_signals
            },
            "recent_signals": [
                {
                    "id": signal.id,
                    "team1": signal.match.team1.name if signal.match and signal.match.team1 else "Unknown",
                    "team2": signal.match.team2.name if signal.match and signal.match.team2 else "Unknown",
                    "sport": signal.sport,
                    "confidence": signal.confidence,
                    "created_at": signal.created_at.isoformat()
                }
                for signal in recent_signals
            ],
            "upcoming_matches": [
                {
                    "id": match.id,
                    "team1": match.team1.name if match.team1 else "Unknown",
                    "team2": match.team2.name if match.team2 else "Unknown",
                    "sport": match.sport,
                    "date": match.date.isoformat() if match.date else None
                }
                for match in upcoming_matches
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
