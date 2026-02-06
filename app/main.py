"""
AIBET Analytics Platform v1.3 FULL - Production Ready
Unified entry point for all services
"""

import os
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, Any

# Import application components
from app.config import settings
from app.cache import cache_manager
from app.logging import setup_logging
from app.metrics import metrics
from app.api.v1 import nhl, khl, cs2, odds, unified, ai

# Setup logging
logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    logger.info("🚀 AIBET Analytics Platform v1.3 starting up...")
    
    # Initialize cache
    await cache_manager.initialize()
    logger.info("✅ Cache initialized")
    
    # Initialize metrics
    metrics.startup()
    logger.info("✅ Metrics initialized")
    
    logger.info("✅ Platform ready")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down AIBET Analytics Platform...")
    await cache_manager.cleanup()
    metrics.shutdown()
    logger.info("✅ Platform shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="AIBET Analytics Platform",
    description="Production-ready analytics backend for NHL, KHL, and CS2 matches and odds",
    version="1.3.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header and metrics"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        # Record metrics
        await metrics.record_request_time(process_time)
        await metrics.increment_requests("total")
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        await metrics.record_error("request_error")
        logger.error(f"Request error: {e}")
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    await metrics.record_error("global_exception")
    logger.error(f"Global exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check cache health
        cache_health = await cache_manager.health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.3.0",
            "cache": cache_health,
            "metrics": metrics.get_stats()
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Metrics endpoint
@app.get("/metrics")
async def metrics_endpoint():
    """Metrics endpoint"""
    try:
        return {
            "success": True,
            "data": metrics.get_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Include API routers
app.include_router(
    nhl.router,
    prefix="/v1/nhl",
    tags=["NHL"]
)

app.include_router(
    khl.router,
    prefix="/v1/khl",
    tags=["KHL"]
)

app.include_router(
    cs2.router,
    prefix="/v1/cs2",
    tags=["CS2"]
)

app.include_router(
    odds.router,
    prefix="/v1/odds",
    tags=["Odds"]
)

app.include_router(
    unified.router,
    prefix="/v1/unified",
    tags=["Unified"]
)

app.include_router(
    ai.router,
    prefix="/v1/ai",
    tags=["AI Analytics"]
)


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
        "metrics": "/metrics",
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


if __name__ == "__main__":
    import uvicorn
    
    # Development server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
