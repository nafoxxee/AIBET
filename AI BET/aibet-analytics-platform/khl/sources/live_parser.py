import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger(__name__)


class KHLLiveParser:
    """Parser for live KHL match data"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.live_matches_cache = {}
        self.period_durations = {
            1: 1200,  # 20 minutes
            2: 1200,  # 20 minutes
            3: 1200,  # 20 minutes
            4: 1200,  # 20 minutes (overtime)
            5: 300    # 5 minutes (shootout)
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_live_matches(self) -> List[Dict[str, Any]]:
        """Get currently live KHL matches"""
        try:
            # This would scrape live KHL matches
            # For now, return simulated live data
            
            live_matches = [
                {
                    'match_id': 'khl_live_001',
                    'team1': 'SKA Saint Petersburg',
                    'team2': 'CSKA Moscow',
                    'score': {'team1': 2, 'team2': 1},
                    'current_period': 2,
                    'time_in_period': 456,  # seconds
                    'status': 'live',
                    'live_data': {
                        'shots': {'team1': 18, 'team2': 12},
                        'penalties': {
                            'team1': [{'player': 'Player1', 'minutes': 2, 'time': '12:34'}],
                            'team2': [{'player': 'Player2', 'minutes': 2, 'time': '08:15'}]
                        },
                        'power_play': {'team': 'team1', 'time_remaining': 78},
                        'time_since_last_goal': 345,  # seconds
                        'goal_scorers': [
                            {'team': 'team1', 'player': 'Igor', 'period': 1, 'time': '05:23'},
                            {'team': 'team2', 'player': 'Sergei', 'period': 1, 'time': '14:45'},
                            {'team': 'team1', 'player': 'Nikita', 'period': 2, 'time': '03:12'}
                        ],
                        'goalies': {
                            'team1': {'player': 'Goalie1', 'saves': 15, 'goals_against': 1},
                            'team2': {'player': 'Goalie2', 'saves': 10, 'goals_against': 2}
                        }
                    },
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'match_id': 'khl_live_002',
                    'team1': 'Ak Bars Kazan',
                    'team2': 'Metallurg Magnitogorsk',
                    'score': {'team1': 0, 'team2': 0},
                    'current_period': 1,
                    'time_in_period': 890,
                    'status': 'live',
                    'live_data': {
                        'shots': {'team1': 8, 'team2': 11},
                        'penalties': [],
                        'power_play': None,
                        'time_since_last_goal': 890,
                        'goal_scorers': [],
                        'goalies': {
                            'team1': {'player': 'Goalie3', 'saves': 11, 'goals_against': 0},
                            'team2': {'player': 'Goalie4', 'saves': 8, 'goals_against': 0}
                        }
                    },
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            # Update cache
            for match in live_matches:
                self.live_matches_cache[match['match_id']] = match
            
            logger.info(f"Found {len(live_matches)} live KHL matches")
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
            live_data = match_data.get('live_data', {})
            current_period = match_data.get('current_period', 1)
            time_in_period = match_data.get('time_in_period', 0)
            
            # Update time
            time_in_period += 30  # Add 30 seconds
            if time_in_period >= self.period_durations.get(current_period, 1200):
                # Period ended
                current_period += 1
                time_in_period = 0
            
            match_data['current_period'] = current_period
            match_data['time_in_period'] = time_in_period
            
            # Simulate shot updates
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            if time_in_period % 60 == 0:  # Every minute
                if shots['team1'] > shots['team2']:
                    shots['team2'] += 1
                else:
                    shots['team1'] += 1
            
            # Update time since last goal
            time_since_goal = live_data.get('time_since_last_goal', 0) + 30
            live_data['time_since_last_goal'] = time_since_goal
            
            # Simulate random goal
            if time_since_goal > 300 and time_in_period > 300:  # After 5 minutes and 5 minutes in period
                if time_in_period % 450 == 0:  # Every 7.5 minutes
                    scoring_team = 'team1' if shots['team1'] > shots['team2'] else 'team2'
                    score = match_data.get('score', {'team1': 0, 'team2': 0})
                    score[scoring_team] += 1
                    match_data['score'] = score
                    live_data['time_since_last_goal'] = 0
            
            match_data['timestamp'] = datetime.now().isoformat()
            return match_data
            
        except Exception as e:
            logger.warning(f"Error updating live data: {e}")
            return None
    
    async def _fetch_live_match_data(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Fetch fresh live match data"""
        try:
            # This would scrape actual live data from sports websites
            # For now, return simulated data
            
            live_data = {
                'match_id': match_id,
                'team1': 'Team A',
                'team2': 'Team B',
                'score': {'team1': 0, 'team2': 0},
                'current_period': 1,
                'time_in_period': 0,
                'status': 'live',
                'live_data': {
                    'shots': {'team1': 0, 'team2': 0},
                    'penalties': [],
                    'power_play': None,
                    'time_since_last_goal': 0,
                    'goal_scorers': [],
                    'goalies': {
                        'team1': {'player': 'GoalieA', 'saves': 0, 'goals_against': 0},
                        'team2': {'player': 'GoalieB', 'saves': 0, 'goals_against': 0}
                    }
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return live_data
            
        except Exception as e:
            logger.error(f"Error fetching live match data: {e}")
            return None
    
    def analyze_period_logic(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze period-specific patterns"""
        analysis = {
            'period_analysis': {},
            'comeback_potential': False,
            'pressure_without_conversion': False,
            'late_period_scenario': False,
            'momentum_shift': False
        }
        
        try:
            current_period = match_data.get('current_period', 1)
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            live_data = match_data.get('live_data', {})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            time_in_period = match_data.get('time_in_period', 0)
            
            # Period-specific analysis
            if current_period == 1:
                analysis['period_analysis'] = self._analyze_first_period(score, shots, time_in_period)
            elif current_period == 2:
                analysis['period_analysis'] = self._analyze_second_period(score, shots, time_in_period)
            elif current_period == 3:
                analysis['period_analysis'] = self._analyze_third_period(score, shots, time_in_period)
            
            # Check for comeback potential
            score_diff = abs(score['team1'] - score['team2'])
            if current_period >= 2 and score_diff <= 2:
                analysis['comeback_potential'] = True
            
            # Check for pressure without conversion
            if shots['team1'] > shots['team2'] + 8 and score['team1'] <= score['team2']:
                analysis['pressure_without_conversion'] = True
            elif shots['team2'] > shots['team1'] + 8 and score['team2'] <= score['team1']:
                analysis['pressure_without_conversion'] = True
            
            # Check for late period scenario
            if time_in_period > 900:  # Last 5 minutes of period
                analysis['late_period_scenario'] = True
            
            # Check momentum shift
            time_since_goal = live_data.get('time_since_last_goal', 0)
            if time_since_goal < 120:  # Recent goal
                analysis['momentum_shift'] = True
            
        except Exception as e:
            logger.warning(f"Error analyzing period logic: {e}")
        
        return analysis
    
    def _analyze_first_period(self, score: Dict, shots: Dict, time_in_period: int) -> Dict[str, Any]:
        """Analyze first period patterns"""
        return {
            'period_type': 'first',
            'scoring_pace': 'normal' if score['team1'] + score['team2'] <= 2 else 'high',
            'shot_differential': shots['team1'] - shots['team2'],
            'early_goals': score['team1'] + score['team2'] > 0 and time_in_period < 600
        }
    
    def _analyze_second_period(self, score: Dict, shots: Dict, time_in_period: int) -> Dict[str, Any]:
        """Analyze second period patterns"""
        return {
            'period_type': 'second',
            'middle_game_adjustment': True,
            'fatigue_factor': 'increasing',
            'strategic_changes': True
        }
    
    def _analyze_third_period(self, score: Dict, shots: Dict, time_in_period: int) -> Dict[str, Any]:
        """Analyze third period patterns"""
        score_diff = abs(score['team1'] - score['team2'])
        
        return {
            'period_type': 'third',
            'desperation_factor': 'high' if score_diff >= 3 else 'moderate',
            'empty_net_potential': score_diff >= 2 and time_in_period > 900,
            'overtime_probability': score_diff <= 1
        }
    
    def detect_pressure_model(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect pressure patterns in the match"""
        pressure = {
            'team1_pressure': 0.0,
            'team2_pressure': 0.0,
            'pressure_differential': 0.0,
            'critical_moments': []
        }
        
        try:
            live_data = match_data.get('live_data', {})
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            time_in_period = match_data.get('time_in_period', 0)
            current_period = match_data.get('current_period', 1)
            
            # Calculate pressure based on shots and score
            if shots['team1'] > 0:
                pressure['team1_pressure'] = min(shots['team1'] / 20.0, 1.0)
            if shots['team2'] > 0:
                pressure['team2_pressure'] = min(shots['team2'] / 20.0, 1.0)
            
            pressure['pressure_differential'] = pressure['team1_pressure'] - pressure['team2_pressure']
            
            # Identify critical moments
            if time_in_period > 900 and abs(score['team1'] - score['team2']) <= 1:
                pressure['critical_moments'].append('late_close_game')
            
            if current_period == 3 and score['team1'] != score['team2']:
                pressure['critical_moments'].append('third_period_lead')
            
            # Check for power play pressure
            power_play = live_data.get('power_play')
            if power_play:
                pressure['critical_moments'].append('power_play_opportunity')
            
        except Exception as e:
            logger.warning(f"Error detecting pressure model: {e}")
        
        return pressure


async def update_live_khl_matches():
    """Update all live KHL matches data"""
    async with KHLLiveParser() as parser:
        live_matches = await parser.get_live_matches()
        
        # Analyze each live match
        analyzed_matches = []
        for match in live_matches:
            # Add period analysis
            match['period_analysis'] = parser.analyze_period_logic(match)
            
            # Add pressure model
            match['pressure_model'] = parser.detect_pressure_model(match)
            
            analyzed_matches.append(match)
        
        # Store in database
        from storage.database import store_live_khl_matches
        await store_live_khl_matches(analyzed_matches)
        
        return analyzed_matches


async def khl_live_task():
    """KHL live data update task for scheduler"""
    logger.info("Starting KHL live data update")
    
    try:
        matches = await update_live_khl_matches()
        
        # Check for important live scenarios
        for match in matches:
            period_analysis = match.get('period_analysis', {})
            
            if period_analysis.get('comeback_potential') or period_analysis.get('pressure_without_conversion'):
                from app.main import telegram_sender
                await telegram_sender.send_khl_analysis({
                    'match': match,
                    'scenarios': [{'name': 'Live pressure scenario', 'confidence': 0.75}],
                    'recommendation': {
                        'text': f"Pressure scenario detected in {match['team1']} vs {match['team2']}",
                        'confidence': 0.75
                    }
                })
        
        logger.info(f"Updated live data for {len(matches)} matches")
        
    except Exception as e:
        logger.error(f"KHL live task failed: {e}")


def setup_khl_live_tasks(scheduler):
    """Setup KHL live data tasks in scheduler"""
    scheduler.add_task('khl_live_update', khl_live_task, 60)  # Every 1 minute
    logger.info("KHL live tasks setup complete")
