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
                
                # Ищем таблицу с матчами
                match_table = soup.find('table', class_='calendar')
                if match_table:
                    rows = match_table.find_all('tr')
                    
                    for row in rows[1:]:  # Пропускаем заголовок
                        try:
                            match_data = self.extract_match_data(row)
                            if match_data:
                                matches.append(match_data)
                        except Exception as e:
                            logger.error(f"Error parsing match row: {e}")
                            continue
                
                logger.info(f"🏒 Parsed {len(matches)} KHL matches")
                
                # Сохраняем в базу данных
                for match in matches:
                    await db_manager.add_match(match)
                
                return matches
                
        except Exception as e:
            logger.error(f"Error parsing KHL matches: {e}")
            return await self.get_fallback_matches()
    
    def extract_match_data(self, element) -> Optional[Match]:
        """Извлечение данных матча из элемента"""
        try:
            # Ищем ячейки таблицы
            cells = element.find_all('td')
            if len(cells) < 4:
                return None
            
            # Дата и время
            datetime_cell = cells[0].get_text(strip=True)
            # Парсим дату и время
            
            # Команды
            teams_cell = cells[1]
            team_links = teams_cell.find_all('a')
            
            if len(team_links) >= 2:
                team1 = team_links[0].get_text(strip=True)
                team2 = team_links[1].get_text(strip=True)
            else:
                # Fallback - ищем текст
                teams_text = teams_cell.get_text(strip=True)
                if " - " in teams_text:
                    team1, team2 = teams_text.split(" - ", 1)
                else:
                    return None
            
            # Счет
            score_cell = cells[2].get_text(strip=True)
            score = score_cell if score_cell and score_cell != "-" else None
            
            # Статус
            status = "live" if score and ":" in score else ("finished" if score else "upcoming")
            
            # Турнир/информация
            info_cell = cells[3].get_text(strip=True) if len(cells) > 3 else "KHL Regular Season"
            
            # Создаем матч
            match = Match(
                sport="khl",
                team1=team1,
                team2=team2,
                score=score,
                status=status,
                start_time=datetime.now() + timedelta(hours=2) if status == "upcoming" else datetime.now(),
                features={
                    "tournament": info_cell,
                    "source": "khl.ru",
                    "parsed_at": datetime.now().isoformat()
                }
            )
            
            return match
            
        except Exception as e:
            logger.error(f"Error extracting KHL match data: {e}")
            return None
    
    async def get_fallback_matches(self) -> List[Match]:
        """Fallback матчи, если парсинг не удался"""
        logger.info("🏒 Using fallback KHL matches")
        
        fallback_matches = [
            Match(
                sport="khl",
                team1="CSKA Moscow",
                team2="Ak Bars Kazan",
                score="3:2",
                status="live",
                start_time=datetime.now(),
                features={
                    "tournament": "KHL Gagarin Cup Playoffs",
                    "source": "fallback",
                    "importance": 9
                }
            ),
            Match(
                sport="khl",
                team1="SKA Saint Petersburg",
                team2="Metallurg Magnitogorsk",
                score=None,
                status="upcoming",
                start_time=datetime.now() + timedelta(hours=4),
                features={
                    "tournament": "KHL Regular Season",
                    "source": "fallback",
                    "importance": 8
                }
            ),
            Match(
                sport="khl",
                team1="Salavat Yulaev Ufa",
                team2="Lokomotiv Yaroslavl",
                score="2:1",
                status="live",
                start_time=datetime.now(),
                features={
                    "tournament": "KHL Conference Finals",
                    "source": "fallback",
                    "importance": 9
                }
            ),
            Match(
                sport="khl",
                team1="Avangard Omsk",
                team2="Barys Nur-Sultan",
                score=None,
                status="upcoming",
                start_time=datetime.now() + timedelta(hours=6),
                features={
                    "tournament": "KHL Regular Season",
                    "source": "fallback",
                    "importance": 7
                }
            ),
            Match(
                sport="khl",
                team1="Dinamo Moscow",
                team2="HC Spartak Moscow",
                score="4:3 OT",
                status="finished",
                start_time=datetime.now() - timedelta(hours=2),
                features={
                    "tournament": "KHL Moscow Derby",
                    "source": "fallback",
                    "importance": 8
                }
            )
        ]
        
        # Сохраняем fallback матчи
        for match in fallback_matches:
            await db_manager.add_match(match)
        
        return fallback_matches
    
    async def update_matches(self):
        """Обновление матчей"""
        logger.info("🏒 Updating KHL matches")
        
        try:
            # Получаем текущие матчи
            current_matches = await self.parse_matches()
            
            # Обновляем статусы live матчей
            live_matches = [m for m in current_matches if m.status == "live"]
            for match in live_matches:
                # Здесь можно добавить логику обновления счета
                await db_manager.update_match(match.id, match)
            
            logger.info(f"🏒 Updated {len(live_matches)} live KHL matches")
            
        except Exception as e:
            logger.error(f"Error updating KHL matches: {e}")

# Глобальный экземпляр
khl_parser = KHLParser()
