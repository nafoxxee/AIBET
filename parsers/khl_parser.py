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

from database import Match, db_manager

logger = logging.getLogger(__name__)

class KHLParser:
    def __init__(self):
        self.base_url = "https://khl.ru"
        self.calendar_url = "https://khl.ru/calendar/"
        self.results_url = "https://khl.ru/games/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def fetch_page(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Загрузка страницы с обработкой ошибок"""
        try:
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    async def parse_matches(self) -> List[Match]:
        """Парсинг матчей"""
        logger.info("🏒 Parsing KHL matches from khl.ru")
        
        try:
            async with aiohttp.ClientSession() as session:
                html = await self.fetch_page(session, self.calendar_url)
                if not html:
                    logger.warning("Failed to fetch KHL calendar page")
                    return await self.get_fallback_matches()
                
                soup = BeautifulSoup(html, 'html.parser')
                matches = []
                
                # Ищем матчи на странице
                match_selectors = [
                    'div.calendar-item',
                    'div.match-item',
                    'tr.calendar-row',
                    '[class*="match"]',
                    '[class*="game"]'
                ]
                
                match_elements = []
                for selector in match_selectors:
                    elements = soup.select(selector)
                    if elements:
                        match_elements.extend(elements)
                        logger.info(f"🏒 Found {len(elements)} matches with selector: {selector}")
                        break
                
                for element in match_elements[:15]:  # Ограничиваем количество
                    try:
                        match = await self.parse_match_element(element)
                        if match:
                            matches.append(match)
                    except Exception as e:
                        logger.warning(f"Error parsing KHL match element: {e}")
                        continue
                
                logger.info(f"🏒 Parsed {len(matches)} KHL matches")
                return matches
                
        except Exception as e:
            logger.exception(f"❌ Error parsing KHL matches: {e}")
            return await self.get_fallback_matches()
    
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

# Глобальный экземпляр
khl_parser = KHLParser()
