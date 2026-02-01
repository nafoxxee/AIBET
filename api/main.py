"""
AIBET MVP FastAPI Application
Main API server for predictions and signals
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    # Startup
    logger.info("🚀 Starting AIBET MVP API...")
    
    # Initialize database
    from database.connection import init_database
    await init_database()
    
    # Initialize ML models
    from ml.predictor import Predictor
    from database.connection import get_db_context
    
    with get_db_context() as db:
        predictor = Predictor(db)
        predictor.initialize_models('cs2')
        predictor.initialize_models('khl')
    
    logger.info("✅ AIBET MVP API ready!")
    
    yield
    
    # Shutdown
    logger.info("🏁 AIBET MVP API stopped")

# Create FastAPI app
app = FastAPI(
    title="AIBET MVP API",
    description="Analytical Betting Platform API",
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

# Dependencies
from database.connection import get_db
from .dependencies import get_predictor

# Import routes
from .routes import matches, signals, statistics

# Include routers
app.include_router(matches.router, prefix="/api", tags=["matches"])
app.include_router(signals.router, prefix="/api", tags=["signals"])
app.include_router(statistics.router, prefix="/api", tags=["statistics"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AIBET MVP API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        from database.connection import get_db_context
        
        with get_db_context() as db:
            # Check database connection
            from database.models import Match, Team
            
            team_count = db.query(Team).count()
            match_count = db.query(Match).count()
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "connected",
                "teams": team_count,
                "matches": match_count,
                "api": "running"
            }
            
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Model status
@app.get("/api/model-status")
async def model_status():
    """Get ML model status"""
    try:
        from database.connection import get_db_context
        from ml.predictor import Predictor
        
        with get_db_context() as db:
            predictor = Predictor(db)
            
            status = {}
            for sport in ['cs2', 'khl']:
                try:
                    model = predictor.model_manager.get_model(sport, 'logistic_regression')
                    rf_model = predictor.model_manager.get_model(sport, 'random_forest')
                    
                    status[sport] = {
                        "logistic_regression": {
                            "trained": model.is_trained,
                            "features": len(model.feature_columns)
                        },
                        "random_forest": {
                            "trained": rf_model.is_trained,
                            "features": len(rf_model.feature_columns)
                        }
                    }
                except Exception as e:
                    status[sport] = {"error": str(e)}
            
            return {
                "status": "success",
                "models": status,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Model status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Generate signals endpoint
@app.post("/api/generate-signals")
async def generate_signals(
    background_tasks: BackgroundTasks,
    sport: Optional[str] = None,
    limit: int = 10
):
    """Generate betting signals"""
    try:
        from database.connection import get_db_context
        from ml.predictor import Predictor
        
        with get_db_context() as db:
            predictor = Predictor(db)
            
            sports = [sport] if sport else ['cs2', 'khl']
            all_signals = []
            
            for s in sports:
                signals = predictor.generate_signals(s, limit)
                all_signals.extend(signals)
            
            return {
                "status": "success",
                "signals_generated": len(all_signals),
                "sports": sports,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Signal generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"❌ Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=1000,
        reload=True,
        log_level="info"
    )
