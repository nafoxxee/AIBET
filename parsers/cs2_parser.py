#!/usr/bin/env python3
"""
AIBET Analytics Platform - CS2 Parser
Парсинг реальных матчей с HLTV.org
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
import re

from database import Match, db_manager

logger = logging.getLogger(__name__)

class CS2Parser:
    def __init__(self):
        self.base_url = "https://www.hltv.org"
        self.matches_url = "https://www.hltv.org/matches"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.api_mirrors = [
            "https://hltv-api.vercel.app/api/matches",
            "https://api.hltv.org/v1/matches",
            "https://json.hltv-api.com/matches"
        ]
    
    async def fetch_page(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Загрузка страницы с обработкой ошибок и retry"""
        for attempt in range(3):
            try:
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 403:
                        logger.warning(f"HTTP 403 for {url}, trying API mirrors")
                        return await self.try_api_mirrors(session)
                    else:
                        logger.warning(f"HTTP {response.status} for {url} (attempt {attempt + 1})")
                        if attempt < 2:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < 2:
                    await asyncio.sleep(1)
                continue
        
        return None
    
    async def try_api_mirrors(self, session: aiohttp.ClientSession) -> Optional[str]:
        """Попытка получить данные через API mirrors"""
        for mirror_url in self.api_mirrors:
            try:
                async with session.get(mirror_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Got data from API mirror: {mirror_url}")
                        return await self.parse_api_data(data)
            except Exception as e:
                logger.warning(f"API mirror {mirror_url} failed: {e}")
                continue
        
        return None
    
    async def parse_api_data(self, data: dict) -> Optional[str]:
        """Парсинг данных из API и возврат HTML формата"""
        try:
            if 'matches' in data and data['matches']:
                # Создаем простой HTML из API данных
                html_content = "<html><body>"
                for match in data['matches'][:20]:
                    team1 = match.get('team1', {}).get('name', 'Team 1')
                    team2 = match.get('team2', {}).get('name', 'Team 2')
                    event = match.get('event', {}).get('name', 'Unknown Event')
                    
                    html_content += f"""
                    <div class="match" data-match-id="{match.get('id', 'unknown')}">
                        <div class="event-name">{event}</div>
                        <div class="team-name">{team1}</div>
                        <div class="team-name">{team2}</div>
                        <div class="time">{match.get('time', 'TBD')}</div>
                        <div class="status">{match.get('status', 'upcoming')}</div>
                    </div>
                    """
                html_content += "</body></html>"
                return html_content
        except Exception as e:
            logger.warning(f"Error parsing API data: {e}")
        
        return None
    
    async def parse_matches(self) -> List[Match]:
        """Парсинг матчей"""
        logger.info("🔴 Parsing CS2 matches from HLTV.org")
        
        try:
            async with aiohttp.ClientSession() as session:
                html = await self.fetch_page(session, self.matches_url)
                if not html:
                    logger.warning("⚠️ Failed to fetch HLTV matches page, no real data available")
                    return []  # Возвращаем пустой список вместо fallback
                
                soup = BeautifulSoup(html, 'html.parser')
                matches = []
                
                # Расширенный поиск матчей на HLTV
                match_selectors = [
                    'a.match',                    # Основные матчи
                    'div.match',                  # Альтернативные матчи
                    'div.matching',               # Live матчи
                    'tr.match',                   # Матчи в таблицах
                    'div[data-match-id]',         # Матчи с ID
                    'a[href*="/match/"]',       # Ссылки на матчи
                    'div.upcoming-match',         # Предстоящие матчи
                    'div.live-match',             # Live матчи
                    'div.completed-match'         # Завершенные матчи
                ]
                
                all_elements = []
                for selector in match_selectors:
                    elements = soup.select(selector)
                    if elements:
                        all_elements.extend(elements)
                        logger.info(f"🔴 Found {len(elements)} elements with selector: {selector}")
                
                # Убираем дубликаты
                unique_elements = []
                seen_texts = set()
                for element in all_elements:
                    text = element.get_text(strip=True)
                    if text and text not in seen_texts and len(text) > 10:
                        unique_elements.append(element)
                        seen_texts.add(text)
                
                logger.info(f"🔴 Processing {len(unique_elements)} unique CS2 matches")
                
                for element in unique_elements[:30]:  # Увеличим лимит для реальных матчей
                    try:
                        match = await self.parse_match_element(element)
                        if match:
                            matches.append(match)
                    except Exception as e:
                        logger.warning(f"Error parsing match element: {e}")
                        continue
                
                logger.info(f"🔴 Parsed {len(matches)} CS2 matches")
                return matches
                
        except Exception as e:
            logger.exception(f"❌ Error parsing CS2 matches: {e}")
            return []  # Возвращаем пустой список вместо fallback
    
    async def parse_match_element(self, element) -> Optional[Match]:
        """Парсинг отдельного элемента матча"""
        try:
            # Извлекаем команды
            team_elements = element.find_all('span', class_='team-name')
            if len(team_elements) < 2:
                team_elements = element.find_all('div', class_='team')
                if len(team_elements) < 2:
                    team_elements = element.find_all('td', class_='team')
            
            if len(team_elements) < 2:
                return None
            
            team1 = team_elements[0].get_text(strip=True)
            team2 = team_elements[1].get_text(strip=True)
            
            if not team1 or not team2:
                return None
            
            # Извлекаем время
            time_element = element.find('span', class_='time')
            if not time_element:
                time_element = element.find('div', class_='time')
            
            start_time = None
            if time_element:
                time_text = time_element.get_text(strip=True)
                start_time = self.parse_time(time_text)
            
            # Извлекаем статус
            status = "upcoming"
            if element.find('span', class_='live') or element.find('div', class_='live'):
                status = "live"
            elif element.find('span', class_='finished') or element.find('div', class_='finished'):
                status = "finished"
            
            # Извлекаем счет
            score_element = element.find('span', class_='score')
            if not score_element:
                score_element = element.find('div', class_='score')
            
            score = ""
            if score_element:
                score = score_element.get_text(strip=True)
            
            # Извлекаем турнир
            tournament_element = element.find('span', class_='event-name')
            if not tournament_element:
                tournament_element = element.find('div', class_='event-name')
            
            tournament = "Unknown Tournament"
            if tournament_element:
                tournament = tournament_element.get_text(strip=True)
            
            # Создаем матч
            match = Match(
                sport="cs2",
                team1=team1,
                team2=team2,
                score=score,
                status=status,
                start_time=start_time,
                features={
                    "tournament": tournament,
                    "importance": 5,
                    "format": "BO3"
                }
            )
            
            return match
            
        except Exception as e:
            logger.warning(f"Error parsing match element: {e}")
            return None
    
    def parse_time(self, time_text: str) -> Optional[datetime]:
        """Парсинг времени матча"""
        try:
            # Примеры: "14:00", "2h ago", "Live"
            if "live" in time_text.lower():
                return datetime.utcnow()
            
            if ":" in time_text:
                # Формат HH:MM
                hour, minute = map(int, time_text.split(":"))
                now = datetime.utcnow()
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if "ago" in time_text.lower():
                # Формат "2h ago"
                hours = int(time_text.split("h")[0])
                return datetime.utcnow() - timedelta(hours=hours)
            
            return None
        except:
            return None
    
    async def get_fallback_matches(self) -> List[Match]:
        """Резервные матчи - отключены, используем только реальные данные"""
        logger.warning("🔴 Fallback matches disabled - using only real data")
        return []
    
    async def update_matches(self):
        """Обновление матчей"""
        try:
            matches = await self.parse_matches()
            
            # Сохраняем в базу данных
            saved_count = 0
            for match in matches:
                try:
                    await db_manager.add_match(match)
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ Error saving match: {e}")
            
            logger.info(f"🔴 Updated {saved_count} CS2 matches")
            return matches
            
        except Exception as e:
            logger.exception(f"❌ Error updating CS2 matches: {e}")
            return []

# Глобальный экземпляр
cs2_parser = CS2Parser()
