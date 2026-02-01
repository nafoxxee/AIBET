#!/usr/bin/env python3
"""
AIBET KHL Parser - Fixed Version
HTML парсинг с Livesport и KHL.ru
С кешированием в SQLite
"""

import asyncio
import aiohttp
import sqlite3
import json
import logging
import random
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class KHLParserFixed:
    def __init__(self):
        self.db_path = "data/khl_cache.db"
        self.session_timeout = aiohttp.ClientTimeout(total=15)
        self.max_retries = 3
        self.cache_hours = 6  # Кеширование на 6 часов
        
        # User-Agent для обхода блокировок
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Источники КХЛ
        self.sources = {
            'livesport': {
                'url': 'https://www.livesport.com/ru/hockey/russia/khl/',
                'priority': 1,
                'enabled': True
            },
            'khl_official': {
                'url': 'https://khl.ru/calendar/',
                'priority': 2,
                'enabled': True
            }
        }
        
        # Топ КХЛ команды
        self.khl_teams = [
            'CSKA Moscow', 'SKA Saint Petersburg', 'Ak Bars Kazan', 'Metallurg Magnitogorsk',
            'Salavat Yulaev Ufa', ' Lokomotiv Yaroslavl', 'Barys Nur-Sultan', 'Traktor Chelyabinsk',
            'Avangard Omsk', 'Dinamo Moscow', 'Dinamo Minsk', 'Dinamo Riga',
            'Jokerit Helsinki', 'Severstal Cherepovets', 'Neftekhimik Nizhnekamsk',
            'Vityaz Podolsk', 'Sibir Novosibirsk', 'Amur Khabarovsk', 'Admiral Vladivostok',
            'Kunlun Red Star Beijing', 'HC Sochi', 'Torpedo Nizhny Novgorod'
        ]
        
        self.session = None
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Инициализация базы данных для кеширования"""
        os.makedirs("data", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                source TEXT PRIMARY KEY,
                data TEXT,
                timestamp DATETIME,
                expires_at DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ KHL cache database initialized")
    
    def _get_cached_data(self, source: str) -> Optional[Dict]:
        """Получить данные из кеша"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT data, expires_at FROM cache 
            WHERE source = ? AND expires_at > datetime('now')
        ''', (source,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            logger.info(f"📦 Using cached data for {source}")
            return json.loads(result[0])
        
        return None
    
    def _save_cached_data(self, source: str, data: Dict):
        """Сохранить данные в кеш"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(hours=self.cache_hours)
        
        cursor.execute('''
            INSERT OR REPLACE INTO cache (source, data, timestamp, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (source, json.dumps(data), datetime.now(), expires_at))
        
        conn.commit()
        conn.close()
        logger.info(f"💾 Cached data for {source} (expires: {expires_at})")
    
    def get_headers(self) -> Dict[str, str]:
        """Получить случайные headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    async def fetch_page(self, url: str, source_name: str) -> Optional[str]:
        """Загрузить страницу с retry и задержкой"""
        # Проверяем кеш
        cached = self._get_cached_data(source_name)
        if cached:
            return cached.get('html')
        
        for attempt in range(self.max_retries):
            try:
                # Задержка между запросами
                await asyncio.sleep(random.uniform(2, 4))
                
                headers = self.get_headers()
                
                async with self.session.get(url, headers=headers, timeout=self.session_timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Кешируем результат
                        self._save_cached_data(source_name, {'html': html})
                        
                        logger.info(f"✅ Successfully fetched {source_name}")
                        return html
                    elif response.status == 403:
                        logger.warning(f"⚠️ 403 Forbidden for {source_name} (attempt {attempt + 1})")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(5)
                            continue
                    elif response.status == 429:
                        logger.warning(f"⚠️ 429 Rate Limited for {source_name} (attempt {attempt + 1})")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(10)
                            continue
                    else:
                        logger.warning(f"⚠️ HTTP {response.status} for {source_name}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Timeout for {source_name} (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(3)
                    continue
            except Exception as e:
                logger.error(f"❌ Error fetching {source_name}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2)
                    continue
        
        logger.error(f"❌ Failed to fetch {source_name} after {self.max_retries} attempts")
        return None
    
    def is_khl_team(self, team_name: str) -> bool:
        """Проверить, что команда КХЛ"""
        team_lower = team_name.lower()
        for khl_team in self.khl_teams:
            if khl_team.lower() in team_lower:
                return True
        return False
    
    def parse_livesport_matches(self, html: str) -> List[Dict]:
        """Парсинг матчей с Livesport"""
        matches = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Livesport использует div с классом event__match
            match_elements = soup.find_all('div', class_='event__match')
            
            for element in match_elements:
                try:
                    # Извлечение команд
                    team_elements = element.find_all('div', class_='event__participant')
                    if len(team_elements) < 2:
                        continue
                    
                    team1 = team_elements[0].get_text(strip=True)
                    team2 = team_elements[1].get_text(strip=True)
                    
                    # Фильтрация КХЛ команд
                    if not (self.is_khl_team(team1) or self.is_khl_team(team2)):
                        continue
                    
                    # Извлечение времени
                    time_elem = element.find('div', class_='event__time')
                    match_time = time_elem.get_text(strip=True) if time_elem else ''
                    
                    # Извлечение даты
                    date_elem = element.find('div', class_='event__date')
                    match_date = date_elem.get_text(strip=True) if date_elem else ''
                    
                    # Извлечение статуса
                    status_elem = element.find('div', class_='event__stage')
                    status = status_elem.get_text(strip=True) if status_elem else 'upcoming'
                    
                    # Извлечение счета
                    score_elem = element.find('div', class_='event__score')
                    score = score_elem.get_text(strip=True) if score_elem else ''
                    
                    # Извлечение турнира
                    tournament_elem = element.find('div', class_='event__title')
                    tournament = tournament_elem.get_text(strip=True) if tournament_elem else 'KHL'
                    
                    # Извлечение ссылки
                    link_elem = element.find('a', href=True)
                    match_link = link_elem['href'] if link_elem else ''
                    
                    match_data = {
                        'match_id': f"livesport_{hash(team1 + team2 + match_time)}",
                        'team1': team1,
                        'team2': team2,
                        'tournament': tournament,
                        'sport': 'khl',
                        'date': f"{match_date} {match_time}".strip(),
                        'status': 'live' if 'live' in status.lower() else ('finished' if score else 'upcoming'),
                        'score': score if score else None,
                        'link': f"https://www.livesport.com{match_link}" if match_link.startswith('/') else match_link,
                        'source': 'livesport'
                    }
                    matches.append(match_data)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing livesport match: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error parsing livesport matches: {e}")
        
        logger.info(f"📊 Livesport: Found {len(matches)} KHL matches")
        return matches
    
    def parse_khl_official_matches(self, html: str) -> List[Dict]:
        """Парсинг матчей с официального сайта КХЛ"""
        matches = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Официальный сайт КХЛ использует таблицы
            match_table = soup.find('table', class_='schedule')
            if not match_table:
                # Альтернативный поиск
                match_table = soup.find('div', class_='calendar')
            
            if match_table:
                rows = match_table.find_all('tr')
                
                for row in rows:
                    try:
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            # Извлечение даты
                            date_cell = cells[0]
                            match_date = date_cell.get_text(strip=True)
                            
                            # Извлечение времени
                            time_cell = cells[1]
                            match_time = time_cell.get_text(strip=True)
                            
                            # Извлечение команд
                            team1_cell = cells[2]
                            team2_cell = cells[3]
                            
                            team1 = team1_cell.get_text(strip=True)
                            team2 = team2_cell.get_text(strip=True)
                            
                            # Фильтрация КХЛ команд
                            if not (self.is_khl_team(team1) or self.is_khl_team(team2)):
                                continue
                            
                            # Извлечение счета
                            score = ''
                            if len(cells) >= 5:
                                score_cell = cells[4]
                                score = score_cell.get_text(strip=True)
                            
                            # Определение статуса
                            status = 'upcoming'
                            if score and ':' in score:
                                status = 'finished'
                            elif 'live' in match_time.lower():
                                status = 'live'
                            
                            match_data = {
                                'match_id': f"khl_{hash(team1 + team2 + match_date + match_time)}",
                                'team1': team1,
                                'team2': team2,
                                'tournament': 'KHL',
                                'sport': 'khl',
                                'date': f"{match_date} {match_time}".strip(),
                                'status': status,
                                'score': score if score else None,
                                'link': 'https://khl.ru/calendar/',
                                'source': 'khl_official'
                            }
                            matches.append(match_data)
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing KHL official row: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Error parsing KHL official matches: {e}")
        
        logger.info(f"📊 KHL Official: Found {len(matches)} matches")
        return matches
    
    async def parse_matches(self) -> List[Dict]:
        """Основной метод парсинга"""
        logger.info("🚀 Starting KHL Parser (Fixed)")
        
        # Создаем сессию
        self.session = aiohttp.ClientSession(timeout=self.session_timeout)
        
        try:
            all_matches = []
            
            # Сортируем источники по приоритету
            sorted_sources = sorted(
                [(name, config) for name, config in self.sources.items() if config['enabled']],
                key=lambda x: x[1]['priority']
            )
            
            for source_name, source_config in sorted_sources:
                try:
                    logger.info(f"📊 Parsing {source_name}...")
                    
                    html = await self.fetch_page(source_config['url'], source_name)
                    if html:
                        if source_name == 'livesport':
                            matches = self.parse_livesport_matches(html)
                        elif source_name == 'khl_official':
                            matches = self.parse_khl_official_matches(html)
                        else:
                            continue
                        
                        all_matches.extend(matches)
                        
                        # Если получили достаточно матчей, не продолжаем
                        if len(all_matches) >= 15:
                            logger.info(f"✅ Got enough matches ({len(all_matches)}), stopping")
                            break
                    else:
                        logger.warning(f"⚠️ No data from {source_name}")
                        continue
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing {source_name}: {e}")
                    continue
            
            # Удаление дубликатов
            unique_matches = []
            seen_matches = set()
            
            for match in all_matches:
                match_key = f"{match['team1']}_{match['team2']}_{match['date']}"
                if match_key not in seen_matches:
                    unique_matches.append(match)
                    seen_matches.add(match_key)
            
            logger.info(f"✅ KHL Parser completed: {len(unique_matches)} unique matches")
            return unique_matches
            
        except Exception as e:
            logger.error(f"❌ KHL Parser error: {e}")
            return []
        finally:
            if self.session:
                await self.session.close()
