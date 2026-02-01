#!/usr/bin/env python3
"""
AIBET Analytics Platform - CS2 Real Data Source
Получение реальных данных о матчах CS2 из API источников
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import asdict

from database import Match, db_manager

logger = logging.getLogger(__name__)

class CS2RealDataSource:
    def __init__(self):
        self.name = "CS2 Real Data"
        self.sources = [
            "https://api.liquipedia.net/api/v1/matches?game=cs2&limit=50",
            "https://hltv.org/api/matches/upcoming",
            "https://scorebot.5eplay.com/api/v1/matches"
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; AIBET-Bot/1.0)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
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
    
    async def parse_liquipedia_data(self, data: Dict) -> List[Match]:
        """Парсинг данных Liquipedia API"""
        matches = []
        
        try:
            if 'matches' in data:
                for match_data in data['matches'][:20]:  # Ограничиваем количество
                    try:
                        # Извлекаем базовую информацию
                        teams = match_data.get('teams', {})
                        team1 = teams.get('team1', {}).get('name', 'Unknown Team 1')
                        team2 = teams.get('team2', {}).get('name', 'Unknown Team 2')
                        
                        if not team1 or not team2 or team1 == 'Unknown Team 1' or team2 == 'Unknown Team 2':
                            continue
                        
                        # Определяем статус и время
                        status = "upcoming"
                        start_time = None
                        
                        if 'date' in match_data:
                            try:
                                start_time = datetime.fromisoformat(match_data['date'].replace('Z', '+00:00'))
                                if start_time <= datetime.utcnow():
                                    status = "live"
                            except:
                                pass
                        
                        # Определяем турнир
                        tournament = match_data.get('tournament', {}).get('name', 'Unknown Tournament')
                        
                        # Создаем матч
                        match = Match(
                            sport="cs2",
                            team1=team1,
                            team2=team2,
                            score="",
                            status=status,
                            start_time=start_time,
                            features={
                                "tournament": tournament,
                                "importance": self._get_tournament_importance(tournament),
                                "format": "BO3",
                                "source": "liquipedia",
                                "api_data": match_data
                            }
                        )
                        matches.append(match)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing match from Liquipedia: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Error parsing Liquipedia data: {e}")
        
        return matches
    
    async def parse_hltv_data(self, data: Dict) -> List[Match]:
        """Парсинг данных HLTV API"""
        matches = []
        
        try:
            if isinstance(data, list):
                for match_data in data[:20]:
                    try:
                        team1 = match_data.get('team1', {}).get('name', '')
                        team2 = match_data.get('team2', {}).get('name', '')
                        
                        if not team1 or not team2:
                            continue
                        
                        status = match_data.get('status', 'upcoming')
                        start_time = None
                        
                        if 'date' in match_data:
                            try:
                                start_time = datetime.fromisoformat(match_data['date'])
                            except:
                                pass
                        
                        tournament = match_data.get('event', {}).get('name', 'Unknown Tournament')
                        
                        match = Match(
                            sport="cs2",
                            team1=team1,
                            team2=team2,
                            score=match_data.get('result', ''),
                            status=status,
                            start_time=start_time,
                            features={
                                "tournament": tournament,
                                "importance": self._get_tournament_importance(tournament),
                                "format": match_data.get('format', 'BO3'),
                                "source": "hltv",
                                "api_data": match_data
                            }
                        )
                        matches.append(match)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing match from HLTV: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Error parsing HLTV data: {e}")
        
        return matches
    
    def _get_tournament_importance(self, tournament_name: str) -> int:
        """Определение важности турнира"""
        tournament_lower = tournament_name.lower()
        
        if any(keyword in tournament_lower for keyword in ['major', 'championship', 'world']):
            return 10
        elif any(keyword in tournament_lower for keyword in ['premier', 'masters', 'pro league']):
            return 8
        elif any(keyword in tournament_lower for keyword in ['cup', 'open', 'qualifier']):
            return 6
        else:
            return 5
    
    async def get_real_matches(self) -> List[Match]:
        """Получение реальных матчей из всех источников"""
        logger.info("🔴 Fetching CS2 matches from real APIs")
        
        all_matches = []
        
        async with aiohttp.ClientSession() as session:
            # Пробуем каждый источник
            for i, url in enumerate(self.sources):
                try:
                    data = await self.fetch_data(session, url)
                    if data:
                        if i == 0:  # Liquipedia
                            matches = await self.parse_liquipedia_data(data)
                        elif i == 1:  # HLTV
                            matches = await self.parse_hltv_data(data)
                        else:  # Другие источники
                            matches = await self.parse_generic_data(data)
                        
                        all_matches.extend(matches)
                        logger.info(f"✅ Got {len(matches)} matches from source {i+1}")
                        
                        # Если получили достаточно матчей, прекращаем
                        if len(all_matches) >= 15:
                            break
                            
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get data from source {i+1}: {e}")
                    continue
        
        # Убираем дубликаты
        unique_matches = self._deduplicate_matches(all_matches)
        
        logger.info(f"🔴 Got {len(unique_matches)} unique CS2 matches from real sources")
        return unique_matches
    
    async def parse_generic_data(self, data: Dict) -> List[Match]:
        """Парсинг данных из общего API"""
        matches = []
        
        try:
            # Общая логика парсинга для различных API
            if isinstance(data, dict) and 'data' in data:
                for item in data['data'][:10]:
                    try:
                        # Извлекаем информацию в зависимости от структуры API
                        team1 = item.get('team1_name') or item.get('home_team', 'Unknown Team 1')
                        team2 = item.get('team2_name') or item.get('away_team', 'Unknown Team 2')
                        
                        if team1 == 'Unknown Team 1' or team2 == 'Unknown Team 2':
                            continue
                        
                        match = Match(
                            sport="cs2",
                            team1=team1,
                            team2=team2,
                            status="upcoming",
                            start_time=datetime.utcnow() + timedelta(hours=2),
                            features={
                                "tournament": item.get('tournament', 'Unknown Tournament'),
                                "importance": 5,
                                "format": "BO3",
                                "source": "generic_api"
                            }
                        )
                        matches.append(match)
                        
                    except Exception as e:
                        continue
                        
        except Exception as e:
            logger.warning(f"⚠️ Error parsing generic data: {e}")
        
        return matches
    
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
                logger.warning("⚠️ No matches found from real sources")
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
                    logger.warning(f"⚠️ Error saving match {match.team1} vs {match.team2}: {e}")
                    continue
            
            logger.info(f"✅ Saved {saved_count} new CS2 matches to database")
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Error updating CS2 database: {e}")
            return 0

# Глобальный экземпляр
cs2_real_source = CS2RealDataSource()
