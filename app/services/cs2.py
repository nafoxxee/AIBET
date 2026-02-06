"""
AIBET Analytics Platform - CS2 Service
Public CS2 match parsing from HLTV and other sources
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


class CS2Service:
    """CS2 data service with multi-source parsing"""
    
    def __init__(self):
        self.base_url = SERVICE_CONFIG["cs2"]["base_url"]
        self.ttl = SERVICE_CONFIG["cs2"]["ttl"]
        self.session = None
        
        # Fallback sources
        self.fallback_sources = [
            {"name": "hltv", "url": "https://hltv.org"},
            {"name": "faceit", "url": "https://faceit.com"},
            {"name": "esea", "url": "https://play.esea.net"}
        ]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9"
                }
            )
        return self.session
    
    async def _make_request(self, url: str) -> Optional[str]:
        """Make HTTP request"""
        await metrics.increment_requests("cs2_scrape")
        
        try:
            session = await self._get_session()
            
            start_time = asyncio.get_event_loop().time()
            
            async with session.get(url) as response:
                await metrics.record_response_time(
                    asyncio.get_event_loop().time() - start_time
                )
                
                if response.status == 200:
                    content = await response.text()
                    logger.debug(f"CS2 scrape success: {url}")
                    return content
                else:
                    logger.error(f"CS2 scrape error: {url} - {response.status}")
                    await metrics.record_source_failure("cs2_scrape")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"CS2 scrape timeout: {url}")
            await metrics.record_source_failure("cs2_scrape")
            return None
        except Exception as e:
            logger.error(f"CS2 scrape exception: {url} - {e}")
            await metrics.record_source_failure("cs2_scrape")
            return None
    
    def _parse_upcoming_matches(self, html: str) -> List[Dict[str, Any]]:
        """Parse upcoming matches from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            matches = []
            
            # Look for match elements (adjust based on actual HLTV structure)
            match_elements = soup.find_all('div', class_='match') or soup.find_all('a', class_='match')
            
            for element in match_elements[:50]:  # Limit to 50 matches
                try:
                    # Extract team names
                    teams = []
                    team_elements = element.find_all('div', class_='team') or element.find_all('span', class_='team')
                    
                    for team_elem in team_elements[:2]:  # Take first 2 teams
                        team_name = team_elem.get_text(strip=True)
                        if team_name:
                            teams.append(team_name)
                    
                    if len(teams) < 2:
                        continue
                    
                    # Extract date and time
                    time_element = element.find('div', class_='time') or element.find('span', class_='time')
                    time_text = time_element.get_text(strip=True) if time_element else ""
                    
                    # Parse datetime
                    start_time = datetime.utcnow()  # Fallback
                    if time_text:
                        from app.utils.time import time_utils
                        start_time = time_utils.parse_datetime(time_text, datetime.utcnow())
                    
                    # Extract format (BO1, BO3, etc.)
                    format_element = element.find('div', class_='format') or element.find('span', class_='format')
                    format_text = format_element.get_text(strip=True) if format_element else "BO1"
                    best_of = 1
                    if "BO3" in format_text:
                        best_of = 3
                    elif "BO5" in format_text:
                        best_of = 5
                    
                    # Extract status
                    status_element = element.find('div', class_='status') or element.find('span', class_='status')
                    status = status_element.get_text(strip=True).lower() if status_element else "scheduled"
                    
                    if "live" in status:
                        status = "live"
                    elif "finished" in status or "over" in status:
                        status = "finished"
                    else:
                        status = "scheduled"
                    
                    match_data = {
                        "teams": teams,
                        "start_time": start_time,
                        "status": status,
                        "best_of": best_of
                    }
                    
                    matches.append(match_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing CS2 match element: {e}")
                    continue
            
            return matches
            
        except Exception as e:
            logger.error(f"Error parsing CS2 HTML: {e}")
            return []
    
    def _parse_results(self, html: str) -> List[Dict[str, Any]]:
        """Parse match results from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            matches = []
            
            # Look for result elements
            result_elements = soup.find_all('div', class_='result') or soup.find_all('tr', class_='result')
            
            for element in result_elements[:50]:
                try:
                    # Extract teams
                    teams = []
                    team_elements = element.find_all('div', class_='team') or element.find_all('td', class_='team')
                    
                    for team_elem in team_elements[:2]:
                        team_name = team_elem.get_text(strip=True)
                        if team_name:
                            teams.append(team_name)
                    
                    if len(teams) < 2:
                        continue
                    
                    # Extract scores
                    score_elements = element.find_all('div', class_='score') or element.find_all('span', class_='score')
                    scores = {}
                    
                    if len(score_elements) >= 2:
                        scores[teams[0]] = int(score_elements[0].get_text(strip=True) or "0")
                        scores[teams[1]] = int(score_elements[1].get_text(strip=True) or "0")
                    
                    # Extract date
                    date_element = element.find('div', class_='date') or element.find('td', class_='date')
                    date_text = date_element.get_text(strip=True) if date_element else ""
                    
                    start_time = datetime.utcnow()
                    if date_text:
                        from app.utils.time import time_utils
                        start_time = time_utils.parse_datetime(date_text, datetime.utcnow())
                    
                    match_data = {
                        "teams": teams,
                        "start_time": start_time,
                        "status": "finished",
                        "score": {"final": scores},
                        "best_of": 1
                    }
                    
                    matches.append(match_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing CS2 result element: {e}")
                    continue
            
            return matches
            
        except Exception as e:
            logger.error(f"Error parsing CS2 results HTML: {e}")
            return []
    
    async def get_upcoming(self, limit: int = 50) -> List[LeagueMatch]:
        """Get CS2 upcoming matches"""
        cache = await cache_manager.get_cache("cs2")
        
        # Try cache first
        cached_data = await cache.get("upcoming")
        if cached_data:
            await metrics.increment_cache_hits()
            logger.debug("CS2 upcoming from cache")
            return cached_data
        
        await metrics.increment_cache_misses()
        
        # Try primary source first
        try:
            url = f"{self.base_url}/matches"
            html = await self._make_request(url)
            
            if html:
                raw_matches = self._parse_upcoming_matches(html)
            else:
                # Try fallback sources
                raw_matches = []
                for source in self.fallback_sources:
                    try:
                        fallback_url = f"{source['url']}/matches"
                        fallback_html = await self._make_request(fallback_url)
                        if fallback_html:
                            fallback_matches = self._parse_upcoming_matches(fallback_html)
                            raw_matches.extend(fallback_matches)
                            logger.info(f"Used fallback source: {source['name']}")
                            break
                    except Exception as e:
                        logger.warning(f"Fallback source {source['name']} failed: {e}")
                        continue
            
            # Normalize matches
            matches = []
            for match_data in raw_matches[:limit]:
                try:
                    normalized_match = await data_normalizer.normalize_match(match_data, "CS2")
                    matches.append(normalized_match)
                except Exception as e:
                    logger.error(f"Error normalizing CS2 match: {e}")
                    continue
            
            # Cache results
            await cache.set("upcoming", matches, self.ttl)
            logger.info(f"Loaded {len(matches)} CS2 upcoming matches")
            
            return matches
            
        except Exception as e:
            logger.error(f"Error getting CS2 upcoming matches: {e}")
            return []
    
    async def get_results(self, limit: int = 50) -> List[LeagueMatch]:
        """Get CS2 match results"""
        cache = await cache_manager.get_cache("cs2")
        
        # Try cache first
        cached_data = await cache.get("results")
        if cached_data:
            await metrics.increment_cache_hits()
            logger.debug("CS2 results from cache")
            return cached_data
        
        await metrics.increment_cache_misses()
        
        # Fetch from primary source
        try:
            url = f"{self.base_url}/results"
            html = await self._make_request(url)
            
            if not html:
                return []
            
            # Parse results
            raw_matches = self._parse_results(html)
            
            # Normalize matches
            matches = []
            for match_data in raw_matches[:limit]:
                try:
                    normalized_match = await data_normalizer.normalize_match(match_data, "CS2")
                    matches.append(normalized_match)
                except Exception as e:
                    logger.error(f"Error normalizing CS2 result: {e}")
                    continue
            
            # Cache results
            await cache.set("results", matches, self.ttl)
            logger.info(f"Loaded {len(matches)} CS2 results")
            
            return matches
            
        except Exception as e:
            logger.error(f"Error getting CS2 results: {e}")
            return []
    
    async def get_matches(self, match_id: Optional[str] = None) -> List[LeagueMatch]:
        """Get CS2 matches (upcoming + results)"""
        if match_id:
            # Search in upcoming and results
            all_matches = []
            all_matches.extend(await self.get_upcoming())
            all_matches.extend(await self.get_results())
            
            return [match for match in all_matches if match.global_match_id == match_id]
        else:
            # Return all matches
            upcoming = await self.get_upcoming()
            results = await self.get_results()
            return upcoming + results
    
    async def get_tournaments(self) -> List[Dict[str, Any]]:
        """Get CS2 tournaments"""
        cache = await cache_manager.get_cache("cs2")
        
        # Try cache first
        cached_data = await cache.get("tournaments")
        if cached_data:
            await metrics.increment_cache_hits()
            return cached_data
        
        await metrics.increment_cache_misses()
        
        # Fetch tournaments
        try:
            url = f"{self.base_url}/tournaments"
            html = await self._make_request(url)
            
            if not html:
                return []
            
            # Parse tournaments (simplified)
            soup = BeautifulSoup(html, 'html.parser')
            tournaments = []
            
            tournament_elements = soup.find_all('div', class_='tournament') or soup.find_all('a', class_='tournament')
            
            for element in tournament_elements[:20]:  # Limit to 20 tournaments
                try:
                    name_element = element.find('div', class_='name') or element.find('span', class_='name')
                    name = name_element.get_text(strip=True) if name_element else "Unknown"
                    
                    tournaments.append({
                        "name": name,
                        "url": element.get('href', '') if element.name == 'a' else ''
                    })
                except Exception as e:
                    logger.error(f"Error parsing CS2 tournament: {e}")
                    continue
            
            # Cache results
            await cache.set("tournaments", tournaments, self.ttl)
            logger.info(f"Loaded {len(tournaments)} CS2 tournaments")
            
            return tournaments
            
        except Exception as e:
            logger.error(f"Error getting CS2 tournaments: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for CS2 service"""
        try:
            # Try to fetch matches page
            url = f"{self.base_url}/matches"
            html = await self._make_request(url)
            
            return {
                "status": "healthy" if html else "unhealthy",
                "last_check": logger.info("CS2 service health checked"),
                "website_accessible": html is not None,
                "fallback_sources": len(self.fallback_sources)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": logger.error(f"CS2 service health error: {e}")
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()


# Global CS2 service instance
cs2_service = CS2Service()
