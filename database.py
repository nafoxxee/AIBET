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
