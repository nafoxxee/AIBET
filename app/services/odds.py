"""
AIBET Analytics Platform - Odds Service
Pre-match odds analysis and movement tracking
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.config import SERVICE_CONFIG
from app.cache import cache_manager
from app.metrics import metrics
from app.schemas import OddsInfo
from app.logging import setup_logging

logger = setup_logging(__name__)


class OddsService:
    """Odds service for pre-match analysis"""
    
    def __init__(self):
        self.ttl = SERVICE_CONFIG["odds"]["ttl"]
        self.session = None
        
        # Mock odds sources (in production, these would be real bookmakers)
        self.odds_sources = [
            {"name": "mock_bookmaker_1", "base_url": "https://example-odds1.com"},
            {"name": "mock_bookmaker_2", "base_url": "https://example-odds2.com"},
            {"name": "mock_bookmaker_3", "base_url": "https://example-odds3.com"}
        ]
    
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
    
    def _generate_mock_odds(self, teams: List[str], league: str) -> List[OddsInfo]:
        """Generate mock odds for demonstration"""
        import random
        
        odds_list = []
        
        # Generate odds from different sources
        for source in self.odds_sources:
            # Generate realistic odds with some variation
            base_odds = {
                teams[0]: round(random.uniform(1.5, 3.5), 2),
                teams[1]: round(random.uniform(1.5, 3.5), 2),
                "draw": round(random.uniform(2.8, 4.2), 2) if league != "CS2" else None
            }
            
            # Remove None values
            base_odds = {k: v for k, v in base_odds.items() if v is not None}
            
            odds_info = OddsInfo(
                source=source["name"],
                odds=base_odds,
                timestamp=datetime.utcnow(),
                movement=[round(random.uniform(-0.3, 0.3), 2) for _ in range(5)]
            )
            
            odds_list.append(odds_info)
        
        return odds_list
    
    async def get_nhl_odds(self, limit: int = 50) -> List[OddsInfo]:
        """Get NHL odds"""
        cache = await cache_manager.get_cache("odds")
        
        # Try cache first
        cached_data = await cache.get("nhl")
        if cached_data:
            await metrics.increment_cache_hits()
            logger.debug("NHL odds from cache")
            return cached_data
        
        await metrics.increment_cache_misses()
        
        # Generate mock odds (in production, fetch from real sources)
        try:
            # Get some NHL teams for demonstration
            nhl_teams = [
                "Toronto Maple Leafs", "Montreal Canadiens", "New York Rangers",
                "Boston Bruins", "Chicago Blackhawks", "Detroit Red Wings"
            ]
            
            # Generate odds for random team combinations
            odds_list = []
            for i in range(min(limit // 2, 15)):
                teams = random.sample(nhl_teams, 2)
                match_odds = self._generate_mock_odds(teams, "NHL")
                odds_list.extend(match_odds)
            
            # Cache results
            await cache.set("nhl", odds_list, self.ttl)
            logger.info(f"Generated {len(odds_list)} NHL odds")
            
            return odds_list
            
        except Exception as e:
            logger.error(f"Error getting NHL odds: {e}")
            return []
    
    async def get_khl_odds(self, limit: int = 50) -> List[OddsInfo]:
        """Get KHL odds"""
        cache = await cache_manager.get_cache("odds")
        
        # Try cache first
        cached_data = await cache.get("khl")
        if cached_data:
            await metrics.increment_cache_hits()
            logger.debug("KHL odds from cache")
            return cached_data
        
        await metrics.increment_cache_misses()
        
        # Generate mock odds
        try:
            khl_teams = [
                "CSKA Moscow", "SKA Saint Petersburg", "Ak Bars Kazan",
                "Metallurg Magnitogorsk", "Lokomotiv Yaroslavl", "Dinamo Moscow"
            ]
            
            odds_list = []
            for i in range(min(limit // 2, 12)):
                teams = random.sample(khl_teams, 2)
                match_odds = self._generate_mock_odds(teams, "KHL")
                odds_list.extend(match_odds)
            
            # Cache results
            await cache.set("khl", odds_list, self.ttl)
            logger.info(f"Generated {len(odds_list)} KHL odds")
            
            return odds_list
            
        except Exception as e:
            logger.error(f"Error getting KHL odds: {e}")
            return []
    
    async def get_cs2_odds(self, limit: int = 50) -> List[OddsInfo]:
        """Get CS2 odds"""
        cache = await cache_manager.get_cache("odds")
        
        # Try cache first
        cached_data = await cache.get("cs2")
        if cached_data:
            await metrics.increment_cache_hits()
            logger.debug("CS2 odds from cache")
            return cached_data
        
        await metrics.increment_cache_misses()
        
        # Generate mock odds
        try:
            cs2_teams = [
                "Natus Vincere", "FaZe Clan", "G2 Esports", "Team Vitality",
                "Astralis", "Heroic", "Cloud9", "Team Liquid"
            ]
            
            odds_list = []
            for i in range(min(limit // 2, 20)):
                teams = random.sample(cs2_teams, 2)
                match_odds = self._generate_mock_odds(teams, "CS2")
                odds_list.extend(match_odds)
            
            # Cache results
            await cache.set("cs2", odds_list, self.ttl)
            logger.info(f"Generated {len(odds_list)} CS2 odds")
            
            return odds_list
            
        except Exception as e:
            logger.error(f"Error getting CS2 odds: {e}")
            return []
    
    async def analyze_odds_movement(self, odds_list: List[OddsInfo]) -> Dict[str, Any]:
        """Analyze odds movement patterns"""
        if not odds_list:
            return {}
        
        movement_analysis = {
            "total_sources": len(odds_list),
            "avg_movement": 0.0,
            "volatility": "low",
            "trend": "stable"
        }
        
        # Calculate average movement
        all_movements = []
        for odds_info in odds_list:
            if odds_info.movement:
                all_movements.extend(odds_info.movement)
        
        if all_movements:
            import statistics
            movement_analysis["avg_movement"] = statistics.mean(all_movements)
            movement_analysis["volatility"] = (
                "high" if abs(movement_analysis["avg_movement"]) > 0.2 else
                "medium" if abs(movement_analysis["avg_movement"]) > 0.1 else
                "low"
            )
            
            # Determine trend
            if movement_analysis["avg_movement"] > 0.05:
                movement_analysis["trend"] = "rising"
            elif movement_analysis["avg_movement"] < -0.05:
                movement_analysis["trend"] = "falling"
            else:
                movement_analysis["trend"] = "stable"
        
        return movement_analysis
    
    async def get_odds_snapshots(self, league: str, hours_back: int = 24) -> List[OddsInfo]:
        """Get historical odds snapshots"""
        cache = await cache_manager.get_cache("odds")
        
        # Try to get historical data
        snapshot_key = f"{league}_snapshots_{hours_back}"
        cached_snapshots = await cache.get(snapshot_key)
        
        if cached_snapshots:
            await metrics.increment_cache_hits()
            return cached_snapshots
        
        await metrics.increment_cache_misses()
        
        # Generate mock historical snapshots
        try:
            snapshots = []
            current_time = datetime.utcnow()
            
            # Generate snapshots for different time points
            for hours_ago in range(0, hours_back, 6):  # Every 6 hours
                snapshot_time = current_time - timedelta(hours=hours_ago)
                
                # Generate odds for this time point
                if league.lower() == "nhl":
                    snapshot_odds = await self.get_nhl_odds(limit=10)
                elif league.lower() == "khl":
                    snapshot_odds = await self.get_khl_odds(limit=10)
                elif league.lower() == "cs2":
                    snapshot_odds = await self.get_cs2_odds(limit=10)
                else:
                    snapshot_odds = []
                
                # Update timestamp for all odds in snapshot
                for odds_info in snapshot_odds:
                    odds_info.timestamp = snapshot_time
                
                snapshots.extend(snapshot_odds)
            
            # Cache snapshots
            await cache.set(snapshot_key, snapshots, self.ttl)
            logger.info(f"Generated {len(snapshots)} {league} odds snapshots")
            
            return snapshots
            
        except Exception as e:
            logger.error(f"Error getting {league} odds snapshots: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for odds service"""
        try:
            # Try to generate some odds
            test_odds = self._generate_mock_odds(["Team A", "Team B"], "TEST")
            
            return {
                "status": "healthy",
                "last_check": logger.info("Odds service health checked"),
                "sources_available": len(self.odds_sources),
                "mock_generation": len(test_odds) > 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": logger.error(f"Odds service health error: {e}")
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()


# Global odds service instance
odds_service = OddsService()
