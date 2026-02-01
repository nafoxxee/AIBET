#!/usr/bin/env python3
"""
AIBET Sports Data Parser
Комплексный парсер CS2 и КХЛ данных с fallback механизмами
"""

import asyncio
import aiohttp
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import re

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MatchData:
    match_id: str
    teams: Dict[str, str]  # {'team1': 'Team A', 'team2': 'Team B'}
    tournament: str
    sport: str  # 'cs2' or 'khl'
    date: str
    status: str  # 'live', 'upcoming', 'completed'
    score: Optional[Dict[str, int]] = None
    stats: Optional[Dict[str, Any]] = None
    odds: Optional[Dict[str, Any]] = None
    prediction: Optional[Dict[str, Any]] = None

class SportsDataParser:
    def __init__(self):
        self.session_timeout = aiohttp.ClientTimeout(total=30)
        self.max_retries = 3
        self.request_delay = (2, 5)  # 2-5 секунд задержка
        
        # User-Agent для обхода блокировок
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Источники CS2
        self.cs2_sources = {
            'hltv': {
                'url': 'https://www.hltv.org/matches',
                'api_mirrors': [
                    'https://hltv-api.vercel.app/api/matches',
                    'https://api.hltv.org/v1/matches',
                    'https://json.hltv-api.com/matches'
                ]
            },
            'liquipedia': {
                'url': 'https://liquipedia.net/counterstrike/Portal:Matches',
                'delay': 3  # Liquipedia rate-limited
            },
            'gosugamers': {
                'url': 'https://www.gosugamers.net/counterstrike/matches'
            }
        }
        
        # Источники КХЛ
        self.khl_sources = {
            'livesport': {
                'url': 'https://www.livesport.com/ru/hockey/russia/khl/'
            },
            'flashscore': {
                'url': 'https://www.flashscore.com/hockey/russia/khl/'
            },
            'sport': {
                'url': 'https://www.sport.ru/hockey/khl/calendar/'
            }
        }
        
        # Источники коэффициентов
        self.odds_sources = {
            'betboom': {
                'url': 'https://betboom.com',
                'sport_mapping': {'cs2': 'counter-strike-2', 'khl': 'hockey-khl'}
            },
            'winline': {
                'url': 'https://winline.ru',
                'sport_mapping': {'cs2': 'cs2', 'khl': 'hockey'}
            },
            'fonbet': {
                'url': 'https://www.fonbet.ru',
                'sport_mapping': {'cs2': 'csgo', 'khl': 'hockey'}
            }
        }
        
        # Топ-100 CS2 команд (пример)
        self.cs2_top_teams = [
            'NaVi', 'FaZe', 'G2', 'Vitality', 'Astralis', 'Heroic', 'Cloud9', 'Fnatic',
            'Team Liquid', 'Complexity', 'Evil Geniuses', 'FURIA', 'MOUZ', 'BIG', 'NIP',
            'ENCE', 'OG', 'Virtus.pro', 'forZe', '9INE', 'Imperial', '00 Nation', 'MIBR',
            'paiN', '9z', 'TYLOO', 'Lynn Vision', 'Rare Atom', 'Monte', 'B8', 'Sangal',
            'Eternal Fire', 'Bad News Eagles', 'Endpoint', 'MAD Lions', 'ex-Ghost',
            'Rebels', 'Into the Breach', 'Permitta', 'ALTERNATE aTTaX', 'ECLOT',
            'Akimbo', 'K23', 'MASONIC', 'Parivision', 'Random', 'FLUFFY AIMERS',
            'Infinity', 'LAG', 'BOSS', 'Nouns', 'Mythic', 'Party Astronauts',
            'Wildcard', 'Vanguard', 'M80', 'Take Flyte', 'NRG', 'OpTic',
            'TSM', 'Ex-GG', 'DF', 'Version1', 'Luminosity', 'Chaos', 'Extra Salt',
            'Bad News Kangaroos', 'Rooster', 'Order', 'Mindfreak', 'K10',
            'Paradox', 'Crown', 'TALON', 'The MongolZ', 'IHC', 'Rare Atom',
            'Lynn Vision', '5yclone', 'TYLOO', 'Rare Atom', 'Let us finish',
            'AZURO', 'GR', 'Betera', 'Qiang', 'Eternal Fire', 'Fire Flux',
            'Sangal', 'PACT', 'Sashi', 'Betera', '1WIN', 'BetBoom',
            '9 Pandas', 'GamerLegion', 'AMKAL', '1WIN', 'Virtus.pro'
        ]
        
        self.session = None
        self.matches_data = []
        
    def get_headers(self) -> Dict[str, str]:
        """Получить случайные headers для обхода блокировок"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    async def fetch_page(self, url: str, source_name: str = "") -> Optional[str]:
        """Загрузить страницу с retry и задержкой"""
        for attempt in range(self.max_retries):
            try:
                # Задержка между запросами
                delay = random.uniform(*self.request_delay)
                if source_name == 'liquipedia':
                    delay = max(delay, 3)  # Минимум 3 сек для Liquipedia
                
                await asyncio.sleep(delay)
                
                headers = self.get_headers()
                
                async with self.session.get(url, headers=headers, timeout=self.session_timeout) as response:
                    if response.status == 200:
                        logger.info(f"✅ Successfully fetched {source_name}: {url}")
                        return await response.text()
                    elif response.status == 403:
                        logger.warning(f"⚠️ 403 Forbidden for {source_name}: {url} (attempt {attempt + 1})")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(5)
                            continue
                    elif response.status == 429:
                        logger.warning(f"⚠️ 429 Rate Limited for {source_name}: {url} (attempt {attempt + 1})")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(10)
                            continue
                    elif response.status == 503:
                        logger.warning(f"⚠️ 503 Service Unavailable for {source_name}: {url} (attempt {attempt + 1})")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(8)
                            continue
                    else:
                        logger.warning(f"⚠️ HTTP {response.status} for {source_name}: {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Timeout for {source_name}: {url} (attempt {attempt + 1})")
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
    
    async def parse_hltv_matches(self) -> List[MatchData]:
        """Парсинг матчей с HLTV.org"""
        matches = []
        
        try:
            # Сначала пробуем API зеркала
            for api_url in self.cs2_sources['hltv']['api_mirrors']:
                try:
                    html = await self.fetch_page(api_url, 'hltv_api')
                    if html:
                        data = json.loads(html)
                        # Обработка API данных
                        for match in data.get('matches', []):
                            if self.is_top_cs2_match(match):
                                match_data = self.convert_hltv_api_match(match)
                                if match_data:
                                    matches.append(match_data)
                        break
                except Exception as e:
                    logger.warning(f"⚠️ HLTV API {api_url} failed: {e}")
                    continue
            
            # Fallback на HTML парсинг
            if not matches:
                html = await self.fetch_page(self.cs2_sources['hltv']['url'], 'hltv')
                if html:
                    soup = BeautifulSoup(html, 'html.parser')
                    match_elements = soup.find_all('div', class_='match')
                    
                    for element in match_elements:
                        try:
                            match_data = self.parse_hltv_match_element(element)
                            if match_data and self.is_top_cs2_match(match_data):
                                matches.append(match_data)
                        except Exception as e:
                            logger.warning(f"⚠️ Error parsing HLTV match element: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"❌ Error parsing HLTV matches: {e}")
        
        logger.info(f"📊 HLTV: Found {len(matches)} top CS2 matches")
        return matches
    
    def is_top_cs2_match(self, match_data) -> bool:
        """Проверить, что матч с топ-100 командой"""
        if isinstance(match_data, dict):
            team1 = match_data.get('team1', '').lower()
            team2 = match_data.get('team2', '').lower()
        else:
            team1 = getattr(match_data, 'team1', '').lower()
            team2 = getattr(match_data, 'team2', '').lower()
        
        for top_team in self.cs2_top_teams:
            top_team_lower = top_team.lower()
            if top_team_lower in team1 or top_team_lower in team2:
                return True
        return False
    
    def convert_hltv_api_match(self, api_match: Dict) -> Optional[MatchData]:
        """Конвертировать API матч HLTV в MatchData"""
        try:
            return MatchData(
                match_id=f"hltv_{api_match.get('id', '')}",
                teams={
                    'team1': api_match.get('team1', {}).get('name', ''),
                    'team2': api_match.get('team2', {}).get('name', '')
                },
                tournament=api_match.get('event', {}).get('name', ''),
                sport='cs2',
                date=api_match.get('date', ''),
                status=api_match.get('status', 'unknown')
            )
        except Exception as e:
            logger.warning(f"⚠️ Error converting HLTV API match: {e}")
            return None
    
    def parse_hltv_match_element(self, element) -> Optional[MatchData]:
        """Парсинг элемента матча HLTV"""
        try:
            # Извлечение данных из HTML элемента
            team1_elem = element.find('div', class_='team1')
            team2_elem = element.find('div', class_='team2')
            
            if not team1_elem or not team2_elem:
                return None
            
            team1 = team1_elem.get_text(strip=True)
            team2 = team2_elem.get_text(strip=True)
            
            event_elem = element.find('div', class_='event-name')
            tournament = event_elem.get_text(strip=True) if event_elem else 'Unknown'
            
            time_elem = element.find('div', class_='time')
            match_time = time_elem.get_text(strip=True) if time_elem else ''
            
            return MatchData(
                match_id=f"hltv_{hash(team1 + team2 + match_time)}",
                teams={'team1': team1, 'team2': team2},
                tournament=tournament,
                sport='cs2',
                date=match_time,
                status='upcoming'
            )
        except Exception as e:
            logger.warning(f"⚠️ Error parsing HLTV match element: {e}")
            return None
    
    async def parse_liquipedia_matches(self) -> List[MatchData]:
        """Парсинг матчей с Liquipedia"""
        matches = []
        
        try:
            html = await self.fetch_page(self.cs2_sources['liquipedia']['url'], 'liquipedia')
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                
                # Liquipedia использует таблицы для матчей
                match_table = soup.find('table', class_='infobox_matches_content')
                if match_table:
                    rows = match_table.find_all('tr')
                    
                    for row in rows:
                        try:
                            cells = row.find_all('td')
                            if len(cells) >= 3:
                                # Извлечение команд
                                team1 = cells[0].get_text(strip=True)
                                team2 = cells[2].get_text(strip=True)
                                
                                # Пропуск если не топ команды
                                if not self.is_top_cs2_match({'team1': team1, 'team2': team2}):
                                    continue
                                
                                # Извлечение времени
                                time_cell = cells[1]
                                match_time = time_cell.get_text(strip=True)
                                
                                # Извлечение турнира
                                tournament_elem = row.find('span', class_='tournament-name')
                                tournament = tournament_elem.get_text(strip=True) if tournament_elem else 'Unknown'
                                
                                match_data = MatchData(
                                    match_id=f"liquipedia_{hash(team1 + team2 + match_time)}",
                                    teams={'team1': team1, 'team2': team2},
                                    tournament=tournament,
                                    sport='cs2',
                                    date=match_time,
                                    status='upcoming'
                                )
                                matches.append(match_data)
                                
                        except Exception as e:
                            logger.warning(f"⚠️ Error parsing Liquipedia row: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"❌ Error parsing Liquipedia matches: {e}")
        
        logger.info(f"📊 Liquipedia: Found {len(matches)} top CS2 matches")
        return matches
    
    async def parse_khl_matches(self) -> List[MatchData]:
        """Парсинг матчей КХЛ"""
        matches = []
        
        # Пробуем все источники КХЛ
        for source_name, source_config in self.khl_sources.items():
            try:
                html = await self.fetch_page(source_config['url'], source_name)
                if html:
                    source_matches = await self.parse_khl_source(html, source_name)
                    matches.extend(source_matches)
                    
                    # Если получили матчи, не продолжаем с другими источниками
                    if source_matches:
                        logger.info(f"✅ Successfully got {len(source_matches)} matches from {source_name}")
                        break
                        
            except Exception as e:
                logger.warning(f"⚠️ Error parsing KHL from {source_name}: {e}")
                continue
        
        logger.info(f"📊 KHL: Found {len(matches)} matches")
        return matches
    
    async def parse_khl_source(self, html: str, source_name: str) -> List[MatchData]:
        """Парсинг КХЛ матчей из конкретного источника"""
        matches = []
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            if source_name == 'livesport':
                # Livesport парсинг
                match_elements = soup.find_all('div', class_='event__match')
                
                for element in match_elements:
                    try:
                        teams = element.find_all('div', class_='event__participant')
                        if len(teams) >= 2:
                            team1 = teams[0].get_text(strip=True)
                            team2 = teams[1].get_text(strip=True)
                            
                            time_elem = element.find('div', class_='event__time')
                            match_time = time_elem.get_text(strip=True) if time_elem else ''
                            
                            # Извлечение турнира
                            tournament_elem = element.find('div', class_='event__title')
                            tournament = tournament_elem.get_text(strip=True) if tournament_elem else 'KHL'
                            
                            match_data = MatchData(
                                match_id=f"khl_{source_name}_{hash(team1 + team2 + match_time)}",
                                teams={'team1': team1, 'team2': team2},
                                tournament=tournament,
                                sport='khl',
                                date=match_time,
                                status='upcoming'
                            )
                            matches.append(match_data)
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing livesport match: {e}")
                        continue
                        
            elif source_name == 'flashscore':
                # Flashscore парсинг
                match_elements = soup.find_all('div', class_='event__match')
                
                for element in match_elements:
                    try:
                        home_elem = element.find('div', class_='event__participant--home')
                        away_elem = element.find('div', class_='event__participant--away')
                        
                        if home_elem and away_elem:
                            team1 = home_elem.get_text(strip=True)
                            team2 = away_elem.get_text(strip=True)
                            
                            time_elem = element.find('div', class_='event__time')
                            match_time = time_elem.get_text(strip=True) if time_elem else ''
                            
                            match_data = MatchData(
                                match_id=f"khl_{source_name}_{hash(team1 + team2 + match_time)}",
                                teams={'team1': team1, 'team2': team2},
                                tournament='KHL',
                                sport='khl',
                                date=match_time,
                                status='upcoming'
                            )
                            matches.append(match_data)
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing flashscore match: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Error parsing KHL source {source_name}: {e}")
        
        return matches
    
    async def collect_team_stats(self, team_name: str, sport: str) -> Dict[str, Any]:
        """Сбор статистики последних 100 матчей команды"""
        stats = {
            'matches_played': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,  # для хоккея
            'score_for': 0,
            'score_against': 0,
            'recent_form': [],  # последние 10 матчей
            'win_rate': 0.0
        }
        
        # Здесь должна быть логика сбора статистики
        # Для примера возвращаем базовую статистику
        stats['matches_played'] = 100
        stats['wins'] = random.randint(40, 80)
        stats['losses'] = 100 - stats['wins']
        stats['win_rate'] = stats['wins'] / 100.0
        
        return stats
    
    async def collect_odds(self, match: MatchData) -> Dict[str, Any]:
        """Сбор коэффициентов с букмекерских сайтов"""
        odds = {}
        
        for bookmaker, config in self.odds_sources.items():
            try:
                # Здесь должна быть логика парсинга коэффициентов
                # Для примера возвращаем базовые коэффициенты
                odds[bookmaker] = {
                    'team1_win': round(random.uniform(1.5, 3.5), 2),
                    'team2_win': round(random.uniform(1.5, 3.5), 2),
                    'draw': round(random.uniform(3.0, 5.0), 2) if match.sport == 'khl' else None
                }
            except Exception as e:
                logger.warning(f"⚠️ Error collecting odds from {bookmaker}: {e}")
                continue
        
        return odds
    
    async def make_prediction(self, match: MatchData, stats1: Dict, stats2: Dict) -> Dict[str, Any]:
        """Сделать прогноз на основе статистики"""
        # Простая логика прогноза на основе win rate
        win_rate_diff = stats1['win_rate'] - stats2['win_rate']
        
        if abs(win_rate_diff) < 0.1:
            prediction = 'draw' if match.sport == 'khl' else 'team1'  # В CS2 нет ничьих
            confidence = 0.5
        elif win_rate_diff > 0:
            prediction = 'team1'
            confidence = 0.5 + win_rate_diff
        else:
            prediction = 'team2'
            confidence = 0.5 - win_rate_diff
        
        confidence = max(0.1, min(0.9, confidence))  # Ограничиваем confidence
        
        return {
            'winner': prediction,
            'confidence': round(confidence, 2),
            'team1_win_prob': round(confidence if prediction == 'team1' else (1 - confidence), 2),
            'team2_win_prob': round(confidence if prediction == 'team2' else (1 - confidence), 2),
            'draw_prob': round(0.1, 2) if match.sport == 'khl' else None
        }
    
    async def process_matches(self, matches: List[MatchData]) -> List[MatchData]:
        """Обработка матчей: сбор статистики, коэффициентов, прогнозов"""
        processed_matches = []
        
        for match in matches:
            try:
                # Сбор статистики команд
                stats1 = await self.collect_team_stats(match.teams['team1'], match.sport)
                stats2 = await self.collect_team_stats(match.teams['team2'], match.sport)
                
                match.stats = {
                    match.teams['team1']: stats1,
                    match.teams['team2']: stats2
                }
                
                # Сбор коэффициентов
                match.odds = await self.collect_odds(match)
                
                # Прогноз
                match.prediction = await self.make_prediction(match, stats1, stats2)
                
                processed_matches.append(match)
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing match {match.match_id}: {e}")
                continue
        
        return processed_matches
    
    async def run_parser(self) -> Dict[str, Any]:
        """Основной метод парсера"""
        logger.info("🚀 Starting AIBET Sports Data Parser")
        
        # Создаем сессию
        self.session = aiohttp.ClientSession(timeout=self.session_timeout)
        
        try:
            all_matches = []
            
            # Парсинг CS2 матчей
            logger.info("📊 Parsing CS2 matches...")
            
            # Пробуем HLTV
            hltv_matches = await self.parse_hltv_matches()
            all_matches.extend(hltv_matches)
            
            # Если мало матчей, пробуем Liquipedia
            if len(hltv_matches) < 5:
                logger.info("📊 Trying Liquipedia for more CS2 matches...")
                liquipedia_matches = await self.parse_liquipedia_matches()
                all_matches.extend(liquipedia_matches)
            
            # Парсинг КХЛ матчей
            logger.info("📊 Parsing KHL matches...")
            khl_matches = await self.parse_khl_matches()
            all_matches.extend(khl_matches)
            
            # Обработка матчей
            logger.info("📊 Processing matches (stats, odds, predictions)...")
            processed_matches = await self.process_matches(all_matches)
            
            # Валидация
            if not processed_matches:
                logger.error("❌ No matches found! Check sources availability.")
                return {
                    'status': 'error',
                    'message': 'No matches found',
                    'matches': []
                }
            
            # Конвертация в JSON
            result = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'total_matches': len(processed_matches),
                'cs2_matches': len([m for m in processed_matches if m.sport == 'cs2']),
                'khl_matches': len([m for m in processed_matches if m.sport == 'khl']),
                'matches': [asdict(match) for match in processed_matches]
            }
            
            logger.info(f"✅ Successfully parsed {len(processed_matches)} matches")
            logger.info(f"   CS2: {result['cs2_matches']}, KHL: {result['khl_matches']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Parser error: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'matches': []
            }
        finally:
            if self.session:
                await self.session.close()

async def main():
    """Главная функция"""
    parser = SportsDataParser()
    result = await parser.run_parser()
    
    # Вывод результата
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Сохранение в файл
    with open('sports_data.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info("💾 Results saved to sports_data.json")

if __name__ == "__main__":
    asyncio.run(main())
