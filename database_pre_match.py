#!/usr/bin/env python3
"""
AIBET Analytics Platform - Pre-Match Database
База данных для pre-match режима с историческими матчами
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
class PreMatchMatch:
    id: Optional[int] = None
    sport: str = ""
    team1: str = ""
    team2: str = ""
    tournament: str = ""
    date: str = ""
    status: str = "upcoming"
    format: Optional[str] = None
    source: str = ""
    match_type: str = "pre_match"
    features: Optional[Dict[str, Any]] = None
    result: Optional[str] = None  # team1, team2, draw
    final_score: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class PreMatchSignal:
    id: Optional[int] = None
    match_id: Optional[int] = None
    sport: str = ""
    team1: str = ""
    team2: str = ""
    tournament: str = ""
    date: str = ""
    prediction: str = ""
    probability: float = 0.0
    confidence: str = ""
    facts: Optional[str] = None
    recommendation: Optional[str] = None
    published: bool = False
    created_at: Optional[datetime] = None

class PreMatchDatabase:
    def __init__(self, db_path: str = "aibet_pre_match.db"):
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
                    format TEXT,
                    source TEXT,
                    match_type TEXT DEFAULT 'pre_match',
                    features TEXT,
                    result TEXT,
                    final_score TEXT,
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
                    confidence TEXT,
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
                    goals_for INTEGER DEFAULT 0,
                    goals_against INTEGER DEFAULT 0,
                    recent_form TEXT,
                    win_rate REAL DEFAULT 0.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(team_name, sport)
                )
            ''')
            
            # Таблица исторических матчей для ML
            await db.execute('''
                CREATE TABLE IF NOT EXISTS historical_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sport TEXT NOT NULL,
                    team1 TEXT NOT NULL,
                    team2 TEXT NOT NULL,
                    tournament TEXT,
                    date TEXT,
                    result TEXT NOT NULL,
                    final_score TEXT,
                    features TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Индексы
            await db.execute('CREATE INDEX IF NOT EXISTS idx_matches_sport ON matches(sport)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_signals_sport ON signals(sport)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_team_stats_team ON team_stats(team_name, sport)')
            
            await db.commit()
        
        self._initialized = True
        logger.info("✅ Pre-Match Database initialized")
    
    async def add_match(self, match_data: Dict) -> int:
        """Добавить матч"""
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
            
            cursor = await db.execute('''
                INSERT INTO matches (sport, team1, team2, tournament, date, status, format, source, match_type, features)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_data['sport'],
                match_data['team1'],
                match_data['team2'],
                match_data.get('tournament', ''),
                match_data.get('date', ''),
                match_data.get('status', 'upcoming'),
                match_data.get('format'),
                match_data.get('source', ''),
                match_data.get('match_type', 'pre_match'),
                json.dumps(match_data.get('features', {}))
            ))
            
            match_id = cursor.lastrowid
            await db.commit()
            
            logger.info(f"✅ Added pre-match: {match_data['team1']} vs {match_data['team2']} (ID: {match_id})")
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
        return await self.get_matches(sport=sport, status='upcoming', limit=30)
    
    async def get_finished_matches(self, sport: Optional[str] = None) -> List[Dict]:
        """Получить завершенные матчи"""
        return await self.get_matches(sport=sport, status='finished', limit=100)
    
    async def get_historical_matches(self, sport: Optional[str] = None, limit: int = 200) -> List[Dict]:
        """Получить исторические матчи для ML"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            query = "SELECT * FROM historical_matches WHERE 1=1"
            params = []
            
            if sport:
                query += " AND sport = ?"
                params.append(sport)
            
            query += " ORDER BY date DESC LIMIT ?"
            params.append(limit)
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            matches = []
            
            for row in rows:
                match_dict = dict(zip(columns, row))
                if match_dict['features']:
                    match_dict['features'] = json.loads(match_dict['features'])
                matches.append(match_dict)
            
            return matches
    
    async def add_historical_match(self, match_data: Dict) -> int:
        """Добавить исторический матч"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO historical_matches (sport, team1, team2, tournament, date, result, final_score, features)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_data['sport'],
                match_data['team1'],
                match_data['team2'],
                match_data.get('tournament', ''),
                match_data.get('date', ''),
                match_data['result'],
                match_data.get('final_score', ''),
                json.dumps(match_data.get('features', {}))
            ))
            
            match_id = cursor.lastrowid
            await db.commit()
            
            return match_id
    
    async def add_signal(self, signal_data: Dict) -> int:
        """Добавить сигнал"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO signals (match_id, sport, team1, team2, tournament, date, prediction, probability, confidence, facts, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_data.get('match_id'),
                signal_data['sport'],
                signal_data['team1'],
                signal_data['team2'],
                signal_data.get('tournament', ''),
                signal_data.get('date', ''),
                signal_data['prediction'],
                signal_data['probability'],
                signal_data.get('confidence', ''),
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
                (team_name, sport, matches_played, wins, losses, draws, goals_for, goals_against, recent_form, win_rate, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                team_name,
                sport,
                stats.get('matches_played', 0),
                stats.get('wins', 0),
                stats.get('losses', 0),
                stats.get('draws', 0),
                stats.get('goals_for', 0),
                stats.get('goals_against', 0),
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
    
    async def get_match_count(self) -> int:
        """Получить общее количество матчей"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM matches")
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def get_historical_match_count(self) -> int:
        """Получить количество исторических матчей"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM historical_matches")
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def initialize_test_data(self):
        """Инициализация тестовыми историческими данными"""
        await self.initialize()
        
        # Проверяем, есть ли уже данные
        historical_count = await self.get_historical_match_count()
        if historical_count > 0:
            logger.info(f"📊 Historical data already exists: {historical_count} matches")
            return
        
        logger.info("🔄 Initializing test historical data...")
        
        # CS2 тестовые матчи
        cs2_matches = [
            {
                'sport': 'cs2',
                'team1': 'NaVi',
                'team2': 'FaZe',
                'tournament': 'BLAST Premier',
                'date': '2024-01-15',
                'result': 'team1',
                'final_score': '2-1',
                'features': {
                    'team1_rank': 1,
                    'team2_rank': 2,
                    'map1_score': '16-14',
                    'map2_score': '13-16',
                    'map3_score': '16-12'
                }
            },
            {
                'sport': 'cs2',
                'team1': 'G2',
                'team2': 'Vitality',
                'tournament': 'IEM Katowice',
                'date': '2024-01-20',
                'result': 'team2',
                'final_score': '2-0',
                'features': {
                    'team1_rank': 3,
                    'team2_rank': 4,
                    'map1_score': '14-16',
                    'map2_score': '12-16'
                }
            },
            # Добавляем еще матчей для обучения
            {
                'sport': 'cs2',
                'team1': 'Astralis',
                'team2': 'Heroic',
                'tournament': 'ESL Pro League',
                'date': '2024-01-25',
                'result': 'team1',
                'final_score': '2-1',
                'features': {
                    'team1_rank': 5,
                    'team2_rank': 6,
                    'map1_score': '16-13',
                    'map2_score': '14-16',
                    'map3_score': '16-11'
                }
            }
        ]
        
        # КХЛ тестовые матчи
        khl_matches = [
            {
                'sport': 'khl',
                'team1': 'CSKA Moscow',
                'team2': 'SKA Saint Petersburg',
                'tournament': 'KHL',
                'date': '2024-01-15',
                'result': 'team1',
                'final_score': '4-2',
                'features': {
                    'team1_position': 1,
                    'team2_position': 2,
                    'period1_score': '1-0',
                    'period2_score': '2-1',
                    'period3_score': '1-1'
                }
            },
            {
                'sport': 'khl',
                'team1': 'Ak Bars Kazan',
                'team2': 'Metallurg Magnitogorsk',
                'tournament': 'KHL',
                'date': '2024-01-20',
                'result': 'draw',
                'final_score': '3-3',
                'features': {
                    'team1_position': 3,
                    'team2_position': 4,
                    'period1_score': '1-1',
                    'period2_score': '1-1',
                    'period3_score': '1-1',
                    'ot_score': '0-0',
                    'shootout_score': '1-1'
                }
            }
        ]
        
        # Добавляем матчи
        all_matches = cs2_matches + khl_matches
        
        for match_data in all_matches:
            await self.add_historical_match(match_data)
        
        # Инициализируем базовую статистику команд
        await self._initialize_team_stats()
        
        logger.info(f"✅ Initialized {len(all_matches)} historical matches")
    
    async def _initialize_team_stats(self):
        """Инициализация базовой статистики команд"""
        # CS2 команды
        cs2_teams = ['NaVi', 'FaZe', 'G2', 'Vitality', 'Astralis', 'Heroic']
        
        for team in cs2_teams:
            stats = {
                'matches_played': 50,
                'wins': random.randint(25, 35),
                'losses': 0,
                'draws': 0,
                'goals_for': random.randint(800, 1200),
                'goals_against': random.randint(700, 1100),
                'recent_form': ['W', 'L', 'W', 'W', 'L'],
                'win_rate': 0.6
            }
            stats['losses'] = stats['matches_played'] - stats['wins']
            stats['win_rate'] = stats['wins'] / stats['matches_played']
            
            await self.update_team_stats(team, 'cs2', stats)
        
        # КХЛ команды
        khl_teams = ['CSKA Moscow', 'SKA Saint Petersburg', 'Ak Bars Kazan', 'Metallurg Magnitogorsk']
        
        for team in khl_teams:
            stats = {
                'matches_played': 40,
                'wins': random.randint(20, 28),
                'losses': 0,
                'draws': 0,
                'goals_for': random.randint(120, 180),
                'goals_against': random.randint(100, 160),
                'recent_form': ['W', 'D', 'W', 'L', 'W'],
                'win_rate': 0.6
            }
            stats['losses'] = stats['matches_played'] - stats['wins'] - stats['draws']
            stats['win_rate'] = stats['wins'] / stats['matches_played']
            
            await self.update_team_stats(team, 'khl', stats)

# Глобальный экземпляр
pre_match_db = PreMatchDatabase()

# Добавляем импорт random
import random
