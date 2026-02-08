"""
AIBET API - Timeweb Version
FastAPI backend for educational sports analytics
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from core.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print(f"🚀 AIBET API starting at {datetime.utcnow()}")
    yield
    print("🔄 AIBET API shutting down")


# Create FastAPI application
app = FastAPI(
    title="AIBET Analytics Platform",
    description="Educational sports analytics backend",
    version="1.0.0",
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AIBET Analytics Platform",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "api_prefix": "/v1",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "AIBET Analytics API"
    }


@app.get("/api/health")
async def api_health():
    """API health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/nhl/schedule")
async def get_nhl_schedule():
    """Get NHL schedule - educational version"""
    return {
        "success": True,
        "data": [],
        "message": "NHL schedule service - educational analytics only",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/khl/schedule")
async def get_khl_schedule():
    """Get KHL schedule - educational version"""
    return {
        "success": True,
        "data": [],
        "message": "KHL schedule service - educational analytics only",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/cs2/upcoming")
async def get_cs2_upcoming():
    """Get CS2 upcoming matches - educational version"""
    return {
        "success": True,
        "data": [],
        "message": "CS2 upcoming matches service - educational analytics only",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/ai/context/{match_id}")
async def get_ai_context(match_id: str):
    """Get AI context - educational version"""
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
    """Get AI score - educational version"""
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


if __name__ == "__main__":
    import uvicorn
    
    print(f"🚀 Starting AIBET API on port {config.API_PORT}")
    
    uvicorn.run(
        "api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG
    )
