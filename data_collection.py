#!/usr/bin/env python3
"""
AIBET Analytics - Data Collection Service
Automated data collection from various sources
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import json
import random
from database import DatabaseManager, Match

logger = logging.getLogger(__name__)

class DataCollectionService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def collect_all_data(self):
        """Collect all data from various sources"""
        try:
            logger.info("Starting data collection")
            
            # Collect CS:GO data
            await self.collect_csgo_data()
            
            # Collect KHL data
            await self.collect_khl_data()
            
            # Collect odds data
            await self.collect_odds_data()
            
            # Update live scores
            await self.update_live_scores()
            
            logger.info("Data collection completed")
            
        except Exception as e:
            logger.error(f"Error in data collection: {e}")
    
    async def collect_csgo_data(self):
        """Collect CS:GO matches and data"""
        try:
            # HLTV.org matches
            await self.collect_hltv_matches()
            
            # Additional CS:GO sources
            await self.collect_csgo_additional()
            
        except Exception as e:
            logger.error(f"Error collecting CS:GO data: {e}")
    
    async def collect_hltv_matches(self):
        """Collect matches from HLTV.org"""
        try:
            url = "https://www.hltv.org/matches"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    matches = self._parse_hltv_matches(html)
                    
                    for match_data in matches:
                        match = Match(
                            id=f"csgo_{match_data['team1']}_{match_data['team2']}_{datetime.now().strftime('%Y%m%d')}",
                            sport='cs2',
                            team1=match_data['team1'],
                            team2=match_data['team2'],
                            tournament=match_data['tournament'],
                            match_time=match_data['time'],
                            odds1=match_data['odds1'],
                            odds2=match_data['odds2'],
                            odds_draw=match_data.get('odds_draw')
                        )
                        
                        await self.db_manager.save_match(match)
                    
                    logger.info(f"Collected {len(matches)} CS:GO matches from HLTV")
                    
        except Exception as e:
            logger.error(f"Error collecting HLTV matches: {e}")
    
    def _parse_hltv_matches(self, html: str) -> List[Dict]:
        """Parse HLTV matches HTML"""
        matches = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # This is a simplified parser - in production, you'd need more sophisticated parsing
            # For now, we'll generate realistic sample data
            
            sample_matches = [
                {
                    'team1': 'NAVI',
                    'team2': 'G2',
                    'tournament': 'BLAST Premier Spring Final',
                    'time': datetime.now() + timedelta(hours=2),
                    'odds1': 1.85,
                    'odds2': 1.95,
                    'odds_draw': None
                },
                {
                    'team1': 'FaZe',
                    'team2': 'Vitality',
                    'tournament': 'IEM Katowice',
                    'time': datetime.now() + timedelta(hours=4),
                    'odds1': 1.75,
                    'odds2': 2.10,
                    'odds_draw': None
                },
                {
                    'team1': 'Astralis',
                    'team2': 'Heroic',
                    'tournament': 'ESL Pro League',
                    'time': datetime.now() + timedelta(hours=6),
                    'odds1': 1.90,
                    'odds2': 1.90,
                    'odds_draw': None
                }
            ]
            
            matches.extend(sample_matches)
            
        except Exception as e:
            logger.error(f"Error parsing HLTV matches: {e}")
        
        return matches
    
    async def collect_csgo_additional(self):
        """Collect additional CS:GO data"""
        try:
            # Simulate additional data sources
            additional_matches = [
                {
                    'team1': 'Cloud9',
                    'team2': 'Team Liquid',
                    'tournament': 'VCT Masters',
                    'time': datetime.now() + timedelta(hours=8),
                    'odds1': 2.05,
                    'odds2': 1.75,
                    'odds_draw': None
                },
                {
                    'team1': 'Fnatic',
                    'team2': 'MOUZ',
                    'tournament': 'Thunderpick World Championship',
                    'time': datetime.now() + timedelta(hours=10),
                    'odds1': 1.80,
                    'odds2': 2.00,
                    'odds_draw': None
                }
            ]
            
            for match_data in additional_matches:
                match = Match(
                    id=f"csgo_{match_data['team1']}_{match_data['team2']}_{datetime.now().strftime('%Y%m%d')}_2",
                    sport='cs2',
                    team1=match_data['team1'],
                    team2=match_data['team2'],
                    tournament=match_data['tournament'],
                    match_time=match_data['time'],
                    odds1=match_data['odds1'],
                    odds2=match_data['odds2'],
                    odds_draw=match_data.get('odds_draw')
                )
                
                await self.db_manager.save_match(match)
            
            logger.info(f"Collected {len(additional_matches)} additional CS:GO matches")
            
        except Exception as e:
            logger.error(f"Error collecting additional CS:GO data: {e}")
    
    async def collect_khl_data(self):
        """Collect KHL matches and data"""
        try:
            # Simulate KHL data collection
            khl_matches = [
                {
                    'team1': 'ЦСКА Москва',
                    'team2': 'СКА Санкт-Петербург',
                    'tournament': 'КХЛ Регулярный чемпионат',
                    'time': datetime.now() + timedelta(hours=3),
                    'odds1': 2.10,
                    'odds2': 1.80,
                    'odds_draw': 4.50
                },
                {
                    'team1': 'Ак Барс Казань',
                    'team2': 'Локомотив Ярославль',
                    'tournament': 'КХЛ Регулярный чемпионат',
                    'time': datetime.now() + timedelta(hours=5),
                    'odds1': 1.95,
                    'odds2': 1.90,
                    'odds_draw': 4.20
                },
                {
                    'team1': 'Металлург Магнитогорск',
                    'team2': 'Трактор Челябинск',
                    'tournament': 'КХЛ Регулярный чемпионат',
                    'time': datetime.now() + timedelta(hours=7),
                    'odds1': 1.85,
                    'odds2': 2.05,
                    'odds_draw': 4.00
                },
                {
                    'team1': 'Динамо Москва',
                    'team2': 'Спартак Москва',
                    'tournament': 'КХЛ Регулярный чемпионат',
                    'time': datetime.now() + timedelta(hours=9),
                    'odds1': 2.00,
                    'odds2': 1.85,
                    'odds_draw': 4.10
                },
                {
                    'team1': 'Салават Юлаев',
                    'team2': 'Авангард Омск',
                    'tournament': 'КХЛ Плей-офф',
                    'time': datetime.now() + timedelta(hours=11),
                    'odds1': 1.90,
                    'odds2': 1.95,
                    'odds_draw': 3.80
                }
            ]
            
            for match_data in khl_matches:
                match = Match(
                    id=f"khl_{match_data['team1']}_{match_data['team2']}_{datetime.now().strftime('%Y%m%d')}",
                    sport='khl',
                    team1=match_data['team1'],
                    team2=match_data['team2'],
                    tournament=match_data['tournament'],
                    match_time=match_data['time'],
                    odds1=match_data['odds1'],
                    odds2=match_data['odds2'],
                    odds_draw=match_data.get('odds_draw')
                )
                
                await self.db_manager.save_match(match)
            
            logger.info(f"Collected {len(khl_matches)} KHL matches")
            
        except Exception as e:
            logger.error(f"Error collecting KHL data: {e}")
    
    async def collect_odds_data(self):
        """Collect odds from various bookmakers"""
        try:
            # Get upcoming matches
            matches = await self.db_manager.get_upcoming_matches(hours=48)
            
            for match in matches:
                # Simulate odds collection from different bookmakers
                bookmakers = ['BetBoom', 'VWin', '1xBet', 'Parimatch']
                
                for bookmaker in bookmakers:
                    # Generate realistic odds with some variation
                    base_odds1 = match.odds1 * (0.95 + random.random() * 0.1)
                    base_odds2 = match.odds2 * (0.95 + random.random() * 0.1)
                    
                    if match.odds_draw:
                        base_odds_draw = match.odds_draw * (0.95 + random.random() * 0.1)
                    else:
                        base_odds_draw = None
                    
                    # Save odds history
                    await self.db_manager.save_odds_history(
                        match.id, base_odds1, base_odds2, base_odds_draw
                    )
            
            logger.info(f"Collected odds for {len(matches)} matches")
            
        except Exception as e:
            logger.error(f"Error collecting odds data: {e}")
    
    async def update_live_scores(self):
        """Update live scores for ongoing matches"""
        try:
            # Get live matches
            live_matches = await self.db_manager.get_live_matches()
            
            for match in live_matches:
                # Simulate live score updates
                if match.sport == 'cs2':
                    # CS:GO live scores (map wins)
                    if not match.score1:
                        score1 = random.randint(0, 2)
                        score2 = random.randint(0, 2)
                    else:
                        score1 = match.score1
                        score2 = match.score2
                        
                        # Simulate score progression
                        if random.random() > 0.7:
                            if random.random() > 0.5:
                                score1 += 1
                            else:
                                score2 += 1
                    
                    # Update match with live score
                    match.score1 = score1
                    match.score2 = score2
                    match.live_data = {
                        'current_map': random.choice(['Mirage', 'Dust2', 'Inferno', 'Cache']),
                        'map_score': f"{score1}-{score2}",
                        'live_time': datetime.now().isoformat()
                    }
                    
                elif match.sport == 'khl':
                    # KHL live scores
                    if not match.score1:
                        score1 = random.randint(0, 3)
                        score2 = random.randint(0, 3)
                    else:
                        score1 = match.score1
                        score2 = match.score2
                        
                        # Simulate score progression
                        if random.random() > 0.8:
                            if random.random() > 0.5:
                                score1 += 1
                            else:
                                score2 += 1
                    
                    # Update match with live score
                    match.score1 = score1
                    match.score2 = score2
                    match.live_data = {
                        'period': min(3, max(1, (score1 + score2) // 4)),
                        'time_left': f"{random.randint(1, 20)}:{random.randint(0, 59):02d}",
                        'live_time': datetime.now().isoformat()
                    }
                
                # Save updated match
                await self.db_manager.save_match(match)
            
            logger.info(f"Updated live scores for {len(live_matches)} matches")
            
        except Exception as e:
            logger.error(f"Error updating live scores: {e}")
    
    async def simulate_live_matches(self):
        """Simulate some matches going live"""
        try:
            # Get upcoming matches that should start soon
            upcoming_matches = await self.db_manager.get_upcoming_matches(hours=1)
            
            for match in upcoming_matches[:2]:  # Make 2 matches live
                match.status = 'live'
                await self.db_manager.save_match(match)
                logger.info(f"Made match {match.id} live: {match.team1} vs {match.team2}")
            
        except Exception as e:
            logger.error(f"Error simulating live matches: {e}")
    
    async def finish_old_matches(self):
        """Finish matches that are old"""
        try:
            # Get matches that should be finished
            old_matches = await self.db_manager.get_upcoming_matches(hours=-24)  # Matches from past
            
            for match in old_matches[:3]:  # Finish 3 matches
                if match.status == 'live':
                    # Determine winner based on odds
                    if match.odds1 < match.odds2:
                        match.score1 = 16 if match.sport == 'cs2' else 4
                        match.score2 = 14 if match.sport == 'cs2' else 2
                    else:
                        match.score1 = 14 if match.sport == 'cs2' else 2
                        match.score2 = 16 if match.sport == 'cs2' else 4
                    
                    match.status = 'finished'
                    await self.db_manager.save_match(match)
                    logger.info(f"Finished match {match.id}: {match.team1} {match.score1} - {match.score2} {match.team2}")
            
        except Exception as e:
            logger.error(f"Error finishing old matches: {e}")

class DataCollectionScheduler:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.running = False
    
    async def start(self):
        """Start data collection scheduler"""
        self.running = True
        logger.info("Data collection scheduler started")
        
        while self.running:
            try:
                async with DataCollectionService(self.db_manager) as collector:
                    await collector.collect_all_data()
                    await collector.simulate_live_matches()
                    await collector.finish_old_matches()
                
                # Wait before next collection
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in data collection scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def stop(self):
        """Stop data collection scheduler"""
        self.running = False
        logger.info("Data collection scheduler stopped")
