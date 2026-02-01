#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real KHL Data Source
Получение реальных данных матчей КХЛ из Livesport и других источников
"""

import asyncio
import aiohttp
import json
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class RealKHLDataSource:
    def __init__(self):
        self.base_urls = [
            "https://www.livesport.com/ru/hockey/russia/",
            "https://www.flashscore.ru/hockey/russia/khl/",
            "https://ru.soccerway.com/national/russia/khl/"
        ]
        
        # Rotating User-Agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        self.session = None
        self.current_ua_index = 0
    
    def get_random_headers(self) -> Dict[str, str]:
        """Получить случайные заголовки для запроса"""
        ua = self.user_agents[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        
        return {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    async def initialize(self):
        """Инициализация сессии"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
    
    async def fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Запрос с retry и обработкой ошибок"""
        for attempt in range(max_retries):
            try:
                # Случайная задержка
                await asyncio.sleep(random.uniform(1, 3))
                
                headers = self.get_random_headers()
                
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 403:
                        logger.warning(f"⚠️ 403 Forbidden for {url} (attempt {attempt + 1})")
                        if attempt < max_retries - 1:
                            # Смена User-Agent и retry
                            await asyncio.sleep(5)
                            continue
                        else:
                            # Пробуем другой источник
                            return None
                    elif response.status == 429:
                        logger.warning(f"⚠️ Rate limited for {url} (attempt {attempt + 1})")
                        await asyncio.sleep(10)
                        continue
                    else:
                        logger.warning(f"⚠️ HTTP {response.status} for {url}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2)
                            continue
                        
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Timeout for {url} (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
                    continue
            except Exception as e:
                logger.warning(f"⚠️ Error fetching {url}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
        
        return None
    
    async def get_livesport_matches(self) -> List[Dict[str, Any]]:
        """Получение матчей с Livesport"""
        matches = []
        
        try:
            url = self.base_urls[0]
            html = await self.fetch_with_retry(url)
            
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем контейнер с матчами КХЛ
            match_containers = soup.select('.event__match, .sportName.soccer, .events__match')
            
            for container in match_containers:
                try:
                    match = await self.parse_livesport_match(container)
                    if match and 'khl' in match.get('tournament', '').lower():
                        matches.append(match)
                except Exception as e:
                    continue
            
            logger.info(f"🏒 Got {len(matches)} KHL matches from Livesport")
            return matches
            
        except Exception as e:
            logger.warning(f"⚠️ Error fetching Livesport matches: {e}")
            return []
    
    async def parse_livesport_match(self, container) -> Optional[Dict[str, Any]]:
        """Парсинг матча Livesport"""
        try:
            # Команды
            team_elements = container.select('.event__participant--home, .event__participant--away, .team-name')
            if len(team_elements) < 2:
                return None
            
            team1 = team_elements[0].get_text(strip=True)
            team2 = team_elements[1].get_text(strip=True)
            
            # Счет
            score_elements = container.select('.event__score, .score')
            score = ""
            if score_elements:
                score = score_elements[0].get_text(strip=True)
            
            # Время
            time_element = container.select_one('.event__time, .time')
            start_time = None
            if time_element:
                time_text = time_element.get_text(strip=True)
                start_time = self.parse_time(time_text)
            
            # Статус
            status = "upcoming"
            if score and ":" in score:
                status = "live"
            elif score and ("-" in score or ":" in score):
                status = "finished"
            
            # Турнир
            tournament_element = container.select_one('.event__title, .tournament-name')
            tournament = tournament_element.get_text(strip=True) if tournament_element else "KHL"
            
            # URL матча
            match_url = container.get('href') or container.select_one('a')
            if match_url:
                if isinstance(match_url, str):
                    match_url = urljoin(self.base_urls[0], match_url)
                else:
                    match_url = match_url.get('href')
                    if match_url:
                        match_url = urljoin(self.base_urls[0], match_url)
            
            return {
                'id': f"ls_{hash(team1 + team2 + str(start_time))}",
                'sport': 'khl',
                'team1': team1,
                'team2': team2,
                'score': score,
                'status': status,
                'start_time': start_time,
                'tournament': tournament,
                'url': match_url,
                'source': 'livesport',
                'features': {
                    'importance': self.get_tournament_importance(tournament),
                    'format': 'Regular Season'
                }
            }
            
        except Exception as e:
            return None
    
    async def get_flashscore_matches(self) -> List[Dict[str, Any]]:
        """Получение матчей с Flashscore"""
        matches = []
        
        try:
            url = self.base_urls[1]
            html = await self.fetch_with_retry(url)
            
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем матчи
            match_elements = soup.select('.match, .event__match, .fixtures__match')
            
            for element in match_elements:
                try:
                    match = await self.parse_flashscore_match(element)
                    if match:
                        matches.append(match)
                except Exception as e:
                    continue
            
            logger.info(f"🏒 Got {len(matches)} KHL matches from Flashscore")
            return matches
            
        except Exception as e:
            logger.warning(f"⚠️ Error fetching Flashscore matches: {e}")
            return []
    
    async def parse_flashscore_match(self, element) -> Optional[Dict[str, Any]]:
        """Парсинг матча Flashscore"""
        try:
            # Команды
            team_elements = element.select('.team-name, .participant, .tname')
            if len(team_elements) < 2:
                return None
            
            team1 = team_elements[0].get_text(strip=True)
            team2 = team_elements[1].get_text(strip=True)
            
            # Счет
            score_element = element.select_one('.score, .result')
            score = score_element.get_text(strip=True) if score_element else ""
            
            # Время
            time_element = element.select_one('.time, .startTime')
            start_time = None
            if time_element:
                time_text = time_element.get_text(strip=True)
                start_time = self.parse_time(time_text)
            
            # Статус
            status = "upcoming"
            if score and ":" in score:
                status = "live"
            elif score and "-" in score:
                status = "finished"
            
            # Турнир
            tournament_element = element.select_one('.category, .tournament')
            tournament = tournament_element.get_text(strip=True) if tournament_element else "KHL"
            
            return {
                'id': f"fs_{hash(team1 + team2 + str(start_time))}",
                'sport': 'khl',
                'team1': team1,
                'team2': team2,
                'score': score,
                'status': status,
                'start_time': start_time,
                'tournament': tournament,
                'url': '',
                'source': 'flashscore',
                'features': {
                    'importance': self.get_tournament_importance(tournament),
                    'format': 'Regular Season'
                }
            }
            
        except Exception as e:
            return None
    
    def parse_time(self, time_text: str) -> Optional[datetime]:
        """Парсинг времени матча"""
        try:
            time_text = time_text.strip().lower()
            
            # Разные форматы времени
            if 'today' in time_text or 'сегодня' in time_text:
                # Извлекаем время
                time_part = time_text.replace('today', '').replace('сегодня', '').strip()
                if ':' in time_part:
                    hour, minute = map(int, time_part.split(':'))
                    now = datetime.now()
                    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            elif 'tomorrow' in time_text or 'завтра' in time_text:
                time_part = time_text.replace('tomorrow', '').replace('завтра', '').strip()
                if ':' in time_part:
                    hour, minute = map(int, time_part.split(':'))
                    tomorrow = datetime.now() + timedelta(days=1)
                    return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            elif 'ago' in time_text:
                # Формат "2h ago"
                if 'h' in time_text:
                    hours = int(time_text.split('h')[0])
                    return datetime.utcnow() - timedelta(hours=hours)
                elif 'm' in time_text:
                    minutes = int(time_text.split('m')[0])
                    return datetime.utcnow() - timedelta(minutes=minutes)
            
            # Стандартный формат HH:MM
            elif ':' in time_text:
                hour, minute = map(int, time_text.split(':'))
                now = datetime.now()
                result = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                # Если время уже прошло, считаем на завтра
                if result < now:
                    result += timedelta(days=1)
                return result
            
            return None
            
        except Exception:
            return None
    
    def get_tournament_importance(self, tournament: str) -> int:
        """Определение важности турнира"""
        tournament_lower = tournament.lower()
        
        if any(word in tournament_lower for word in ['playoffs', 'плей-офф', 'финал', 'final']):
            return 10
        elif any(word in tournament_lower for word in ['conference', 'конференция']):
            return 8
        elif any(word in tournament_lower for word in ['regular season', 'регулярный чемпионат']):
            return 6
        elif any(word in tournament_lower for word in ['preseason', 'предсезонный']):
            return 4
        else:
            return 5
    
    async def get_all_matches(self) -> List[Dict[str, Any]]:
        """Получение всех матчей из всех источников"""
        await self.initialize()
        
        all_matches = []
        
        try:
            # Livesport основной источник
            livesport_matches = await self.get_livesport_matches()
            all_matches.extend(livesport_matches)
            
            # Flashscore fallback
            if len(all_matches) < 20:
                flashscore_matches = await self.get_flashscore_matches()
                all_matches.extend(flashscore_matches)
            
            # Удаляем дубликаты
            unique_matches = self.deduplicate_matches(all_matches)
            
            logger.info(f"🏒 Total unique KHL matches: {len(unique_matches)}")
            return unique_matches
            
        except Exception as e:
            logger.error(f"❌ Error getting KHL matches: {e}")
            return []
        finally:
            await self.close()
    
    def deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Удаление дубликатов матчей"""
        seen = set()
        unique_matches = []
        
        for match in matches:
            # Создаем уникальный ключ из команд и времени
            key = f"{match['team1']}_{match['team2']}_{match.get('start_time', '')}"
            
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return unique_matches

# Глобальный экземпляр
real_khl_source = RealKHLDataSource()
