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

from database import Match, db_manager

logger = logging.getLogger(__name__)

class CS2Parser:
    def __init__(self):
        self.base_url = "https://www.hltv.org"
        self.matches_url = "https://www.hltv.org/matches"
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
        logger.info("🔴 Parsing CS2 matches from HLTV.org")
        
        try:
            async with aiohttp.ClientSession() as session:
                html = await self.fetch_page(session, self.matches_url)
                if not html:
                    logger.warning("⚠️ Failed to fetch HLTV matches page, using fallback")
                    return await self.get_fallback_matches()
                
                soup = BeautifulSoup(html, 'html.parser')
                matches = []
                
                # Ищем все матчи на странице
                match_elements = soup.find_all('a', class_='match')
                
                for element in match_elements[:20]:  # Ограничиваем количество
                    try:
                        match = await self.parse_match_element(element)
                        if match:
                            matches.append(match)
                    except Exception as e:
                        logger.warning(f"Error parsing match element: {e}")
                        continue
                
                logger.info(f"🔴 Parsed {len(matches)} CS2 matches")
                return matches
                
        except Exception as e:
            logger.exception(f"❌ Error parsing CS2 matches: {e}")
            return await self.get_fallback_matches()
    
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
        """Резервные матчи, если парсинг не удался"""
        logger.info("🔴 Using fallback CS2 matches")
        
        fallback_matches = [
            Match(
                sport="cs2",
                team1="NAVI",
                team2="FaZe",
                score="",
                status="upcoming",
                start_time=datetime.utcnow() + timedelta(hours=2),
                features={"tournament": "ESL Pro League", "importance": 8, "format": "BO3"}
            ),
            Match(
                sport="cs2",
                team1="G2",
                team2="Vitality",
                score="",
                status="upcoming",
                start_time=datetime.utcnow() + timedelta(hours=4),
                features={"tournament": "BLAST Premier", "importance": 9, "format": "BO3"}
            ),
            Match(
                sport="cs2",
                team1="Astralis",
                team2="Heroic",
                score="16-14",
                status="live",
                start_time=datetime.utcnow(),
                features={"tournament": "IEM Katowice", "importance": 10, "format": "BO3"}
            ),
            Match(
                sport="cs2",
                team1="Liquid",
                team2="Cloud9",
                score="2-1",
                status="finished",
                start_time=datetime.utcnow() - timedelta(hours=1),
                features={"tournament": "ESL One", "importance": 7, "format": "BO3"}
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
            
            logger.info(f"🔴 Updated {saved_count} CS2 matches")
            return matches
            
        except Exception as e:
            logger.exception(f"❌ Error updating CS2 matches: {e}")
            return []

# Глобальный экземпляр
cs2_parser = CS2Parser()
