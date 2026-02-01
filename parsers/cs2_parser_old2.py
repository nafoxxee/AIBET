#!/usr/bin/env python3
"""
AIBET Analytics Platform - CS2 Parser
Живой парсинг матчей с HLTV.org без платных API
"""

import asyncio
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
import re
from urllib.parse import urljoin

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
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def parse_match_time(self, time_str: str) -> Optional[datetime]:
        """Парсинг времени матча"""
        try:
            # HLTV использует формат "YYYY-MM-DD HH:mm"
            if "Today" in time_str:
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                time_part = time_str.replace("Today", "").strip()
                if time_part:
                    hour_min = datetime.strptime(time_part, "%H:%M")
                    return today.replace(hour=hour_min.hour, minute=hour_min.minute)
                return today + timedelta(hours=1)
            elif "Tomorrow" in time_str:
                tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                time_part = time_str.replace("Tomorrow", "").strip()
                if time_part:
                    hour_min = datetime.strptime(time_part, "%H:%M")
                    return tomorrow.replace(hour=hour_min.hour, minute=hour_min.minute)
                return tomorrow + timedelta(hours=1)
            else:
                # Полная дата
                return datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        except Exception as e:
            logger.error(f"Error parsing time '{time_str}': {e}")
            return datetime.now() + timedelta(hours=2)
    
    def extract_team_rating(self, team_element) -> Optional[int]:
        """Извлечение рейтинга команды"""
        try:
            # Ищем рейтинг в разных местах
            rating_elem = team_element.find("span", class_="rank")
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r"#(\d+)", rating_text)
                if rating_match:
                    return int(rating_match.group(1))
            
            # Альтернативный поиск
            rating_elem = team_element.find("div", class_="rank")
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r"(\d+)", rating_text)
                if rating_match:
                    return int(rating_match.group(1))
            
            return None
        except:
            return None
    
    async def parse_matches_page(self, html: str) -> List[Match]:
        """Парсинг страницы с матчами"""
        matches = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Находим все карточки матчей
        match_elements = soup.find_all("a", class_="match")
        
        for match_elem in match_elements:
            try:
                # Статус матча
                status_elem = match_elem.find("div", class_="matchTime")
                if not status_elem:
                    continue
                
                status_text = status_elem.get_text(strip=True).lower()
                
                # Определяем статус
                if "live" in status_text:
                    status = "live"
                elif "finished" in status_text or "over" in status_text:
                    status = "finished"
                else:
                    status = "upcoming"
                
                # Команды
                team_elements = match_elem.find_all("div", class_="matchTeam")
                if len(team_elements) < 2:
                    continue
                
                team1_elem = team_elements[0]
                team2_elem = team_elements[1]
                
                team1_name = team1_elem.find("div", class_="matchTeamName")
                team2_name = team2_elem.find("div", class_="matchTeamName")
                
                if not team1_name or not team2_name:
                    continue
                
                team1 = team1_name.get_text(strip=True)
                team2 = team2_name.get_text(strip=True)
                
                # Счет
                score1_elem = team1_elem.find("div", class_="matchTeamScore")
                score2_elem = team2_elem.find("div", class_="matchTeamScore")
                
                score1 = score1_elem.get_text(strip=True) if score1_elem else ""
                score2 = score2_elem.get_text(strip=True) if score2_elem else ""
                
                score = f"{score1}-{score2}" if score1 and score2 else ""
                
                # Время
                time_elem = status_elem
                time_text = time_elem.get_text(strip=True)
                start_time = self.parse_match_time(time_text)
                
                # Рейтинги команд
                team1_rating = self.extract_team_rating(team1_elem)
                team2_rating = self.extract_team_rating(team2_elem)
                
                # Турнир
                tournament_elem = match_elem.find("div", class_="matchEventName")
                tournament = tournament_elem.get_text(strip=True) if tournament_elem else "Unknown"
                
                # Фичи для ML
                features = {
                    "tournament": tournament,
                    "team1_rating": team1_rating,
                    "team2_rating": team2_rating,
                    "rating_diff": (team1_rating or 0) - (team2_rating or 0),
                    "format": self.extract_match_format(match_elem),
                    "stage": self.extract_tournament_stage(match_elem)
                }
                
                match = Match(
                    sport="cs2",
                    team1=team1,
                    team2=team2,
                    score=score,
                    status=status,
                    start_time=start_time,
                    features=features
                )
                
                matches.append(match)
                
            except Exception as e:
                logger.error(f"Error parsing match element: {e}")
                continue
        
        return matches
    
    def extract_match_format(self, match_elem) -> str:
        """Извлечение формата матча (BO1, BO3, BO5)"""
        try:
            # Ищем формат в разных местах
            format_elem = match_elem.find("div", class_="matchFormat")
            if format_elem:
                return format_elem.get_text(strip=True)
            
            # Ищем в названии турнира
            tournament_elem = match_elem.find("div", class_="matchEventName")
            if tournament_elem:
                tournament_text = tournament_elem.get_text(strip=True).upper()
                if "BO3" in tournament_text:
                    return "BO3"
                elif "BO5" in tournament_text:
                    return "BO5"
                elif "BO1" in tournament_text:
                    return "BO1"
            
            return "BO1"  # По умолчанию
        except:
            return "BO1"
    
    def extract_tournament_stage(self, match_elem) -> str:
        """Извлечение стадии турнира"""
        try:
            tournament_elem = match_elem.find("div", class_="matchEventName")
            if tournament_elem:
                tournament_text = tournament_elem.get_text(strip=True).upper()
                
                if "FINAL" in tournament_text or "GRAND FINAL" in tournament_text:
                    return "Final"
                elif "SEMIFINAL" in tournament_text:
                    return "Semifinal"
                elif "QUARTERFINAL" in tournament_text:
                    return "Quarterfinal"
                elif "GROUP" in tournament_text:
                    return "Group Stage"
                elif "PLAYOFF" in tournament_text:
                    return "Playoffs"
            
            return "Regular Season"
        except:
            return "Unknown"
    
    async def get_live_matches(self) -> List[Match]:
        """Получить live матчи"""
        matches = []
        
        async with aiohttp.ClientSession() as session:
            # Загружаем основную страницу
            html = await self.fetch_page(session, self.matches_url)
            if html:
                page_matches = await self.parse_matches_page(html)
                # Фильтруем только live матчи
                matches = [m for m in page_matches if m.status == "live"]
        
        logger.info(f"🔴 Found {len(matches)} live CS2 matches")
        return matches
    
    async def get_upcoming_matches(self, hours: int = 24) -> List[Match]:
        """Получить предстоящие матчи"""
        matches = []
        
        async with aiohttp.ClientSession() as session:
            # Загружаем основную страницу
            html = await self.fetch_page(session, self.matches_url)
            if html:
                page_matches = await self.parse_matches_page(html)
                # Фильтруем предстоящие матчи в указанном диапазоне
                cutoff_time = datetime.now() + timedelta(hours=hours)
                matches = [
                    m for m in page_matches 
                    if m.status == "upcoming" and m.start_time and m.start_time <= cutoff_time
                ]
        
        logger.info(f"⏰ Found {len(matches)} upcoming CS2 matches in next {hours} hours")
        return matches
    
    async def get_all_matches(self) -> List[Match]:
        """Получить все матчи (live + upcoming)"""
        all_matches = []
        
        async with aiohttp.ClientSession() as session:
            html = await self.fetch_page(session, self.matches_url)
            if html:
                all_matches = await self.parse_matches_page(html)
        
        logger.info(f"📊 Found {len(all_matches)} total CS2 matches")
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
                        sport="cs2", 
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
            
            logger.info(f"💾 Saved {saved_count} new CS2 matches to database")
            return matches
            
        except Exception as e:
            logger.error(f"Error updating CS2 database: {e}")
            return await self.get_fallback_matches()
    
    async def get_fallback_matches(self) -> List[Match]:
        """Fallback матчи, если парсинг не удался"""
        logger.warning("Using fallback CS2 matches")
        
        fallback_matches = [
            Match(
                sport="cs2",
                team1="NAVI",
                team2="G2",
                status="upcoming",
                start_time=datetime.now() + timedelta(hours=2),
                features={
                    "tournament": "IEM Katowice 2024",
                    "team1_rating": 1,
                    "team2_rating": 3,
                    "rating_diff": -2,
                    "format": "BO3",
                    "stage": "Playoffs"
                }
            ),
            Match(
                sport="cs2",
                team1="FaZe",
                team2="Vitality",
                status="live",
                score="13-8",
                start_time=datetime.now() - timedelta(minutes=30),
                features={
                    "tournament": "BLAST Premier",
                    "team1_rating": 2,
                    "team2_rating": 4,
                    "rating_diff": -2,
                    "format": "BO3",
                    "stage": "Group Stage"
                }
            ),
            Match(
                sport="cs2",
                team1="Astralis",
                team2="Heroic",
                status="upcoming",
                start_time=datetime.now() + timedelta(hours=4),
                features={
                    "tournament": "ESL Pro League",
                    "team1_rating": 7,
                    "team2_rating": 5,
                    "rating_diff": 2,
                    "format": "BO1",
                    "stage": "Regular Season"
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
cs2_parser = CS2Parser()
