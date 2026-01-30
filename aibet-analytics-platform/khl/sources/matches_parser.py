import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from bs4 import BeautifulSoup
import re
import json

logger = logging.getLogger(__name__)


class KHLMatchesParser:
    """Parser for KHL matches from public sources"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_urls = [
            'https://www.flashscore.com/hockey/russia/khl/',
            'https://www.sofascore.com/tournament/khl/10069'
        ]
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_khl_matches(self) -> List[Dict[str, Any]]:
        """Get KHL matches from public sources"""
        try:
            all_matches = []
            
            # Try multiple sources
            for url in self.base_urls:
                matches = await self._parse_source(url)
                all_matches.extend(matches)
            
            # Remove duplicates by match_id
            unique_matches = {}
            for match in all_matches:
                match_id = match.get('match_id', '')
                if match_id and match_id not in unique_matches:
                    unique_matches[match_id] = match
            
            matches_list = list(unique_matches.values())
            logger.info(f"Found {len(matches_list)} unique KHL matches")
            
            return matches_list
            
        except Exception as e:
            logger.error(f"Error getting KHL matches: {e}")
            return []
    
    async def _parse_source(self, url: str) -> List[Dict[str, Any]]:
        """Parse matches from specific source"""
        try:
            async with self.session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
            
            matches = []
            
            # This is a simplified implementation - in production, you would
            # parse the actual HTML structure of these websites
            
            # Simulate matches data (replace with actual parsing)
            if 'flashscore' in url:
                matches = self._parse_flashscore_matches(soup)
            elif 'sofascore' in url:
                matches = self._parse_sofascore_matches(soup)
            
            return matches
            
        except Exception as e:
            logger.warning(f"Error parsing source {url}: {e}")
            return []
    
    def _parse_flashscore_matches(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse matches from Flashscore"""
        # Simulated data - replace with actual parsing
        return [
            {
                'match_id': 'khl_001',
                'team1': 'SKA Saint Petersburg',
                'team2': 'CSKA Moscow',
                'date': '2024-01-29',
                'time': '18:00',
                'venue': 'Ice Palace Saint Petersburg',
                'league': 'KHL',
                'season': '2023-24',
                'status': 'upcoming',
                'source': 'flashscore',
                'parsed_at': datetime.now().isoformat()
            },
            {
                'match_id': 'khl_002',
                'team1': 'Ak Bars Kazan',
                'team2': 'Metallurg Magnitogorsk',
                'date': '2024-01-29',
                'time': '19:30',
                'venue': 'TatNeft Arena',
                'league': 'KHL',
                'season': '2023-24',
                'status': 'upcoming',
                'source': 'flashscore',
                'parsed_at': datetime.now().isoformat()
            }
        ]
    
    def _parse_sofascore_matches(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse matches from SofaScore"""
        # Simulated data - replace with actual parsing
        return [
            {
                'match_id': 'khl_003',
                'team1': 'Lokomotiv Yaroslavl',
                'team2': 'Dynamo Moscow',
                'date': '2024-01-29',
                'time': '17:00',
                'venue': 'Arena 2000',
                'league': 'KHL',
                'season': '2023-24',
                'status': 'upcoming',
                'source': 'sofascore',
                'parsed_at': datetime.now().isoformat()
            }
        ]
    
    async def get_match_details(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed match information"""
        try:
            # This would fetch detailed match information
            # For now, return simulated data
            
            details = {
                'match_id': match_id,
                'team1_stats': {
                    'recent_form': ['W', 'W', 'L', 'W', 'D'],
                    'home_record': {'wins': 12, 'losses': 3, 'ot_losses': 2},
                    'away_record': {'wins': 8, 'losses': 5, 'ot_losses': 3},
                    'goals_for': 87,
                    'goals_against': 65,
                    'power_play_percentage': 22.5,
                    'penalty_kill_percentage': 85.2
                },
                'team2_stats': {
                    'recent_form': ['L', 'W', 'W', 'L', 'W'],
                    'home_record': {'wins': 10, 'losses': 4, 'ot_losses': 3},
                    'away_record': {'wins': 10, 'losses': 6, 'ot_losses': 1},
                    'goals_for': 79,
                    'goals_against': 70,
                    'power_play_percentage': 19.8,
                    'penalty_kill_percentage': 82.7
                },
                'head_to_head': {
                    'meetings': 45,
                    'team1_wins': 23,
                    'team2_wins': 20,
                    'ot_losses': 2,
                    'last_5_games': ['W', 'L', 'W', 'L', 'D']
                },
                'match_importance': self._calculate_match_importance(match_id),
                'updated_at': datetime.now().isoformat()
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting match details for {match_id}: {e}")
            return None
    
    def _calculate_match_importance(self, match_id: str) -> float:
        """Calculate match importance score"""
        try:
            # Simulate importance calculation based on teams and context
            # In production, this would consider playoff implications, rivalries, etc.
            
            # Base importance for KHL matches
            base_importance = 0.6
            
            # Adjust based on teams (top teams get higher importance)
            top_teams = {
                'SKA Saint Petersburg', 'CSKA Moscow', 'Ak Bars Kazan',
                'Metallurg Magnitogorsk', 'Lokomotiv Yaroslavl', 'Dynamo Moscow'
            }
            
            # This would be extracted from match data
            importance = base_importance
            
            return min(importance, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating match importance: {e}")
            return 0.6
    
    def determine_home_advantage(self, match_data: Dict[str, Any]) -> float:
        """Determine home advantage factor"""
        try:
            venue = match_data.get('venue', '')
            team1 = match_data.get('team1', '')
            
            # Check if team1 is playing at home (simplified)
            if any(city in venue.lower() for city in ['st. petersburg', 'saint petersburg']) and 'ska' in team1.lower():
                return 0.15  # Strong home advantage
            elif any(city in venue.lower() for city in ['moscow']) and 'cska' in team1.lower():
                return 0.12  # Moderate home advantage
            elif any(city in venue.lower() for city in ['kazan']) and 'ak bars' in team1.lower():
                return 0.13  # Moderate home advantage
            else:
                return 0.08  # Standard home advantage
                
        except Exception as e:
            logger.warning(f"Error determining home advantage: {e}")
            return 0.08


async def parse_khl_matches():
    """Main function to parse KHL matches"""
    async with KHLMatchesParser() as parser:
        matches = await parser.get_khl_matches()
        
        # Get detailed info for matches
        detailed_matches = []
        for match in matches:
            details = await parser.get_match_details(match['match_id'])
            if details:
                match.update(details)
            
            # Add home advantage calculation
            match['home_advantage'] = parser.determine_home_advantage(match)
            
            detailed_matches.append(match)
        
        return detailed_matches


async def khl_parsing_task():
    """KHL parsing task for scheduler"""
    logger.info("Starting KHL match parsing")
    
    try:
        matches = await parse_khl_matches()
        
        # Store matches in database
        from storage.database import store_khl_matches
        await store_khl_matches(matches)
        
        # Trigger analysis
        from khl.analysis.scenarios import analyze_khl_matches
        analysis_results = await analyze_khl_matches(matches)
        
        # Send to Telegram if analysis found scenarios
        if analysis_results:
            from app.main import telegram_sender
            await telegram_sender.send_khl_analysis(analysis_results)
        
        logger.info(f"KHL parsing completed. Processed {len(matches)} matches")
        
    except Exception as e:
        logger.error(f"KHL parsing task failed: {e}")


def setup_khl_tasks(scheduler):
    """Setup KHL tasks in scheduler"""
    scheduler.add_task('khl_parsing', khl_parsing_task, 300)  # Every 5 minutes
    logger.info("KHL tasks setup complete")
