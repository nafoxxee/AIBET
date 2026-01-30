import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import re
import json

from bs4 import BeautifulSoup
from .base_parser import BaseParser, ParsedMatch

logger = logging.getLogger(__name__)


class KHLParser(BaseParser):
    """Парсер КХЛ матчей с различных источников"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.base_urls = [
            "https://www.flashscore.ru/hockey/russia/khl/",
            "https://ru.sofascore.com/tournament/211/khl"
        ]
        self.odds_sources = [
            "https://www.flashscore.ru/odds-comparison/hockey/russia/khl/",
            "https://ru.sofascore.com/tournament/211/khl/odds"
        ]
    
    async def parse_matches(self) -> List[ParsedMatch]:
        """Парсинг предстоящих матчей КХЛ"""
        matches = []
        
        # Парсим с Flashscore
        flashscore_matches = await self._parse_flashscore_matches()
        matches.extend(flashscore_matches)
        
        # Парсим с SofaScore
        sofascore_matches = await self._parse_sofascore_matches()
        matches.extend(sofascore_matches)
        
        # Удаляем дубликаты
        unique_matches = self._remove_duplicates(matches)
        
        logger.info(f"Parsed {len(unique_matches)} KHL matches")
        return unique_matches
    
    async def parse_live_matches(self) -> List[ParsedMatch]:
        """Парсинг live матчей КХЛ"""
        matches = []
        
        # Live матчи с Flashscore
        live_matches = await self._parse_flashscore_live_matches()
        matches.extend(live_matches)
        
        logger.info(f"Parsed {len(matches)} KHL live matches")
        return matches
    
    async def parse_odds(self, match_id: str) -> Dict[str, float]:
        """Парсинг коэффициентов для матча"""
        odds = {}
        
        try:
            # Получаем коэффициенты с разных источников
            flashscore_odds = await self._parse_flashscore_odds(match_id)
            odds.update(flashscore_odds)
            
            # Если нет коэффициентов, используем средние значения
            if not odds:
                odds = {'odds1': 2.10, 'odds2': 3.20, 'odds_draw': 4.50}
            
        except Exception as e:
            logger.error(f"Error parsing KHL odds for {match_id}: {e}")
            odds = {'odds1': 2.10, 'odds2': 3.20, 'odds_draw': 4.50}
        
        return odds
    
    async def _parse_flashscore_matches(self) -> List[ParsedMatch]:
        """Парсинг матчей с Flashscore"""
        matches = []
        
        try:
            url = "https://www.flashscore.ru/hockey/russia/khl/"
            content = await self.get_page_content(url)
            
            if not content:
                return matches
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Ищем блоки с матчами
            match_elements = soup.find_all('div', class_='event__match')
            
            for element in match_elements:
                try:
                    match_data = self._extract_flashscore_match_data(element)
                    if match_data:
                        matches.append(match_data)
                except Exception as e:
                    logger.error(f"Error extracting Flashscore match: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Flashscore matches: {e}")
        
        return matches
    
    async def _parse_flashscore_live_matches(self) -> List[ParsedMatch]:
        """Парсинг live матчей с Flashscore"""
        matches = []
        
        try:
            url = "https://www.flashscore.ru/hockey/russia/khl/"
            content = await self.get_page_content(url)
            
            if not content:
                return matches
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Ищем live матчи (обычно имеют специальный класс)
            live_elements = soup.find_all('div', class_='event__match--live')
            
            for element in live_elements:
                try:
                    match_data = self._extract_flashscore_live_match_data(element)
                    if match_data:
                        matches.append(match_data)
                except Exception as e:
                    logger.error(f"Error extracting Flashscore live match: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Flashscore live matches: {e}")
        
        return matches
    
    async def _parse_sofascore_matches(self) -> List[ParsedMatch]:
        """Парсинг матчей с SofaScore"""
        matches = []
        
        try:
            url = "https://ru.sofascore.com/tournament/211/khl"
            content = await self.get_page_content(url)
            
            if not content:
                return matches
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Ищем матчи
            match_elements = soup.find_all('div', class_='sc-match-row')
            
            for element in match_elements:
                try:
                    match_data = self._extract_sofascore_match_data(element)
                    if match_data:
                        matches.append(match_data)
                except Exception as e:
                    logger.error(f"Error extracting SofaScore match: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing SofaScore matches: {e}")
        
        return matches
    
    def _extract_flashscore_match_data(self, element) -> Optional[ParsedMatch]:
        """Извлечение данных матча с Flashscore"""
        try:
            # Команды
            home_team = element.find('div', class_='event__participant--home')
            away_team = element.find('div', class_='event__participant--away')
            
            if not home_team or not away_team:
                return None
            
            team1 = home_team.get_text(strip=True)
            team2 = away_team.get_text(strip=True)
            
            # Время матча
            time_element = element.find('div', class_='event__time')
            if not time_element:
                return None
            
            time_text = time_element.get_text(strip=True)
            match_time = self._parse_match_time(time_text)
            
            # Турнир (для КХЛ это будет "КХЛ")
            tournament = "КХЛ"
            
            # Коэффициенты
            odds = self._extract_flashscore_match_odds(element)
            
            # ID матча
            match_id = self.generate_match_id(team1, team2, match_time)
            
            return ParsedMatch(
                id=match_id,
                team1=team1,
                team2=team2,
                tournament=tournament,
                match_time=match_time,
                odds1=odds.get('odds1', 2.10),
                odds2=odds.get('odds2', 3.20),
                odds_draw=odds.get('odds_draw', 4.50)
            )
        
        except Exception as e:
            logger.error(f"Error extracting Flashscore match data: {e}")
            return None
    
    def _extract_flashscore_live_match_data(self, element) -> Optional[ParsedMatch]:
        """Извлечение данных live матча с Flashscore"""
        try:
            # Команды
            home_team = element.find('div', class_='event__participant--home')
            away_team = element.find('div', class_='event__participant--away')
            
            if not home_team or not away_team:
                return None
            
            team1 = home_team.get_text(strip=True)
            team2 = away_team.get_text(strip=True)
            
            # Счет
            home_score = element.find('div', class_='event__score--home')
            away_score = element.find('div', class_='event__score--away')
            
            score1 = int(home_score.get_text(strip=True)) if home_score else 0
            score2 = int(away_score.get_text(strip=True)) if away_score else 0
            
            # Время в матче
            period_element = element.find('div', class_='event__stage')
            period_text = period_element.get_text(strip=True) if period_element else "1-й период"
            
            # ID матча
            match_id = self.generate_match_id(team1, team2, datetime.now())
            
            return ParsedMatch(
                id=match_id,
                team1=team1,
                team2=team2,
                tournament="КХЛ",
                match_time=datetime.now(),
                odds1=1.0,  # Live коэффициенты будут обновлены отдельно
                odds2=1.0,
                odds_draw=1.0,
                status='live',
                score1=score1,
                score2=score2,
                live_data={
                    'source': 'flashscore',
                    'live': True,
                    'period': period_text
                }
            )
        
        except Exception as e:
            logger.error(f"Error extracting Flashscore live match data: {e}")
            return None
    
    def _extract_sofascore_match_data(self, element) -> Optional[ParsedMatch]:
        """Извлечение данных матча с SofaScore"""
        try:
            # Команды
            teams = element.find_all('div', class_='team-name')
            if len(teams) < 2:
                return None
            
            team1 = teams[0].get_text(strip=True)
            team2 = teams[1].get_text(strip=True)
            
            # Время
            time_element = element.find('div', class_='match-time')
            if not time_element:
                return None
            
            time_text = time_element.get_text(strip=True)
            match_time = self._parse_match_time(time_text)
            
            # ID матча
            match_id = self.generate_match_id(team1, team2, match_time)
            
            return ParsedMatch(
                id=match_id,
                team1=team1,
                team2=team2,
                tournament="КХЛ",
                match_time=match_time,
                odds1=2.10,  # Будут обновлены
                odds2=3.20,
                odds_draw=4.50
            )
        
        except Exception as e:
            logger.error(f"Error extracting SofaScore match data: {e}")
            return None
    
    def _extract_flashscore_match_odds(self, element) -> Dict[str, float]:
        """Извлечение коэффициентов с Flashscore"""
        odds = {}
        
        try:
            # Ищем коэффициенты в элементе
            odds_elements = element.find_all('div', class_='event__odd')
            
            if len(odds_elements) >= 2:
                odds1_text = odds_elements[0].get_text(strip=True)
                odds2_text = odds_elements[1].get_text(strip=True)
                
                odds['odds1'] = self._parse_odds_value(odds1_text)
                odds['odds2'] = self._parse_odds_value(odds2_text)
                
                if len(odds_elements) >= 3:
                    odds_draw_text = odds_elements[2].get_text(strip=True)
                    odds['odds_draw'] = self._parse_odds_value(odds_draw_text)
        
        except Exception as e:
            logger.error(f"Error extracting Flashscore odds: {e}")
        
        return odds
    
    def _parse_match_time(self, time_text: str) -> datetime:
        """Парсинг времени матча"""
        try:
            # Разные форматы времени для КХЛ
            if 'сегодня' in time_text.lower():
                time_part = re.search(r'(\d{1,2}:\d{2})', time_text)
                if time_part:
                    hour, minute = map(int, time_part.group(1).split(':'))
                    today = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                    return today
            
            elif 'завтра' in time_text.lower():
                time_part = re.search(r'(\d{1,2}:\d{2})', time_text)
                if time_part:
                    hour, minute = map(int, time_part.group(1).split(':'))
                    tomorrow = datetime.now() + timedelta(days=1)
                    return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            else:
                # Полная дата или только время
                date_patterns = [
                    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})',
                    r'(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2})',
                    r'(\d{1,2}:\d{2})',
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, time_text)
                    if match:
                        time_str = match.group(1)
                        if len(time_str) == 5:  # Только время
                            hour, minute = map(int, time_str.split(':'))
                            today = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                            return today
                        elif '.' in time_str:  # Формат ДД.ММ.ГГГГ ЧЧ:ММ
                            return datetime.strptime(time_str, '%d.%m.%Y %H:%M')
                        else:  # Формат ГГГГ-ММ-ДД ЧЧ:ММ
                            return datetime.strptime(time_str, '%Y-%m-%d %H:%M')
            
            # Если не удалось распарсить, возвращаем время через 24 часа
            return datetime.now() + timedelta(hours=24)
        
        except Exception as e:
            logger.error(f"Error parsing KHL match time '{time_text}': {e}")
            return datetime.now() + timedelta(hours=24)
    
    def _parse_odds_value(self, odds_text: str) -> float:
        """Парсинг значения коэффициента"""
        try:
            # Удаляем все символы кроме цифр и точки
            clean_text = re.sub(r'[^\d.]', '', odds_text)
            if clean_text:
                return float(clean_text)
            return 2.10  # Значение по умолчанию для КХЛ
        except:
            return 2.10
    
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
