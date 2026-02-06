"""
AIBET Analytics Platform - NHL Service
Public NHL JSON API (api-web.nhle.com)
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

import aiohttp
from app.config import SERVICE_CONFIG
from app.cache import cache_manager
from app.metrics import metrics
from app.schemas import LeagueMatch
from app.normalizer import data_normalizer
from app.logging import setup_logging

logger = setup_logging(__name__)


class NHLService:
    """NHL data service using public API"""
    
    def __init__(self):
        self.base_url = SERVICE_CONFIG["nhl"]["base_url"]
        self.ttl = SERVICE_CONFIG["nhl"]["ttl"]
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "AIBET-Analytics/1.0",
                    "Accept": "application/json",
                    "Accept-Language": "en-US"
                }
            )
        return self.session
    
    async def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make HTTP request to NHL API"""
        await metrics.increment_requests("nhl_api")
        
        try:
            session = await self._get_session()
            url = f"{self.base_url}{endpoint}"
            
            start_time = asyncio.get_event_loop().time()
            
            async with session.get(url) as response:
                await metrics.record_response_time(
                    asyncio.get_event_loop().time() - start_time
                )
                
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"NHL API success: {endpoint}")
                    return data
                else:
                    logger.error(f"NHL API error: {endpoint} - {response.status}")
                    await metrics.record_source_failure("nhl_api")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"NHL API timeout: {endpoint}")
            await metrics.record_source_failure("nhl_api")
            return None
        except Exception as e:
            logger.error(f"NHL API exception: {endpoint} - {e}")
            await metrics.record_source_failure("nhl_api")
            return None
    
    async def get_schedule(self, limit: int = 50) -> List[LeagueMatch]:
        """Get NHL schedule"""
        cache = await cache_manager.get_cache("nhl")
        
        # Try cache first
        cached_data = await cache.get("schedule")
        if cached_data:
            await metrics.increment_cache_hits()
            logger.debug("NHL schedule from cache")
            return cached_data
        
        await metrics.increment_cache_misses()
        
        # Fetch from API
        try:
            data = await self._make_request("/v1/schedule")
            if not data:
                return []
            
            matches = []
            games = data.get("games", [])
            
            for game in games[:limit]:
                try:
                    # Extract match data
                    match_data = {
                        "teams": [
                            game.get("awayTeam", {}).get("name", "Unknown"),
                            game.get("homeTeam", {}).get("name", "Unknown")
                        ],
                        "start_time": game.get("startTimeUTC"),
                        "status": game.get("gameState", "scheduled"),
                        "score": {
                            "current": {
                                game.get("awayTeam", {}).get("name", "Unknown"): game.get("awayTeam", {}).get("score", 0),
                                game.get("homeTeam", {}).get("name", "Unknown"): game.get("homeTeam", {}).get("score", 0)
                            } if game.get("gameState") == "LIVE" else None,
                            "final": {
                                game.get("awayTeam", {}).get("name", "Unknown"): game.get("awayTeam", {}).get("score", 0),
                                game.get("homeTeam", {}).get("name", "Unknown"): game.get("homeTeam", {}).get("score", 0)
                            } if game.get("gameState") == "FINAL" else None
                        },
                        "best_of": 1
                    }
                    
                    # Normalize match
                    normalized_match = await data_normalizer.normalize_match(match_data, "NHL")
                    matches.append(normalized_match)
                    
                except Exception as e:
                    logger.error(f"Error processing NHL game: {e}")
                    continue
            
            # Cache results
            await cache.set("schedule", matches, self.ttl)
            logger.info(f"Loaded {len(matches)} NHL matches from API")
            
            return matches
            
        except Exception as e:
            logger.error(f"Error getting NHL schedule: {e}")
            return []
    
    async def get_games(self, game_id: Optional[str] = None) -> List[LeagueMatch]:
        """Get NHL games"""
        if game_id:
            # Get specific game
            cache = await cache_manager.get_cache("nhl")
            cached_game = await cache.get(f"game_{game_id}")
            
            if cached_game:
                await metrics.increment_cache_hits()
                return [cached_game]
            
            await metrics.increment_cache_misses()
            data = await self._make_request(f"/v1/game/{game_id}")
            
            if data:
                match_data = {
                    "teams": [
                        data.get("awayTeam", {}).get("name", "Unknown"),
                        data.get("homeTeam", {}).get("name", "Unknown")
                    ],
                    "start_time": data.get("startTimeUTC"),
                    "status": data.get("gameState", "scheduled"),
                    "score": {
                        "current": {
                            data.get("awayTeam", {}).get("name", "Unknown"): data.get("awayTeam", {}).get("score", 0),
                            data.get("homeTeam", {}).get("name", "Unknown"): data.get("homeTeam", {}).get("score", 0)
                        } if data.get("gameState") == "LIVE" else None,
                        "final": {
                            data.get("awayTeam", {}).get("name", "Unknown"): data.get("awayTeam", {}).get("score", 0),
                            data.get("homeTeam", {}).get("name", "Unknown"): data.get("homeTeam", {}).get("score", 0)
                        } if data.get("gameState") == "FINAL" else None
                    }
                }
                
                normalized_match = await data_normalizer.normalize_match(match_data, "NHL")
                await cache.set(f"game_{game_id}", normalized_match, self.ttl)
                
                return [normalized_match]
            
            return []
        else:
            # Get all games (same as schedule)
            return await self.get_schedule()
    
    async def get_standings(self) -> Dict[str, Any]:
        """Get NHL standings"""
        cache = await cache_manager.get_cache("nhl")
        
        # Try cache first
        cached_data = await cache.get("standings")
        if cached_data:
            await metrics.increment_cache_hits()
            return cached_data
        
        await metrics.increment_cache_misses()
        
        # Fetch from API
        data = await self._make_request("/v1/standings")
        
        if data:
            await cache.set("standings", data, self.ttl)
            logger.info("Loaded NHL standings from API")
        
        return data or {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for NHL service"""
        try:
            # Try to fetch a small amount of data
            data = await self._make_request("/v1/schedule")
            
            return {
                "status": "healthy" if data else "unhealthy",
                "last_check": logger.info("NHL service health checked"),
                "api_accessible": data is not None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": logger.error(f"NHL service health error: {e}")
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()


# Global NHL service instance
nhl_service = NHLService()
