from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "aibet-analytics"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI BET Analytics Platform",
        "status": "running",
        "health": "/health"
    }
