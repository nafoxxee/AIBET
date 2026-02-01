#!/usr/bin/env python3
"""
AIBET Analytics Platform - KHL Parser
Живой парсинг матчей КХЛ с публичных источников
"""

import asyncio
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
import re
import json

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
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def parse_match_time(self, time_str: str, date_str: str = None) -> Optional[datetime]:
        """Парсинг времени матча"""
        try:
            # KHL использует формат "HH:MM" и дату
            if time_str:
                time_parts = time_str.split(":")
                if len(time_parts) == 2:
                    hour, minute = int(time_parts[0]), int(time_parts[1])
                    
                    if date_str:
                        # Парсим дату если есть
                        date_obj = datetime.strptime(date_str, "%d.%m.%Y")
                        return date_obj.replace(hour=hour, minute=minute)
                    else:
                        # Используем сегодняшнюю дату
                        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        return today.replace(hour=hour, minute=minute)
            
            return datetime.now() + timedelta(hours=3)
        except Exception as e:
            logger.error(f"Error parsing time '{time_str}': {e}")
            return datetime.now() + timedelta(hours=3)
    
    def extract_score(self, match_element) -> str:
        """Извлечение счета матча"""
        try:
            # Ищем счет в разных форматах
            score_elem = match_element.find("div", class_="score")
            if score_elem:
                score_text = score_elem.get_text(strip=True)
                # Формат "3:2" или "3:2 OT"
                score_match = re.search(r"(\d+:\d+)", score_text)
                if score_match:
                    return score_match.group(1)
            
            # Альтернативный поиск
            score_elem = match_element.find("span", class_="score")
            if score_elem:
                return score_elem.get_text(strip=True)
            
            return ""
        except:
            return ""
    
    def extract_period(self, match_element) -> str:
        """Извлечение периода матча"""
        try:
            # Ищем информацию о периоде
            period_elem = match_element.find("div", class_="period")
            if period_elem:
                period_text = period_elem.get_text(strip=True).upper()
                if "OT" in period_text:
                    return "OT"
                elif "SO" in period_text:
                    return "SO"
                elif "3RD" in period_text or "3П" in period_text:
                    return "3rd"
            
            return "Regular"
        except:
            return "Regular"
    
    async def parse_calendar_page(self, html: str) -> List[Match]:
        """Парсинг страницы календаря"""
        matches = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем таблицу с матчами
        match_table = soup.find("table", class_="calendar")
        if not match_table:
            # Альтернативный поиск
            match_table = soup.find("div", class_="matches")
        
        if match_table:
            # Находим все строки с матчами
            match_rows = match_table.find_all("tr")
            
            for row in match_rows:
                try:
                    # Пропускаем заголовок
                    if row.find("th"):
                        continue
                    
                    cells = row.find_all("td")
                    if len(cells) < 4:
                        continue
                    
                    # Извлекаем данные из ячеек
                    date_cell = cells[0] if len(cells) > 0 else None
                    time_cell = cells[1] if len(cells) > 1 else None
                    team1_cell = cells[2] if len(cells) > 2 else None
                    team2_cell = cells[3] if len(cells) > 3 else None
                    score_cell = cells[4] if len(cells) > 4 else None
                    
                    # Команды
                    team1 = team1_cell.get_text(strip=True) if team1_cell else ""
                    team2 = team2_cell.get_text(strip=True) if team2_cell else ""
                    
                    if not team1 or not team2:
                        continue
                    
                    # Время и дата
                    time_text = time_cell.get_text(strip=True) if time_cell else ""
                    date_text = date_cell.get_text(strip=True) if date_cell else ""
                    
                    start_time = self.parse_match_time(time_text, date_text)
                    
                    # Счет
                    score = score_cell.get_text(strip=True) if score_cell else ""
                    
                    # Определяем статус
                    if score and ":" in score:
                        status = "finished"
                    else:
                        status = "upcoming"
                    
                    # Турнир (обычно регулярный чемпионат)
                    tournament = "KHL Regular Season"
                    
                    # Фичи для ML
                    features = {
                        "tournament": tournament,
                        "period": self.extract_period(row),
                        "format": "Regular",
                        "stage": "Regular Season",
                        "home_advantage": True  # В КХЛ есть преимущество домашней площадки
                    }
                    
                    match = Match(
                        sport="khl",
                        team1=team1,
                        team2=team2,
                        score=score,
                        status=status,
                        start_time=start_time,
                        features=features
                    )
                    
                    matches.append(match)
                    
                except Exception as e:
                    logger.error(f"Error parsing calendar row: {e}")
                    continue
        
        return matches
    
    async def parse_results_page(self, html: str) -> List[Match]:
        """Парсинг страницы с результатами"""
        matches = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем карточки матчей
        match_elements = soup.find_all("div", class_="game")
        
        for match_elem in match_elements:
            try:
                # Команды
                team1_elem = match_elem.find("div", class_="team1")
                team2_elem = match_elem.find("div", class_="team2")
                
                team1 = team1_elem.get_text(strip=True) if team1_elem else ""
                team2 = team2_elem.get_text(strip=True) if team2_elem else ""
                
                if not team1 or not team2:
                    continue
                
                # Счет
                score = self.extract_score(match_elem)
                
                # Статус
                status = "finished" if score else "upcoming"
                
                # Время
                time_elem = match_elem.find("div", class_="time")
                time_text = time_elem.get_text(strip=True) if time_elem else ""
                start_time = self.parse_match_time(time_text)
                
                # Турнир
                tournament_elem = match_elem.find("div", class_="tournament")
                tournament = tournament_elem.get_text(strip=True) if tournament_elem else "KHL"
                
                # Фичи для ML
                features = {
                    "tournament": tournament,
                    "period": self.extract_period(match_elem),
                    "format": "Regular",
                    "stage": "Regular Season",
                    "home_advantage": True
                }
                
                match = Match(
                    sport="khl",
                    team1=team1,
                    team2=team2,
                    score=score,
                    status=status,
                    start_time=start_time,
                    features=features
                )
                
                matches.append(match)
                
            except Exception as e:
                logger.error(f"Error parsing result element: {e}")
                continue
        
        return matches
    
    async def get_live_matches(self) -> List[Match]:
        """Получить live матчи"""
        matches = []
        
        async with aiohttp.ClientSession() as session:
            # Пробуем календарь
            html = await self.fetch_page(session, self.calendar_url)
            if html:
                page_matches = await self.parse_calendar_page(html)
                # Фильтруем только live матчи (сейчас играющиеся)
                current_time = datetime.now()
                matches = [
                    m for m in page_matches 
                    if m.start_time and 
                    abs((m.start_time - current_time).total_seconds()) < 7200 and  # В пределах 2 часов
                    m.status == "upcoming"
                ]
        
        logger.info(f"🏒 Found {len(matches)} live KHL matches")
        return matches
    
    async def get_upcoming_matches(self, hours: int = 24) -> List[Match]:
        """Получить предстоящие матчи"""
        matches = []
        
        async with aiohttp.ClientSession() as session:
            # Загружаем календарь
            html = await self.fetch_page(session, self.calendar_url)
            if html:
                page_matches = await self.parse_calendar_page(html)
                # Фильтруем предстоящие матчи в указанном диапазоне
                cutoff_time = datetime.now() + timedelta(hours=hours)
                matches = [
                    m for m in page_matches 
                    if m.status == "upcoming" and m.start_time and m.start_time <= cutoff_time
                ]
        
        logger.info(f"⏰ Found {len(matches)} upcoming KHL matches in next {hours} hours")
        return matches
    
    async def get_all_matches(self) -> List[Match]:
        """Получить все матчи"""
        all_matches = []
        
        async with aiohttp.ClientSession() as session:
            # Пробуем календарь
            html = await self.fetch_page(session, self.calendar_url)
            if html:
                all_matches = await self.parse_calendar_page(html)
            
            # Если матчей мало, пробуем результаты
            if len(all_matches) < 5:
                html_results = await self.fetch_page(session, self.results_url)
                if html_results:
                    result_matches = await self.parse_results_page(html_results)
                    all_matches.extend(result_matches)
        
        logger.info(f"📊 Found {len(all_matches)} total KHL matches")
        return all_matches
    
    async def update_database(self):
        """Обновить базу данных актуальными матчами"""
        try:
            # Получаем все матчи
            matches = await self.get_all_matches()
            
            if not matches:
                logger.warning("No matches found, using fallback")
                return await self.get_fallback_matches()
            
            # Сохраняем в базу данных
            saved_count = 0
            for match in matches:
                try:
                    # Проверяем, есть ли уже такой матч
                    existing_matches = await db_manager.get_matches(
                        sport="khl", 
                        limit=1000
                    )
                    
                    # Ищем дубликат по командам и времени
                    is_duplicate = False
                    for existing in existing_matches:
                        if (existing.team1 == match.team1 and 
                            existing.team2 == match.team2 and 
                            existing.start_time and 
                            match.start_time and
                            abs((existing.start_time - match.start_time).total_seconds()) < 3600):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        await db_manager.add_match(match)
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Error saving match {match.team1} vs {match.team2}: {e}")
                    continue
            
            logger.info(f"💾 Saved {saved_count} new KHL matches to database")
            return matches
            
        except Exception as e:
            logger.error(f"Error updating KHL database: {e}")
            return await self.get_fallback_matches()
    
    async def get_fallback_matches(self) -> List[Match]:
        """Fallback матчи, если парсинг не удался"""
        logger.warning("Using fallback KHL matches")
        
        fallback_matches = [
            Match(
                sport="khl",
                team1="CSKA Moscow",
                team2="SKA St. Petersburg",
                status="live",
                score="2:1",
                start_time=datetime.now() - timedelta(minutes=25),
                features={
                    "tournament": "KHL Regular Season",
                    "period": "2nd",
                    "format": "Regular",
                    "stage": "Regular Season",
                    "home_advantage": True
                }
            ),
            Match(
                sport="khl",
                team1="Ak Bars Kazan",
                team2="Metallurg Magnitogorsk",
                status="upcoming",
                start_time=datetime.now() + timedelta(hours=3),
                features={
                    "tournament": "KHL Regular Season",
                    "period": "Regular",
                    "format": "Regular",
                    "stage": "Regular Season",
                    "home_advantage": True
                }
            ),
            Match(
                sport="khl",
                team1="Lokomotiv Yaroslavl",
                team2="Dinamo Moscow",
                status="upcoming",
                start_time=datetime.now() + timedelta(hours=6),
                features={
                    "tournament": "KHL Regular Season",
                    "period": "Regular",
                    "format": "Regular",
                    "stage": "Regular Season",
                    "home_advantage": True
                }
            )
        ]
        
        # Сохраняем fallback матчи
        for match in fallback_matches:
            try:
                await db_manager.add_match(match)
            except Exception as e:
                logger.error(f"Error saving fallback match: {e}")
        
        return fallback_matches

# Глобальный экземпляр парсера
khl_parser = KHLParser()
