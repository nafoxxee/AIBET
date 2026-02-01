#!/usr/bin/env python3
"""
AIBET Analytics Platform - CS2 Parser
Парсинг реальных матчей с HLTV.org
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
import re
import random

from database import Match, db_manager

logger = logging.getLogger(__name__)

class CS2Parser:
    def __init__(self):
        self.base_url = "https://www.hltv.org"
        self.matches_url = "https://www.hltv.org/matches"
        
        # Enhanced User-Agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # API mirrors and endpoints
        self.api_mirrors = [
            "https://hltv-api.vercel.app/api/matches",
            "https://api.hltv.org/v1/matches", 
            "https://json.hltv-api.com/matches",
            "https://hltv-api-nu.vercel.app/matches",
            "https://www.hltv.org/api/matches"
        ]
        
        # Fallback sources
        self.fallback_sources = [
            "https://liquipedia.net/counterstrike/Portal:Matches",
            "https://www.gosugamers.net/counterstrike/matches",
            "https://www.scoreboard.com/matches/cs2"
        ]
        
        self.session_timeout = aiohttp.ClientTimeout(total=15)
        self.max_retries = 3
        self.request_delay = (1, 3)
    
    def get_random_headers(self) -> Dict[str, str]:
        """Get random headers for request"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    async def fetch_page(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Enhanced page fetching with retry and anti-blocking"""
        for attempt in range(self.max_retries):
            try:
                # Random delay to avoid detection
                await asyncio.sleep(random.uniform(*self.request_delay))
                
                headers = self.get_random_headers()
                
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
                    elif response.status == 503:
                        logger.warning(f"⚠️ HTTP 503 for {url} - service unavailable")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(8)
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
    
    async def try_api_mirrors(self) -> Optional[List[Match]]:
        """Try to get data from API mirrors"""
        logger.info("🔄 Trying API mirrors for CS2 data")
        
        async with aiohttp.ClientSession() as session:
            for mirror_url in self.api_mirrors:
                try:
                    headers = self.get_random_headers()
                    response_text = await self.fetch_page(session, mirror_url)
                    
                    if response_text:
                        try:
                            data = json.loads(response_text)
                            matches = self._parse_api_response(data)
                            if matches:
                                logger.info(f"✅ Successfully got {len(matches)} matches from {mirror_url}")
                                return matches
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON from {mirror_url}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"Error trying mirror {mirror_url}: {e}")
                    continue
        
        return None
    
    def _parse_api_response(self, data: Dict) -> List[Match]:
        """Parse API response and convert to Match objects"""
        matches = []
        
        try:
            if 'matches' in data:
                for match_data in data['matches'][:20]:
                    match = self._convert_api_match(match_data)
                    if match:
                        matches.append(match)
            elif isinstance(data, list):
                for match_data in data[:20]:
                    match = self._convert_api_match(match_data)
                    if match:
                        matches.append(match)
                        
        except Exception as e:
            logger.warning(f"Error parsing API response: {e}")
        
        return matches
    
    def _convert_api_match(self, match_data: Dict) -> Optional[Match]:
        """Convert API match data to Match object"""
        try:
            team1 = match_data.get('team1', {}).get('name') or match_data.get('team1')
            team2 = match_data.get('team2', {}).get('name') or match_data.get('team2')
            
            if not team1 or not team2:
                return None
            
            event_name = match_data.get('event', {}).get('name') or match_data.get('tournament', 'Unknown')
            status = match_data.get('status', 'upcoming')
            match_time = match_data.get('time') or match_data.get('date')
            
            # Parse time
            start_time = None
            if match_time:
                try:
                    if isinstance(match_time, str):
                        if ':' in match_time:
                            hour, minute = map(int, match_time.split(':'))
                            now = datetime.utcnow()
                            start_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                except:
                    pass
            
            return Match(
                sport="cs2",
                team1=team1,
                team2=team2,
                score=match_data.get('score', ''),
                status=status,
                start_time=start_time,
                features={
                    "tournament": event_name,
                    "importance": 5,
                    "format": match_data.get('format', 'BO3'),
                    "api_source": True
                }
            )
            
        except Exception as e:
            logger.warning(f"Error converting API match: {e}")
            return None

    async def get_database_fallback(self) -> Optional[str]:
        """Fallback: последние матчи из базы данных"""
        try:
            from database import db_manager
            matches = await db_manager.get_matches(sport="cs2", limit=5)
            
            if not matches:
                logger.warning("🔴 No CS2 matches in database")
                return None
            
            # Создаем HTML из матчей базы
            html_content = "<html><body>"
            for match in matches:
                html_content += f"""
                <div class="match" data-match-id="{match.id}">
                    <div class="event-name">{match.features.get('tournament', 'Unknown')}</div>
                    <div class="team-name">{match.team1}</div>
                    <div class="team-name">{match.team2}</div>
                    <div class="time">{match.start_time.strftime('%H:%M') if match.start_time else 'TBD'}</div>
                    <div class="status">{match.status}</div>
                </div>
                """
            html_content += "</body></html>"
            
            logger.info(f"🔴 Using database fallback: {len(matches)} CS2 matches")
            return html_content
            
        except Exception as e:
            logger.error(f"Error getting database fallback: {e}")
            return None
    
    async def parse_api_data(self, data: dict) -> Optional[str]:
        """Парсинг данных из API и возврат HTML формата"""
        try:
            if 'matches' in data and data['matches']:
                # Создаем простой HTML из API данных
                html_content = "<html><body>"
                for match in data['matches'][:20]:
                    team1 = match.get('team1', {}).get('name', 'Team 1')
                    team2 = match.get('team2', {}).get('name', 'Team 2')
                    event = match.get('event', {}).get('name', 'Unknown Event')
                    
                    html_content += f"""
                    <div class="match" data-match-id="{match.get('id', 'unknown')}">
                        <div class="event-name">{event}</div>
                        <div class="team-name">{team1}</div>
                        <div class="team-name">{team2}</div>
                        <div class="time">{match.get('time', 'TBD')}</div>
                        <div class="status">{match.get('status', 'upcoming')}</div>
                    </div>
                    """
                html_content += "</body></html>"
                return html_content
        except Exception as e:
            logger.warning(f"Error parsing API data: {e}")
        
        return None
    
    async def parse_matches(self) -> List[Match]:
        """Enhanced parsing with API mirrors and fallbacks"""
        logger.info("🔴 Parsing CS2 matches with enhanced sources")
        
        # Try API mirrors first
        api_matches = await self.try_api_mirrors()
        if api_matches:
            logger.info(f"✅ Got {len(api_matches)} matches from API mirrors")
            return api_matches
        
        # Fallback to HTML parsing
        logger.info("🔄 Falling back to HTML parsing")
        try:
            async with aiohttp.ClientSession() as session:
                html = await self.fetch_page(session, self.matches_url)
                if not html:
                    logger.warning("⚠️ Failed to fetch HLTV matches page")
                    return await self._try_fallback_sources()
                
                soup = BeautifulSoup(html, 'html.parser')
                matches = []
                
                # Enhanced match selectors
                match_selectors = [
                    'a.match',
                    'div.match',
                    'div.matching',
                    'tr.match',
                    'div[data-match-id]',
                    'a[href*="/matches/"]',
                    'div.upcoming-match',
                    'div.live-match',
                    'div.completed-match'
                ]
                
                all_elements = []
                for selector in match_selectors:
                    elements = soup.select(selector)
                    if elements:
                        all_elements.extend(elements)
                        logger.info(f"🔴 Found {len(elements)} elements with selector: {selector}")
                
                # Remove duplicates
                unique_elements = []
                seen_texts = set()
                for element in all_elements:
                    text = element.get_text(strip=True)
                    if text and text not in seen_texts and len(text) > 10:
                        unique_elements.append(element)
                        seen_texts.add(text)
                
                logger.info(f"🔴 Processing {len(unique_elements)} unique CS2 matches")
                
                for element in unique_elements[:30]:
                    try:
                        match = await self.parse_match_element(element)
                        if match:
                            matches.append(match)
                    except Exception as e:
                        logger.warning(f"Error parsing match element: {e}")
                        continue
                
                if matches:
                    logger.info(f"✅ Parsed {len(matches)} CS2 matches from HTML")
                    return matches
                
        except Exception as e:
            logger.exception(f"❌ Error parsing CS2 matches: {e}")
        
        # Final fallback
        return await self._try_fallback_sources()
    
    async def _try_fallback_sources(self) -> List[Match]:
        """Try fallback sources"""
        logger.info("🔄 Trying fallback sources")
        
        for source_url in self.fallback_sources:
            try:
                async with aiohttp.ClientSession() as session:
                    headers = self.get_random_headers()
                    html = await self.fetch_page(session, source_url)
                    
                    if html:
                        # Parse fallback source (implementation depends on source)
                        matches = await self._parse_fallback_source(html, source_url)
                        if matches:
                            logger.info(f"✅ Got {len(matches)} matches from fallback: {source_url}")
                            return matches
                            
            except Exception as e:
                logger.warning(f"Error with fallback {source_url}: {e}")
                continue
        
        logger.warning("🔴 All sources failed, returning empty list")
        return []
    
    async def _parse_fallback_source(self, html: str, source_url: str) -> List[Match]:
        """Parse fallback source based on URL"""
        matches = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            if 'liquipedia' in source_url:
                matches = await self._parse_liquipedia(soup)
            elif 'gosugamers' in source_url:
                matches = await self._parse_gosugamers(soup)
            elif 'scoreboard' in source_url:
                matches = await self._parse_scoreboard(soup)
                
        except Exception as e:
            logger.warning(f"Error parsing fallback source: {e}")
        
        return matches
    
    async def _parse_liquipedia(self, soup) -> List[Match]:
        """Parse Liquipedia matches"""
        matches = []
        # Implementation for Liquipedia parsing
        return matches
    
    async def _parse_gosugamers(self, soup) -> List[Match]:
        """Parse GosuGamers matches"""
        matches = []
        # Implementation for GosuGamers parsing
        return matches
    
    async def _parse_scoreboard(self, soup) -> List[Match]:
        """Parse Scoreboard matches"""
        matches = []
        # Implementation for Scoreboard parsing
        return matches
    
    async def parse_match_element(self, element) -> Optional[Match]:
        """Парсинг отдельного элемента матча"""
        try:
            # Извлекаем команды
            team_elements = element.find_all('span', class_='team-name')
            if len(team_elements) < 2:
                team_elements = element.find_all('div', class_='team')
                if len(team_elements) < 2:
                    team_elements = element.find_all('td', class_='team')
            
            if len(team_elements) < 2:
                return None
            
            team1 = team_elements[0].get_text(strip=True)
            team2 = team_elements[1].get_text(strip=True)
            
            if not team1 or not team2:
                return None
            
            # Извлекаем время
            time_element = element.find('span', class_='time')
            if not time_element:
                time_element = element.find('div', class_='time')
            
            start_time = None
            if time_element:
                time_text = time_element.get_text(strip=True)
                start_time = self.parse_time(time_text)
            
            # Извлекаем статус
            status = "upcoming"
            if element.find('span', class_='live') or element.find('div', class_='live'):
                status = "live"
            elif element.find('span', class_='finished') or element.find('div', class_='finished'):
                status = "finished"
            
            # Извлекаем счет
            score_element = element.find('span', class_='score')
            if not score_element:
                score_element = element.find('div', class_='score')
            
            score = ""
            if score_element:
                score = score_element.get_text(strip=True)
            
            # Извлекаем турнир
            tournament_element = element.find('span', class_='event-name')
            if not tournament_element:
                tournament_element = element.find('div', class_='event-name')
            
            tournament = "Unknown Tournament"
            if tournament_element:
                tournament = tournament_element.get_text(strip=True)
            
            # Создаем матч
            match = Match(
                sport="cs2",
                team1=team1,
                team2=team2,
                score=score,
                status=status,
                start_time=start_time,
                features={
                    "tournament": tournament,
                    "importance": 5,
                    "format": "BO3"
                }
            )
            
            return match
            
        except Exception as e:
            logger.warning(f"Error parsing match element: {e}")
            return None
    
    def parse_time(self, time_text: str) -> Optional[datetime]:
        """Парсинг времени матча"""
        try:
            # Примеры: "14:00", "2h ago", "Live"
            if "live" in time_text.lower():
                return datetime.utcnow()
            
            if ":" in time_text:
                # Формат HH:MM
                hour, minute = map(int, time_text.split(":"))
                now = datetime.utcnow()
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if "ago" in time_text.lower():
                # Формат "2h ago"
                hours = int(time_text.split("h")[0])
                return datetime.utcnow() - timedelta(hours=hours)
            
            return None
        except:
            return None
    
    async def get_fallback_matches(self) -> List[Match]:
        """Резервные матчи - отключены, используем только реальные данные"""
        logger.warning("🔴 Fallback matches disabled - using only real data")
        return []
    
    async def update_matches(self):
        """Обновление матчей"""
        try:
            matches = await self.parse_matches()
            
            # Сохраняем в базу данных
            saved_count = 0
            for match in matches:
                try:
                    await db_manager.add_match(match)
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ Error saving match: {e}")
            
            logger.info(f"🔴 Updated {saved_count} CS2 matches")
            return matches
            
        except Exception as e:
            logger.exception(f"❌ Error updating CS2 matches: {e}")
            return []

# Глобальный экземпляр
cs2_parser = CS2Parser()
