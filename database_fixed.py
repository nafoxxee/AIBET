#!/usr/bin/env python3
"""
AIBET Analytics Platform - Fixed Database Manager
Единый источник правды с SQLite
"""

import asyncio
import aiosqlite
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class Match:
    id: Optional[int] = None
    sport: str = ""
    team1: str = ""
    team2: str = ""
    tournament: str = ""
    date: str = ""
    status: str = "upcoming"  # upcoming, live, finished
    score: Optional[str] = None
    format: Optional[str] = None
    link: Optional[str] = None
    source: str = ""
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
    team1: str = ""
    team2: str = ""
    tournament: str = ""
    date: str = ""
    prediction: str = ""  # team1, team2, draw
    probability: float = 0.0
    facts: Optional[str] = None
    recommendation: Optional[str] = None
    published: bool = False
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class TeamStats:
    id: Optional[int] = None
    team_name: str = ""
    sport: str = ""
    matches_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    score_for: int = 0
    score_against: int = 0
    recent_form: List[str] = None
    win_rate: float = 0.0
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.recent_form is None:
            self.recent_form = []
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()

class DatabaseManager:
    def __init__(self, db_path: str = "aibet.db"):
        self.db_path = db_path
        self._initialized = False
    
    async def initialize(self):
        """Инициализация базы данных"""
        if self._initialized:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица матчей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sport TEXT NOT NULL,
                    team1 TEXT NOT NULL,
                    team2 TEXT NOT NULL,
                    tournament TEXT,
                    date TEXT,
                    status TEXT DEFAULT 'upcoming',
                    score TEXT,
                    format TEXT,
                    link TEXT,
                    source TEXT,
                    features TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица сигналов
            await db.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER,
                    sport TEXT NOT NULL,
                    team1 TEXT NOT NULL,
                    team2 TEXT NOT NULL,
                    tournament TEXT,
                    date TEXT,
                    prediction TEXT NOT NULL,
                    probability REAL NOT NULL,
                    facts TEXT,
                    recommendation TEXT,
                    published BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES matches (id)
                )
            ''')
            
            # Таблица статистики команд
            await db.execute('''
                CREATE TABLE IF NOT EXISTS team_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_name TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    matches_played INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    draws INTEGER DEFAULT 0,
                    score_for INTEGER DEFAULT 0,
                    score_against INTEGER DEFAULT 0,
                    recent_form TEXT,
                    win_rate REAL DEFAULT 0.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(team_name, sport)
                )
            ''')
            
            # Таблица результатов матчей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS match_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER,
                    winner TEXT,
                    final_score TEXT,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES matches (id)
                )
            ''')
            
            # Индексы для оптимизации
            await db.execute('CREATE INDEX IF NOT EXISTS idx_matches_sport ON matches(sport)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_signals_sport ON signals(sport)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_signals_published ON signals(published)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_team_stats_team ON team_stats(team_name, sport)')
            
            await db.commit()
        
        self._initialized = True
        logger.info("✅ Database initialized successfully")
    
    async def add_match(self, match_data: Dict) -> int:
        """Добавить матч в базу"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Проверка на дубликаты
            cursor = await db.execute('''
                SELECT id FROM matches 
                WHERE team1 = ? AND team2 = ? AND date = ? AND sport = ?
            ''', (match_data['team1'], match_data['team2'], match_data['date'], match_data['sport']))
            
            if await cursor.fetchone():
                logger.debug(f"Match already exists: {match_data['team1']} vs {match_data['team2']}")
                return -1
            
            # Вставка нового матча
            cursor = await db.execute('''
                INSERT INTO matches (sport, team1, team2, tournament, date, status, score, format, link, source, features)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_data['sport'],
                match_data['team1'],
                match_data['team2'],
                match_data.get('tournament', ''),
                match_data.get('date', ''),
                match_data.get('status', 'upcoming'),
                match_data.get('score'),
                match_data.get('format'),
                match_data.get('link'),
                match_data.get('source', ''),
                json.dumps(match_data.get('features', {}))
            ))
            
            match_id = cursor.lastrowid
            await db.commit()
            
            logger.info(f"✅ Added match: {match_data['team1']} vs {match_data['team2']} (ID: {match_id})")
            return match_id
    
    async def get_matches(self, sport: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Получить матчи"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            query = "SELECT * FROM matches WHERE 1=1"
            params = []
            
            if sport:
                query += " AND sport = ?"
                params.append(sport)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY date ASC LIMIT ?"
            params.append(limit)
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            # Конвертация в список словарей
            columns = [desc[0] for desc in cursor.description]
            matches = []
            
            for row in rows:
                match_dict = dict(zip(columns, row))
                if match_dict['features']:
                    match_dict['features'] = json.loads(match_dict['features'])
                matches.append(match_dict)
            
            return matches
    
    async def get_upcoming_matches(self, sport: Optional[str] = None) -> List[Dict]:
        """Получить предстоящие матчи"""
        return await self.get_matches(sport=sport, status='upcoming', limit=20)
    
    async def get_match_count(self) -> int:
        """Получить общее количество матчей"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM matches")
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def add_signal(self, signal_data: Dict) -> int:
        """Добавить сигнал"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO signals (match_id, sport, team1, team2, tournament, date, prediction, probability, facts, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_data.get('match_id'),
                signal_data['sport'],
                signal_data['team1'],
                signal_data['team2'],
                signal_data.get('tournament', ''),
                signal_data.get('date', ''),
                signal_data['prediction'],
                signal_data['probability'],
                signal_data.get('facts'),
                signal_data.get('recommendation')
            ))
            
            signal_id = cursor.lastrowid
            await db.commit()
            
            logger.info(f"✅ Added signal: {signal_data['team1']} vs {signal_data['team2']} (ID: {signal_id})")
            return signal_id
    
    async def get_signals(self, sport: Optional[str] = None, published: Optional[bool] = None) -> List[Dict]:
        """Получить сигналы"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            query = "SELECT * FROM signals WHERE 1=1"
            params = []
            
            if sport:
                query += " AND sport = ?"
                params.append(sport)
            
            if published is not None:
                query += " AND published = ?"
                params.append(published)
            
            query += " ORDER BY created_at DESC"
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            signals = [dict(zip(columns, row)) for row in rows]
            
            return signals
    
    async def update_team_stats(self, team_name: str, sport: str, stats: Dict) -> bool:
        """Обновить статистику команды"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO team_stats 
                (team_name, sport, matches_played, wins, losses, draws, score_for, score_against, recent_form, win_rate, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                team_name,
                sport,
                stats.get('matches_played', 0),
                stats.get('wins', 0),
                stats.get('losses', 0),
                stats.get('draws', 0),
                stats.get('score_for', 0),
                stats.get('score_against', 0),
                json.dumps(stats.get('recent_form', [])),
                stats.get('win_rate', 0.0),
                datetime.utcnow()
            ))
            
            await db.commit()
            return True
    
    async def get_team_stats(self, team_name: str, sport: str) -> Optional[Dict]:
        """Получить статистику команды"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT * FROM team_stats WHERE team_name = ? AND sport = ?
            ''', (team_name, sport))
            
            row = await cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                stats_dict = dict(zip(columns, row))
                if stats_dict['recent_form']:
                    stats_dict['recent_form'] = json.loads(stats_dict['recent_form'])
                return stats_dict
            
            return None
    
    async def mark_signal_published(self, signal_id: int) -> bool:
        """Отметить сигнал как опубликованный"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE signals SET published = TRUE WHERE id = ?", (signal_id,))
            await db.commit()
            return True
    
    async def cleanup_old_data(self, days: int = 7):
        """Очистка старых данных"""
        await self.initialize()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Удаление старых матчей
            cursor = await db.execute('''
                DELETE FROM matches WHERE created_at < ? AND status = 'finished'
            ''', (cutoff_date,))
            
            deleted_matches = cursor.rowcount
            
            # Удаление старых сигналов
            cursor = await db.execute('''
                DELETE FROM signals WHERE created_at < ?
            ''', (cutoff_date,))
            
            deleted_signals = cursor.rowcount
            
            await db.commit()
            
            logger.info(f"🧹 Cleaned up {deleted_matches} old matches and {deleted_signals} old signals")

# Глобальный экземпляр
db_manager = DatabaseManager()
