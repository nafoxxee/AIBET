import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger(__name__)


class LiveParser:
    """Parser for live CS2 match data"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.live_matches_cache = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_live_matches(self) -> List[Dict[str, Any]]:
        """Get currently live CS2 matches"""
        try:
            # This would scrape HLTV live matches page
            # For now, return simulated live data
            
            live_matches = [
                {
                    'match_id': '234567',
                    'team1': 'Natus Vincere',
                    'team2': 'FaZe Clan',
                    'score': {'team1': 1, 'team2': 0},
                    'current_map': 'de_mirage',
                    'maps_played': [
                        {'map': 'de_dust2', 'score': '16-12', 'winner': 'team1'},
                        {'map': 'de_mirage', 'score': '8-5', 'winner': None}
                    ],
                    'status': 'live',
                    'live_data': {
                        'current_round': 14,
                        'team1_economy': 'full_buy',
                        'team2_economy': 'eco',
                        'round_time': 45,
                        'bomb_planted': False,
                        'players_alive': {'team1': 5, 'team2': 3}
                    },
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'match_id': '234568',
                    'team1': 'G2 Esports',
                    'team2': 'Vitality',
                    'score': {'team1': 0, 'team2': 1},
                    'current_map': 'de_inferno',
                    'maps_played': [
                        {'map': 'de_inferno', 'score': '9-6', 'winner': None}
                    ],
                    'status': 'live',
                    'live_data': {
                        'current_round': 16,
                        'team1_economy': 'force_buy',
                        'team2_economy': 'full_buy',
                        'round_time': 78,
                        'bomb_planted': True,
                        'players_alive': {'team1': 2, 'team2': 4}
                    },
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            # Update cache
            for match in live_matches:
                self.live_matches_cache[match['match_id']] = match
            
            logger.info(f"Found {len(live_matches)} live matches")
            return live_matches
            
        except Exception as e:
            logger.error(f"Error getting live matches: {e}")
            return []
    
    async def get_match_live_data(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed live data for specific match"""
        try:
            # Check cache first
            if match_id in self.live_matches_cache:
                cached_match = self.live_matches_cache[match_id]
                # Update with new live data
                updated_data = await self._update_live_data(cached_match)
                if updated_data:
                    self.live_matches_cache[match_id] = updated_data
                    return updated_data
            
            # If not in cache, fetch fresh data
            live_data = await self._fetch_live_match_data(match_id)
            if live_data:
                self.live_matches_cache[match_id] = live_data
            
            return live_data
            
        except Exception as e:
            logger.error(f"Error getting live data for {match_id}: {e}")
            return None
    
    async def _update_live_data(self, match_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update live data with new information"""
        try:
            # Simulate live data updates
            current_round = match_data['live_data']['current_round']
            
            # Update round progress
            new_round_time = match_data['live_data']['round_time'] - 15
            if new_round_time <= 0:
                # Round ended, start new round
                current_round += 1
                new_round_time = 75  # New round start time
                
                # Simulate round outcome
                if current_round % 3 == 0:  # Every 3rd round, team1 wins
                    match_data['live_data']['players_alive'] = {'team1': 3, 'team2': 0}
                else:
                    match_data['live_data']['players_alive'] = {'team1': 1, 'team2': 5}
            
            match_data['live_data']['current_round'] = current_round
            match_data['live_data']['round_time'] = max(0, new_round_time)
            match_data['timestamp'] = datetime.now().isoformat()
            
            return match_data
            
        except Exception as e:
            logger.warning(f"Error updating live data: {e}")
            return None
    
    async def _fetch_live_match_data(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Fetch fresh live match data"""
        try:
            # This would scrape actual live data from HLTV or other sources
            # For now, return simulated data
            
            live_data = {
                'match_id': match_id,
                'team1': 'Team A',
                'team2': 'Team B',
                'score': {'team1': 0, 'team2': 0},
                'current_map': 'de_mirage',
                'status': 'live',
                'live_data': {
                    'current_round': 1,
                    'team1_economy': 'pistol',
                    'team2_economy': 'pistol',
                    'round_time': 75,
                    'bomb_planted': False,
                    'players_alive': {'team1': 5, 'team2': 5}
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return live_data
            
        except Exception as e:
            logger.error(f"Error fetching live match data: {e}")
            return None
    
    def analyze_map_progression(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze map progression patterns"""
        analysis = {
            'comeback_potential': False,
            'momentum_shift': False,
            'economy_mismatch': False,
            'round_streak': {'team1': 0, 'team2': 0},
            'key_rounds': []
        }
        
        try:
            live_data = match_data.get('live_data', {})
            score = match_data.get('score', {})
            
            # Check for comeback potential
            current_round = live_data.get('current_round', 0)
            if current_round > 15:  # Second half
                score_diff = abs(score.get('team1', 0) - score.get('team2', 0))
                if score_diff <= 3:
                    analysis['comeback_potential'] = True
            
            # Check economy mismatch
            team1_econ = live_data.get('team1_economy', '')
            team2_econ = live_data.get('team2_economy', '')
            
            if ('full_buy' in team1_econ and 'eco' in team2_econ) or \
               ('full_buy' in team2_econ and 'eco' in team1_econ):
                analysis['economy_mismatch'] = True
            
            # Identify key rounds
            if current_round in [15, 16, 30]:  # Half-time and match point rounds
                analysis['key_rounds'].append(current_round)
            
        except Exception as e:
            logger.warning(f"Error analyzing map progression: {e}")
        
        return analysis
    
    def detect_overtime_probability(self, match_data: Dict[str, Any]) -> float:
        """Detect probability of overtime"""
        try:
            score = match_data.get('score', {})
            live_data = match_data.get('live_data', {})
            current_round = live_data.get('current_round', 0)
            
            if current_round < 25:
                return 0.0  # Too early for overtime prediction
            
            team1_score = score.get('team1', 0)
            team2_score = score.get('team2', 0)
            
            # If score is close near the end, higher overtime probability
            if current_round >= 28:
                score_diff = abs(team1_score - team2_score)
                if score_diff == 0:
                    return 0.8  # Very high probability
                elif score_diff == 1:
                    return 0.4  # Medium probability
                elif score_diff == 2:
                    return 0.15  # Low probability
                else:
                    return 0.05  # Very low probability
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error detecting overtime probability: {e}")
            return 0.0


async def update_live_matches():
    """Update all live matches data"""
    async with LiveParser() as parser:
        live_matches = await parser.get_live_matches()
        
        # Analyze each live match
        analyzed_matches = []
        for match in live_matches:
            # Add progression analysis
            match['progression_analysis'] = parser.analyze_map_progression(match)
            
            # Add overtime probability
            match['overtime_probability'] = parser.detect_overtime_probability(match)
            
            analyzed_matches.append(match)
        
        # Store in database
        from storage.database import store_live_cs2_matches
        await store_live_cs2_matches(analyzed_matches)
        
        return analyzed_matches


async def cs2_live_task():
    """CS2 live data update task for scheduler"""
    logger.info("Starting CS2 live data update")
    
    try:
        matches = await update_live_matches()
        
        # Check for important live scenarios
        for match in matches:
            if match['progression_analysis']['comeback_potential']:
                from app.main import telegram_sender
                await telegram_sender.send_cs2_analysis({
                    'match': match,
                    'scenarios': [{'name': 'Live comeback potential', 'confidence': 0.75}],
                    'recommendation': {
                        'text': f"Comeback scenario detected in {match['team1']} vs {match['team2']}",
                        'confidence': 0.75
                    }
                })
        
        logger.info(f"Updated live data for {len(matches)} matches")
        
    except Exception as e:
        logger.error(f"CS2 live task failed: {e}")


def setup_cs2_live_tasks(scheduler):
    """Setup CS2 live data tasks in scheduler"""
    scheduler.add_task('cs2_live_update', cs2_live_task, 60)  # Every 1 minute
    logger.info("CS2 live tasks setup complete")
