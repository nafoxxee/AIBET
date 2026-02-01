#!/usr/bin/env python3
"""
AIBET CS2 Parser - Fixed Version
Только HTML парсинг с Liquipedia и HLTV.org
Без API, с кешированием в SQLite
"""

import asyncio
import aiohttp
import sqlite3
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class CS2ParserFixed:
    def __init__(self):
        self.db_path = "data/cs2_cache.db"
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
        
        # Источники (ТОЛЬКО HTML)
        self.sources = {
            'liquipedia': {
                'url': 'https://liquipedia.net/counterstrike/Portal:Matches',
                'priority': 1,
                'enabled': True
            },
            'hltv': {
                'url': 'https://www.hltv.org/matches',
                'priority': 2,
                'enabled': True  # Fallback только
            }
        }
        
        # Топ-30 CS2 команд (для фильтрации)
        self.top_teams = [
            'NaVi', 'FaZe', 'G2', 'Vitality', 'Astralis', 'Heroic', 'Cloud9', 'Fnatic',
            'Team Liquid', 'Complexity', 'Evil Geniuses', 'FURIA', 'MOUZ', 'BIG', 'NIP',
            'ENCE', 'OG', 'Virtus.pro', 'forZe', '9INE', 'Imperial', '00 Nation', 'MIBR',
            'paiN', '9z', 'TYLOO', 'Lynn Vision', 'Rare Atom', 'Monte', 'B8', 'Sangal'
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
        logger.info("✅ CS2 cache database initialized")
    
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
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
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
                        else:
                            # При 403 от HLTV - пропускаем источник
                            if source_name == 'hltv':
                                logger.warning(f"⚠️ HLTV blocked, skipping...")
                                return None
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
    
    def is_top_team(self, team_name: str) -> bool:
        """Проверить, что команда в топе"""
        team_lower = team_name.lower()
        for top_team in self.top_teams:
            if top_team.lower() in team_lower:
                return True
        return False
    
    def parse_liquipedia_matches(self, html: str) -> List[Dict]:
        """Парсинг матчей с Liquipedia"""
        matches = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Liquipedia использует таблицы для матчей
            match_table = soup.find('table', class_='infobox_matches_content')
            if not match_table:
                # Альтернативный поиск
                match_table = soup.find('div', class_='matches-list')
            
            if match_table:
                rows = match_table.find_all('tr')
                
                for row in rows:
                    try:
                        cells = row.find_all('td')
                        if len(cells) >= 3:
                            # Извлечение команд
                            team1_elem = cells[0].find('span', class_='team-template-text')
                            team2_elem = cells[2].find('span', class_='team-template-text')
                            
                            if not team1_elem or not team2_elem:
                                continue
                            
                            team1 = team1_elem.get_text(strip=True)
                            team2 = team2_elem.get_text(strip=True)
                            
                            # Фильтрация топ команд
                            if not (self.is_top_team(team1) or self.is_top_team(team2)):
                                continue
                            
                            # Извлечение времени
                            time_cell = cells[1]
                            time_elem = time_cell.find('span', class_='timer-object')
                            match_time = time_elem.get_text(strip=True) if time_elem else time_cell.get_text(strip=True)
                            
                            # Извлечение турнира
                            tournament_elem = row.find('div', class_='tournament-text')
                            tournament = tournament_elem.get_text(strip=True) if tournament_elem else 'Unknown Tournament'
                            
                            # Извлечение формата
                            format_elem = row.find('div', class_='match-format')
                            match_format = format_elem.get_text(strip=True) if format_elem else 'BO1'
                            
                            # Извлечение ссылки
                            link_elem = row.find('a', href=True)
                            match_link = link_elem['href'] if link_elem else ''
                            
                            match_data = {
                                'match_id': f"liquipedia_{hash(team1 + team2 + match_time)}",
                                'team1': team1,
                                'team2': team2,
                                'tournament': tournament,
                                'sport': 'cs2',
                                'date': match_time,
                                'status': 'upcoming',
                                'format': match_format,
                                'link': match_link,
                                'source': 'liquipedia'
                            }
                            matches.append(match_data)
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing Liquipedia row: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Error parsing Liquipedia matches: {e}")
        
        logger.info(f"📊 Liquipedia: Found {len(matches)} top CS2 matches")
        return matches
    
    def parse_hltv_matches(self, html: str) -> List[Dict]:
        """Парсинг матчей с HLTV.org (только HTML)"""
        matches = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # HLTV использует div с классом match-day
            match_days = soup.find_all('div', class_='match-day')
            
            for match_day in match_days:
                try:
                    # Извлечение даты
                    date_elem = match_day.find('div', class_='standard-headline')
                    match_date = date_elem.get_text(strip=True) if date_elem else 'Unknown'
                    
                    # Поиск матчей за день
                    match_elements = match_day.find_all('div', class_='match')
                    
                    for element in match_elements:
                        try:
                            # Извлечение команд
                            team_elements = element.find_all('div', class_='team')
                            if len(team_elements) < 2:
                                continue
                            
                            team1 = team_elements[0].get_text(strip=True)
                            team2 = team_elements[1].get_text(strip=True)
                            
                            # Фильтрация топ команд
                            if not (self.is_top_team(team1) or self.is_top_team(team2)):
                                continue
                            
                            # Извлечение времени
                            time_elem = element.find('div', class_='time')
                            match_time = time_elem.get_text(strip=True) if time_elem else ''
                            
                            # Извлечение турнира
                            event_elem = element.find('div', class_='event')
                            tournament = event_elem.get_text(strip=True) if event_elem else 'Unknown Tournament'
                            
                            # Извлечение формата
                            format_elem = element.find('div', class_='best-of')
                            match_format = format_elem.get_text(strip=True) if format_elem else 'BO1'
                            
                            # Извлечение ссылки
                            link_elem = element.find('a', href=True)
                            match_link = link_elem['href'] if link_elem else ''
                            
                            match_data = {
                                'match_id': f"hltv_{hash(team1 + team2 + match_time)}",
                                'team1': team1,
                                'team2': team2,
                                'tournament': tournament,
                                'sport': 'cs2',
                                'date': f"{match_date} {match_time}",
                                'status': 'upcoming',
                                'format': match_format,
                                'link': f"https://www.hltv.org{match_link}" if match_link.startswith('/') else match_link,
                                'source': 'hltv'
                            }
                            matches.append(match_data)
                            
                        except Exception as e:
                            logger.warning(f"⚠️ Error parsing HLTV match element: {e}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing HLTV match day: {e}")
                    continue
                            
        except Exception as e:
            logger.error(f"❌ Error parsing HLTV matches: {e}")
        
        logger.info(f"📊 HLTV: Found {len(matches)} top CS2 matches")
        return matches
    
    async def parse_matches(self) -> List[Dict]:
        """Основной метод парсинга"""
        logger.info("🚀 Starting CS2 Parser (Fixed)")
        
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
                        if source_name == 'liquipedia':
                            matches = self.parse_liquipedia_matches(html)
                        elif source_name == 'hltv':
                            matches = self.parse_hltv_matches(html)
                        else:
                            continue
                        
                        all_matches.extend(matches)
                        
                        # Если получили достаточно матчей, не продолжаем
                        if len(all_matches) >= 10:
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
            
            logger.info(f"✅ CS2 Parser completed: {len(unique_matches)} unique matches")
            return unique_matches
            
        except Exception as e:
            logger.error(f"❌ CS2 Parser error: {e}")
            return []
        finally:
            if self.session:
                await self.session.close()

# Импорт os для создания директории
import os
