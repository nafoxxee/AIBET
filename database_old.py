#!/usr/bin/env python3
"""
AIBET Analytics Platform - Database Manager
Автоматическая инициализация и управление SQLite базой данных
"""

import asyncio
import aiosqlite
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Match:
    id: Optional[int] = None
    sport: str = ""
    team1: str = ""
    team2: str = ""
    score: str = ""
    status: str = "upcoming"  # upcoming, live, finished
    start_time: Optional[datetime] = None
    features: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class Signal:
    id: Optional[int] = None
    match_id: Optional[int] = None
    sport: str = ""
    signal: str = ""
    confidence: float = 0.0
    published: bool = False
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class Statistics:
    id: Optional[int] = None
    sport: str = ""
    total: int = 0
    wins: int = 0
    losses: int = 0
    roi: float = 0.0
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    @property
    def winrate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.wins / self.total) * 100

@dataclass
class User:
    id: Optional[int] = None
    telegram_id: int = 0
    is_admin: bool = False
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class DatabaseManager:
    def __init__(self, db_path: str = "database.db"):
        self.db_path = db_path
        self._initialized = False
    
    async def initialize(self):
        """Инициализация базы данных и создание таблиц"""
        if self._initialized:
            return
            
        logger.info(f"🗄️ Initializing database: {self.db_path}")
        
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица матчей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sport TEXT NOT NULL,
                    team1 TEXT NOT NULL,
                    team2 TEXT NOT NULL,
                    score TEXT DEFAULT '',
                    status TEXT DEFAULT 'upcoming',
                    start_time DATETIME,
                    features TEXT DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица сигналов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER,
                    sport TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    published BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES matches (id)
                )
            """)
            
            # Таблица статистики
            await db.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sport TEXT NOT NULL UNIQUE,
                    total INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    roi REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Индексы для оптимизации
            await db.execute("CREATE INDEX IF NOT EXISTS idx_matches_sport ON matches(sport)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_signals_published ON signals(published)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_signals_sport ON signals(sport)")
            
            await db.commit()
        
        self._initialized = True
        logger.info("✅ Database initialized successfully")
    
    async def add_match(self, match: Match) -> int:
        """Добавить матч в базу"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO matches (sport, team1, team2, score, status, start_time, features)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                match.sport,
                match.team1,
                match.team2,
                match.score,
                match.status,
                match.start_time.isoformat() if match.start_time else None,
                json.dumps(match.features) if match.features else "{}"
            ))
            
            match_id = cursor.lastrowid
            await db.commit()
            return match_id
    
    async def get_matches(self, sport: str = None, status: str = None, limit: int = 50) -> List[Match]:
        """Получить матчи"""
        query = "SELECT * FROM matches"
        params = []
        
        conditions = []
        if sport:
            conditions.append("sport = ?")
            params.append(sport)
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            matches = []
            for row in rows:
                match = Match(
                    id=row['id'],
                    sport=row['sport'],
                    team1=row['team1'],
                    team2=row['team2'],
                    score=row['score'],
                    status=row['status'],
                    start_time=datetime.fromisoformat(row['start_time']) if row['start_time'] else None,
                    features=json.loads(row['features']) if row['features'] else {},
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                matches.append(match)
            
            return matches
    
    async def add_signal(self, signal: Signal) -> int:
        """Добавить сигнал"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO signals (match_id, sport, signal, confidence, published)
                VALUES (?, ?, ?, ?, ?)
            """, (
                signal.match_id,
                signal.sport,
                signal.signal,
                signal.confidence,
                signal.published
            ))
            
            signal_id = cursor.lastrowid
            await db.commit()
            return signal_id
    
    async def get_signals(self, sport: str = None, published: bool = None, limit: int = 50) -> List[Signal]:
        """Получить сигналы"""
        query = "SELECT * FROM signals"
        params = []
        
        conditions = []
        if sport:
            conditions.append("sport = ?")
            params.append(sport)
        if published is not None:
            conditions.append("published = ?")
            params.append(published)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            signals = []
            for row in rows:
                signal = Signal(
                    id=row['id'],
                    match_id=row['match_id'],
                    sport=row['sport'],
                    signal=row['signal'],
                    confidence=row['confidence'],
                    published=bool(row['published']),
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                signals.append(signal)
            
            return signals
    
    async def update_signal_published(self, signal_id: int, published: bool = True):
        """Обновить статус публикации сигнала"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE signals SET published = ? WHERE id = ?
            """, (published, signal_id))
            await db.commit()
    
    async def get_statistics(self, sport: str) -> Optional[Statistics]:
        """Получить статистику по виду спорта"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM statistics WHERE sport = ?
            """, (sport,))
            row = await cursor.fetchone()
            
            if row:
                return Statistics(
                    id=row['id'],
                    sport=row['sport'],
                    total=row['total'],
                    wins=row['wins'],
                    losses=row['losses'],
                    roi=row['roi'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
            return None
    
    async def update_statistics(self, sport: str, win: bool = None, roi_change: float = 0.0):
        """Обновить статистику"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем существование записи
            cursor = await db.execute("""
                SELECT id FROM statistics WHERE sport = ?
            """, (sport,))
            exists = await cursor.fetchone()
            
            if exists:
                if win is not None:
                    if win:
                        await db.execute("""
                            UPDATE statistics SET total = total + 1, wins = wins + 1, roi = roi + ?
                            WHERE sport = ?
                        """, (roi_change, sport))
                    else:
                        await db.execute("""
                            UPDATE statistics SET total = total + 1, losses = losses + 1, roi = roi + ?
                            WHERE sport = ?
                        """, (roi_change, sport))
                else:
                    await db.execute("""
                        UPDATE statistics SET roi = roi + ? WHERE sport = ?
                    """, (roi_change, sport))
            else:
                # Создаем новую запись
                total = 1 if win is not None else 0
                wins = 1 if win else 0
                losses = 0 if win else 1 if win is not None else 0
                
                await db.execute("""
                    INSERT INTO statistics (sport, total, wins, losses, roi)
                    VALUES (?, ?, ?, ?, ?)
                """, (sport, total, wins, losses, roi_change))
            
            await db.commit()
    
    async def add_user(self, user: User) -> int:
        """Добавить пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT OR REPLACE INTO users (telegram_id, is_admin)
                VALUES (?, ?)
            """, (user.telegram_id, user.is_admin))
            
            user_id = cursor.lastrowid
            await db.commit()
            return user_id
    
    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            row = await cursor.fetchone()
            
            if row:
                return User(
                    id=row['id'],
                    telegram_id=row['telegram_id'],
                    is_admin=bool(row['is_admin']),
                    created_at=datetime.fromisoformat(row['created_at'])
                )
            return None
    
    async def cleanup_old_data(self, days: int = 30):
        """Очистка старых данных"""
        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Удаляем старые матчи
            await db.execute("""
                DELETE FROM matches WHERE created_at < ? AND status = 'finished'
            """, (cutoff_date.isoformat(),))
            
            # Удаляем старые сигналы
            await db.execute("""
                DELETE FROM signals WHERE created_at < ?
            """, (cutoff_date.isoformat(),))
            
            await db.commit()
            logger.info(f"🧹 Cleaned up data older than {days} days")

# Глобальный экземпляр базы данных
db_manager = DatabaseManager()
    odds2: float
    odds_draw: Optional[float] = None
    status: str = 'upcoming'  # upcoming, live, finished
    score1: Optional[int] = None
    score2: Optional[int] = None
    live_data: Optional[Dict] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Signal:
    id: str
    match_id: str
    sport: str
    scenario: str
    confidence: str  # LOW, MEDIUM, HIGH
    probability: float
    explanation: str
    factors: List[str]
    odds_at_signal: float
    published_at: datetime
    result: Optional[str] = None  # win, lose, push
    prediction: Optional[str] = None  # team1, team2, draw
    expected_value: Optional[float] = None
    prediction_type: Optional[str] = None  # HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, etc.
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class MLModel:
    sport: str
    model_type: str
    model_data: bytes
    accuracy: float
    last_trained: datetime
    training_samples: int


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = None
    
    async def initialize(self):
        """Initialize database and create tables"""
        self._connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        logger.info(f"Database initialized: {self.db_path}")
    
    async def _create_tables(self):
        """Create all necessary tables"""
        
        # Matches table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                sport TEXT NOT NULL,
                team1 TEXT NOT NULL,
                team2 TEXT NOT NULL,
                tournament TEXT NOT NULL,
                match_time TIMESTAMP NOT NULL,
                odds1 REAL NOT NULL,
                odds2 REAL NOT NULL,
                odds_draw REAL,
                status TEXT DEFAULT 'upcoming',
                score1 INTEGER,
                score2 INTEGER,
                live_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Signals table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id TEXT PRIMARY KEY,
                match_id TEXT NOT NULL,
                sport TEXT NOT NULL,
                scenario TEXT NOT NULL,
                confidence TEXT NOT NULL,
                probability REAL NOT NULL,
                explanation TEXT NOT NULL,
                factors TEXT NOT NULL,
                odds_at_signal REAL NOT NULL,
                published_at TIMESTAMP NOT NULL,
                result TEXT,
                prediction TEXT,
                expected_value REAL,
                prediction_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches (id)
            )
        """)
        
        # ML models table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS ml_models (
                sport TEXT NOT NULL,
                model_type TEXT NOT NULL,
                model_data BLOB NOT NULL,
                accuracy REAL NOT NULL,
                last_trained TIMESTAMP NOT NULL,
                training_samples INTEGER NOT NULL,
                PRIMARY KEY (sport, model_type)
            )
        """)
        
        # Odds history table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS odds_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT NOT NULL,
                odds1 REAL NOT NULL,
                odds2 REAL NOT NULL,
                odds_draw REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches (id)
            )
        """)
        
        # Team statistics table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS team_stats (
                sport TEXT NOT NULL,
                team_name TEXT NOT NULL,
                matches_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                avg_odds REAL,
                form_trend TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (sport, team_name)
            )
        """)
        
        # Create indexes
        await self._connection.execute("CREATE INDEX IF NOT EXISTS idx_matches_sport_time ON matches(sport, match_time)")
        await self._connection.execute("CREATE INDEX IF NOT EXISTS idx_signals_sport ON signals(sport)")
        await self._connection.execute("CREATE INDEX IF NOT EXISTS idx_signals_published ON signals(published_at)")
        await self._connection.execute("CREATE INDEX IF NOT EXISTS idx_odds_history_match ON odds_history(match_id)")
        
        await self._connection.commit()
    
    async def save_match(self, match: Match) -> bool:
        """Save or update match"""
        try:
            await self._connection.execute("""
                INSERT OR REPLACE INTO matches 
                (id, sport, team1, team2, tournament, match_time, odds1, odds2, odds_draw, 
                 status, score1, score2, live_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match.id, match.sport, match.team1, match.team2, match.tournament,
                match.match_time, match.odds1, match.odds2, match.odds_draw,
                match.status, match.score1, match.score2,
                json.dumps(match.live_data) if match.live_data else None,
                match.created_at
            ))
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving match {match.id}: {e}")
            return False
    
    async def get_match(self, match_id: str) -> Optional[Match]:
        """Get match by ID"""
        try:
            cursor = await self._connection.execute(
                "SELECT * FROM matches WHERE id = ?", (match_id,)
            )
            row = await cursor.fetchone()
            if row:
                return self._row_to_match(row)
            return None
        except Exception as e:
            logger.error(f"Error getting match {match_id}: {e}")
            return None
    
    async def get_upcoming_matches(self, sport: str = None, hours: int = 24) -> List[Match]:
        """Get upcoming matches"""
        try:
            time_limit = datetime.now() + timedelta(hours=hours)
            query = """
                SELECT * FROM matches 
                WHERE status = 'upcoming' AND match_time <= ?
            """
            params = [time_limit]
            
            if sport:
                query += " AND sport = ?"
                params.append(sport)
            
            query += " ORDER BY match_time ASC"
            
            cursor = await self._connection.execute(query, params)
            rows = await cursor.fetchall()
            return [self._row_to_match(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting upcoming matches: {e}")
            return []
    
    async def get_live_matches(self, sport: str = None) -> List[Match]:
        """Get live matches"""
        try:
            query = "SELECT * FROM matches WHERE status = 'live'"
            params = []
            
            if sport:
                query += " AND sport = ?"
                params.append(sport)
            
            cursor = await self._connection.execute(query, params)
            rows = await cursor.fetchall()
            return [self._row_to_match(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting live matches: {e}")
            return []
    
    async def save_signal(self, signal: Signal) -> bool:
        """Save signal"""
        try:
            await self._connection.execute("""
                INSERT OR REPLACE INTO signals 
                (id, match_id, sport, scenario, confidence, probability, explanation, 
                 factors, odds_at_signal, published_at, result, prediction, expected_value, prediction_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal.id, signal.match_id, signal.sport, signal.scenario,
                signal.confidence, signal.probability, signal.explanation,
                json.dumps(signal.factors), signal.odds_at_signal,
                signal.published_at, signal.result, signal.prediction,
                signal.expected_value, signal.prediction_type, signal.created_at
            ))
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving signal {signal.id}: {e}")
            return False
    
    async def get_signals(self, sport: str = None, limit: int = 50) -> List[Signal]:
        """Get signals"""
        try:
            query = "SELECT * FROM signals"
            params = []
            
            if sport:
                query += " WHERE sport = ?"
                params.append(sport)
            
            query += " ORDER BY published_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = await self._connection.execute(query, params)
            rows = await cursor.fetchall()
            return [self._row_to_signal(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return []
    
    async def update_signal_result(self, signal_id: str, result: str) -> bool:
        """Update signal result"""
        try:
            await self._connection.execute(
                "UPDATE signals SET result = ? WHERE id = ?",
                (result, signal_id)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating signal result {signal_id}: {e}")
            return False
    
    async def save_odds_history(self, match_id: str, odds1: float, odds2: float, odds_draw: float = None):
        """Save odds history"""
        try:
            await self._connection.execute("""
                INSERT INTO odds_history (match_id, odds1, odds2, odds_draw)
                VALUES (?, ?, ?, ?)
            """, (match_id, odds1, odds2, odds_draw))
            await self._connection.commit()
        except Exception as e:
            logger.error(f"Error saving odds history for {match_id}: {e}")
    
    async def get_statistics(self, sport: str = None) -> Dict[str, Any]:
        """Get statistics"""
        try:
            query = "SELECT COUNT(*) as total, result FROM signals"
            params = []
            
            if sport:
                query += " WHERE sport = ?"
                params.append(sport)
            
            query += " GROUP BY result"
            
            cursor = await self._connection.execute(query, params)
            rows = await cursor.fetchall()
            
            stats = {'total': 0, 'wins': 0, 'losses': 0, 'pushes': 0}
            for row in rows:
                result = row[1]
                count = row[0]
                stats['total'] += count
                if result == 'win':
                    stats['wins'] = count
                elif result == 'lose':
                    stats['losses'] = count
                elif result == 'push':
                    stats['pushes'] = count
            
            # Calculate accuracy
            resolved_bets = stats['wins'] + stats['losses']
            stats['accuracy'] = (stats['wins'] / resolved_bets * 100) if resolved_bets > 0 else 0
            
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'total': 0, 'wins': 0, 'losses': 0, 'pushes': 0, 'accuracy': 0}
    
    async def save_ml_model(self, model: MLModel) -> bool:
        """Save ML model"""
        try:
            await self._connection.execute("""
                INSERT OR REPLACE INTO ml_models 
                (sport, model_type, model_data, accuracy, last_trained, training_samples)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                model.sport, model.model_type, model.model_data,
                model.accuracy, model.last_trained, model.training_samples
            ))
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving ML model: {e}")
            return False
    
    async def get_ml_model(self, sport: str, model_type: str) -> Optional[MLModel]:
        """Get ML model"""
        try:
            cursor = await self._connection.execute("""
                SELECT * FROM ml_models WHERE sport = ? AND model_type = ?
            """, (sport, model_type))
            row = await cursor.fetchone()
            if row:
                return MLModel(
                    sport=row[0],
                    model_type=row[1],
                    model_data=row[2],
                    accuracy=row[3],
                    last_trained=datetime.fromisoformat(row[4]),
                    training_samples=row[5]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting ML model: {e}")
            return None
    
    def _row_to_match(self, row) -> Match:
        """Convert database row to Match object"""
        return Match(
            id=row[0],
            sport=row[1],
            team1=row[2],
            team2=row[3],
            tournament=row[4],
            match_time=datetime.fromisoformat(row[5]),
            odds1=row[6],
            odds2=row[7],
            odds_draw=row[8],
            status=row[9],
            score1=row[10],
            score2=row[11],
            live_data=json.loads(row[12]) if row[12] else None,
            created_at=datetime.fromisoformat(row[13])
        )
    
    def _row_to_signal(self, row) -> Signal:
        """Convert database row to Signal object"""
        return Signal(
            id=row[0],
            match_id=row[1],
            sport=row[2],
            scenario=row[3],
            confidence=row[4],
            probability=row[5],
            explanation=row[6],
            factors=json.loads(row[7]),
            odds_at_signal=row[8],
            published_at=datetime.fromisoformat(row[9]),
            result=row[10],
            prediction=row[11] if len(row) > 11 else None,
            expected_value=row[12] if len(row) > 12 else None,
            prediction_type=row[13] if len(row) > 13 else None,
            created_at=datetime.fromisoformat(row[14]) if len(row) > 14 else datetime.now()
        )
    
    async def close(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            logger.info("Database connection closed")
