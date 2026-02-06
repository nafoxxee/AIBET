"""
AIBET Analytics Platform - Unified Schemas
"""

from datetime import datetime
from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field


class GlobalMatchID(BaseModel):
    """Global match ID generator"""
    
    @staticmethod
    def generate(league: str, team_a: str, team_b: str, start_time: datetime) -> str:
        """Generate deterministic global match ID"""
        import hashlib
        
        # Create deterministic hash
        data = f"{league}_{team_a}_{team_b}_{start_time.isoformat()}"
        hash_obj = hashlib.sha256(data.encode())
        return hash_obj.hexdigest()[:16]


class TeamScore(BaseModel):
    """Team score information"""
    team: str
    score: int


class MatchScore(BaseModel):
    """Match score information"""
    current: Optional[Dict[str, int]] = None
    periods: Optional[Dict[str, int]] = None
    final: Optional[Dict[str, int]] = None


class OddsInfo(BaseModel):
    """Odds information"""
    source: str
    odds: Dict[str, float]
    timestamp: datetime
    movement: Optional[List[float]] = None


class SourceConfidence(BaseModel):
    """Source confidence information"""
    source: str
    confidence: float
    last_updated: datetime


class LeagueMatch(BaseModel):
    """Unified league match schema"""
    global_match_id: str
    league: Literal["NHL", "KHL", "CS2"]
    teams: List[str] = Field(..., min_length=2, max_length=2)
    start_time: datetime
    status: Literal["scheduled", "upcoming", "live", "finished", "archived"]
    score: Optional[MatchScore] = None
    best_of: int = 1
    odds: Optional[List[OddsInfo]] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    value_score: float = Field(ge=0.0, le=1.0)
    lifecycle_state: Literal["UPCOMING", "LIVE", "FINISHED", "ARCHIVED"]
    source_confidence: List[SourceConfidence] = []
    data_quality: Literal["high", "medium", "low"]


class AIScore(BaseModel):
    """AI scoring information"""
    ai_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: Literal["low", "medium", "high"]


class AIExplanation(BaseModel):
    """AI explanation response"""
    not_a_prediction: bool = True
    educational_purpose: bool = True
    global_match_id: str
    summary: str
    positive_factors: List[str]
    negative_factors: List[str]
    verdict: str
    ai_score: AIScore
    explanation_timestamp: datetime


class AIContext(BaseModel):
    """AI context information"""
    global_match_id: str
    context_data: Dict[str, Any]
    analysis_timestamp: datetime


class ValueSignal(BaseModel):
    """Value betting signal"""
    global_match_id: str
    league: str
    teams: List[str]
    signal_type: Literal["value", "confidence", "momentum"]
    strength: float = Field(ge=0.0, le=1.0)
    reasoning: str
    odds_reference: Dict[str, float]
    signal_timestamp: datetime


class UnifiedResponse(BaseModel):
    """Unified API response"""
    success: bool
    data: Optional[Union[List[LeagueMatch], LeagueMatch, Dict[str, Any]]] = None
    error: Optional[str] = None
    timestamp: datetime
    cache_hit: bool = False


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, Any]


class MetricsResponse(BaseModel):
    """Metrics response"""
    uptime_seconds: int
    requests_total: int
    requests_by_endpoint: Dict[str, int]
    response_time_stats: Dict[str, float]
    cache_stats: Dict[str, Any]
    source_failures: Dict[str, int]
    errors: Dict[str, int]
    timestamp: datetime
