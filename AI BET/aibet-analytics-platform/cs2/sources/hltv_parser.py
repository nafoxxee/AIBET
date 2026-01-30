import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class HLTVParser:
    """Parser for HLTV.org CS2 matches and data"""
    
    BASE_URL = "https://www.hltv.org"
    
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
    
    async def get_upcoming_matches(self) -> List[Dict[str, Any]]:
        """Get upcoming CS2 matches from HLTV"""
        try:
            url = f"{self.BASE_URL}/matches"
            async with self.session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
            
            matches = []
            
            # Find match elements
            match_elements = soup.find_all('a', class_='match')
            
            for element in match_elements[:20]:  # Limit to first 20 matches
                try:
                    match_data = self._parse_match_element(element)
                    if match_data:
                        matches.append(match_data)
                except Exception as e:
                    logger.warning(f"Error parsing match element: {e}")
                    continue
            
            logger.info(f"Found {len(matches)} upcoming matches")
            return matches
            
        except Exception as e:
            logger.error(f"Error fetching upcoming matches: {e}")
            return []
    
    def _parse_match_element(self, element) -> Optional[Dict[str, Any]]:
        """Parse individual match element from HLTV"""
        try:
            # Extract teams
            team_elements = element.find_all('div', class_='team')
            if len(team_elements) < 2:
                return None
            
            team1 = team_elements[0].text.strip()
            team2 = team_elements[1].text.strip()
            
            # Extract match time
            time_element = element.find('div', class_='time')
            match_time = time_element.text.strip() if time_element else ""
            
            # Extract tournament
            tournament_element = element.find('div', class_='event-name')
            tournament = tournament_element.text.strip() if tournament_element else "Unknown"
            
            # Extract match ID from URL
            match_url = element.get('href', '')
            match_id = self._extract_match_id(match_url)
            
            # Determine tournament tier
            tier = self._determine_tournament_tier(tournament)
            
            return {
                'match_id': match_id,
                'team1': team1,
                'team2': team2,
                'tournament': tournament,
                'tier': tier,
                'time': match_time,
                'url': f"{self.BASE_URL}{match_url}",
                'source': 'hltv',
                'parsed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Error parsing match element: {e}")
            return None
    
    def _extract_match_id(self, url: str) -> str:
        """Extract match ID from HLTV URL"""
        match = re.search(r'/matches/(\d+)', url)
        return match.group(1) if match else ""
    
    def _determine_tournament_tier(self, tournament: str) -> str:
        """Determine tournament tier based on name"""
        tournament_lower = tournament.lower()
        
        # S-tier tournaments
        s_tier_keywords = ['major', 'iem katowice', 'iem cologne', 'blast world final', 'pgl major']
        if any(keyword in tournament_lower for keyword in s_tier_keywords):
            return 'S'
        
        # A-tier tournaments
        a_tier_keywords = ['blast', 'iem', 'esl pro league', 'pgl', 'dreamhack', 'esl one']
        if any(keyword in tournament_lower for keyword in a_tier_keywords):
            return 'A'
        
        # B-tier tournaments
        b_tier_keywords = ['esl challenger', 'pinnacle', 'cc', 'elisa', 'thunderpick']
        if any(keyword in tournament_lower for keyword in b_tier_keywords):
            return 'B'
        
        # C-tier and below
        return 'C'
    
    async def get_match_details(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed match information including lineups"""
        try:
            url = f"{self.BASE_URL}/matches/{match_id}"
            async with self.session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
            
            # Extract lineups
            lineup_data = self._extract_lineups(soup)
            
            # Extract additional match info
            match_info = {
                'match_id': match_id,
                'lineups': lineup_data,
                'stand_ins': self._detect_stand_ins(lineup_data),
                'map_pool': self._extract_map_pool(soup),
                'format': self._extract_match_format(soup),
                'updated_at': datetime.now().isoformat()
            }
            
            return match_info
            
        except Exception as e:
            logger.error(f"Error fetching match details for {match_id}: {e}")
            return None
    
    def _extract_lineups(self, soup) -> Dict[str, List[Dict[str, str]]]:
        """Extract team lineups from match page"""
        lineups = {'team1': [], 'team2': []}
        
        try:
            # Find lineup containers
            lineup_containers = soup.find_all('div', class_='lineup')
            
            for i, container in enumerate(lineup_containers[:2]):
                team_key = 'team1' if i == 0 else 'team2'
                player_elements = container.find_all('div', class_='player')
                
                for player_elem in player_elements:
                    player_name = player_elem.text.strip()
                    player_country = self._extract_player_country(player_elem)
                    
                    lineups[team_key].append({
                        'name': player_name,
                        'country': player_country
                    })
        
        except Exception as e:
            logger.warning(f"Error extracting lineups: {e}")
        
        return lineups
    
    def _detect_stand_ins(self, lineups: Dict[str, List[Dict[str, str]]]) -> Dict[str, bool]:
        """Detect if teams have stand-ins"""
        result = {'team1': False, 'team2': False}
        
        for team_key in ['team1', 'team2']:
            if len(lineups.get(team_key, [])) < 5:  # Less than 5 players indicates stand-ins
                result[team_key] = True
        
        return result
    
    def _extract_player_country(self, player_elem) -> str:
        """Extract player country from flag element"""
        try:
            flag_elem = player_elem.find('img')
            if flag_elem:
                alt_text = flag_elem.get('alt', '')
                return alt_text.split()[-1] if alt_text else "Unknown"
        except:
            pass
        return "Unknown"
    
    def _extract_map_pool(self, soup) -> List[str]:
        """Extract map pool from match page"""
        try:
            map_elements = soup.find_all('div', class_='map')
            maps = []
            for map_elem in map_elements:
                map_name = map_elem.text.strip()
                if map_name and map_name not in maps:
                    maps.append(map_name)
            return maps
        except:
            return ['de_dust2', 'de_mirage', 'de_inferno', 'de_overpass', 'de_nuke', 'de_ancient', 'de_vertigo']
    
    def _extract_match_format(self, soup) -> str:
        """Extract match format (BO1, BO3, BO5)"""
        try:
            format_element = soup.find('div', class_='format')
            if format_element:
                return format_element.text.strip()
        except:
            pass
        return "BO3"  # Default assumption


async def parse_cs2_matches():
    """Main function to parse CS2 matches"""
    async with HLTVParser() as parser:
        matches = await parser.get_upcoming_matches()
        
        # Get detailed info for top matches
        detailed_matches = []
        for match in matches[:5]:  # Limit to top 5 matches
            details = await parser.get_match_details(match['match_id'])
            if details:
                match.update(details)
            detailed_matches.append(match)
        
        return detailed_matches


async def cs2_parsing_task():
    """CS2 parsing task for scheduler"""
    logger.info("Starting CS2 match parsing")
    
    try:
        matches = await parse_cs2_matches()
        
        # Store matches in database
        from storage.database import store_cs2_matches
        await store_cs2_matches(matches)
        
        # Trigger analysis
        from cs2.analysis.scenarios import analyze_cs2_matches
        analysis_results = await analyze_cs2_matches(matches)
        
        # Send to Telegram if analysis found scenarios
        if analysis_results:
            from app.main import telegram_sender
            await telegram_sender.send_cs2_analysis(analysis_results)
        
        logger.info(f"CS2 parsing completed. Processed {len(matches)} matches")
        
    except Exception as e:
        logger.error(f"CS2 parsing task failed: {e}")


def setup_cs2_tasks(scheduler):
    """Setup CS2 tasks in scheduler"""
    scheduler.add_task('cs2_parsing', cs2_parsing_task, 300)  # Every 5 minutes
    logger.info("CS2 tasks setup complete")
