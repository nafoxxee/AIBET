import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from base_analyzer import BaseAnalyzer, Scenario
from database import Match, Signal

logger = logging.getLogger(__name__)


class KHLAnalyzer(BaseAnalyzer):
    """Анализатор матчей КХЛ"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager, 'khl')
        
        # КХЛ специфичные сценарии
        self.khl_scenarios = {
            'home_ice_advantage': self._detect_home_ice_advantage,
            'goalie_mismatch': self._detect_goalie_mismatch,
            'power_play_efficiency': self._detect_power_play_efficiency,
            'fatigue_factor': self._detect_fatigue_factor,
            'rivalry_match': self._detect_rivalry_match,
            'playoff_intensity': self._detect_playoff_intensity,
            'scoring_drought': self._detect_scoring_drought,
            'overtime_tendency': self._detect_overtime_tendency,
            'period_performance': self._detect_period_performance,
            'momentum_shift': self._detect_momentum_shift
        }
    
    async def _detect_scenarios(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> List[Scenario]:
        """Обнаружение КХЛ сценариев"""
        scenarios = []
        
        # Проверяем каждый сценарий
        for scenario_name, detector_func in self.khl_scenarios.items():
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
    
    async def _detect_home_ice_advantage(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение преимущества домашнего льда"""
        try:
            # Анализируем домашнюю статистику
            home_stats = await self._analyze_home_performance(match.team1)
            away_stats = await self._analyze_away_performance(match.team2)
            
            home_advantage = home_stats['home_win_rate'] - away_stats['away_win_rate']
            
            if home_advantage > 0.15:  # Значительное преимущество
                return Scenario(
                    name="Преимущество домашнего льда",
                    confidence="MEDIUM",
                    probability=0.62,
                    explanation=f"Команда {match.team1} имеет сильное преимущество домашнего льда ({home_stats['home_win_rate']:.1%} побед дома). {match.team2} выигрывает только {away_stats['away_win_rate']:.1%} в гостях.",
                    factors=[
                        f"Домашний win rate: {home_stats['home_win_rate']:.1%}",
                        f"Гостевой win rate соперника: {away_stats['away_win_rate']:.1%}",
                        "Поддержка болельщиков",
                        "Знание ледовой арены"
                    ],
                    recommendation="Учесть преимущество домашней команды"
                )
        
        except Exception as e:
            logger.error(f"Error in home_ice_advantage detection: {e}")
        
        return None
    
    async def _detect_goalie_mismatch(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение несоответствия вратарей"""
        try:
            # Анализируем статистику вратарей
            goalie1_stats = await self._analyze_goalie_performance(match.team1)
            goalie2_stats = await self._analyze_goalie_performance(match.team2)
            
            save_rate_diff = goalie1_stats['save_rate'] - goalie2_stats['save_rate']
            
            if abs(save_rate_diff) > 0.05:  # Значительная разница
                better_goalie = match.team1 if save_rate_diff > 0 else match.team2
                better_stats = goalie1_stats if save_rate_diff > 0 else goalie2_stats
                
                return Scenario(
                    name="Преимущество вратаря",
                    confidence="MEDIUM",
                    probability=0.58,
                    explanation=f"Вратарь команды {better_goalie} показывает значительно лучшие показатели ({better_stats['save_rate']:.1%} save rate, {better_stats['gaa']:.2f} GAA). Это может быть решающим фактором.",
                    factors=[
                        f"Save rate: {better_stats['save_rate']:.1%}",
                        f"GAA: {better_stats['gaa']:.2f}",
                        "Надежность в критические моменты"
                    ],
                    recommendation="Учесть качество вратаря"
                )
        
        except Exception as e:
            logger.error(f"Error in goalie_mismatch detection: {e}")
        
        return None
    
    async def _detect_power_play_efficiency(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение эффективности большинства/меньшинства"""
        try:
            # Анализируем игру в большинстве
            pp1_stats = await self._analyze_power_play(match.team1)
            pp2_stats = await self._analyze_power_play(match.team2)
            
            pk1_stats = await self._analyze_penalty_kill(match.team1)
            pk2_stats = await self._analyze_penalty_kill(match.team2)
            
            # Команда с лучшим большинством и худшим меньшинством соперника
            team1_advantage = (pp1_stats['efficiency'] - pk2_stats['efficiency'])
            team2_advantage = (pp2_stats['efficiency'] - pk1_stats['efficiency'])
            
            if abs(team1_advantage) > 0.15 or abs(team2_advantage) > 0.15:
                advantaged_team = match.team1 if team1_advantage > team2_advantage else match.team2
                advantage = max(team1_advantage, team2_advantage)
                
                return Scenario(
                    name="Преимущество в специальных бригадах",
                    confidence="LOW",
                    probability=0.53,
                    explanation=f"Команда {advantaged_team} имеет преимущество в игре в большинстве/меньшинстве ({advantage:+.1%}). Это может быть важно при удалениях.",
                    factors=[
                        f"Эффективность большинства: {advantage:+.1%}",
                        "Игра в меньшинстве",
                        "Дисциплина команд"
                    ],
                    recommendation="Следить за удалениями"
                )
        
        except Exception as e:
            logger.error(f"Error in power_play_efficiency detection: {e}")
        
        return None
    
    async def _detect_fatigue_factor(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение фактора усталости"""
        try:
            # Анализируем плотность расписания
            fatigue1 = await self._analyze_fatigue(match.team1)
            fatigue2 = await self._analyze_fatigue(match.team2)
            
            fatigue_diff = fatigue1['fatigue_score'] - fatigue2['fatigue_score']
            
            if abs(fatigue_diff) > 20:  # Значительная разница в усталости
                more_fatigued = match.team1 if fatigue_diff > 0 else match.team2
                less_fatigued = match.team2 if fatigue_diff > 0 else match.team1
                
                return Scenario(
                    name="Фактор усталости",
                    confidence="MEDIUM",
                    probability=0.56,
                    explanation=f"Команда {more_fatigued} имеет более плотное расписание ({fatigue1['games_in_7_days'] if fatigue_diff > 0 else fatigue2['games_in_7_days']} игр за 7 дней). Усталость может повлиять на производительность.",
                    factors=[
                        f"Игр за 7 дней: {fatigue1['games_in_7_days'] if fatigue_diff > 0 else fatigue2['games_in_7_days']}",
                        "Короткое время на восстановление",
                        "Физическая подготовка"
                    ],
                    recommendation="Учесть физическое состояние"
                )
        
        except Exception as e:
            logger.error(f"Error in fatigue_factor detection: {e}")
        
        return None
    
    async def _detect_rivalry_match(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение принципиального матча"""
        try:
            # Проверяем историю противостояний
            rivalry_data = await self._analyze_rivalry(match.team1, match.team2)
            
            if rivalry_data['is_rivalry'] and rivalry_data['close_games']:
                return Scenario(
                    name="Принципиальное противостояние",
                    confidence="MEDIUM",
                    probability=0.55,
                    explanation=f"Матч между {match.team1} и {match.team2} является принципиальным. История показывает напряженные игры ({rivalry_data['avg_goal_diff']:.1f} средняя разница голов).",
                    factors=[
                        f"История противостояний: {rivalry_data['total_games']} игр",
                        f"Средняя разница голов: {rivalry_data['avg_goal_diff']:.1f}",
                        "Эмоциональная составляющая",
                        "Мотивация превзойти соперника"
                    ],
                    recommendation="Ожидать напряженной игры"
                )
        
        except Exception as e:
            logger.error(f"Error in rivalry_match detection: {e}")
        
        return None
    
    async def _detect_playoff_intensity(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение плейофф интенсивности"""
        try:
            # Проверяем, является ли матч плейофф
            if 'playoff' in match.tournament.lower() or 'play-offs' in match.tournament.lower():
                playoff_stats = await self._analyze_playoff_performance(match)
                
                return Scenario(
                    name="Плейофф интенсивность",
                    confidence="HIGH",
                    probability=0.70,
                    explanation="Это плейофф матч, который характеризуется повышенной интенсивностью, физической борьбой и непредсказуемостью. Коэффициенты могут быть менее надежными.",
                    factors=[
                        "Плейофф формат",
                        "Повышенная интенсивность",
                        "Непредсказуемость результатов",
                        "Эмоциональное давление"
                    ],
                    recommendation="Осторожность с предсказаниями"
                )
        
        except Exception as e:
            logger.error(f"Error in playoff_intensity detection: {e}")
        
        return None
    
    async def _detect_scoring_drought(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение голевой засухи"""
        try:
            # Анализируем голевую продуктивность
            scoring1 = await self._analyze_scoring_trends(match.team1)
            scoring2 = await self._analyze_scoring_trends(match.team2)
            
            drought_detected = False
            drought_team = None
            
            if scoring1['recent_goals_per_game'] < 1.5:
                drought_detected = True
                drought_team = match.team1
            elif scoring2['recent_goals_per_game'] < 1.5:
                drought_detected = True
                drought_team = match.team2
            
            if drought_detected:
                return Scenario(
                    name="Голевая засуха",
                    confidence="MEDIUM",
                    probability=0.54,
                    explanation=f"Команда {drought_team} испытывает трудности с реализацией ({scoring1['recent_goals_per_game'] if drought_team == match.team1 else scoring2['recent_goals_per_game']:.1f} гола за игру). Это может повлиять на результат.",
                    factors=[
                        f"Голы за игру: {scoring1['recent_goals_per_game'] if drought_team == match.team1 else scoring2['recent_goals_per_game']:.1f}",
                        "Проблемы в атаке",
                        "Низкая реализация моментов"
                    ],
                    recommendation="Учесть атакующие проблемы"
                )
        
        except Exception as e:
            logger.error(f"Error in scoring_drought detection: {e}")
        
        return None
    
    async def _detect_overtime_tendency(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение тенденции к овертаймам"""
        try:
            # Анализируем историю овертаймов
            ot_stats1 = await self._analyze_overtime_history(match.team1)
            ot_stats2 = await self._analyze_overtime_history(match.team2)
            
            combined_ot_rate = (ot_stats1['ot_rate'] + ot_stats2['ot_rate']) / 2
            
            if combined_ot_rate > 0.25:  # Более 25% матчей уходят в овертайм
                return Scenario(
                    name="Склонность к овертаймам",
                    confidence="LOW",
                    probability=0.52,
                    explanation=f"Обе команды имеют историю овертаймов ({ot_stats1['ot_rate']:.1%} и {ot_stats2['ot_rate']:.1%}). Матч может дойти до дополнительного времени.",
                    factors=[
                        f"OT rate {match.team1}: {ot_stats1['ot_rate']:.1%}",
                        f"OT rate {match.team2}: {ot_stats2['ot_rate']:.1%}",
                        "Сбалансированные команды",
                        "Возможность овертайма"
                    ],
                    recommendation="Рассмотреть ставки на овертайм"
                )
        
        except Exception as e:
            logger.error(f"Error in overtime_tendency detection: {e}")
        
        return None
    
    async def _detect_period_performance(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение периодической производительности"""
        try:
            # Анализируем производительность по периодам
            period1_stats = await self._analyze_period_performance(match.team1, match.team2, 1)
            period2_stats = await self._analyze_period_performance(match.team1, match.team2, 2)
            period3_stats = await self._analyze_period_performance(match.team1, match.team2, 3)
            
            # Ищем аномалии в периодах
            anomalies = []
            
            if period1_stats['goal_diff'] > 1.5:
                anomalies.append(f"1-й период: {period1_stats['goal_diff']:+.1f}")
            if period2_stats['goal_diff'] > 1.5:
                anomalies.append(f"2-й период: {period2_stats['goal_diff']:+.1f}")
            if period3_stats['goal_diff'] > 1.5:
                anomalies.append(f"3-й период: {period3_stats['goal_diff']:+.1f}")
            
            if anomalies:
                return Scenario(
                    name="Периодическая аномалия",
                    confidence="LOW",
                    probability=0.51,
                    explanation=f"История противостояний показывает аномалии в периодах: {', '.join(anomalies)}. Это может указывать на особенности игры команд.",
                    factors=[
                        f"Аномалии: {', '.join(anomalies)}",
                        "Особенности периодов",
                        "Тактические паттерны"
                    ],
                    recommendation="Учесть периодическую динамику"
                )
        
        except Exception as e:
            logger.error(f"Error in period_performance detection: {e}")
        
        return None
    
    async def _detect_momentum_shift(self, match: Match, historical_data: List[Dict], odds_analysis: Dict) -> Optional[Scenario]:
        """Обнаружение смены момента"""
        try:
            # Анализируем текущий момент команд
            momentum1 = await self._analyze_current_momentum(match.team1)
            momentum2 = await self._analyze_current_momentum(match.team2)
            
            momentum_diff = momentum1['momentum_score'] - momentum2['momentum_score']
            
            if abs(momentum_diff) > 30:  # Значительная разница в моменте
                momentum_team = match.team1 if momentum_diff > 0 else match.team2
                
                return Scenario(
                    name="Смена момента",
                    confidence="MEDIUM",
                    probability=0.57,
                    explanation=f"Команда {momentum_team} находится на подъеме ({momentum1['recent_points'] if momentum_diff > 0 else momentum2['recent_points']} очков в последних 5 играх). Текущий момент может быть решающим.",
                    factors=[
                        f"Очки в последних 5 играх: {momentum1['recent_points'] if momentum_diff > 0 else momentum2['recent_points']}",
                        "Позитивная динамика",
                        "Высокая уверенность"
                    ],
                    recommendation="Учесть текущий момент"
                )
        
        except Exception as e:
            logger.error(f"Error in momentum_shift detection: {e}")
        
        return None
    
    # Вспомогательные методы для анализа КХЛ
    async def _analyze_home_performance(self, team: str) -> Dict:
        """Анализ домашней производительности"""
        # В реальном приложении здесь будет анализ статистики
        return {
            'home_win_rate': 0.65,
            'home_goals_for': 3.2,
            'home_goals_against': 2.1
        }
    
    async def _analyze_away_performance(self, team: str) -> Dict:
        """Анализ гостевой производительности"""
        return {
            'away_win_rate': 0.45,
            'away_goals_for': 2.4,
            'away_goals_against': 2.8
        }
    
    async def _analyze_goalie_performance(self, team: str) -> Dict:
        """Анализ производительности вратаря"""
        return {
            'save_rate': 0.91,
            'gaa': 2.45,
            'so': 3
        }
    
    async def _analyze_power_play(self, team: str) -> Dict:
        """Анализ игры в большинстве"""
        return {
            'efficiency': 0.22,
            'goals_per_game': 0.65
        }
    
    async def _analyze_penalty_kill(self, team: str) -> Dict:
        """Анализ игры в меньшинстве"""
        return {
            'efficiency': 0.82,
            'goals_against_per_game': 0.45
        }
    
    async def _analyze_fatigue(self, team: str) -> Dict:
        """Анализ усталости"""
        return {
            'fatigue_score': 15,
            'games_in_7_days': 3,
            'days_since_last_game': 1
        }
    
    async def _analyze_rivalry(self, team1: str, team2: str) -> Dict:
        """Анализ противостояния"""
        return {
            'is_rivalry': True,
            'total_games': 25,
            'avg_goal_diff': 1.2,
            'close_games': 18
        }
    
    async def _analyze_playoff_performance(self, match: Match) -> Dict:
        """Анализ плейофф производительности"""
        return {
            'playoff_experience': True,
            'intensity_level': 'high'
        }
    
    async def _analyze_scoring_trends(self, team: str) -> Dict:
        """Анализ голевых трендов"""
        return {
            'recent_goals_per_game': 2.1,
            'trend': 'stable'
        }
    
    async def _analyze_overtime_history(self, team: str) -> Dict:
        """Анализ истории овертаймов"""
        return {
            'ot_rate': 0.28,
            'ot_record': '5-3-2'
        }
    
    async def _analyze_period_performance(self, team1: str, team2: str, period: int) -> Dict:
        """Анализ производительности по периодам"""
        return {
            'goal_diff': 0.8,
            'goals_for': 1.2,
            'goals_against': 0.4
        }
    
    async def _analyze_current_momentum(self, team: str) -> Dict:
        """Анализ текущего момента"""
        return {
            'momentum_score': 45,
            'recent_points': 8,
            'recent_record': '4-1-0'
        }
