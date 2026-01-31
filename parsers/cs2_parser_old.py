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
        self.odds_sources = [
            "https://www.hltv.org/betting/matches",
            "https://www.gosugamers.net/counter-strike/matches"
        ]
    
    async def parse_matches(self) -> List[ParsedMatch]:
        """Парсинг предстоящих матчей CS2"""
        matches = []
        
        # Парсим с HLTV
        hltv_matches = await self._parse_hltv_matches()
        matches.extend(hltv_matches)
        
        # Парсим с других источников
        gosu_matches = await self._parse_gosugamers_matches()
        matches.extend(gosu_matches)
        
        # Удаляем дубликаты
        unique_matches = self._remove_duplicates(matches)
        
        logger.info(f"Parsed {len(unique_matches)} CS2 matches")
        return unique_matches
    
    async def parse_live_matches(self) -> List[ParsedMatch]:
        """Парсинг live матчей CS2"""
        matches = []
        
        # Live матчи с HLTV
        live_matches = await self._parse_hltv_live_matches()
        matches.extend(live_matches)
        
        logger.info(f"Parsed {len(matches)} CS2 live matches")
        return matches
    
    async def parse_odds(self, match_id: str) -> Dict[str, float]:
        """Парсинг коэффициентов для матча"""
        odds = {}
        
        try:
            # Получаем коэффициенты с разных источников
            hltv_odds = await self._parse_hltv_odds(match_id)
            odds.update(hltv_odds)
            
            # Если нет коэффициентов, используем средние значения
            if not odds:
                odds = {'odds1': 1.85, 'odds2': 1.85, 'odds_draw': None}
            
        except Exception as e:
            logger.error(f"Error parsing odds for {match_id}: {e}")
            odds = {'odds1': 1.85, 'odds2': 1.85, 'odds_draw': None}
        
        return odds
    
    async def _parse_hltv_matches(self) -> List[ParsedMatch]:
        """Парсинг матчей с HLTV"""
        matches = []
        
        try:
            url = "https://www.hltv.org/matches"
            content = await self.get_page_content(url)
            
            if not content:
                return matches
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Ищем блоки с матчами
            match_elements = soup.find_all('a', class_='match-day')
            
            for element in match_elements:
                try:
                    match_data = self._extract_hltv_match_data(element)
                    if match_data:
                        matches.append(match_data)
                except Exception as e:
                    logger.error(f"Error extracting HLTV match: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing HLTV matches: {e}")
        
        return matches
    
    async def _parse_hltv_live_matches(self) -> List[ParsedMatch]:
        """Парсинг live матчей с HLTV"""
        matches = []
        
        try:
            url = "https://www.hltv.org/matches"
            content = await self.get_page_content(url)
            
            if not content:
                return matches
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Ищем live матчи
            live_elements = soup.find_all('div', class_='live-match')
            
            for element in live_elements:
                try:
                    match_data = self._extract_hltv_live_match_data(element)
                    if match_data:
                        matches.append(match_data)
                except Exception as e:
                    logger.error(f"Error extracting HLTV live match: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing HLTV live matches: {e}")
        
        return matches
    
    async def _parse_gosugamers_matches(self) -> List[ParsedMatch]:
        """Парсинг матчей с GosuGamers"""
        matches = []
        
        try:
            url = "https://www.gosugamers.net/counter-strike/matches"
            content = await self.get_page_content(url)
            
            if not content:
                return matches
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Ищем матчи
            match_elements = soup.find_all('div', class_='match')
            
            for element in match_elements:
                try:
                    match_data = self._extract_gosugamers_match_data(element)
                    if match_data:
                        matches.append(match_data)
                except Exception as e:
                    logger.error(f"Error extracting GosuGamers match: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing GosuGamers matches: {e}")
        
        return matches
    
    def _extract_hltv_match_data(self, element) -> Optional[ParsedMatch]:
        """Извлечение данных матча с HLTV"""
        try:
            # Команды
            teams = element.find_all('div', class_='team')
            if len(teams) < 2:
                return None
            
            team1 = teams[0].get_text(strip=True)
            team2 = teams[1].get_text(strip=True)
            
            # Время матча
            time_element = element.find('div', class_='time')
            if not time_element:
                return None
            
            time_text = time_element.get_text(strip=True)
            match_time = self._parse_match_time(time_text)
            
            # Турнир
            tournament_element = element.find('div', class_='event-name')
            tournament = tournament_element.get_text(strip=True) if tournament_element else "Unknown"
            
            # Коэффициенты
            odds = self._extract_hltv_match_odds(element)
            
            # ID матча
            match_id = self.generate_match_id(team1, team2, match_time)
            
            return ParsedMatch(
                id=match_id,
                team1=team1,
                team2=team2,
                tournament=tournament,
                match_time=match_time,
                odds1=odds.get('odds1', 1.85),
                odds2=odds.get('odds2', 1.85),
                odds_draw=odds.get('odds_draw')
            )
        
        except Exception as e:
            logger.error(f"Error extracting HLTV match data: {e}")
            return None
    
    def _extract_hltv_live_match_data(self, element) -> Optional[ParsedMatch]:
        """Извлечение данных live матча с HLTV"""
        try:
            # Команды
            teams = element.find_all('div', class_='team')
            if len(teams) < 2:
                return None
            
            team1 = teams[0].get_text(strip=True)
            team2 = teams[1].get_text(strip=True)
            
            # Счет
            score_element = element.find('div', class_='score')
            score_text = score_element.get_text(strip=True) if score_element else "0-0"
            
            score1, score2 = self._parse_score(score_text)
            
            # Турнир
            tournament_element = element.find('div', class_='event-name')
            tournament = tournament_element.get_text(strip=True) if tournament_element else "Unknown"
            
            # ID матча
            match_id = self.generate_match_id(team1, team2, datetime.now())
            
            return ParsedMatch(
                id=match_id,
                team1=team1,
                team2=team2,
                tournament=tournament,
                match_time=datetime.now(),
                odds1=1.0,  # Live коэффициенты будут обновлены отдельно
                odds2=1.0,
                status='live',
                score1=score1,
                score2=score2,
                live_data={'source': 'hltv', 'live': True}
            )
        
        except Exception as e:
            logger.error(f"Error extracting HLTV live match data: {e}")
            return None
    
    def _extract_gosugamers_match_data(self, element) -> Optional[ParsedMatch]:
        """Извлечение данных матча с GosuGamers"""
        try:
            # Команды
            teams = element.find_all('div', class_='team')
            if len(teams) < 2:
                return None
            
            team1 = teams[0].get_text(strip=True)
            team2 = teams[1].get_text(strip=True)
            
            # Время
            time_element = element.find('div', class_='time')
            if not time_element:
                return None
            
            time_text = time_element.get_text(strip=True)
            match_time = self._parse_match_time(time_text)
            
            # Турнир
            tournament_element = element.find('div', class_='tournament')
            tournament = tournament_element.get_text(strip=True) if tournament_element else "Unknown"
            
            # ID матча
            match_id = self.generate_match_id(team1, team2, match_time)
            
            return ParsedMatch(
                id=match_id,
                team1=team1,
                team2=team2,
                tournament=tournament,
                match_time=match_time,
                odds1=1.85,  # Будут обновлены
                odds2=1.85
            )
        
        except Exception as e:
            logger.error(f"Error extracting GosuGamers match data: {e}")
            return None
    
    def _extract_hltv_match_odds(self, element) -> Dict[str, float]:
        """Извлечение коэффициентов с HLTV"""
        odds = {}
        
        try:
            # Ищем коэффициенты в элементе
            odds_elements = element.find_all('div', class_='odds')
            
            if len(odds_elements) >= 2:
                odds1_text = odds_elements[0].get_text(strip=True)
                odds2_text = odds_elements[1].get_text(strip=True)
                
                odds['odds1'] = self._parse_odds_value(odds1_text)
                odds['odds2'] = self._parse_odds_value(odds2_text)
        
        except Exception as e:
            logger.error(f"Error extracting HLTV odds: {e}")
        
        return odds
    
    def _parse_match_time(self, time_text: str) -> datetime:
        """Парсинг времени матча"""
        try:
            # Разные форматы времени
            if 'today' in time_text.lower():
                time_part = re.search(r'(\d{1,2}:\d{2})', time_text)
                if time_part:
                    hour, minute = map(int, time_part.group(1).split(':'))
                    today = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                    return today
            
            elif 'tomorrow' in time_text.lower():
                time_part = re.search(r'(\d{1,2}:\d{2})', time_text)
                if time_part:
                    hour, minute = map(int, time_part.group(1).split(':'))
                    tomorrow = datetime.now() + timedelta(days=1)
                    return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            else:
                # Полная дата
                date_patterns = [
                    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})',
                    r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2})',
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, time_text)
                    if match:
                        return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M')
            
            # Если не удалось распарсить, возвращаем время через 24 часа
            return datetime.now() + timedelta(hours=24)
        
        except Exception as e:
            logger.error(f"Error parsing match time '{time_text}': {e}")
            return datetime.now() + timedelta(hours=24)
    
    def _parse_score(self, score_text: str) -> tuple:
        """Парсинг счета матча"""
        try:
            if ':' in score_text:
                parts = score_text.split(':')
                return int(parts[0]), int(parts[1])
            elif '-' in score_text:
                parts = score_text.split('-')
                return int(parts[0]), int(parts[1])
            else:
                return 0, 0
        except:
            return 0, 0
    
    def _parse_odds_value(self, odds_text: str) -> float:
        """Парсинг значения коэффициента"""
        try:
            # Удаляем все символы кроме цифр и точки
            clean_text = re.sub(r'[^\d.]', '', odds_text)
            if clean_text:
                return float(clean_text)
            return 1.85  # Значение по умолчанию
        except:
            return 1.85
    
    def _remove_duplicates(self, matches: List[ParsedMatch]) -> List[ParsedMatch]:
        """Удаление дубликатов матчей"""
        seen = set()
        unique_matches = []
        
        for match in matches:
            # Создаем уникальный ключ из команд и времени
            key = f"{match.team1}_{match.team2}_{match.match_time.strftime('%Y%m%d_%H%M')}"
            
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return unique_matches
