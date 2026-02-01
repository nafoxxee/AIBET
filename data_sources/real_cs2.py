#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real CS2 Data Source
Получение реальных данных матчей CS2 из HLTV и других источников
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

class RealCS2DataSource:
    def __init__(self):
        self.base_urls = [
            "https://www.hltv.org",
            "https://www.hltv.com"
        ]
        self.lqpedia_url = "https://liquipedia.net/counterstrike"
        
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
            'Accept-Language': 'en-US,en;q=0.5',
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
    
    async def get_hltv_matches(self) -> List[Dict[str, Any]]:
        """Получение матчей с HLTV"""
        matches = []
        
        for base_url in self.base_urls:
            try:
                # Live матчи
                live_url = f"{base_url}/matches"
                html = await self.fetch_with_retry(live_url)
                
                if html:
                    live_matches = await self.parse_hltv_matches_page(html, "live")
                    matches.extend(live_matches)
                    logger.info(f"🔴 Got {len(live_matches)} live matches from {base_url}")
                
                # Upcoming матчи
                upcoming_url = f"{base_url}/matches/upcoming"
                html = await self.fetch_with_retry(upcoming_url)
                
                if html:
                    upcoming_matches = await self.parse_hltv_matches_page(html, "upcoming")
                    matches.extend(upcoming_matches)
                    logger.info(f"🔴 Got {len(upcoming_matches)} upcoming matches from {base_url}")
                
                # Если получили достаточно матчей, выходим
                if len(matches) >= 50:
                    break
                    
            except Exception as e:
                logger.warning(f"⚠️ Error parsing {base_url}: {e}")
                continue
        
        return matches
    
    async def parse_hltv_matches_page(self, html: str, match_type: str) -> List[Dict[str, Any]]:
        """Парсинг страницы матчей HLTV"""
        soup = BeautifulSoup(html, 'html.parser')
        matches = []
        
        # Разные селекторы для разных типов матчей
        if match_type == "live":
            selectors = [
                'a.match.a-reset',
                'div.live-match',
                'div.match-live',
                'tr.match-row'
            ]
        else:
            selectors = [
                'a.match.a-reset',
                'div.match',
                'div.upcoming-match',
                'tr.match-row'
            ]
        
        for selector in selectors:
            elements = soup.select(selector)
            logger.info(f"🔴 Found {len(elements)} elements with selector: {selector}")
            
            for element in elements:
                try:
                    match = await self.parse_hltv_match_element(element, match_type)
                    if match:
                        matches.append(match)
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing match element: {e}")
                    continue
            
            if matches:
                break
        
        return matches
    
    async def parse_hltv_match_element(self, element, match_type: str) -> Optional[Dict[str, Any]]:
        """Парсинг отдельного элемента матча"""
        try:
            # Извлекаем команды
            team_elements = element.select('.team-name, .team, td.team')
            if len(team_elements) < 2:
                return None
            
            team1 = team_elements[0].get_text(strip=True)
            team2 = team_elements[1].get_text(strip=True)
            
            if not team1 or not team2:
                return None
            
            # Извлекаем время
            time_element = element.select_one('.time, .match-time, .date')
            start_time = None
            if time_element:
                time_text = time_element.get_text(strip=True)
                start_time = self.parse_time(time_text)
            
            # Извлекаем счет
            score_element = element.select_one('.score, .match-score, .result')
            score = ""
            if score_element:
                score = score_element.get_text(strip=True)
            
            # Извлекаем турнир
            tournament_element = element.select_one('.event-name, .tournament, .event')
            tournament = tournament_element.get_text(strip=True) if tournament_element else "Unknown"
            
            # Извлекаем URL матча
            match_url = element.get('href') or element.select_one('a')['href']
            if match_url:
                match_url = urljoin("https://www.hltv.org", match_url)
            
            # Определяем статус
            status = match_type
            if match_type == "live" and score:
                status = "live"
            elif match_type == "upcoming" and not score:
                status = "upcoming"
            elif score and "-" in score:
                status = "finished"
            
            # Извлекаем ID матча
            match_id = element.get('data-match-id') or element.get('id')
            if not match_id and match_url:
                # Извлекаем ID из URL
                path_parts = urlparse(match_url).path.split('/')
                if 'match' in path_parts:
                    match_index = path_parts.index('match')
                    if match_index + 1 < len(path_parts):
                        match_id = path_parts[match_index + 1]
            
            return {
                'id': match_id,
                'sport': 'cs2',
                'team1': team1,
                'team2': team2,
                'score': score,
                'status': status,
                'start_time': start_time,
                'tournament': tournament,
                'url': match_url,
                'source': 'hltv',
                'features': {
                    'importance': self.get_tournament_importance(tournament),
                    'format': self.get_match_format(element)
                }
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing match element: {e}")
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
        
        if any(word in tournament_lower for word in ['major', 'championship', 'world']):
            return 10
        elif any(word in tournament_lower for word in ['blast premier', 'iem', 'esl pro league']):
            return 9
        elif any(word in tournament_lower for word in ['esl', 'blast', 'iem katowice', 'iem cologne']):
            return 8
        elif any(word in tournament_lower for word in ['premier', 'masters', 'showdown']):
            return 7
        elif any(word in tournament_lower for word in ['cup', 'trophy', 'open']):
            return 6
        elif any(word in tournament_lower for word in ['qualifier', 'qualification']):
            return 5
        else:
            return 4
    
    def get_match_format(self, element) -> str:
        """Определение формата матча"""
        text = element.get_text().lower()
        
        if 'bo5' in text:
            return 'BO5'
        elif 'bo3' in text:
            return 'BO3'
        elif 'bo1' in text:
            return 'BO1'
        else:
            return 'BO3'  # По умолчанию
    
    async def get_liquipedia_matches(self) -> List[Dict[str, Any]]:
        """Получение матчей с Liquipedia"""
        try:
            url = f"{self.lqpedia_url}/Liquipedia:Upcoming_matches"
            html = await self.fetch_with_retry(url)
            
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            matches = []
            
            # Ищем таблицы с матчами
            match_tables = soup.select('.infobox_matches_content')
            
            for table in match_tables:
                rows = table.select('tr')
                for row in rows:
                    try:
                        match = await self.parse_liquipedia_row(row)
                        if match:
                            matches.append(match)
                    except Exception as e:
                        continue
            
            logger.info(f"🔴 Got {len(matches)} matches from Liquipedia")
            return matches
            
        except Exception as e:
            logger.warning(f"⚠️ Error fetching Liquipedia matches: {e}")
            return []
    
    async def parse_liquipedia_row(self, row) -> Optional[Dict[str, Any]]:
        """Парсинг строки матча Liquipedia"""
        try:
            cells = row.select('td')
            if len(cells) < 3:
                return None
            
            # Извлекаем данные
            time_cell = cells[0]
            match_cell = cells[1]
            tournament_cell = cells[2] if len(cells) > 2 else None
            
            # Команды
            team_elements = match_cell.select('.team-template-text')
            if len(team_elements) < 2:
                return None
            
            team1 = team_elements[0].get_text(strip=True)
            team2 = team_elements[1].get_text(strip=True)
            
            # Время
            time_text = time_cell.get_text(strip=True)
            start_time = self.parse_time(time_text)
            
            # Турнир
            tournament = tournament_cell.get_text(strip=True) if tournament_cell else "Unknown"
            
            return {
                'id': f"lqp_{hash(team1 + team2 + str(start_time))}",
                'sport': 'cs2',
                'team1': team1,
                'team2': team2,
                'score': '',
                'status': 'upcoming',
                'start_time': start_time,
                'tournament': tournament,
                'url': '',
                'source': 'liquipedia',
                'features': {
                    'importance': self.get_tournament_importance(tournament),
                    'format': 'BO3'
                }
            }
            
        except Exception as e:
            return None
    
    async def get_all_matches(self) -> List[Dict[str, Any]]:
        """Получение всех матчей из всех источников"""
        await self.initialize()
        
        all_matches = []
        
        try:
            # HLTV основной источник
            hltv_matches = await self.get_hltv_matches()
            all_matches.extend(hltv_matches)
            
            # Liquipedia fallback
            if len(all_matches) < 20:
                liquipedia_matches = await self.get_liquipedia_matches()
                all_matches.extend(liquipedia_matches)
            
            # Удаляем дубликаты
            unique_matches = self.deduplicate_matches(all_matches)
            
            logger.info(f"🔴 Total unique CS2 matches: {len(unique_matches)}")
            return unique_matches
            
        except Exception as e:
            logger.error(f"❌ Error getting CS2 matches: {e}")
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
real_cs2_source = RealCS2DataSource()
