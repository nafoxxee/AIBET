import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
from bs4 import BeautifulSoup
import re
import json

logger = logging.getLogger(__name__)


class KHLOddsParser:
    """Parser for KHL betting odds from public sources"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.bookmaker_sources = [
            'https://example-bookmaker1.com/khl',
            'https://example-bookmaker2.com/hockey/khl'
        ]
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_khl_odds(self, team1: str, team2: str) -> Optional[Dict[str, Any]]:
        """Get odds for KHL match between two teams"""
        try:
            # Search for odds on multiple public sources
            odds_data = await self._search_public_khl_odds(team1, team2)
            
            if odds_data:
                # Analyze odds patterns
                analysis = self._analyze_khl_odds_patterns(odds_data)
                odds_data['analysis'] = analysis
                
                return odds_data
            
        except Exception as e:
            logger.error(f"Error getting KHL odds for {team1} vs {team2}: {e}")
        
        return None
    
    async def _search_public_khl_odds(self, team1: str, team2: str) -> Optional[Dict[str, Any]]:
        """Search odds on public KHL betting websites"""
        try:
            # Simulate odds data (replace with actual scraping)
            odds_data = {
                'team1': team1,
                'team2': team2,
                'bookmakers': [],
                'average_odds': {},
                'handicap_odds': {},
                'total_odds': {},
                'period_odds': {},
                'movement_history': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Simulate multiple bookmakers
            bookmakers_data = [
                {
                    'name': 'BookmakerA',
                    'team1_odds': 1.85,
                    'team2_odds': 1.95,
                    'draw_odds': 4.20,
                    'handicap': {'team1': -1.5, 'team1_odds': 2.10, 'team2': 1.70},
                    'total': {'line': 5.5, 'over_odds': 1.90, 'under_odds': 1.90}
                },
                {
                    'name': 'BookmakerB',
                    'team1_odds': 1.82,
                    'team2_odds': 1.98,
                    'draw_odds': 4.10,
                    'handicap': {'team1': -1.5, 'team1_odds': 2.05, 'team2': 1.75},
                    'total': {'line': 5.5, 'over_odds': 1.85, 'under_odds': 1.95}
                },
                {
                    'name': 'BookmakerC',
                    'team1_odds': 1.88,
                    'team2_odds': 1.92,
                    'draw_odds': 4.30,
                    'handicap': {'team1': -1.5, 'team1_odds': 2.15, 'team2': 1.65},
                    'total': {'line': 5.5, 'over_odds': 1.95, 'under_odds': 1.85}
                }
            ]
            
            for bm in bookmakers_data:
                odds_data['bookmakers'].append(bm)
            
            # Calculate average odds
            team1_odds = [bm['team1_odds'] for bm in bookmakers_data]
            team2_odds = [bm['team2_odds'] for bm in bookmakers_data]
            draw_odds = [bm['draw_odds'] for bm in bookmakers_data]
            
            odds_data['average_odds'] = {
                'team1': sum(team1_odds) / len(team1_odds),
                'team2': sum(team2_odds) / len(team2_odds),
                'draw': sum(draw_odds) / len(draw_odds)
            }
            
            # Calculate handicap averages
            handicap_team1_odds = [bm['handicap']['team1_odds'] for bm in bookmakers_data]
            handicap_team2_odds = [bm['handicap']['team2_odds'] for bm in bookmakers_data]
            
            odds_data['handicap_odds'] = {
                'line': -1.5,
                'team1_odds': sum(handicap_team1_odds) / len(handicap_team1_odds),
                'team2_odds': sum(handicap_team2_odds) / len(handicap_team2_odds)
            }
            
            # Calculate total averages
            total_over_odds = [bm['total']['over_odds'] for bm in bookmakers_data]
            total_under_odds = [bm['total']['under_odds'] for bm in bookmakers_data]
            
            odds_data['total_odds'] = {
                'line': 5.5,
                'over_odds': sum(total_over_odds) / len(total_over_odds),
                'under_odds': sum(total_under_odds) / len(total_under_odds)
            }
            
            # Simulate period odds
            odds_data['period_odds'] = {
                'period1': {'team1': 2.10, 'team2': 2.80, 'draw': 3.60},
                'period2': {'team1': 2.15, 'team2': 2.75, 'draw': 3.50},
                'period3': {'team1': 2.20, 'team2': 2.70, 'draw': 3.40}
            }
            
            # Simulate odds movement
            odds_data['movement_history'] = [
                {'time': '2h ago', 'team1_odds': 1.80, 'team2_odds': 2.00},
                {'time': '1h ago', 'team1_odds': 1.83, 'team2_odds': 1.97},
                {'time': 'now', 'team1_odds': 1.85, 'team2_odds': 1.95}
            ]
            
            return odds_data
            
        except Exception as e:
            logger.error(f"Error searching public KHL odds: {e}")
            return None
    
    def _analyze_khl_odds_patterns(self, odds_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze KHL odds patterns for market insights"""
        analysis = {
            'favorite_team': '',
            'favorite_odds': 0,
            'is_close_match': False,
            'draw_probability': 0,
            'handicap_analysis': {},
            'total_analysis': {},
            'period_analysis': {},
            'odds_movement_trend': '',
            'market_efficiency': 0
        }
        
        try:
            avg_odds = odds_data.get('average_odds', {})
            movement = odds_data.get('movement_history', [])
            
            # Determine favorite
            if avg_odds.get('team1', 0) < avg_odds.get('team2', 0):
                analysis['favorite_team'] = odds_data['team1']
                analysis['favorite_odds'] = avg_odds['team1']
            else:
                analysis['favorite_team'] = odds_data['team2']
                analysis['favorite_odds'] = avg_odds['team2']
            
            # Check if close match
            odds_diff = abs(avg_odds.get('team1', 0) - avg_odds.get('team2', 0))
            analysis['is_close_match'] = odds_diff < 0.15
            
            # Calculate draw probability
            draw_odds = avg_odds.get('draw', 0)
            if draw_odds > 0:
                analysis['draw_probability'] = 1 / draw_odds
            
            # Analyze handicap
            handicap_odds = odds_data.get('handicap_odds', {})
            analysis['handicap_analysis'] = self._analyze_handicap(handicap_odds)
            
            # Analyze total
            total_odds = odds_data.get('total_odds', {})
            analysis['total_analysis'] = self._analyze_total(total_odds)
            
            # Analyze period odds
            period_odds = odds_data.get('period_odds', {})
            analysis['period_analysis'] = self._analyze_period_odds(period_odds)
            
            # Analyze odds movement trend
            if len(movement) >= 2:
                recent_change = movement[-1]['team1_odds'] - movement[-2]['team1_odds']
                if recent_change > 0.02:
                    analysis['odds_movement_trend'] = 'team1_drifting'
                elif recent_change < -0.02:
                    analysis['odds_movement_trend'] = 'team1_strengthening'
                else:
                    analysis['odds_movement_trend'] = 'stable'
            
            # Calculate market efficiency
            bookmaker_count = len(odds_data.get('bookmakers', []))
            if bookmaker_count > 0:
                analysis['market_efficiency'] = min(bookmaker_count / 5.0, 1.0)
            
        except Exception as e:
            logger.warning(f"Error analyzing KHL odds patterns: {e}")
        
        return analysis
    
    def _analyze_handicap(self, handicap_odds: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze handicap odds"""
        analysis = {
            'line': handicap_odds.get('line', 0),
            'team1_value': 0,
            'team2_value': 0,
            'recommended_side': ''
        }
        
        try:
            team1_odds = handicap_odds.get('team1_odds', 0)
            team2_odds = handicap_odds.get('team2_odds', 0)
            
            # Calculate value (simplified)
            if team1_odds > 0:
                analysis['team1_value'] = (1 / team1_odds) * 100 - 50
            if team2_odds > 0:
                analysis['team2_value'] = (1 / team2_odds) * 100 - 50
            
            # Recommend side with better value
            if analysis['team1_value'] > analysis['team2_value']:
                analysis['recommended_side'] = 'team1'
            else:
                analysis['recommended_side'] = 'team2'
            
        except Exception as e:
            logger.warning(f"Error analyzing handicap: {e}")
        
        return analysis
    
    def _analyze_total(self, total_odds: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze total goals odds"""
        analysis = {
            'line': total_odds.get('line', 0),
            'over_value': 0,
            'under_value': 0,
            'recommended_side': '',
            'expected_goals': 0
        }
        
        try:
            over_odds = total_odds.get('over_odds', 0)
            under_odds = total_odds.get('under_odds', 0)
            
            # Calculate implied probabilities
            if over_odds > 0 and under_odds > 0:
                over_prob = 1 / over_odds
                under_prob = 1 / under_odds
                
                # Calculate expected goals based on line and probabilities
                line = total_odds.get('line', 5.5)
                analysis['expected_goals'] = line + (over_prob - under_prob) * 2
                
                # Calculate value
                analysis['over_value'] = (over_prob * 100) - 50
                analysis['under_value'] = (under_prob * 100) - 50
                
                # Recommend side
                if analysis['over_value'] > analysis['under_value']:
                    analysis['recommended_side'] = 'over'
                else:
                    analysis['recommended_side'] = 'under'
            
        except Exception as e:
            logger.warning(f"Error analyzing total: {e}")
        
        return analysis
    
    def _analyze_period_odds(self, period_odds: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze period-by-period odds"""
        analysis = {
            'period1_favorite': '',
            'period2_favorite': '',
            'period3_favorite': '',
            'period_patterns': []
        }
        
        try:
            for period in ['period1', 'period2', 'period3']:
                if period in period_odds:
                    period_data = period_odds[period]
                    team1_odds = period_data.get('team1', 0)
                    team2_odds = period_data.get('team2', 0)
                    
                    if team1_odds < team2_odds:
                        analysis[f'{period}_favorite'] = 'team1'
                    else:
                        analysis[f'{period}_favorite'] = 'team2'
                    
                    # Identify patterns
                    if period == 'period1' and min(team1_odds, team2_odds) > 2.5:
                        analysis['period_patterns'].append('conservative_first_period')
                    elif period == 'period3' and max(team1_odds, team2_odds) < 2.0:
                        analysis['period_patterns'].append('decisive_third_period')
            
        except Exception as e:
            logger.warning(f"Error analyzing period odds: {e}")
        
        return analysis
    
    async def get_live_odds(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get live odds for ongoing KHL match"""
        try:
            # This would scrape live odds from bookmaker sites
            # For now, return simulated live odds data
            
            live_odds = {
                'match_id': match_id,
                'current_score': {'team1': 2, 'team2': 1},
                'current_period': 2,
                'time_in_period': 456,
                'live_odds': {
                    'team1_win': 1.35,
                    'team2_win': 3.80,
                    'draw': 4.50,
                    'live_handicap': {'line': -1.5, 'team1_odds': 1.55, 'team2_odds': 2.40},
                    'live_total': {'line': 3.5, 'over_odds': 1.75, 'under_odds': 2.05}
                },
                'next_period_odds': {
                    'period3': {'team1': 1.95, 'team2': 2.25, 'draw': 3.40}
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return live_odds
            
        except Exception as e:
            logger.error(f"Error getting live KHL odds for {match_id}: {e}")
            return None


async def update_khl_odds():
    """Update odds for KHL matches"""
    async with KHLOddsParser() as parser:
        # Get matches from database
        from storage.database import get_pending_khl_matches
        matches = await get_pending_khl_matches()
        
        updated_matches = []
        
        for match in matches:
            odds_data = await parser.get_khl_odds(match['team1'], match['team2'])
            
            if odds_data:
                match['odds'] = odds_data
                updated_matches.append(match)
        
        # Store updated matches
        from storage.database import store_khl_odds
        await store_khl_odds(updated_matches)
        
        return updated_matches


async def khl_odds_task():
    """KHL odds update task for scheduler"""
    logger.info("Starting KHL odds update")
    
    try:
        matches = await update_khl_odds()
        logger.info(f"Updated odds for {len(matches)} KHL matches")
        
    except Exception as e:
        logger.error(f"KHL odds task failed: {e}")


def setup_khl_odds_tasks(scheduler):
    """Setup KHL odds tasks in scheduler"""
    scheduler.add_task('khl_odds_update', khl_odds_task, 600)  # Every 10 minutes
    logger.info("KHL odds tasks setup complete")
