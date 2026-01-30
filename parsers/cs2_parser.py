import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import re
import json

from bs4 import BeautifulSoup
from base_parser import BaseParser, ParsedMatch

logger = logging.getLogger(__name__)


class CS2Parser(BaseParser):
    """Парсер CS2 матчей с HLTV и других источников"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.base_url = "https://www.hltv.org"
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
