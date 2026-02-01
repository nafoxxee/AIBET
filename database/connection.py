"""
AIBET MVP Database Connection
SQLite connection and initialization
"""

import os
import sqlite3
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aibet_mvp.db")

# SQLAlchemy 2.0+ compatible Base
class Base(DeclarativeBase):
    pass

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    echo=False  # Set to True for SQL logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

async def init_database():
    """Initialize database with tables and sample data"""
    try:
        logger.info("🔄 Initializing AIBET MVP database...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Check if we need to populate with initial data
        with get_db_context() as db:
            # Check if teams exist
            team_count = db.query(Team).count()
            if team_count == 0:
                logger.info("📊 Populating database with initial data...")
                await populate_initial_data(db)
            
            # Check if historical matches exist
            match_count = db.query(Match).count()
            if match_count == 0:
                logger.info("📈 Loading historical match data...")
                await load_historical_data(db)
        
        logger.info("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

async def populate_initial_data(db: Session):
    """Populate database with initial team data"""
    try:
        # CS2 Teams
        cs2_teams = [
            {"name": "NaVi", "sport": "cs2", "country": "Ukraine", "rating": 1850},
            {"name": "FaZe", "sport": "cs2", "country": "International", "rating": 1820},
            {"name": "G2", "sport": "cs2", "country": "International", "rating": 1800},
            {"name": "Vitality", "sport": "cs2", "country": "France", "rating": 1780},
            {"name": "Astralis", "sport": "cs2", "country": "Denmark", "rating": 1750},
            {"name": "Heroic", "sport": "cs2", "country": "Denmark", "rating": 1720},
            {"name": "Cloud9", "sport": "cs2", "country": "USA", "rating": 1700},
            {"name": "Fnatic", "sport": "cs2", "country": "Sweden", "rating": 1680},
            {"name": "Team Liquid", "sport": "cs2", "country": "USA", "rating": 1650},
            {"name": "Complexity", "sport": "cs2", "country": "USA", "rating": 1620},
        ]
        
        # KHL Teams
        khl_teams = [
            {"name": "CSKA Moscow", "sport": "khl", "country": "Russia", "rating": 1850},
            {"name": "SKA Saint Petersburg", "sport": "khl", "country": "Russia", "rating": 1820},
            {"name": "Ak Bars Kazan", "sport": "khl", "country": "Russia", "rating": 1800},
            {"name": "Metallurg Magnitogorsk", "sport": "khl", "country": "Russia", "rating": 1780},
            {"name": "Salavat Yulaev Ufa", "sport": "khl", "country": "Russia", "rating": 1750},
            {"name": "Lokomotiv Yaroslavl", "sport": "khl", "country": "Russia", "rating": 1720},
            {"name": "Barys Nur-Sultan", "sport": "khl", "country": "Kazakhstan", "rating": 1700},
            {"name": "Traktor Chelyabinsk", "sport": "khl", "country": "Russia", "rating": 1680},
            {"name": "Avangard Omsk", "sport": "khl", "country": "Russia", "rating": 1650},
            {"name": "Dinamo Moscow", "sport": "khl", "country": "Russia", "rating": 1620},
        ]
        
        # Insert teams
        for team_data in cs2_teams + khl_teams:
            team = Team(**team_data)
            db.add(team)
        
        logger.info(f"✅ Added {len(cs2_teams)} CS2 teams and {len(khl_teams)} KHL teams")
        
    except Exception as e:
        logger.error(f"❌ Error populating initial data: {e}")
        raise

async def load_historical_data(db: Session):
    """Load historical match data from CSV files"""
    try:
        import pandas as pd
        from datetime import datetime, timedelta
        import random
        
        # Generate sample historical matches if CSV doesn't exist
        logger.info("📊 Generating sample historical matches...")
        
        # Get teams
        cs2_teams = db.query(Team).filter(Team.sport == "cs2").all()
        khl_teams = db.query(Team).filter(Team.sport == "khl").all()
        
        # Generate CS2 historical matches
        for i in range(100):  # 100 historical CS2 matches
            team1, team2 = random.sample(cs2_teams, 2)
            
            # Simulate match result based on ratings
            rating_diff = team1.rating - team2.rating
            prob1 = 1 / (1 + 10 ** (-rating_diff / 400))
            
            result = "team1" if random.random() < prob1 else "team2"
            
            match = Match(
                team1_id=team1.id,
                team2_id=team2.id,
                sport="cs2",
                date=datetime.now() - timedelta(days=random.randint(1, 365)),
                tournament=f"CS2 Tournament {random.randint(1, 10)}",
                result=result,
                score=f"{random.randint(16, 25)}-{random.randint(8, 15)}" if result == "team1" else f"{random.randint(8, 15)}-{random.randint(16, 25)}",
                best_of=random.choice([1, 3, 5]),
                map_name=random.choice(["Mirage", "Dust2", "Inferno", "Cache", "Overpass"])
            )
            db.add(match)
        
        # Generate KHL historical matches
        for i in range(80):  # 80 historical KHL matches
            team1, team2 = random.sample(khl_teams, 2)
            
            # Simulate match result
            rating_diff = team1.rating - team2.rating
            prob1 = 1 / (1 + 10 ** (-rating_diff / 400))
            
            rand = random.random()
            if rand < prob1 * 0.8:  # 20% chance of draw in hockey
                result = "team1"
            elif rand < prob1 * 0.8 + 0.2:
                result = "draw"
            else:
                result = "team2"
            
            # Generate score based on result
            if result == "team1":
                score = f"{random.randint(3, 6)}-{random.randint(0, 2)}"
            elif result == "team2":
                score = f"{random.randint(0, 2)}-{random.randint(3, 6)}"
            else:  # draw
                score = f"{random.randint(2, 4)}-{random.randint(2, 4)}"
            
            match = Match(
                team1_id=team1.id,
                team2_id=team2.id,
                sport="khl",
                date=datetime.now() - timedelta(days=random.randint(1, 365)),
                tournament=f"KHL Regular Season {random.randint(2021, 2024)}",
                result=result,
                score=score,
                best_of=1,
                arena=f"Arena {random.randint(1, 20)}"
            )
            db.add(match)
        
        logger.info(f"✅ Generated 100 CS2 and 80 KHL historical matches")
        
    except Exception as e:
        logger.error(f"❌ Error loading historical data: {e}")
        raise

# Import models will be done in __init__.py to avoid circular imports
