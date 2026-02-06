"""
AIBET Analytics Platform - Production Ready Backend
NHL + KHL + CS2 • AI Analytics • FastAPI • Python • Render Free
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.cache import cache_manager
from app.logging import setup_logging
from app.metrics import metrics
from app.api.v1 import nhl, khl, cs2, odds, unified, ai

# Setup logging
logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 AIBET Analytics Platform starting up...")
    await cache_manager.initialize()
    metrics.startup()
    logger.info("✅ Platform ready")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down AIBET Analytics Platform...")
    await cache_manager.cleanup()
    metrics.shutdown()
    logger.info("✅ Platform shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AIBET Analytics API",
    description="Production-ready analytics backend for NHL, KHL, CS2 matches and odds",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(nhl.router, prefix="/v1/nhl", tags=["NHL"])
app.include_router(khl.router, prefix="/v1/khl", tags=["KHL"])
app.include_router(cs2.router, prefix="/v1/cs2", tags=["CS2"])
app.include_router(odds.router, prefix="/v1/odds", tags=["Odds"])
app.include_router(unified.router, prefix="/v1/unified", tags=["Unified"])
app.include_router(ai.router, prefix="/v1/ai", tags=["AI Analytics"])

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "cache": await cache_manager.health_check(),
            "metrics": metrics.get_status()
        }
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AIBET Analytics Platform",
        "version": "1.0.0",
        "status": "running",
        "description": "Production-ready analytics backend for NHL, KHL, CS2",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "nhl": "/v1/nhl",
            "khl": "/v1/khl", 
            "cs2": "/v1/cs2",
            "odds": "/v1/odds",
            "ai": "/v1/ai",
            "metrics": "/metrics"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(settings.PORT),
        reload=settings.DEBUG,
        log_level="info"
    )
