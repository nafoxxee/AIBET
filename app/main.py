"""
AIBET Analytics Platform - Production Ready FastAPI Application
Simplified for Render Free deployment
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print(f"🚀 AIBET Analytics Platform starting at {datetime.utcnow()}")
    yield
    print("🔄 AIBET Analytics Platform shutting down")


# Create FastAPI application
app = FastAPI(
    title="AIBET Analytics Platform",
    description="Production-ready analytics backend for NHL, KHL, and CS2 matches",
    version="1.3.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.3.0",
        "service": "AIBET Analytics Platform"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AIBET Analytics Platform",
        "version": "1.3.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "api_prefix": "/v1",
        "endpoints": {
            "nhl": "/v1/nhl/schedule",
            "khl": "/v1/khl/schedule", 
            "cs2": "/v1/cs2/upcoming",
            "odds": "/v1/odds/nhl",
            "unified": "/v1/unified/matches",
            "ai": {
                "context": "/v1/ai/context/{match_id}",
                "score": "/v1/ai/score/{match_id}",
                "explain": "/v1/ai/explain/{match_id}",
                "value": "/v1/ai/value"
            }
        }
    }


# Basic API endpoints (simplified for stability)
@app.get("/v1/nhl/schedule")
async def get_nhl_schedule():
    """Get NHL schedule - simplified version"""
    return {
        "success": True,
        "data": [],
        "message": "NHL schedule service - coming soon",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/khl/schedule")
async def get_khl_schedule():
    """Get KHL schedule - simplified version"""
    return {
        "success": True,
        "data": [],
        "message": "KHL schedule service - coming soon",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/cs2/upcoming")
async def get_cs2_upcoming():
    """Get CS2 upcoming matches - simplified version"""
    return {
        "success": True,
        "data": [],
        "message": "CS2 upcoming matches service - coming soon",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/odds/nhl")
async def get_nhl_odds():
    """Get NHL odds - simplified version"""
    return {
        "success": True,
        "data": [],
        "message": "NHL odds service - coming soon",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/unified/matches")
async def get_unified_matches():
    """Get unified matches - simplified version"""
    return {
        "success": True,
        "data": [],
        "message": "Unified matches service - coming soon",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/ai/context/{match_id}")
async def get_ai_context(match_id: str):
    """Get AI context - simplified educational version"""
    return {
        "success": True,
        "data": {
            "match_id": match_id,
            "context": "Educational analysis only",
            "not_a_prediction": True,
            "educational_purpose": True,
            "message": "AI context service - educational analysis only"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/ai/score/{match_id}")
async def get_ai_score(match_id: str):
    """Get AI score - simplified educational version"""
    return {
        "success": True,
        "data": {
            "match_id": match_id,
            "ai_score": 0.5,
            "confidence": 0.5,
            "risk_level": "medium",
            "not_a_prediction": True,
            "educational_purpose": True,
            "message": "AI scoring service - educational analysis only"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/ai/explain/{match_id}")
async def get_ai_explanation(match_id: str):
    """Get AI explanation - simplified educational version"""
    return {
        "success": True,
        "data": {
            "match_id": match_id,
            "explanation": "Educational analysis only - not a prediction",
            "not_a_prediction": True,
            "educational_purpose": True,
            "message": "AI explanation service - educational analysis only"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/ai/value")
async def get_ai_value():
    """Get AI value signals - simplified educational version"""
    return {
        "success": True,
        "data": [],
        "message": "AI value signals service - educational analysis only",
        "not_a_prediction": True,
        "educational_purpose": True,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting AIBET Analytics Platform on port {port}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
