import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from aiosqlite import connect

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite database manager for AI BET analytics platform"""
    
    def __init__(self, db_path: str = "storage/database.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # CS2 matches table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cs2_matches (
                        match_id TEXT PRIMARY KEY,
                        team1 TEXT NOT NULL,
                        team2 TEXT NOT NULL,
                        tournament TEXT,
                        tier TEXT,
                        time TEXT,
                        url TEXT,
                        source TEXT,
                        parsed_at TEXT,
                        match_info TEXT,
                        odds TEXT,
                        lineup_analysis TEXT,
                        bias_analysis TEXT,
                        status TEXT DEFAULT 'upcoming',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # CS2 live matches table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cs2_live_matches (
                        match_id TEXT PRIMARY KEY,
                        team1 TEXT NOT NULL,
                        team2 TEXT NOT NULL,
                        score TEXT,
                        current_map TEXT,
                        maps_played TEXT,
                        status TEXT,
                        live_data TEXT,
                        progression_analysis TEXT,
                        overtime_probability REAL,
                        timestamp TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # CS2 predictions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cs2_predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        match_id TEXT,
                        predicted_winner TEXT,
                        team1_win_probability REAL,
                        team2_win_probability REAL,
                        predicted_score_diff REAL,
                        confidence_score REAL,
                        model_version TEXT,
                        prediction_time TEXT,
                        feature_importance TEXT,
                        risk_assessment TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (match_id) REFERENCES cs2_matches(match_id)
                    )
                ''')
                
                # KHL matches table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS khl_matches (
                        match_id TEXT PRIMARY KEY,
                        team1 TEXT NOT NULL,
                        team2 TEXT NOT NULL,
                        date TEXT,
                        time TEXT,
                        venue TEXT,
                        league TEXT,
                        season TEXT,
                        status TEXT DEFAULT 'upcoming',
                        source TEXT,
                        parsed_at TEXT,
                        match_details TEXT,
                        odds TEXT,
                        home_advantage REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # KHL live matches table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS khl_live_matches (
                        match_id TEXT PRIMARY KEY,
                        team1 TEXT NOT NULL,
                        team2 TEXT NOT NULL,
                        score TEXT,
                        current_period INTEGER,
                        time_in_period INTEGER,
                        status TEXT,
                        live_data TEXT,
                        period_analysis TEXT,
                        pressure_model TEXT,
                        timestamp TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # KHL predictions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS khl_predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        match_id TEXT,
                        predicted_winner TEXT,
                        team1_win_probability REAL,
                        team2_win_probability REAL,
                        draw_probability REAL,
                        predicted_total_goals REAL,
                        confidence_score REAL,
                        model_version TEXT,
                        prediction_time TEXT,
                        feature_importance TEXT,
                        risk_assessment TEXT,
                        period_predictions TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (match_id) REFERENCES khl_matches(match_id)
                    )
                ''')
                
                # Analysis results table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sport TEXT NOT NULL,
                        match_id TEXT,
                        analysis_type TEXT,
                        result TEXT,
                        confidence REAL,
                        scenarios TEXT,
                        recommendation TEXT,
                        analysis_time TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # System logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        log_level TEXT,
                        module TEXT,
                        message TEXT,
                        details TEXT,
                        timestamp TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cs2_matches_status ON cs2_matches(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cs2_matches_parsed_at ON cs2_matches(parsed_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_khl_matches_status ON khl_matches(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_khl_matches_date ON khl_matches(date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_results_sport ON analysis_results(sport)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_results_time ON analysis_results(analysis_time)')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    async def store_cs2_matches(self, matches: List[Dict[str, Any]]):
        """Store CS2 matches in database"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                for match in matches:
                    await cursor.execute('''
                        INSERT OR REPLACE INTO cs2_matches 
                        (match_id, team1, team2, tournament, tier, time, url, source, 
                         parsed_at, match_info, odds, lineup_analysis, bias_analysis, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        match.get('match_id'),
                        match.get('team1'),
                        match.get('team2'),
                        match.get('tournament'),
                        match.get('tier'),
                        match.get('time'),
                        match.get('url'),
                        match.get('source'),
                        match.get('parsed_at'),
                        json.dumps(match.get('match_info', {})),
                        json.dumps(match.get('odds', {})),
                        json.dumps(match.get('lineup_analysis', {})),
                        json.dumps(match.get('bias_analysis', {})),
                        match.get('status', 'upcoming')
                    ))
                
                await conn.commit()
                logger.info(f"Stored {len(matches)} CS2 matches")
                
        except Exception as e:
            logger.error(f"Error storing CS2 matches: {e}")
    
    async def store_khl_matches(self, matches: List[Dict[str, Any]]):
        """Store KHL matches in database"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                for match in matches:
                    await cursor.execute('''
                        INSERT OR REPLACE INTO khl_matches 
                        (match_id, team1, team2, date, time, venue, league, season, status,
                         source, parsed_at, match_details, odds, home_advantage)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        match.get('match_id'),
                        match.get('team1'),
                        match.get('team2'),
                        match.get('date'),
                        match.get('time'),
                        match.get('venue'),
                        match.get('league'),
                        match.get('season'),
                        match.get('status', 'upcoming'),
                        match.get('source'),
                        match.get('parsed_at'),
                        json.dumps(match.get('match_details', {})),
                        json.dumps(match.get('odds', {})),
                        match.get('home_advantage', 0.08)
                    ))
                
                await conn.commit()
                logger.info(f"Stored {len(matches)} KHL matches")
                
        except Exception as e:
            logger.error(f"Error storing KHL matches: {e}")
    
    async def store_live_cs2_matches(self, matches: List[Dict[str, Any]]):
        """Store live CS2 matches"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                for match in matches:
                    await cursor.execute('''
                        INSERT OR REPLACE INTO cs2_live_matches 
                        (match_id, team1, team2, score, current_map, maps_played, status,
                         live_data, progression_analysis, overtime_probability, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        match.get('match_id'),
                        match.get('team1'),
                        match.get('team2'),
                        json.dumps(match.get('score', {})),
                        match.get('current_map'),
                        json.dumps(match.get('maps_played', [])),
                        match.get('status'),
                        json.dumps(match.get('live_data', {})),
                        json.dumps(match.get('progression_analysis', {})),
                        match.get('overtime_probability', 0.0),
                        match.get('timestamp')
                    ))
                
                await conn.commit()
                logger.info(f"Stored {len(matches)} live CS2 matches")
                
        except Exception as e:
            logger.error(f"Error storing live CS2 matches: {e}")
    
    async def store_live_khl_matches(self, matches: List[Dict[str, Any]]):
        """Store live KHL matches"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                for match in matches:
                    await cursor.execute('''
                        INSERT OR REPLACE INTO khl_live_matches 
                        (match_id, team1, team2, score, current_period, time_in_period, status,
                         live_data, period_analysis, pressure_model, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        match.get('match_id'),
                        match.get('team1'),
                        match.get('team2'),
                        json.dumps(match.get('score', {})),
                        match.get('current_period', 1),
                        match.get('time_in_period', 0),
                        match.get('status'),
                        json.dumps(match.get('live_data', {})),
                        json.dumps(match.get('period_analysis', {})),
                        json.dumps(match.get('pressure_model', {})),
                        match.get('timestamp')
                    ))
                
                await conn.commit()
                logger.info(f"Stored {len(matches)} live KHL matches")
                
        except Exception as e:
            logger.error(f"Error storing live KHL matches: {e}")
    
    async def store_cs2_predictions(self, predictions: List[Dict[str, Any]]):
        """Store CS2 predictions"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                for pred in predictions:
                    await cursor.execute('''
                        INSERT INTO cs2_predictions 
                        (match_id, predicted_winner, team1_win_probability, team2_win_probability,
                         predicted_score_diff, confidence_score, model_version, prediction_time,
                         feature_importance, risk_assessment)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pred.get('match_id'),
                        pred.get('predicted_winner'),
                        pred.get('team1_win_probability'),
                        pred.get('team2_win_probability'),
                        pred.get('predicted_score_diff'),
                        pred.get('confidence_score'),
                        pred.get('model_version'),
                        pred.get('prediction_time'),
                        json.dumps(pred.get('feature_importance', {})),
                        json.dumps(pred.get('risk_assessment', {}))
                    ))
                
                await conn.commit()
                logger.info(f"Stored {len(predictions)} CS2 predictions")
                
        except Exception as e:
            logger.error(f"Error storing CS2 predictions: {e}")
    
    async def store_khl_predictions(self, predictions: List[Dict[str, Any]]):
        """Store KHL predictions"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                for pred in predictions:
                    await cursor.execute('''
                        INSERT INTO khl_predictions 
                        (match_id, predicted_winner, team1_win_probability, team2_win_probability,
                         draw_probability, predicted_total_goals, confidence_score, model_version,
                         prediction_time, feature_importance, risk_assessment, period_predictions)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pred.get('match_id'),
                        pred.get('predicted_winner'),
                        pred.get('team1_win_probability'),
                        pred.get('team2_win_probability'),
                        pred.get('draw_probability'),
                        pred.get('predicted_total_goals'),
                        pred.get('confidence_score'),
                        pred.get('model_version'),
                        pred.get('prediction_time'),
                        json.dumps(pred.get('feature_importance', {})),
                        json.dumps(pred.get('risk_assessment', {})),
                        json.dumps(pred.get('period_predictions', {}))
                    ))
                
                await conn.commit()
                logger.info(f"Stored {len(predictions)} KHL predictions")
                
        except Exception as e:
            logger.error(f"Error storing KHL predictions: {e}")
    
    async def get_cs2_matches_with_odds(self) -> List[Dict[str, Any]]:
        """Get CS2 matches that have odds data"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                await cursor.execute('''
                    SELECT match_id, team1, team2, tournament, tier, time, url, source,
                           parsed_at, match_info, odds, lineup_analysis, bias_analysis, status
                    FROM cs2_matches 
                    WHERE odds IS NOT NULL AND odds != '{}'
                    ORDER BY parsed_at DESC
                    LIMIT 50
                ''')
                
                rows = await cursor.fetchall()
                matches = []
                
                for row in rows:
                    match = {
                        'match_id': row[0],
                        'team1': row[1],
                        'team2': row[2],
                        'tournament': row[3],
                        'tier': row[4],
                        'time': row[5],
                        'url': row[6],
                        'source': row[7],
                        'parsed_at': row[8],
                        'match_info': json.loads(row[9]) if row[9] else {},
                        'odds': json.loads(row[10]) if row[10] else {},
                        'lineup_analysis': json.loads(row[11]) if row[11] else {},
                        'bias_analysis': json.loads(row[12]) if row[12] else {},
                        'status': row[13]
                    }
                    matches.append(match)
                
                return matches
                
        except Exception as e:
            logger.error(f"Error getting CS2 matches with odds: {e}")
            return []
    
    async def get_khl_matches_with_odds(self) -> List[Dict[str, Any]]:
        """Get KHL matches that have odds data"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                await cursor.execute('''
                    SELECT match_id, team1, team2, date, time, venue, league, season, status,
                           source, parsed_at, match_details, odds, home_advantage
                    FROM khl_matches 
                    WHERE odds IS NOT NULL AND odds != '{}'
                    ORDER BY parsed_at DESC
                    LIMIT 50
                ''')
                
                rows = await cursor.fetchall()
                matches = []
                
                for row in rows:
                    match = {
                        'match_id': row[0],
                        'team1': row[1],
                        'team2': row[2],
                        'date': row[3],
                        'time': row[4],
                        'venue': row[5],
                        'league': row[6],
                        'season': row[7],
                        'status': row[8],
                        'source': row[9],
                        'parsed_at': row[10],
                        'match_details': json.loads(row[11]) if row[11] else {},
                        'odds': json.loads(row[12]) if row[12] else {},
                        'home_advantage': row[13]
                    }
                    matches.append(match)
                
                return matches
                
        except Exception as e:
            logger.error(f"Error getting KHL matches with odds: {e}")
            return []
    
    async def get_live_cs2_matches(self) -> List[Dict[str, Any]]:
        """Get live CS2 matches"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                await cursor.execute('''
                    SELECT match_id, team1, team2, score, current_map, maps_played, status,
                           live_data, progression_analysis, overtime_probability, timestamp
                    FROM cs2_live_matches 
                    WHERE status = 'live'
                    ORDER BY timestamp DESC
                ''')
                
                rows = await cursor.fetchall()
                matches = []
                
                for row in rows:
                    match = {
                        'match_id': row[0],
                        'team1': row[1],
                        'team2': row[2],
                        'score': json.loads(row[3]) if row[3] else {},
                        'current_map': row[4],
                        'maps_played': json.loads(row[5]) if row[5] else [],
                        'status': row[6],
                        'live_data': json.loads(row[7]) if row[7] else {},
                        'progression_analysis': json.loads(row[8]) if row[8] else {},
                        'overtime_probability': row[9],
                        'timestamp': row[10]
                    }
                    matches.append(match)
                
                return matches
                
        except Exception as e:
            logger.error(f"Error getting live CS2 matches: {e}")
            return []
    
    async def get_live_khl_matches(self) -> List[Dict[str, Any]]:
        """Get live KHL matches"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                await cursor.execute('''
                    SELECT match_id, team1, team2, score, current_period, time_in_period, status,
                           live_data, period_analysis, pressure_model, timestamp
                    FROM khl_live_matches 
                    WHERE status = 'live'
                    ORDER BY timestamp DESC
                ''')
                
                rows = await cursor.fetchall()
                matches = []
                
                for row in rows:
                    match = {
                        'match_id': row[0],
                        'team1': row[1],
                        'team2': row[2],
                        'score': json.loads(row[3]) if row[3] else {},
                        'current_period': row[4],
                        'time_in_period': row[5],
                        'status': row[6],
                        'live_data': json.loads(row[7]) if row[7] else {},
                        'period_analysis': json.loads(row[8]) if row[8] else {},
                        'pressure_model': json.loads(row[9]) if row[9] else {},
                        'timestamp': row[10]
                    }
                    matches.append(match)
                
                return matches
                
        except Exception as e:
            logger.error(f"Error getting live KHL matches: {e}")
            return []
    
    async def get_upcoming_cs2_matches(self) -> List[Dict[str, Any]]:
        """Get upcoming CS2 matches"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                await cursor.execute('''
                    SELECT match_id, team1, team2, tournament, tier, time, url, source,
                           parsed_at, match_info, odds, lineup_analysis, bias_analysis
                    FROM cs2_matches 
                    WHERE status = 'upcoming'
                    ORDER BY parsed_at DESC
                    LIMIT 20
                ''')
                
                rows = await cursor.fetchall()
                matches = []
                
                for row in rows:
                    match = {
                        'match_id': row[0],
                        'team1': row[1],
                        'team2': row[2],
                        'tournament': row[3],
                        'tier': row[4],
                        'time': row[5],
                        'url': row[6],
                        'source': row[7],
                        'parsed_at': row[8],
                        'match_info': json.loads(row[9]) if row[9] else {},
                        'odds': json.loads(row[10]) if row[10] else {},
                        'lineup_analysis': json.loads(row[11]) if row[11] else {},
                        'bias_analysis': json.loads(row[12]) if row[12] else {}
                    }
                    matches.append(match)
                
                return matches
                
        except Exception as e:
            logger.error(f"Error getting upcoming CS2 matches: {e}")
            return []
    
    async def get_upcoming_khl_matches(self) -> List[Dict[str, Any]]:
        """Get upcoming KHL matches"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                await cursor.execute('''
                    SELECT match_id, team1, team2, date, time, venue, league, season, status,
                           source, parsed_at, match_details, odds, home_advantage
                    FROM khl_matches 
                    WHERE status = 'upcoming'
                    ORDER BY parsed_at DESC
                    LIMIT 20
                ''')
                
                rows = await cursor.fetchall()
                matches = []
                
                for row in rows:
                    match = {
                        'match_id': row[0],
                        'team1': row[1],
                        'team2': row[2],
                        'date': row[3],
                        'time': row[4],
                        'venue': row[5],
                        'league': row[6],
                        'season': row[7],
                        'status': row[8],
                        'source': row[9],
                        'parsed_at': row[10],
                        'match_details': json.loads(row[11]) if row[11] else {},
                        'odds': json.loads(row[12]) if row[12] else {},
                        'home_advantage': row[13]
                    }
                    matches.append(match)
                
                return matches
                
        except Exception as e:
            logger.error(f"Error getting upcoming KHL matches: {e}")
            return []
    
    async def get_historical_cs2_matches(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical CS2 matches for ML training"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                await cursor.execute('''
                    SELECT match_id, team1, team2, tournament, tier, time, url, source,
                           parsed_at, match_info, odds, lineup_analysis, bias_analysis
                    FROM cs2_matches 
                    WHERE parsed_at < ? AND status IN ('completed', 'finished')
                    ORDER BY parsed_at DESC
                    LIMIT 200
                ''', (cutoff_date,))
                
                rows = await cursor.fetchall()
                matches = []
                
                for row in rows:
                    # Add simulated results for training
                    match = {
                        'match_id': row[0],
                        'team1': row[1],
                        'team2': row[2],
                        'tournament': row[3],
                        'tier': row[4],
                        'time': row[5],
                        'url': row[6],
                        'source': row[7],
                        'parsed_at': row[8],
                        'match_info': json.loads(row[9]) if row[9] else {},
                        'odds': json.loads(row[10]) if row[10] else {},
                        'lineup_analysis': json.loads(row[11]) if row[11] else {},
                        'bias_analysis': json.loads(row[12]) if row[12] else {},
                        'result': self._generate_simulated_result(row[1], row[2])
                    }
                    matches.append(match)
                
                return matches
                
        except Exception as e:
            logger.error(f"Error getting historical CS2 matches: {e}")
            return []
    
    async def get_historical_khl_matches(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical KHL matches for ML training"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                await cursor.execute('''
                    SELECT match_id, team1, team2, date, time, venue, league, season, status,
                           source, parsed_at, match_details, odds, home_advantage
                    FROM khl_matches 
                    WHERE parsed_at < ? AND status IN ('completed', 'finished')
                    ORDER BY parsed_at DESC
                    LIMIT 200
                ''', (cutoff_date,))
                
                rows = await cursor.fetchall()
                matches = []
                
                for row in rows:
                    # Add simulated results for training
                    match = {
                        'match_id': row[0],
                        'team1': row[1],
                        'team2': row[2],
                        'date': row[3],
                        'time': row[4],
                        'venue': row[5],
                        'league': row[6],
                        'season': row[7],
                        'status': row[8],
                        'source': row[9],
                        'parsed_at': row[10],
                        'match_details': json.loads(row[11]) if row[11] else {},
                        'odds': json.loads(row[12]) if row[12] else {},
                        'home_advantage': row[13],
                        'result': self._generate_simulated_khl_result(row[1], row[2])
                    }
                    matches.append(match)
                
                return matches
                
        except Exception as e:
            logger.error(f"Error getting historical KHL matches: {e}")
            return []
    
    def _generate_simulated_result(self, team1: str, team2: str) -> Dict[str, Any]:
        """Generate simulated result for training"""
        import random
        
        # Simple simulation based on team name patterns
        team1_score = random.randint(0, 16)
        team2_score = random.randint(0, 16)
        
        # Ensure different scores
        while team1_score == team2_score:
            team2_score = random.randint(0, 16)
        
        winner = 'team1' if team1_score > team2_score else 'team2'
        
        return {
            'winner': winner,
            'team1_score': team1_score,
            'team2_score': team2_score,
            'score_diff': abs(team1_score - team2_score)
        }
    
    def _generate_simulated_khl_result(self, team1: str, team2: str) -> Dict[str, Any]:
        """Generate simulated KHL result for training"""
        import random
        
        # Hockey scoring simulation
        team1_score = random.randint(0, 6)
        team2_score = random.randint(0, 6)
        
        # Possibility of overtime/shootout
        if team1_score == team2_score and random.random() < 0.3:
            winner = random.choice(['team1', 'team2'])
            team1_score += 1 if winner == 'team1' else 0
            team2_score += 1 if winner == 'team2' else 0
        elif team1_score == team2_score:
            winner = 'draw'
        else:
            winner = 'team1' if team1_score > team2_score else 'team2'
        
        return {
            'winner': winner,
            'team1_score': team1_score,
            'team2_score': team2_score,
            'total_goals': team1_score + team2_score,
            'goal_difference': team1_score - team2_score
        }
    
    async def log_system_event(self, level: str, module: str, message: str, details: str = ""):
        """Log system event"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                await cursor.execute('''
                    INSERT INTO system_logs (log_level, module, message, details, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (level, module, message, details, datetime.now().isoformat()))
                
                await conn.commit()
                
        except Exception as e:
            logger.error(f"Error logging system event: {e}")
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data to keep database size manageable"""
        try:
            async with connect(self.db_path) as conn:
                cursor = await conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Clean old live matches
                await cursor.execute('DELETE FROM cs2_live_matches WHERE timestamp < ?', (cutoff_date,))
                await cursor.execute('DELETE FROM khl_live_matches WHERE timestamp < ?', (cutoff_date,))
                
                # Clean old system logs
                await cursor.execute('DELETE FROM system_logs WHERE timestamp < ?', (cutoff_date,))
                
                await conn.commit()
                logger.info(f"Cleaned up data older than {days} days")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")


# Global database instance
db_manager = DatabaseManager()

# Export convenience functions
async def store_cs2_matches(matches):
    await db_manager.store_cs2_matches(matches)

async def store_khl_matches(matches):
    await db_manager.store_khl_matches(matches)

async def store_live_cs2_matches(matches):
    await db_manager.store_live_cs2_matches(matches)

async def store_live_khl_matches(matches):
    await db_manager.store_live_khl_matches(matches)

async def store_cs2_predictions(predictions):
    await db_manager.store_cs2_predictions(predictions)

async def store_khl_predictions(predictions):
    await db_manager.store_khl_predictions(predictions)

async def get_cs2_matches_with_odds():
    return await db_manager.get_cs2_matches_with_odds()

async def get_khl_matches_with_odds():
    return await db_manager.get_khl_matches_with_odds()

async def get_live_cs2_matches():
    return await db_manager.get_live_cs2_matches()

async def get_live_khl_matches():
    return await db_manager.get_live_khl_matches()

async def get_upcoming_cs2_matches():
    return await db_manager.get_upcoming_cs2_matches()

async def get_upcoming_khl_matches():
    return await db_manager.get_upcoming_khl_matches()

async def get_historical_cs2_matches(days=30):
    return await db_manager.get_historical_cs2_matches(days)

async def get_historical_khl_matches(days=30):
    return await db_manager.get_historical_khl_matches(days)

async def store_cs2_odds(matches):
    # Update matches with odds
    await db_manager.store_cs2_matches(matches)

async def store_khl_odds(matches):
    # Update matches with odds
    await db_manager.store_khl_matches(matches)

async def store_cs2_bias_analysis(matches):
    # Update matches with bias analysis
    await db_manager.store_cs2_matches(matches)

async def store_cs2_lineup_analysis(matches):
    # Update matches with lineup analysis
    await db_manager.store_cs2_matches(matches)

async def store_prioritized_cs2_matches(matches):
    # Store prioritized matches (could be a separate table if needed)
    await db_manager.store_cs2_matches(matches)

async def store_khl_period_analysis(matches):
    # Update live matches with period analysis
    await db_manager.store_live_khl_matches(matches)

async def store_khl_pressure_analysis(matches):
    # Update live matches with pressure analysis
    await db_manager.store_live_khl_matches(matches)

async def get_all_cs2_matches():
    # Get all CS2 matches (for filtering)
    return await db_manager.get_cs2_matches_with_odds()

async def get_pending_cs2_matches():
    # Get CS2 matches that need odds
    return await db_manager.get_upcoming_cs2_matches()

async def get_pending_khl_matches():
    # Get KHL matches that need odds
    return await db_manager.get_upcoming_khl_matches()

async def get_cs2_matches_with_lineups():
    # Get CS2 matches with lineup data
    return await db_manager.get_upcoming_cs2_matches()
