import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
from bs4 import BeautifulSoup
import re
import json

logger = logging.getLogger(__name__)


class OddsParser:
    """Parser for public bookmaker odds data"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_cs2_odds(self, team1: str, team2: str) -> Optional[Dict[str, Any]]:
        """Get odds for CS2 match between two teams"""
        try:
            # Search for odds on multiple public sources
            odds_data = await self._search_public_odds(team1, team2)
            
            if odds_data:
                # Analyze odds patterns
                analysis = self._analyze_odds_patterns(odds_data)
                odds_data['analysis'] = analysis
                
                return odds_data
            
        except Exception as e:
            logger.error(f"Error getting odds for {team1} vs {team2}: {e}")
        
        return None
    
    async def _search_public_odds(self, team1: str, team2: str) -> Optional[Dict[str, Any]]:
        """Search odds on public betting websites"""
        # This is a simplified implementation - in production, you would scrape
        # actual betting websites that allow public access
        
        try:
            # Simulate odds data (replace with actual scraping)
            odds_data = {
                'team1': team1,
                'team2': team2,
                'bookmakers': [],
                'average_odds': {},
                'public_money': {},
                'movement_history': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Simulate multiple bookmakers
            bookmakers_data = [
                {'name': 'BookmakerA', 'team1_odds': 1.25, 'team2_odds': 3.80, 'draw_odds': None},
                {'name': 'BookmakerB', 'team1_odds': 1.22, 'team2_odds': 3.95, 'draw_odds': None},
                {'name': 'BookmakerC', 'team1_odds': 1.28, 'team2_odds': 3.70, 'draw_odds': None},
            ]
            
            for bm in bookmakers_data:
                odds_data['bookmakers'].append(bm)
            
            # Calculate average odds
            team1_odds = [bm['team1_odds'] for bm in bookmakers_data]
            team2_odds = [bm['team2_odds'] for bm in bookmakers_data]
            
            odds_data['average_odds'] = {
                'team1': sum(team1_odds) / len(team1_odds),
                'team2': sum(team2_odds) / len(team2_odds)
            }
            
            # Simulate public money distribution
            odds_data['public_money'] = {
                'team1_percentage': 75.5,  # Heavy favorite
                'team2_percentage': 24.5
            }
            
            # Simulate odds movement
            odds_data['movement_history'] = [
                {'time': '2h ago', 'team1_odds': 1.20, 'team2_odds': 4.10},
                {'time': '1h ago', 'team1_odds': 1.23, 'team2_odds': 3.90},
                {'time': 'now', 'team1_odds': 1.25, 'team2_odds': 3.80}
            ]
            
            return odds_data
            
        except Exception as e:
            logger.error(f"Error searching public odds: {e}")
            return None
    
    def _analyze_odds_patterns(self, odds_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze odds patterns for market insights"""
        analysis = {
            'favorite_team': '',
            'favorite_odds': 0,
            'is_heavy_favorite': False,
            'public_bias_detected': False,
            'odds_movement_trend': '',
            'market_efficiency': 0
        }
        
        try:
            avg_odds = odds_data.get('average_odds', {})
            public_money = odds_data.get('public_money', {})
            movement = odds_data.get('movement_history', [])
            
            # Determine favorite
            if avg_odds.get('team1', 0) < avg_odds.get('team2', 0):
                analysis['favorite_team'] = odds_data['team1']
                analysis['favorite_odds'] = avg_odds['team1']
            else:
                analysis['favorite_team'] = odds_data['team2']
                analysis['favorite_odds'] = avg_odds['team2']
            
            # Check if heavy favorite (odds < 1.40)
            analysis['is_heavy_favorite'] = analysis['favorite_odds'] < 1.40
            
            # Check public bias (>70% on one team)
            team1_pct = public_money.get('team1_percentage', 0)
            team2_pct = public_money.get('team2_percentage', 0)
            analysis['public_bias_detected'] = max(team1_pct, team2_pct) > 70
            
            # Analyze odds movement trend
            if len(movement) >= 2:
                recent_change = movement[-1]['team1_odds'] - movement[-2]['team1_odds']
                if recent_change > 0.02:
                    analysis['odds_movement_trend'] = 'favorite_drifting'
                elif recent_change < -0.02:
                    analysis['odds_movement_trend'] = 'favorite_strengthening'
                else:
                    analysis['odds_movement_trend'] = 'stable'
            
            # Calculate market efficiency (simplified)
            bookmaker_count = len(odds_data.get('bookmakers', []))
            if bookmaker_count > 0:
                # More bookmakers = more efficient market
                analysis['market_efficiency'] = min(bookmaker_count / 5.0, 1.0)
            
        except Exception as e:
            logger.warning(f"Error analyzing odds patterns: {e}")
        
        return analysis
    
    async def get_live_odds(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get live odds for ongoing match"""
        try:
            # This would scrape live odds from bookmaker sites
            # For now, return simulated live odds data
            
            live_odds = {
                'match_id': match_id,
                'current_score': {'team1': 12, 'team2': 8},
                'current_map': 'de_mirage',
                'live_odds': {
                    'team1_win': 1.15,
                    'team2_win': 5.20,
                    'total_rounds_over_26.5': 1.85,
                    'total_rounds_under_26.5': 1.95
                },
                'map_progression': {
                    'current_round': 21,
                    'first_half_winner': 'team1',
                    'second_half_starting': True
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return live_odds
            
        except Exception as e:
            logger.error(f"Error getting live odds for {match_id}: {e}")
            return None
    
    async def get_betting_percentages(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get public betting percentages"""
        try:
            # This would scrape public betting data
            betting_data = {
                'match_id': match_id,
                'total_bets': 15420,
                'total_volume': '$2,847,320',
                'team1': {
                    'percentage': 78.5,
                    'volume': '$2,235,130',
                    'bet_count': 12105
                },
                'team2': {
                    'percentage': 21.5,
                    'volume': '$612,190',
                    'bet_count': 3315
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return betting_data
            
        except Exception as e:
            logger.error(f"Error getting betting percentages for {match_id}: {e}")
            return None


async def update_cs2_odds():
    """Update odds for CS2 matches"""
    async with OddsParser() as parser:
        # Get matches from database
        from storage.database import get_pending_cs2_matches
        matches = await get_pending_cs2_matches()
        
        updated_matches = []
        
        for match in matches:
            odds_data = await parser.get_cs2_odds(match['team1'], match['team2'])
            
            if odds_data:
                match['odds'] = odds_data
                updated_matches.append(match)
        
        # Store updated matches
        from storage.database import store_cs2_odds
        await store_cs2_odds(updated_matches)
        
        return updated_matches


async def cs2_odds_task():
    """CS2 odds update task for scheduler"""
    logger.info("Starting CS2 odds update")
    
    try:
        matches = await update_cs2_odds()
        logger.info(f"Updated odds for {len(matches)} CS2 matches")
        
    except Exception as e:
        logger.error(f"CS2 odds task failed: {e}")


def setup_cs2_odds_tasks(scheduler):
    """Setup CS2 odds tasks in scheduler"""
    scheduler.add_task('cs2_odds_update', cs2_odds_task, 600)  # Every 10 minutes
    logger.info("CS2 odds tasks setup complete")
