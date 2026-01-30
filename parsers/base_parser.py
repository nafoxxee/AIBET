import asyncio
import aiohttp
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from dataclasses import dataclass

from database import Match, DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class ParsedMatch:
    """Структура распарсенного матча"""
    id: str
    team1: str
    team2: str
    tournament: str
    match_time: datetime
    odds1: float
    odds2: float
    odds_draw: Optional[float] = None
    status: str = 'upcoming'
    score1: Optional[int] = None
    score2: Optional[int] = None
    live_data: Optional[Dict] = None


class BaseParser(ABC):
    """Базовый класс парсера"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def initialize(self):
        """Инициализация парсера"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        logger.info(f"{self.__class__.__name__} initialized")
    
    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def parse_matches(self) -> List[ParsedMatch]:
        """Парсинг матчей"""
        pass
    
    @abstractmethod
    async def parse_live_matches(self) -> List[ParsedMatch]:
        """Парсинг live матчей"""
        pass
    
    @abstractmethod
    async def parse_odds(self, match_id: str) -> Dict[str, float]:
        """Парсинг коэффициентов"""
        pass
    
    async def save_matches(self, matches: List[ParsedMatch], sport: str):
        """Сохранение матчей в базу"""
        for parsed_match in matches:
            match = Match(
                id=parsed_match.id,
                sport=sport,
                team1=parsed_match.team1,
                team2=parsed_match.team2,
                tournament=parsed_match.tournament,
                match_time=parsed_match.match_time,
                odds1=parsed_match.odds1,
                odds2=parsed_match.odds2,
                odds_draw=parsed_match.odds_draw,
                status=parsed_match.status,
                score1=parsed_match.score1,
                score2=parsed_match.score2,
                live_data=parsed_match.live_data
            )
            
            await self.db_manager.save_match(match)
            
            # Сохраняем историю коэффициентов
            await self.db_manager.save_odds_history(
                match.id, match.odds1, match.odds2, match.odds_draw
            )
    
    async def get_page_content(self, url: str) -> Optional[str]:
        """Получение содержимого страницы"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def generate_match_id(self, team1: str, team2: str, match_time: datetime) -> str:
        """Генерация ID матча"""
        return f"{team1}_{team2}_{match_time.strftime('%Y%m%d_%H%M')}".replace(' ', '_')
    
    async def retry_request(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Повторный запрос при ошибке"""
        for attempt in range(max_retries):
            content = await self.get_page_content(url)
            if content:
                return content
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Экспоненциальный бэкоф
        
        return None
