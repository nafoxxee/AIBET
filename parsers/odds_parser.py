#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real Odds Parser
Парсинг реальных коэффициентов с BetBoom, Winline, Fonbet
"""

import asyncio
import aiohttp
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

# Global instance
odds_parser = RealOddsParser()

@dataclass
class OddsData:
    match_id: str
    sport: str  # 'cs2' or 'khl'
    bookmaker: str
    team1: str
    team2: str
    odds1: float  # П1
    odds2: float  # П2
    odds_draw: Optional[float] = None  # Ничья (для KHL)
    total_over: Optional[float] = None  # Тотал больше
    total_under: Optional[float] = None  # Тотал меньше
    handicap1: Optional[float] = None  # Фора 1
    handicap2: Optional[float] = None  # Фора 2
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()

class RealOddsParser:
    def __init__(self):
        self.name = "Real Odds Parser"
        self.session_timeout = aiohttp.ClientTimeout(total=15)
        self.max_retries = 3
        self.request_delay = (1, 3)  # Random delay between requests
        
        # User-Agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Bookmaker configurations
        self.bookmakers = {
            'betboom': {
                'base_url': 'https://betboom.com',
                'api_url': 'https://betboom.com/api/v1/odds',
                'enabled': True
            },
            'winline': {
                'base_url': 'https://winline.ru',
                'api_url': 'https://winline.ru/api/v2/odds',
                'enabled': True
            },
            'fonbet': {
                'base_url': 'https://www.fonbet.ru',
                'api_url': 'https://www.fonbet.ru/api/v1/odds',
                'enabled': True
            }
        }
        
        # Sport mappings
        self.sport_mappings = {
            'cs2': {
                'betboom': 'counter-strike-2',
                'winline': 'cs2',
                'fonbet': 'csgo'
            },
            'khl': {
                'betboom': 'hockey-khl',
                'winline': 'hockey',
                'fonbet': 'hockey'
            }
        }
    
    def get_random_headers(self) -> Dict[str, str]:
        """Get random headers for request"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site'
        }
    
    async def fetch_with_retry(self, session: aiohttp.ClientSession, url: str, headers: Dict[str, str]) -> Optional[str]:
        """Fetch URL with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Random delay to avoid blocking
                await asyncio.sleep(random.uniform(*self.request_delay))
                
                async with session.get(url, headers=headers, timeout=self.session_timeout) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 403:
                        logger.warning(f"⚠️ HTTP 403 for {url} - attempt {attempt + 1}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(5)  # Wait longer on 403
                            continue
                    elif response.status == 429:
                        logger.warning(f"⚠️ HTTP 429 for {url} - rate limited")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(10)  # Wait longer on rate limit
                            continue
                    else:
                        logger.warning(f"⚠️ HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Timeout for {url} - attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(3)
                    continue
            except Exception as e:
                logger.error(f"❌ Error fetching {url}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2)
                    continue
        
        return None
    
    async def parse_betboom_odds(self, sport: str) -> List[OddsData]:
        """Parse odds from BetBoom"""
        logger.info(f"🎯 Parsing BetBoom odds for {sport}")
        odds_data = []
        
        if not self.bookmakers['betboom']['enabled']:
            logger.warning("BetBoom parser disabled")
            return odds_data
        
        try:
            sport_path = self.sport_mappings[sport]['betboom']
            url = f"{self.bookmakers['betboom']['api_url']}/{sport_path}"
            
            async with aiohttp.ClientSession() as session:
                headers = self.get_random_headers()
                response_text = await self.fetch_with_retry(session, url, headers)
                
                if not response_text:
                    logger.warning("Failed to fetch BetBoom odds")
                    return odds_data
                
                try:
                    data = json.loads(response_text)
                    matches = data.get('matches', [])
                    
                    for match in matches[:20]:  # Limit to first 20 matches
                        try:
                            odds = self._extract_betboom_match_odds(match, sport)
                            if odds:
                                odds_data.append(odds)
                        except Exception as e:
                            logger.warning(f"Error parsing BetBoom match: {e}")
                            continue
                            
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse BetBoom JSON: {e}")
                    # Try HTML fallback
                    odds_data = await self._parse_betboom_html_fallback(session, sport)
                    
        except Exception as e:
            logger.error(f"❌ BetBoom parser error: {e}")
        
        logger.info(f"✅ BetBoom: parsed {len(odds_data)} odds for {sport}")
        return odds_data
    
    def _extract_betboom_match_odds(self, match: Dict, sport: str) -> Optional[OddsData]:
        """Extract odds from BetBoom match data"""
        try:
            team1 = match.get('team1', {}).get('name', '')
            team2 = match.get('team2', {}).get('name', '')
            
            if not team1 or not team2:
                return None
            
            markets = match.get('markets', [])
            odds1, odds2, odds_draw = None, None, None
            total_over, total_under = None, None
            handicap1, handicap2 = None, None
            
            for market in markets:
                market_type = market.get('type', '')
                outcomes = market.get('outcomes', [])
                
                if market_type == 'match_winner':
                    for outcome in outcomes:
                        if outcome.get('name') == team1:
                            odds1 = float(outcome.get('price', 0))
                        elif outcome.get('name') == team2:
                            odds2 = float(outcome.get('price', 0))
                        elif outcome.get('name') == 'Draw':
                            odds_draw = float(outcome.get('price', 0))
                
                elif market_type == 'total_over_under':
                    for outcome in outcomes:
                        if 'Over' in outcome.get('name', ''):
                            total_over = float(outcome.get('price', 0))
                        elif 'Under' in outcome.get('name', ''):
                            total_under = float(outcome.get('price', 0))
                
                elif market_type == 'handicap':
                    for outcome in outcomes:
                        if team1 in outcome.get('name', ''):
                            handicap1 = float(outcome.get('price', 0))
                        elif team2 in outcome.get('name', ''):
                            handicap2 = float(outcome.get('price', 0))
            
            if odds1 and odds2:
                return OddsData(
                    match_id=f"betboom_{match.get('id', '')}",
                    sport=sport,
                    bookmaker='betboom',
                    team1=team1,
                    team2=team2,
                    odds1=odds1,
                    odds2=odds2,
                    odds_draw=odds_draw,
                    total_over=total_over,
                    total_under=total_under,
                    handicap1=handicap1,
                    handicap2=handicap2
                )
        
        except Exception as e:
            logger.warning(f"Error extracting BetBoom odds: {e}")
        
        return None
    
    async def _parse_betboom_html_fallback(self, session: aiohttp.ClientSession, sport: str) -> List[OddsData]:
        """HTML fallback for BetBoom"""
        logger.info("Using BetBoom HTML fallback")
        odds_data = []
        
        try:
            sport_path = self.sport_mappings[sport]['betboom']
            url = f"{self.bookmakers['betboom']['base_url']}/{sport_path}"
            
            headers = self.get_random_headers()
            response_text = await self.fetch_with_retry(session, url, headers)
            
            if response_text:
                soup = BeautifulSoup(response_text, 'html.parser')
                # Parse HTML structure (implementation depends on actual HTML)
                # This is a placeholder for HTML parsing logic
                logger.info("BetBoom HTML fallback parsed (placeholder)")
        
        except Exception as e:
            logger.error(f"BetBoom HTML fallback error: {e}")
        
        return odds_data
    
    async def parse_winline_odds(self, sport: str) -> List[OddsData]:
        """Parse odds from Winline"""
        logger.info(f"🎯 Parsing Winline odds for {sport}")
        odds_data = []
        
        if not self.bookmakers['winline']['enabled']:
            logger.warning("Winline parser disabled")
            return odds_data
        
        try:
            sport_path = self.sport_mappings[sport]['winline']
            url = f"{self.bookmakers['winline']['api_url']}/{sport_path}"
            
            async with aiohttp.ClientSession() as session:
                headers = self.get_random_headers()
                response_text = await self.fetch_with_retry(session, url, headers)
                
                if not response_text:
                    logger.warning("Failed to fetch Winline odds")
                    return odds_data
                
                try:
                    data = json.loads(response_text)
                    events = data.get('events', [])
                    
                    for event in events[:20]:
                        try:
                            odds = self._extract_winline_match_odds(event, sport)
                            if odds:
                                odds_data.append(odds)
                        except Exception as e:
                            logger.warning(f"Error parsing Winline event: {e}")
                            continue
                            
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Winline JSON: {e}")
        
        except Exception as e:
            logger.error(f"❌ Winline parser error: {e}")
        
        logger.info(f"✅ Winline: parsed {len(odds_data)} odds for {sport}")
        return odds_data
    
    def _extract_winline_match_odds(self, event: Dict, sport: str) -> Optional[OddsData]:
        """Extract odds from Winline event data"""
        try:
            team1 = event.get('team1', {}).get('name', '')
            team2 = event.get('team2', {}).get('name', '')
            
            if not team1 or not team2:
                return None
            
            # Similar extraction logic as BetBoom
            markets = event.get('markets', [])
            odds1, odds2, odds_draw = None, None, None
            
            for market in markets:
                if market.get('type') == 'winner':
                    outcomes = market.get('outcomes', [])
                    for outcome in outcomes:
                        if outcome.get('team') == team1:
                            odds1 = float(outcome.get('coefficient', 0))
                        elif outcome.get('team') == team2:
                            odds2 = float(outcome.get('coefficient', 0))
                        elif outcome.get('team') == 'Draw':
                            odds_draw = float(outcome.get('coefficient', 0))
            
            if odds1 and odds2:
                return OddsData(
                    match_id=f"winline_{event.get('id', '')}",
                    sport=sport,
                    bookmaker='winline',
                    team1=team1,
                    team2=team2,
                    odds1=odds1,
                    odds2=odds2,
                    odds_draw=odds_draw
                )
        
        except Exception as e:
            logger.warning(f"Error extracting Winline odds: {e}")
        
        return None
    
    async def parse_fonbet_odds(self, sport: str) -> List[OddsData]:
        """Parse odds from Fonbet"""
        logger.info(f"🎯 Parsing Fonbet odds for {sport}")
        odds_data = []
        
        if not self.bookmakers['fonbet']['enabled']:
            logger.warning("Fonbet parser disabled")
            return odds_data
        
        try:
            sport_path = self.sport_mappings[sport]['fonbet']
            url = f"{self.bookmakers['fonbet']['api_url']}/{sport_path}"
            
            async with aiohttp.ClientSession() as session:
                headers = self.get_random_headers()
                response_text = await self.fetch_with_retry(session, url, headers)
                
                if not response_text:
                    logger.warning("Failed to fetch Fonbet odds")
                    return odds_data
                
                try:
                    data = json.loads(response_text)
                    events = data.get('events', [])
                    
                    for event in events[:20]:
                        try:
                            odds = self._extract_fonbet_match_odds(event, sport)
                            if odds:
                                odds_data.append(odds)
                        except Exception as e:
                            logger.warning(f"Error parsing Fonbet event: {e}")
                            continue
                            
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Fonbet JSON: {e}")
        
        except Exception as e:
            logger.error(f"❌ Fonbet parser error: {e}")
        
        logger.info(f"✅ Fonbet: parsed {len(odds_data)} odds for {sport}")
        return odds_data
    
    def _extract_fonbet_match_odds(self, event: Dict, sport: str) -> Optional[OddsData]:
        """Extract odds from Fonbet event data"""
        try:
            team1 = event.get('team1', {}).get('name', '')
            team2 = event.get('team2', {}).get('name', '')
            
            if not team1 or not team2:
                return None
            
            # Fonbet-specific extraction logic
            factors = event.get('factors', [])
            odds1, odds2, odds_draw = None, None, None
            
            for factor in factors:
                factor_type = factor.get('type', '')
                if factor_type == 'win1':
                    odds1 = float(factor.get('value', 0))
                elif factor_type == 'win2':
                    odds2 = float(factor.get('value', 0))
                elif factor_type == 'draw':
                    odds_draw = float(factor.get('value', 0))
            
            if odds1 and odds2:
                return OddsData(
                    match_id=f"fonbet_{event.get('id', '')}",
                    sport=sport,
                    bookmaker='fonbet',
                    team1=team1,
                    team2=team2,
                    odds1=odds1,
                    odds2=odds2,
                    odds_draw=odds_draw
                )
        
        except Exception as e:
            logger.warning(f"Error extracting Fonbet odds: {e}")
        
        return None
    
    async def get_all_odds(self, sport: str) -> List[OddsData]:
        """Get odds from all enabled bookmakers"""
        logger.info(f"🎲 Getting all odds for {sport}")
        
        tasks = []
        if self.bookmakers['betboom']['enabled']:
            tasks.append(self.parse_betboom_odds(sport))
        if self.bookmakers['winline']['enabled']:
            tasks.append(self.parse_winline_odds(sport))
        if self.bookmakers['fonbet']['enabled']:
            tasks.append(self.parse_fonbet_odds(sport))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_odds = []
        for result in results:
            if isinstance(result, list):
                all_odds.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Error in odds parsing: {result}")
        
        logger.info(f"✅ Total odds collected: {len(all_odds)} for {sport}")
        return all_odds
    
    async def get_average_odds(self, sport: str) -> List[Dict]:
        """Calculate average odds across bookmakers"""
        all_odds = await self.get_all_odds(sport)
        
        # Group by match (team1 vs team2)
        matches = {}
        for odds in all_odds:
            key = f"{odds.team1}_{odds.team2}"
            if key not in matches:
                matches[key] = []
            matches[key].append(odds)
        
        # Calculate averages
        average_odds = []
        for match_key, odds_list in matches.items():
            if len(odds_list) >= 2:  # At least 2 bookmakers
                avg_odds1 = sum(o.odds1 for o in odds_list) / len(odds_list)
                avg_odds2 = sum(o.odds2 for o in odds_list) / len(odds_list)
                avg_draw = sum(o.odds_draw for o in odds_list if o.odds_draw) / len([o for o in odds_list if o.odds_draw]) if any(o.odds_draw for o in odds_list) else None
                
                average_odds.append({
                    'team1': odds_list[0].team1,
                    'team2': odds_list[0].team2,
                    'sport': sport,
                    'avg_odds1': round(avg_odds1, 2),
                    'avg_odds2': round(avg_odds2, 2),
                    'avg_odds_draw': round(avg_draw, 2) if avg_draw else None,
                    'bookmakers_count': len(odds_list),
                    'updated_at': datetime.now().isoformat()
                })
        
        return average_odds

# Global instance
odds_parser = RealOddsParser()
