import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base_analyzer import BaseAnalyzer, Scenario
from ..database import Match, Signal

logger = logging.getLogger(__name__)


class CS2Analyzer(BaseAnalyzer):
    """Анализатор матчей CS2"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager, 'cs2')
        
        # CS2 специфичные сценарии
        self.cs2_scenarios = {
            'overvalued_favorite': self._detect_overvalued_favorite,
            'public_trap': self._detect_public_trap,
            'delayed_reaction': self._detect_delayed_reaction,
            'comeback_scenario': self._detect_comeback_scenario,
            'map_advantage': self._detect_map_advantage,
            'roster_instability': self._detect_roster_instability,
            'tournament_mismatch': self._detect_tournament_mismatch,
            'form_momentum': self._detect_form_momentum
        }
    
    async def _detect_scenarios(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> List[Scenario]:
        """Обнаружение CS2 сценариев"""
        scenarios = []
        
        # Проверяем каждый сценарий
        for scenario_name, detector_func in self.cs2_scenarios.items():
            try:
                scenario = await detector_func(match, historical_data, odds_analysis)
                if scenario:
                    scenarios.append(scenario)
            except Exception as e:
                logger.error(f"Error detecting scenario {scenario_name}: {e}")
        
        # Сортируем по вероятности
        scenarios.sort(key=lambda x: x.probability, reverse=True)
        
        # Возвращаем топ-5 сценариев
        return scenarios[:5]
    
    async def _detect_overvalued_favorite(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение переоцененного фаворита"""
        try:
            # Проверяем, является ли одна команда явным фаворитом
            if not odds_analysis.get('favorite'):
                return None
            
            favorite_odds = odds_analysis['favorite_odds']
            
            # Фаворит считается переоцененным, если коэффициент слишком низкий
            if favorite_odds < 1.30:
                # Проверяем историческую производительность
                historical_performance = self._analyze_historical_performance(match.team1, historical_data)
                
                if historical_performance['win_rate'] < 0.7:  # Фаворит не доминирует исторически
                    return Scenario(
                        name="Переоцененный фаворит",
                        confidence="HIGH",
                        probability=0.75,
                        explanation=f"Команда {odds_analysis['favorite']} является фаворитом с коэффициентом {favorite_odds:.2f}, но исторически выигрывает только {historical_performance['win_rate']:.1%} матчей. Коэффициент не отражает реальную силу команды.",
                        factors=[
                            f"Низкий коэффициент фаворита ({favorite_odds:.2f})",
                            f"Историческая win rate: {historical_performance['win_rate']:.1%}",
                            "Возможная переоценка букмекерами"
                        ],
                        recommendation="Рассмотреть ставку на андердога"
                    )
        
        except Exception as e:
            logger.error(f"Error in overvalued_favorite detection: {e}")
        
        return None
    
    async def _detect_public_trap(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение ловушки для общественных ставок"""
        try:
            # Проверяем перекос коэффициентов
            if odds_analysis.get('is_skewed'):
                odds_ratio = odds_analysis['odds_ratio']
                
                # Анализируем движение коэффициентов
                odds_movement = await self._analyze_odds_movement(match)
                
                if odds_movement['public_trend'] == 'favorite' and odds_ratio > 2.5:
                    return Scenario(
                        name="Ловушка общественных ставок",
                        confidence="MEDIUM",
                        probability=0.65,
                        explanation=f"Высокий перекос коэффициентов ({odds_ratio:.2f}) и движение линии в пользу фаворита могут указывать на ловушку для общественных ставок. Букмекеры могут искусственно занижать коэффициент на фаворита.",
                        factors=[
                            f"Перекос коэффициентов: {odds_ratio:.2f}",
                            "Движение линии в пользу фаворита",
                            "Высокий интерес публики"
                        ],
                        recommendation="Осторожность со ставками на фаворита"
                    )
        
        except Exception as e:
            logger.error(f"Error in public_trap detection: {e}")
        
        return None
    
    async def _detect_delayed_reaction(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение запоздалой реакции линии"""
        try:
            # Анализируем недавние изменения в составах
            roster_changes = await self._check_recent_roster_changes(match)
            
            if roster_changes['has_changes']:
                # Проверяем, отразились ли изменения в коэффициентах
                odds_reaction = await self._analyze_odds_reaction_to_changes(match)
                
                if not odds_reaction['reacted']:
                    return Scenario(
                        name="Запоздалая реакция линии",
                        confidence="MEDIUM",
                        probability=0.60,
                        explanation=f"Команда {roster_changes['team']} имела изменения в составе, но коэффициенты не отразили это изменение. Линия может быть неточной.",
                        factors=[
                            f"Изменения в составе {roster_changes['team']}",
                            "Коэффициенты не изменились",
                            "Возможная недооценка/переоценка"
                        ],
                        recommendation="Следить за движением линии"
                    )
        
        except Exception as e:
            logger.error(f"Error in delayed_reaction detection: {e}")
        
        return None
    
    async def _detect_comeback_scenario(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение сценария камбэка"""
        try:
            # Анализируем исторические камбэки команд
            comeback_stats = await self._analyze_comeback_history(match)
            
            if comeback_stats['frequent_comebacks']:
                # Проверяем, является ли матч потенциальным для камбэка
                if odds_analysis.get('odds_ratio', 0) > 1.8:  # Не слишком неравный матч
                    return Scenario(
                        name="Потенциальный камбэк",
                        confidence="MEDIUM",
                        probability=0.55,
                        explanation=f"Одна из команд ({comeback_stats['team']}) имеет историю камбэков ({comeback_stats['comeback_rate']:.1%}). Матч может быть драматичным с возможностью развернуться.",
                        factors=[
                            f"История камбэков: {comeback_stats['comeback_rate']:.1%}",
                            "Сбалансированные коэффициенты",
                            "Потенциально драматичный матч"
                        ],
                        recommendation="Рассмотреть live ставки"
                    )
        
        except Exception as e:
            logger.error(f"Error in comeback_scenario detection: {e}")
        
        return None
    
    async def _detect_map_advantage(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаруж преимущества на картах"""
        try:
            # Анализируем преимущества команд на картах
            map_stats = await self._analyze_map_advantage(match)
            
            if map_stats['significant_advantage']:
                return Scenario(
                    name="Преимущество на картах",
                    confidence="LOW",
                    probability=0.52,
                    explanation=f"Команда {map_stats['advantaged_team']} имеет преимущество на картах ({map_stats['win_rate']:.1%} win rate). В BO3 это может быть решающим фактором.",
                    factors=[
                        f"Преимущество на картах: {map_stats['win_rate']:.1%}",
                        "Формат BO3",
                        "Стратегическая подготовка"
                    ],
                    recommendation="Учесть в BO3 ставках"
                )
        
        except Exception as e:
            logger.error(f"Error in map_advantage detection: {e}")
        
        return None
    
    async def _detect_roster_instability(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение нестабильности составов"""
        try:
            # Проверяем стабильность составов
            roster_stability = await self._analyze_roster_stability(match)
            
            if roster_stability['unstable']:
                return Scenario(
                    name="Нестабильность состава",
                    confidence="MEDIUM",
                    probability=0.58,
                    explanation=f"Команда {roster_stability['unstable_team']} имеет нестабильный состав ({roster_stability['changes_count']} изменений за 3 месяца). Это может повлиять на производительность.",
                    factors=[
                        f"Изменения в составе: {roster_stability['changes_count']}",
                        "Короткое время игры вместе",
                        "Потенциальные проблемы с синхронизацией"
                    ],
                    recommendation="Осторожность с ставками на эту команду"
                )
        
        except Exception as e:
            logger.error(f"Error in roster_instability detection: {e}")
        
        return None
    
    async def _detect_tournament_mismatch(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение несоответствия уровней турниров"""
        try:
            # Анализируем уровни турниров
            tournament_analysis = await self._analyze_tournament_levels(match)
            
            if tournament_analysis['mismatch']:
                return Scenario(
                    name="Несоответствие уровней турниров",
                    confidence="LOW",
                    probability=0.51,
                    explanation=f"Команды имеют разный опыт на турнирах разного уровня. {tournament_analysis['experienced_team']} имеет больше опыта на высокоуровневых турнирах.",
                    factors=[
                        f"Разница в уровне турниров",
                        f"Опыт {tournament_analysis['experienced_team']}",
                        "Психологический фактор"
                    ],
                    recommendation="Учесть опыт турниров"
                )
        
        except Exception as e:
            logger.error(f"Error in tournament_mismatch detection: {e}")
        
        return None
    
    async def _detect_form_momentum(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение формы и момента"""
        try:
            # Анализируем текущую форму команд
            form_analysis = await self._analyze_current_form(match)
            
            if form_analysis['momentum_team']:
                return Scenario(
                    name="Форма и момент",
                    confidence="MEDIUM",
                    probability=0.57,
                    explanation=f"Команда {form_analysis['momentum_team']} находится в отличной форме ({form_analysis['recent_win_rate']:.1%} побед в последних 5 матчах). Текущий момент может быть решающим.",
                    factors=[
                        f"Форма: {form_analysis['recent_win_rate']:.1%}",
                        "Позитивная динамика",
                        "Высокий моральный дух"
                    ],
                    recommendation="Учесть текущую форму"
                )
        
        except Exception as e:
            logger.error(f"Error in form_momentum detection: {e}")
        
        return None
    
    # Вспомогательные методы
    def _analyze_historical_performance(self, team: str, historical_data: List[Dict]) -> Dict:
        """Анализ исторической производительности команды"""
        team_matches = [
            match for match in historical_data 
            if match['team1'] == team or match['team2'] == team
        ]
        
        if not team_matches:
            return {'win_rate': 0.5, 'matches': 0}
        
        wins = sum(1 for match in team_matches if match['result'] == team)
        win_rate = wins / len(team_matches)
        
        return {'win_rate': win_rate, 'matches': len(team_matches)}
    
    async def _analyze_odds_movement(self, match: Match) -> Dict:
        """Анализ движения коэффициентов"""
        # В реальном приложении здесь будет анализ истории коэффициентов
        return {
            'public_trend': 'favorite' if match.odds1 < match.odds2 else 'underdog',
            'movement_significant': False,
            'direction': 'stable'
        }
    
    async def _check_recent_roster_changes(self, match: Match) -> Dict:
        """Проверка недавних изменений в составах"""
        # В реальном приложении здесь будет проверка составов
        return {
            'has_changes': False,
            'team': match.team1,
            'changes_count': 0
        }
    
    async def _analyze_odds_reaction_to_changes(self, match: Match) -> Dict:
        """Анализ реакции коэффициентов на изменения"""
        return {
            'reacted': False,
            'reaction_time': 0
        }
    
    async def _analyze_comeback_history(self, match: Match) -> Dict:
        """Анализ истории камбэков"""
        # В реальном приложении здесь будет анализ истории камбэков
        return {
            'frequent_comebacks': False,
            'team': match.team1,
            'comeback_rate': 0.15
        }
    
    async def _analyze_map_advantage(self, match: Match) -> Dict:
        """Анализ преимуществ на картах"""
        # В реальном приложении здесь будет анализ статистики на картах
        return {
            'significant_advantage': False,
            'advantaged_team': match.team1,
            'win_rate': 0.55
        }
    
    async def _analyze_roster_stability(self, match: Match) -> Dict:
        """Анализ стабильности составов"""
        # В реальном приложении здесь будет анализ стабильности
        return {
            'unstable': False,
            'unstable_team': match.team1,
            'changes_count': 0
        }
    
    async def _analyze_tournament_levels(self, match: Match) -> Dict:
        """Анализ уровней турниров"""
        # В реальном приложении здесь будет анализ уровней турниров
        return {
            'mismatch': False,
            'experienced_team': match.team1
        }
    
    async def _analyze_current_form(self, match: Match) -> Dict:
        """Анализ текущей формы"""
        # В реальном приложении здесь будет анализ формы
        return {
            'momentum_team': None,
            'recent_win_rate': 0.5
        }
