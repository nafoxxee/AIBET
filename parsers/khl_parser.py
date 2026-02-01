#!/usr/bin/env python3
"""
AIBET Analytics Platform - KHL Parser
Парсинг реальных матчей с khl.ru
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

class KHLParser:
    def __init__(self):
        self.base_url = "https://www.livesport.com"
        self.khl_url = "https://www.livesport.com/ru/hockey/russia/khl/"
        self.results_url = "https://www.livesport.com/ru/hockey/russia/khl/results/"
        
        # Enhanced User-Agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Alternative sources
        self.fallback_sources = [
            "https://khl.ru/calendar/",
            "https://khl.ru/games/",
            "https://www.sofascore.com/hockey/russia/khl",
            "https://www.flashscore.com/hockey/russia/khl/"
        ]
        
        self.session_timeout = aiohttp.ClientTimeout(total=15)
        self.max_retries = 3
        self.request_delay = (1, 3)
    
    def get_random_headers(self) -> Dict[str, str]:
        """Get random headers for request"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
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
                            await asyncio.sleep(5)
                            continue
                    elif response.status == 429:
                        logger.warning(f"⚠️ HTTP 429 for {url} - rate limited")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(10)
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
    
    async def parse_matches(self) -> List[Match]:
        """Enhanced KHL parsing with livesport.com as primary source"""
        logger.info("🏒 Parsing KHL matches with enhanced sources")
        
        # Try livesport.com first
        matches = await self._parse_livesport()
        if matches:
            logger.info(f"✅ Got {len(matches)} matches from livesport.com")
            return matches
        
        # Try fallback sources
        for source_url in self.fallback_sources:
            try:
                matches = await self._parse_fallback_source(source_url)
                if matches:
                    logger.info(f"✅ Got {len(matches)} matches from fallback: {source_url}")
                    return matches
            except Exception as e:
                logger.warning(f"Error with fallback {source_url}: {e}")
                continue
        
        logger.warning("🏒 All KHL sources failed, returning empty list")
        return []
    
    async def _parse_livesport(self) -> List[Match]:
        """Parse matches from livesport.com"""
        matches = []
        
        try:
            async with aiohttp.ClientSession() as session:
                html = await self.fetch_page(session, self.khl_url)
                if not html:
                    logger.warning("Failed to fetch livesport.com KHL page")
                    return []
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Livesport.com specific selectors
                match_selectors = [
                    'div.event__match',
                    'div[data-id]',
                    'tr.event__row',
                    'div.sportEvent',
                    'a[href*="/match/"]'
                ]
                
                all_elements = []
                for selector in match_selectors:
                    elements = soup.select(selector)
                    if elements:
                        all_elements.extend(elements)
                        logger.info(f"🏒 Found {len(elements)} elements with selector: {selector}")
                
                # Remove duplicates and parse
                unique_elements = []
                seen_texts = set()
                for element in all_elements:
                    text = element.get_text(strip=True)
                    if text and text not in seen_texts and len(text) > 10:
                        unique_elements.append(element)
                        seen_texts.add(text)
                
                logger.info(f"🏒 Processing {len(unique_elements)} unique KHL matches")
                
                for element in unique_elements[:30]:
                    try:
                        match = await self._parse_khl_match_element(element)
                        if match:
                            matches.append(match)
                    except Exception as e:
                        logger.warning(f"Error parsing KHL match element: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"❌ Error parsing livesport.com: {e}")
        
        return matches
    
    async def _parse_fallback_source(self, source_url: str) -> List[Match]:
        """Parse fallback source based on URL"""
        matches = []
        
        try:
            async with aiohttp.ClientSession() as session:
                html = await self.fetch_page(session, source_url)
                if not html:
                    return []
                
                soup = BeautifulSoup(html, 'html.parser')
                
                if 'khl.ru' in source_url:
                    matches = await self._parse_khl_official(soup)
                elif 'sofascore' in source_url:
                    matches = await self._parse_sofascore(soup)
                elif 'flashscore' in source_url:
                    matches = await self._parse_flashscore(soup)
                    
        except Exception as e:
            logger.warning(f"Error parsing fallback source: {e}")
        
        return matches
    
    async def _parse_khl_official(self, soup) -> List[Match]:
        """Parse KHL official website"""
        matches = []
        # Implementation for khl.ru parsing
        return matches
    
    async def _parse_sofascore(self, soup) -> List[Match]:
        """Parse Sofascore KHL matches"""
        matches = []
        # Implementation for Sofascore parsing
        return matches
    
    async def _parse_flashscore(self, soup) -> List[Match]:
        """Parse Flashscore KHL matches"""
        matches = []
        # Implementation for Flashscore parsing
        return matches
    
    async def _parse_khl_match_element(self, element) -> Optional[Match]:
        """Parse individual KHL match element"""
        try:
            # Extract team names
            team_selectors = [
                'div.event__participant--home',
                'div.event__participant--away', 
                'span.team-name',
                'div.team'
            ]
            
            team1, team2 = None, None
            for selector in team_selectors:
                teams = element.select(selector)
                if len(teams) >= 2:
                    team1 = teams[0].get_text(strip=True)
                    team2 = teams[1].get_text(strip=True)
                    break
            
            if not team1 or not team2:
                return None
            
            # Extract match time
            time_element = element.select_one('div.event__time')
            if not time_element:
                time_element = element.select_one('span.time')
            
            start_time = None
            if time_element:
                time_text = time_element.get_text(strip=True)
                start_time = self._parse_time(time_text)
            
            # Extract status
            status = "upcoming"
            if element.select_one('div.event__status--live'):
                status = "live"
            elif element.select_one('div.event__status--finished'):
                status = "finished"
            
            # Extract score
            score_element = element.select_one('div.event__score')
            score = ""
            if score_element:
                score = score_element.get_text(strip=True)
            
            # Extract tournament info
            tournament = "KHL"
            tournament_element = element.select_one('div.event__tournament')
            if tournament_element:
                tournament = tournament_element.get_text(strip=True)
            
            return Match(
                sport="khl",
                team1=team1,
                team2=team2,
                score=score,
                status=status,
                start_time=start_time,
                features={
                    "tournament": tournament,
                    "importance": 5,
                    "format": "Regular Season"
                }
            )
            
        except Exception as e:
            logger.warning(f"Error parsing KHL match element: {e}")
            return None
    
    def _parse_time(self, time_text: str) -> Optional[datetime]:
        """Parse match time"""
        try:
            if "live" in time_text.lower():
                return datetime.utcnow()
            
            if ":" in time_text:
                hour, minute = map(int, time_text.split(":"))
                now = datetime.utcnow()
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return None
        except:
            return None
    
    async def parse_match_element(self, element) -> Optional[Match]:
        """Парсинг отдельного элемента матча"""
        try:
            # Извлекаем команды
            team_elements = element.find_all('span', class_='team')
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
            
            # Извлекаем турнир/лигу
            league_element = element.find('span', class_='league')
            if not league_element:
                league_element = element.find('div', class_='league')
            
            tournament = "KHL Regular Season"
            if league_element:
                tournament = league_element.get_text(strip=True)
            
            # Создаем матч
            match = Match(
                sport="khl",
                team1=team1,
                team2=team2,
                score=score,
                status=status,
                start_time=start_time,
                features={
                    "tournament": tournament,
                    "importance": 7,
                    "format": "Регулярный сезон"
                }
            )
            
            return match
            
        except Exception as e:
            logger.warning(f"Error parsing KHL match element: {e}")
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
        """Резервные матчи, если парсинг не удался"""
        logger.info("🏒 Using fallback KHL matches")
        
        fallback_matches = [
            Match(
                sport="khl",
                team1="CSKA Moscow",
                team2="SKA St. Petersburg",
                score="",
                status="upcoming",
                start_time=datetime.utcnow() + timedelta(hours=3),
                features={"tournament": "KHL Regular Season", "importance": 8, "format": "Регулярный сезон"}
            ),
            Match(
                sport="khl",
                team1="Ak Bars Kazan",
                team2="Metallurg Magnitogorsk",
                score="",
                status="upcoming",
                start_time=datetime.utcnow() + timedelta(hours=5),
                features={"tournament": "KHL Regular Season", "importance": 7, "format": "Регулярный сезон"}
            ),
            Match(
                sport="khl",
                team1="Salavat Yulaev",
                team2="Lokomotiv Yaroslavl",
                score="2:1",
                status="live",
                start_time=datetime.utcnow(),
                features={"tournament": "KHL Regular Season", "importance": 9, "format": "Регулярный сезон"}
            ),
            Match(
                sport="khl",
                team1="Avangard Omsk",
                team2="Barys Nur-Sultan",
                score="4:2",
                status="finished",
                start_time=datetime.utcnow() - timedelta(hours=2),
                features={"tournament": "KHL Regular Season", "importance": 6, "format": "Регулярный сезон"}
            )
        ]
        
        return fallback_matches
    
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
            
            logger.info(f"🏒 Updated {saved_count} KHL matches")
            return matches
            
        except Exception as e:
            logger.exception(f"❌ Error updating KHL matches: {e}")
            return []
    
    async def get_database_fallback(self) -> List[Match]:
        """Fallback: последние матчи из базы данных"""
        try:
            matches = await db_manager.get_matches(sport="khl", limit=5)
            
            if not matches:
                logger.warning("🏒 No KHL matches in database")
                return []
            
            logger.info(f"🏒 Using database fallback: {len(matches)} KHL matches")
            return matches
            
        except Exception as e:
            logger.error(f"Error getting database fallback: {e}")
            return []

# Глобальный экземпляр
khl_parser = KHLParser()
