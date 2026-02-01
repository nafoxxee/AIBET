#!/usr/bin/env python3
"""
AIBET CS2 Pre-Match Data Source
Только стабильные pre-match источники без live данных
"""

import asyncio
import aiohttp
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

class CS2PreMatchSource:
    def __init__(self):
        self.cache_file = "data/cs2_pre_match_cache.json"
        self.cache_hours = 12  # Кеширование на 12 часов
        self.session_timeout = aiohttp.ClientTimeout(total=15)
        self.max_retries = 2
        
        # User-Agent для обхода блокировок
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # ТОЛЬКО стабильные pre-match источники
        self.pre_match_sources = {
            'hltv_matches': {
                'url': 'https://www.hltv.org/matches',
                'enabled': True,
                'priority': 1
            },
            'hltv_upcoming': {
                'url': 'https://www.hltv.org/matches/upcoming',
                'enabled': True,
                'priority': 2
            }
        }
        
        # Топ-30 CS2 команд для фильтрации
        self.top_teams = [
            'NaVi', 'FaZe', 'G2', 'Vitality', 'Astralis', 'Heroic', 'Cloud9', 'Fnatic',
            'Team Liquid', 'Complexity', 'Evil Geniuses', 'FURIA', 'MOUZ', 'BIG', 'NIP',
            'ENCE', 'OG', 'Virtus.pro', 'forZe', '9INE', 'Imperial', '00 Nation', 'MIBR',
            'paiN', '9z', 'TYLOO', 'Lynn Vision', 'Rare Atom', 'Monte', 'B8', 'Sangal'
        ]
        
        self.session = None
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Создать директорию для кеша"""
        os.makedirs("data", exist_ok=True)
    
    def _load_cache(self) -> Dict:
        """Загрузить кеш"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                # Проверяем актуальность кеша
                cache_time = datetime.fromisoformat(cache_data.get('timestamp', '1970-01-01'))
                if datetime.now() - cache_time < timedelta(hours=self.cache_hours):
                    logger.info("📦 Using cached CS2 pre-match data")
                    return cache_data.get('matches', [])
                    
        except Exception as e:
            logger.warning(f"⚠️ Error loading cache: {e}")
        
        return None
    
    def _save_cache(self, matches: List[Dict]):
        """Сохранить кеш"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'matches': matches
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"💾 Cached {len(matches)} CS2 pre-match matches")
            
        except Exception as e:
            logger.warning(f"⚠️ Error saving cache: {e}")
    
    def get_headers(self) -> Dict[str, str]:
        """Получить случайные headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def fetch_page(self, url: str, source_name: str) -> Optional[str]:
        """Загрузить страницу с retry"""
        for attempt in range(self.max_retries):
            try:
                # Задержка между запросами
                await asyncio.sleep(random.uniform(3, 6))
                
                headers = self.get_headers()
                
                async with self.session.get(url, headers=headers, timeout=self.session_timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        logger.info(f"✅ Successfully fetched {source_name}")
                        return html
                    elif response.status == 403:
                        logger.warning(f"⚠️ 403 Forbidden for {source_name} - skipping")
                        return None
                    elif response.status == 429:
                        logger.warning(f"⚠️ 429 Rate Limited for {source_name} - skipping")
                        return None
                    else:
                        logger.warning(f"⚠️ HTTP {response.status} for {source_name}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Timeout for {source_name}")
                continue
            except Exception as e:
                logger.warning(f"⚠️ Error fetching {source_name}: {e}")
                continue
        
        logger.error(f"❌ Failed to fetch {source_name}")
        return None
    
    def is_top_team(self, team_name: str) -> bool:
        """Проверить, что команда в топе"""
        team_lower = team_name.lower()
        for top_team in self.top_teams:
            if top_team.lower() in team_lower:
                return True
        return False
    
    def parse_hltv_matches(self, html: str) -> List[Dict]:
        """Парсинг pre-match матчей с HLTV"""
        matches = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем предстоящие матчи
            match_elements = soup.find_all('div', class_='match')
            
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
                    
                    # Извлечение даты
                    date_elem = element.find('div', class_='date')
                    match_date = date_elem.get_text(strip=True) if date_elem else ''
                    
                    # Извлечение турнира
                    event_elem = element.find('div', class_='event')
                    tournament = event_elem.get_text(strip=True) if event_elem else 'Unknown Tournament'
                    
                    # Извлечение формата
                    format_elem = element.find('div', class_='best-of')
                    match_format = format_elem.get_text(strip=True) if format_elem else 'BO1'
                    
                    # Проверяем, что матч не live
                    status_elem = element.find('div', class_='status')
                    status = status_elem.get_text(strip=True).lower() if status_elem else ''
                    
                    if 'live' in status or 'live' in match_time.lower():
                        continue  # Пропускаем live матчи
                    
                    # Создаем datetime для будущего матча
                    match_datetime = self._parse_datetime(match_date, match_time)
                    
                    match_data = {
                        'match_id': f"hltv_{hash(team1 + team2 + match_time)}",
                        'team1': team1,
                        'team2': team2,
                        'tournament': tournament,
                        'sport': 'cs2',
                        'date': match_datetime,
                        'status': 'upcoming',
                        'format': match_format,
                        'source': 'hltv_pre_match',
                        'match_type': 'pre_match'
                    }
                    matches.append(match_data)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing match element: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error parsing HLTV matches: {e}")
        
        logger.info(f"📊 HLTV Pre-Match: Found {len(matches)} matches")
        return matches
    
    def _parse_datetime(self, date_str: str, time_str: str) -> str:
        """Парсинг даты и времени"""
        try:
            # Простая логика парсинга
            if 'today' in date_str.lower():
                date = datetime.now()
            elif 'tomorrow' in date_str.lower():
                date = datetime.now() + timedelta(days=1)
            else:
                # Попытка парсинга формата YYYY-MM-DD
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    date = datetime.now()
            
            # Парсинг времени
            if time_str:
                try:
                    time_parts = time_str.split(':')
                    if len(time_parts) == 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        date = date.replace(hour=hour, minute=minute)
                except:
                    pass
            
            return date.isoformat()
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing datetime: {e}")
            return datetime.now().isoformat()
    
    async def get_pre_match_matches(self) -> List[Dict]:
        """Получить pre-match матчи"""
        logger.info("🚀 Starting CS2 Pre-Match data collection")
        
        # Проверяем кеш
        cached_matches = self._load_cache()
        if cached_matches:
            return cached_matches
        
        # Создаем сессию
        self.session = aiohttp.ClientSession(timeout=self.session_timeout)
        
        try:
            all_matches = []
            
            # Сортируем источники по приоритету
            sorted_sources = sorted(
                [(name, config) for name, config in self.pre_match_sources.items() if config['enabled']],
                key=lambda x: x[1]['priority']
            )
            
            for source_name, source_config in sorted_sources:
                try:
                    logger.info(f"📊 Parsing {source_name}...")
                    
                    html = await self.fetch_page(source_config['url'], source_name)
                    if html:
                        if 'hltv' in source_name:
                            matches = self.parse_hltv_matches(html)
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
            
            # Фильтруем только будущие матчи
            now = datetime.now()
            future_matches = []
            
            for match in all_matches:
                try:
                    match_date = datetime.fromisoformat(match['date'])
                    if match_date > now:
                        future_matches.append(match)
                except:
                    continue
            
            # Удаление дубликатов
            unique_matches = []
            seen_matches = set()
            
            for match in future_matches:
                match_key = f"{match['team1']}_{match['team2']}_{match['date']}"
                if match_key not in seen_matches:
                    unique_matches.append(match)
                    seen_matches.add(match_key)
            
            # Сортировка по дате
            unique_matches.sort(key=lambda x: x['date'])
            
            # Кешируем результат
            self._save_cache(unique_matches)
            
            logger.info(f"✅ CS2 Pre-Match completed: {len(unique_matches)} unique future matches")
            return unique_matches
            
        except Exception as e:
            logger.error(f"❌ CS2 Pre-Match error: {e}")
            return []
        finally:
            if self.session:
                await self.session.close()

# Глобальный экземпляр
cs2_pre_match_source = CS2PreMatchSource()
