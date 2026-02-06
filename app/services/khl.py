"""
AIBET Analytics Platform - KHL Service
HTML → JSON parsing with fallback to cache
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
from app.config import SERVICE_CONFIG
from app.cache import cache_manager
from app.metrics import metrics
from app.schemas import LeagueMatch
from app.normalizer import data_normalizer
from app.logging import setup_logging

logger = setup_logging(__name__)


class KHLService:
    """KHL data service with HTML parsing"""
    
    def __init__(self):
        self.base_url = SERVICE_CONFIG["khl"]["base_url"]
        self.ttl = SERVICE_CONFIG["khl"]["ttl"]
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
                }
            )
        return self.session
    
    async def _make_request(self, url: str) -> Optional[str]:
        """Make HTTP request"""
        await metrics.increment_requests("khl_scrape")
        
        try:
            session = await self._get_session()
            
            start_time = asyncio.get_event_loop().time()
            
            async with session.get(url) as response:
                await metrics.record_response_time(
                    asyncio.get_event_loop().time() - start_time
                )
                
                if response.status == 200:
                    content = await response.text()
                    logger.debug(f"KHL scrape success: {url}")
                    return content
                else:
                    logger.error(f"KHL scrape error: {url} - {response.status}")
                    await metrics.record_source_failure("khl_scrape")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"KHL scrape timeout: {url}")
            await metrics.record_source_failure("khl_scrape")
            return None
        except Exception as e:
            logger.error(f"KHL scrape exception: {url} - {e}")
            await metrics.record_source_failure("khl_scrape")
            return None
    
    def _parse_schedule_html(self, html: str) -> List[Dict[str, Any]]:
        """Parse schedule HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            matches = []
            
            # Look for schedule table or match cards
            # This is a simplified parser - adjust based on actual KHL website structure
            match_elements = soup.find_all('div', class_='match-item') or soup.find_all('tr', class_='match-row')
            
            for element in match_elements[:50]:  # Limit to 50 matches
                try:
                    # Extract team names
                    teams = []
                    team_elements = element.find_all('div', class_='team') or element.find_all('td', class_='team')
                    
                    for team_elem in team_elements[:2]:  # Take first 2 teams
                        team_name = team_elem.get_text(strip=True)
                        if team_name:
                            teams.append(team_name)
                    
                    if len(teams) < 2:
                        continue
                    
                    # Extract date and time
                    time_element = element.find('div', class_='time') or element.find('td', class_='time')
                    time_text = time_element.get_text(strip=True) if time_element else ""
                    
                    # Parse datetime (simplified)
                    start_time = datetime.utcnow()  # Fallback
                    if time_text:
                        # Try to parse common Russian date formats
                        from app.utils.time import time_utils
                        start_time = time_utils.parse_datetime(time_text, datetime.utcnow())
                    
                    # Extract status
                    status_element = element.find('div', class_='status') or element.find('td', class_='status')
                    status = status_element.get_text(strip=True).lower() if status_element else "scheduled"
                    
                    if "live" in status or "идет" in status:
                        status = "live"
                    elif "завершен" in status or "finished" in status:
                        status = "finished"
                    else:
                        status = "scheduled"
                    
                    match_data = {
                        "teams": teams,
                        "start_time": start_time,
                        "status": status,
                        "best_of": 1
                    }
                    
                    matches.append(match_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing KHL match element: {e}")
                    continue
            
            return matches
            
        except Exception as e:
            logger.error(f"Error parsing KHL HTML: {e}")
            return []
    
    async def get_schedule(self, limit: int = 50) -> List[LeagueMatch]:
        """Get KHL schedule"""
        cache = await cache_manager.get_cache("khl")
        
        # Try cache first
        cached_data = await cache.get("schedule")
        if cached_data:
            await metrics.increment_cache_hits()
            logger.debug("KHL schedule from cache")
            return cached_data
        
        await metrics.increment_cache_misses()
        
        # Fetch from website
        try:
            url = f"{self.base_url}/calendar"
            html = await self._make_request(url)
            
            if not html:
                logger.warning("KHL HTML not available, using fallback")
                return []
            
            # Parse HTML
            raw_matches = self._parse_schedule_html(html)
            
            # Normalize matches
            matches = []
            for match_data in raw_matches[:limit]:
                try:
                    normalized_match = await data_normalizer.normalize_match(match_data, "KHL")
                    matches.append(normalized_match)
                except Exception as e:
                    logger.error(f"Error normalizing KHL match: {e}")
                    continue
            
            # Cache results
            await cache.set("schedule", matches, self.ttl)
            logger.info(f"Loaded {len(matches)} KHL matches from HTML")
            
            return matches
            
        except Exception as e:
            logger.error(f"Error getting KHL schedule: {e}")
            return []
    
    async def get_games(self, game_id: Optional[str] = None) -> List[LeagueMatch]:
        """Get KHL games"""
        if game_id:
            # For specific games, try to find in schedule
            all_games = await self.get_schedule()
            return [game for match in all_games if match.global_match_id == game_id]
        else:
            # Get all games
            return await self.get_schedule()
    
    async def get_standings(self) -> Dict[str, Any]:
        """Get KHL standings"""
        cache = await cache_manager.get_cache("khl")
        
        # Try cache first
        cached_data = await cache.get("standings")
        if cached_data:
            await metrics.increment_cache_hits()
            return cached_data
        
        await metrics.increment_cache_misses()
        
        # Fetch from website
        try:
            url = f"{self.base_url}/standings"
            html = await self._make_request(url)
            
            if not html:
                return {}
            
            # Parse standings HTML (simplified)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract standings data
            standings = []
            table_rows = soup.find_all('tr', class_='standing-row')
            
            for row in table_rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        standings.append({
                            "position": cells[0].get_text(strip=True),
                            "team": cells[1].get_text(strip=True),
                            "games": cells[2].get_text(strip=True),
                            "points": cells[3].get_text(strip=True)
                        })
                except Exception as e:
                    logger.error(f"Error parsing KHL standings row: {e}")
                    continue
            
            standings_data = {"standings": standings}
            
            # Cache results
            await cache.set("standings", standings_data, self.ttl)
            logger.info("Loaded KHL standings from HTML")
            
            return standings_data
            
        except Exception as e:
            logger.error(f"Error getting KHL standings: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for KHL service"""
        try:
            # Try to fetch schedule page
            url = f"{self.base_url}/calendar"
            html = await self._make_request(url)
            
            return {
                "status": "healthy" if html else "unhealthy",
                "last_check": logger.info("KHL service health checked"),
                "website_accessible": html is not None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": logger.error(f"KHL service health error: {e}")
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()


# Global KHL service instance
khl_service = KHLService()
