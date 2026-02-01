#!/usr/bin/env python3
"""
AIBET KHL Pre-Match Data Source
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

class KHLPreMatchSource:
    def __init__(self):
        self.cache_file = "data/khl_pre_match_cache.json"
        self.cache_hours = 12  # Кеширование на 12 часов
        self.session_timeout = aiohttp.ClientTimeout(total=15)
        self.max_retries = 2
        
        # User-Agent для обхода блокировок
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # ТОЛЬКО стабильные pre-match источники КХЛ
        self.pre_match_sources = {
            'khl_calendar': {
                'url': 'https://khl.ru/calendar/',
                'enabled': True,
                'priority': 1
            },
            'khl_schedule': {
                'url': 'https://khl.ru/games/',
                'enabled': True,
                'priority': 2
            }
        }
        
        # Все КХЛ команды
        self.khl_teams = [
            'CSKA Moscow', 'SKA Saint Petersburg', 'Ak Bars Kazan', 'Metallurg Magnitogorsk',
            'Salavat Yulaev Ufa', 'Lokomotiv Yaroslavl', 'Barys Nur-Sultan', 'Traktor Chelyabinsk',
            'Avangard Omsk', 'Dinamo Moscow', 'Dinamo Minsk', 'Dinamo Riga',
            'Jokerit Helsinki', 'Severstal Cherepovets', 'Neftekhimik Nizhnekamsk',
            'Vityaz Podolsk', 'Sibir Novosibirsk', 'Amur Khabarovsk', 'Admiral Vladivostok',
            'Kunlun Red Star Beijing', 'HC Sochi', 'Torpedo Nizhny Novgorod'
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
                    logger.info("📦 Using cached KHL pre-match data")
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
                
            logger.info(f"💾 Cached {len(matches)} KHL pre-match matches")
            
        except Exception as e:
            logger.warning(f"⚠️ Error saving cache: {e}")
    
    def get_headers(self) -> Dict[str, str]:
        """Получить случайные headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
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
    
    def is_khl_team(self, team_name: str) -> bool:
        """Проверить, что команда КХЛ"""
        team_lower = team_name.lower()
        for khl_team in self.khl_teams:
            if khl_team.lower() in team_lower:
                return True
        return False
    
    def parse_khl_calendar(self, html: str) -> List[Dict]:
        """Парсинг pre-match матчей с календаря КХЛ"""
        matches = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем таблицу с матчами
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
                            
                            # Проверяем, что матч не завершен
                            score_cell = cells[4] if len(cells) > 4 else None
                            score = score_cell.get_text(strip=True) if score_cell else ''
                            
                            if score and ':' in score:
                                continue  # Пропускаем завершенные матчи
                            
                            # Проверяем, что не live
                            if 'live' in match_time.lower() or 'идет' in match_time.lower():
                                continue  # Пропускаем live матчи
                            
                            # Создаем datetime
                            match_datetime = self._parse_datetime(match_date, match_time)
                            
                            match_data = {
                                'match_id': f"khl_{hash(team1 + team2 + match_date + match_time)}",
                                'team1': team1,
                                'team2': team2,
                                'tournament': 'KHL',
                                'sport': 'khl',
                                'date': match_datetime,
                                'status': 'upcoming',
                                'format': 'Регулярный сезон',
                                'source': 'khl_calendar',
                                'match_type': 'pre_match'
                            }
                            matches.append(match_data)
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing KHL row: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Error parsing KHL calendar: {e}")
        
        logger.info(f"📊 KHL Calendar: Found {len(matches)} pre-match matches")
        return matches
    
    def parse_khl_schedule(self, html: str) -> List[Dict]:
        """Парсинг pre-match матчей с расписания КХЛ"""
        matches = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем блоки с матчами
            match_blocks = soup.find_all('div', class_='match-item')
            
            for block in match_blocks:
                try:
                    # Извлечение команд
                    team_elements = block.find_all('div', class_='team-name')
                    if len(team_elements) < 2:
                        continue
                    
                    team1 = team_elements[0].get_text(strip=True)
                    team2 = team_elements[1].get_text(strip=True)
                    
                    # Фильтрация КХЛ команд
                    if not (self.is_khl_team(team1) or self.is_khl_team(team2)):
                        continue
                    
                    # Извлечение даты и времени
                    datetime_elem = block.find('div', class_='match-datetime')
                    datetime_str = datetime_elem.get_text(strip=True) if datetime_elem else ''
                    
                    # Извлечение турнира
                    tournament_elem = block.find('div', class_='tournament')
                    tournament = tournament_elem.get_text(strip=True) if tournament_elem else 'KHL'
                    
                    # Проверяем статус
                    status_elem = block.find('div', class_='match-status')
                    status = status_elem.get_text(strip=True).lower() if status_elem else ''
                    
                    if 'live' in status or 'завершен' in status:
                        continue  # Пропускаем live и завершенные матчи
                    
                    # Создаем datetime
                    match_datetime = self._parse_datetime(datetime_str, '')
                    
                    match_data = {
                        'match_id': f"khl_schedule_{hash(team1 + team2 + datetime_str)}",
                        'team1': team1,
                        'team2': team2,
                        'tournament': tournament,
                        'sport': 'khl',
                        'date': match_datetime,
                        'status': 'upcoming',
                        'format': 'Регулярный сезон',
                        'source': 'khl_schedule',
                        'match_type': 'pre_match'
                    }
                    matches.append(match_data)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing KHL schedule block: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error parsing KHL schedule: {e}")
        
        logger.info(f"📊 KHL Schedule: Found {len(matches)} pre-match matches")
        return matches
    
    def _parse_datetime(self, date_str: str, time_str: str) -> str:
        """Парсинг даты и времени"""
        try:
            # Комбинируем дату и время
            datetime_str = f"{date_str} {time_str}".strip()
            
            # Простая логика парсинга
            if 'сегодня' in date_str.lower():
                date = datetime.now()
            elif 'завтра' in date_str.lower():
                date = datetime.now() + timedelta(days=1)
            else:
                # Попытка парсинга различных форматов
                formats = [
                    '%d.%m.%Y %H:%M',
                    '%Y-%m-%d %H:%M',
                    '%d/%m/%Y %H:%M'
                ]
                
                date = None
                for fmt in formats:
                    try:
                        date = datetime.strptime(datetime_str, fmt)
                        break
                    except:
                        continue
                
                if date is None:
                    date = datetime.now()
            
            return date.isoformat()
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing datetime: {e}")
            return datetime.now().isoformat()
    
    async def get_pre_match_matches(self) -> List[Dict]:
        """Получить pre-match матчи"""
        logger.info("🚀 Starting KHL Pre-Match data collection")
        
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
                        if 'calendar' in source_name:
                            matches = self.parse_khl_calendar(html)
                        elif 'schedule' in source_name:
                            matches = self.parse_khl_schedule(html)
                        else:
                            continue
                        
                        all_matches.extend(matches)
                        
                        # Если получили достаточно матчей, не продолжаем
                        if len(all_matches) >= 20:
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
            
            logger.info(f"✅ KHL Pre-Match completed: {len(unique_matches)} unique future matches")
            return unique_matches
            
        except Exception as e:
            logger.error(f"❌ KHL Pre-Match error: {e}")
            return []
        finally:
            if self.session:
                await self.session.close()

# Глобальный экземпляр
khl_pre_match_source = KHLPreMatchSource()
