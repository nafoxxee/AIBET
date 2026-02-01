"""
AIBET MVP API Dependencies
Common dependencies for API endpoints
"""

from functools import lru_cache
from sqlalchemy.orm import Session
from ml.predictor import Predictor

@lru_cache()
def get_predictor() -> Predictor:
    """Get predictor instance (cached)"""
    from database.connection import get_db_context
    
    with get_db_context() as db:
        return Predictor(db)
