#!/usr/bin/env python3
"""
AIBET Analytics Platform - KHL Real Data Source
Получение реальных данных о матчах КХЛ из API источников
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from database import Match, db_manager

logger = logging.getLogger(__name__)

class KHLRealDataSource:
    def __init__(self):
        self.name = "KHL Real Data"
        self.sources = [
            "https://api.khl.ru/game/results",
            "https://khl.ru/api/calendar",
            "https://russianhockeyfans.com/api/khl/matches",
            "https://sportscore.io/api/v1/sports/ice-hockey/matches"
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; AIBET-Bot/1.0)',
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8'
        }
    
    async def fetch_data(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """Получение данных из API"""
        try:
            async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Successfully fetched data from {url}")
                    return data
                else:
                    logger.warning(f"⚠️ HTTP {response.status} from {url}")
                    return None
        except Exception as e:
            logger.error(f"❌ Error fetching from {url}: {e}")
            return None
    
    async def parse_khl_official_data(self, data: Dict) -> List[Match]:
        """Парсинг данных официального API КХЛ"""
        matches = []
        
        try:
            if 'games' in data:
                for game_data in data['games'][:20]:
                    try:
                        # Извлекаем информацию о командах
                        home_team = game_data.get('home_team', {}).get('name', '')
                        away_team = game_data.get('away_team', {}).get('name', '')
                        
                        if not home_team or not away_team:
                            continue
                        
                        # Определяем статус и время
                        status = "upcoming"
                        start_time = None
                        
                        if 'date_time' in game_data:
                            try:
                                start_time = datetime.fromisoformat(game_data['date_time'])
                                if start_time <= datetime.utcnow():
                                    status = "live"
                            except:
                                pass
                        
                        # Извлекаем счет
                        score = ""
                        if 'score' in game_data:
                            score_data = game_data['score']
                            home_score = score_data.get('home', 0)
                            away_score = score_data.get('away', 0)
                            score = f"{home_score}:{away_score}"
                            if home_score > 0 or away_score > 0:
                                status = "live"
                        
                        # Определяем турнир
                        tournament = game_data.get('season', {}).get('title', 'КХЛ')
                        
                        # Создаем матч
                        match = Match(
                            sport="khl",
                            team1=home_team,
                            team2=away_team,
                            score=score,
                            status=status,
                            start_time=start_time,
                            features={
                                "tournament": tournament,
                                "importance": self._get_tournament_importance(tournament),
                                "format": "Регулярный чемпионат",
                                "source": "khl_official",
                                "api_data": game_data
                            }
                        )
                        matches.append(match)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing KHL match: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Error parsing KHL official data: {e}")
        
        return matches
    
    async def parse_calendar_data(self, data: Dict) -> List[Match]:
        """Парсинг данных календаря"""
        matches = []
        
        try:
            if isinstance(data, list):
                for match_data in data[:15]:
                    try:
                        team1 = match_data.get('team1', '')
                        team2 = match_data.get('team2', '')
                        
                        if not team1 or not team2:
                            continue
                        
                        status = match_data.get('status', 'upcoming')
                        start_time = None
                        
                        if 'datetime' in match_data:
                            try:
                                start_time = datetime.fromisoformat(match_data['datetime'])
                            except:
                                pass
                        
                        tournament = match_data.get('tournament', 'КХЛ')
                        
                        match = Match(
                            sport="khl",
                            team1=team1,
                            team2=team2,
                            score=match_data.get('score', ''),
                            status=status,
                            start_time=start_time,
                            features={
                                "tournament": tournament,
                                "importance": 6,
                                "format": "Регулярный чемпионат",
                                "source": "calendar_api"
                            }
                        )
                        matches.append(match)
                        
                    except Exception as e:
                        continue
                        
        except Exception as e:
            logger.warning(f"⚠️ Error parsing calendar data: {e}")
        
        return matches
    
    async def parse_generic_hockey_data(self, data: Dict) -> List[Match]:
        """Парсинг данных из общего хоккейного API"""
        matches = []
        
        try:
            if isinstance(data, dict) and 'matches' in data:
                for item in data['matches'][:10]:
                    try:
                        home_team = item.get('home_team_name') or item.get('homeTeam', 'Unknown Team 1')
                        away_team = item.get('away_team_name') or item.get('awayTeam', 'Unknown Team 2')
                        
                        if home_team == 'Unknown Team 1' or away_team == 'Unknown Team 2':
                            continue
                        
                        status = "upcoming"
                        start_time = datetime.utcnow() + timedelta(hours=3)
                        
                        if 'match_time' in item:
                            try:
                                start_time = datetime.fromisoformat(item['match_time'])
                            except:
                                pass
                        
                        match = Match(
                            sport="khl",
                            team1=home_team,
                            team2=away_team,
                            status=status,
                            start_time=start_time,
                            features={
                                "tournament": item.get('league', 'КХЛ'),
                                "importance": 5,
                                "format": "Хоккей",
                                "source": "generic_hockey_api"
                            }
                        )
                        matches.append(match)
                        
                    except Exception as e:
                        continue
                        
        except Exception as e:
            logger.warning(f"⚠️ Error parsing generic hockey data: {e}")
        
        return matches
    
    def _get_tournament_importance(self, tournament_name: str) -> int:
        """Определение важности турнира КХЛ"""
        tournament_lower = tournament_name.lower()
        
        if any(keyword in tournament_lower for keyword in ['плей-офф', 'кубок', 'финал']):
            return 10
        elif any(keyword in tournament_lower for keyword in ['конференция', 'полуфинал']):
            return 8
        elif 'кхл' in tournament_lower:
            return 7
        else:
            return 5
    
    async def get_real_matches(self) -> List[Match]:
        """Получение реальных матчей из всех источников"""
        logger.info("🏒 Fetching KHL matches from real APIs")
        
        all_matches = []
        
        async with aiohttp.ClientSession() as session:
            # Пробуем каждый источник
            for i, url in enumerate(self.sources):
                try:
                    data = await self.fetch_data(session, url)
                    if data:
                        if i == 0:  # Официальный API КХЛ
                            matches = await self.parse_khl_official_data(data)
                        elif i == 1:  # Календарь КХЛ
                            matches = await self.parse_calendar_data(data)
                        else:  # Другие источники
                            matches = await self.parse_generic_hockey_data(data)
                        
                        all_matches.extend(matches)
                        logger.info(f"✅ Got {len(matches)} matches from KHL source {i+1}")
                        
                        # Если получили достаточно матчей, прекращаем
                        if len(all_matches) >= 12:
                            break
                            
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get data from KHL source {i+1}: {e}")
                    continue
        
        # Убираем дубликаты
        unique_matches = self._deduplicate_matches(all_matches)
        
        logger.info(f"🏒 Got {len(unique_matches)} unique KHL matches from real sources")
        return unique_matches
    
    def _deduplicate_matches(self, matches: List[Match]) -> List[Match]:
        """Удаление дубликатов матчей"""
        seen = set()
        unique_matches = []
        
        for match in matches:
            # Создаем уникальный ключ из команд и времени
            key = (match.team1.lower(), match.team2.lower(), match.start_time.date() if match.start_time else None)
            
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return unique_matches
    
    async def update_database(self):
        """Обновление базы данных реальными матчами"""
        try:
            matches = await self.get_real_matches()
            
            if not matches:
                logger.warning("⚠️ No KHL matches found from real sources")
                return 0
            
            saved_count = 0
            for match in matches:
                try:
                    # Проверяем, существует ли уже такой матч
                    existing_matches = await db_manager.get_matches(
                        sport=match.sport,
                        limit=100
                    )
                    
                    # Ищем дубликат по командам и времени
                    is_duplicate = False
                    for existing in existing_matches:
                        if (existing.team1.lower() == match.team1.lower() and 
                            existing.team2.lower() == match.team2.lower() and
                            existing.start_time and match.start_time and
                            abs((existing.start_time - match.start_time).total_seconds()) < 3600):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        await db_manager.add_match(match)
                        saved_count += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error saving KHL match {match.team1} vs {match.team2}: {e}")
                    continue
            
            logger.info(f"✅ Saved {saved_count} new KHL matches to database")
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Error updating KHL database: {e}")
            return 0

# Глобальный экземпляр
khl_real_source = KHLRealDataSource()
