#!/usr/bin/env python3
"""
AIBET Analytics Platform - Feature Engineering
Создание признаков для ML моделей из реальных данных
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import numpy as np

from database import Match, db_manager

logger = logging.getLogger(__name__)

class FeatureEngineering:
    def __init__(self):
        self.name = "Feature Engineering"
        self.min_history_matches = 5  # Минимум матчей для истории
    
    async def extract_team_stats(self, team_name: str, sport: str) -> Dict[str, Any]:
        """Извлечение статистики команды"""
        try:
            # Получаем все матчи команды
            all_matches = await db_manager.get_matches(sport=sport, limit=200)
            
            team_matches = []
            for match in all_matches:
                if match.team1.lower() == team_name.lower() or match.team2.lower() == team_name.lower():
                    team_matches.append(match)
            
            if len(team_matches) < 3:
                return self._get_default_team_stats()
            
            # Сортируем по времени
            team_matches.sort(key=lambda x: x.start_time or datetime.min, reverse=True)
            
            # Берем последние 20 матчей
            recent_matches = team_matches[:20]
            
            # Вычисляем статистику
            wins = 0
            losses = 0
            total_goals = 0
            total_conceded = 0
            
            for match in recent_matches:
                if match.status != 'finished' or not match.score:
                    continue
                
                try:
                    # Определяем результат для команды
                    is_team1 = match.team1.lower() == team_name.lower()
                    score_parts = match.score.split(':')
                    
                    if len(score_parts) >= 2:
                        team_score = int(score_parts[0]) if is_team1 else int(score_parts[1])
                        opponent_score = int(score_parts[1]) if is_team1 else int(score_parts[0])
                        
                        total_goals += team_score
                        total_conceded += opponent_score
                        
                        if team_score > opponent_score:
                            wins += 1
                        else:
                            losses += 1
                            
                except:
                    continue
            
            total_games = wins + losses
            winrate = (wins / total_games * 100) if total_games > 0 else 0
            avg_goals = total_goals / total_games if total_games > 0 else 0
            avg_conceded = total_conceded / total_games if total_games > 0 else 0
            
            # Форма последних 5 матчей
            last_5_form = 0
            for match in recent_matches[:5]:
                if match.status != 'finished' or not match.score:
                    continue
                    
                try:
                    is_team1 = match.team1.lower() == team_name.lower()
                    score_parts = match.score.split(':')
                    
                    if len(score_parts) >= 2:
                        team_score = int(score_parts[0]) if is_team1 else int(score_parts[1])
                        opponent_score = int(score_parts[1]) if is_team1 else int(score_parts[0])
                        
                        if team_score > opponent_score:
                            last_5_form += 1
                except:
                    continue
            
            return {
                'total_games': total_games,
                'wins': wins,
                'losses': losses,
                'winrate': winrate,
                'avg_goals': avg_goals,
                'avg_conceded': avg_conceded,
                'last_5_form': last_5_form,
                'momentum': last_5_form / 5.0 if last_5_form > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error extracting stats for {team_name}: {e}")
            return self._get_default_team_stats()
    
    def _get_default_team_stats(self) -> Dict[str, Any]:
        """Статистика по умолчанию для новых команд"""
        return {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'winrate': 50.0,  # Нейтральная
            'avg_goals': 2.5,
            'avg_conceded': 2.5,
            'last_5_form': 0,
            'momentum': 0.5
        }
    
    async def get_head_to_head(self, team1: str, team2: str, sport: str) -> Dict[str, Any]:
        """Получение H2H статистики"""
        try:
            all_matches = await db_manager.get_matches(sport=sport, limit=200)
            
            h2h_matches = []
            for match in all_matches:
                if ((match.team1.lower() == team1.lower() and match.team2.lower() == team2.lower()) or
                    (match.team1.lower() == team2.lower() and match.team2.lower() == team1.lower())):
                    h2h_matches.append(match)
            
            if len(h2h_matches) < 2:
                return {'team1_wins': 0, 'team2_wins': 0, 'total_matches': 0, 'team1_advantage': 0.5}
            
            team1_wins = 0
            team2_wins = 0
            
            for match in h2h_matches:
                if match.status != 'finished' or not match.score:
                    continue
                
                try:
                    score_parts = match.score.split(':')
                    if len(score_parts) >= 2:
                        score1 = int(score_parts[0])
                        score2 = int(score_parts[1])
                        
                        # Определяем кто есть кто
                        if match.team1.lower() == team1.lower():
                            if score1 > score2:
                                team1_wins += 1
                            else:
                                team2_wins += 1
                        else:
                            if score2 > score1:
                                team1_wins += 1
                            else:
                                team2_wins += 1
                                
                except:
                    continue
            
            total_matches = team1_wins + team2_wins
            team1_advantage = team1_wins / total_matches if total_matches > 0 else 0.5
            
            return {
                'team1_wins': team1_wins,
                'team2_wins': team2_wins,
                'total_matches': total_matches,
                'team1_advantage': team1_advantage
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting H2H for {team1} vs {team2}: {e}")
            return {'team1_wins': 0, 'team2_wins': 0, 'total_matches': 0, 'team1_advantage': 0.5}
    
    async def create_match_features(self, match: Match) -> Dict[str, Any]:
        """Создание признаков для матча"""
        try:
            # Получаем статистику команд
            team1_stats = await self.extract_team_stats(match.team1, match.sport)
            team2_stats = await self.extract_team_stats(match.team2, match.sport)
            
            # Получаем H2H
            h2h = await self.get_head_to_head(match.team1, match.team2, match.sport)
            
            # Базовые признаки из матча
            base_features = match.features or {}
            
            # Создаем вектор признаков
            features = {
                # Базовая информация
                'sport': match.sport,
                'tournament': base_features.get('tournament', 'Unknown'),
                'importance': base_features.get('importance', 5),
                
                # Статистика команд
                'team1_total_games': team1_stats['total_games'],
                'team1_winrate': team1_stats['winrate'],
                'team1_avg_goals': team1_stats['avg_goals'],
                'team1_avg_conceded': team1_stats['avg_conceded'],
                'team1_last_5_form': team1_stats['last_5_form'],
                'team1_momentum': team1_stats['momentum'],
                
                'team2_total_games': team2_stats['total_games'],
                'team2_winrate': team2_stats['winrate'],
                'team2_avg_goals': team2_stats['avg_goals'],
                'team2_avg_conceded': team2_stats['avg_conceded'],
                'team2_last_5_form': team2_stats['last_5_form'],
                'team2_momentum': team2_stats['momentum'],
                
                # H2H статистика
                'h2h_total_matches': h2h['total_matches'],
                'h2h_team1_wins': h2h['team1_wins'],
                'h2h_team2_wins': h2h['team2_wins'],
                'h2h_team1_advantage': h2h['team1_advantage'],
                
                # Разницы и отношения
                'winrate_diff': team1_stats['winrate'] - team2_stats['winrate'],
                'goals_diff': team1_stats['avg_goals'] - team2_stats['avg_goals'],
                'conceded_diff': team1_stats['avg_conceded'] - team2_stats['avg_conceded'],
                'form_diff': team1_stats['last_5_form'] - team2_stats['last_5_form'],
                'momentum_diff': team1_stats['momentum'] - team2_stats['momentum'],
                
                # Временные признаки
                'hours_until_match': 0,
                'is_weekend': 0,
                'is_prime_time': 0
            }
            
            # Добавляем временные признаки
            if match.start_time:
                now = datetime.utcnow()
                time_diff = match.start_time - now
                features['hours_until_match'] = max(0, time_diff.total_seconds() / 3600)
                features['is_weekend'] = 1 if match.start_time.weekday() >= 5 else 0
                features['is_prime_time'] = 1 if 18 <= match.start_time.hour <= 22 else 0
            
            # Спортивно-специфичные признаки
            if match.sport == 'cs2':
                features.update(self._get_cs2_features(base_features))
            elif match.sport == 'khl':
                features.update(self._get_khl_features(base_features))
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Error creating features for {match.team1} vs {match.team2}: {e}")
            return self._get_default_features(match)
    
    def _get_cs2_features(self, base_features: Dict) -> Dict[str, Any]:
        """CS2 специфичные признаки"""
        return {
            'format_bo3': 1 if base_features.get('format', '').upper() == 'BO3' else 0,
            'format_bo5': 1 if base_features.get('format', '').upper() == 'BO5' else 0,
            'is_lan': 1 if 'lan' in base_features.get('tournament', '').lower() else 0,
            'is_major': 1 if 'major' in base_features.get('tournament', '').lower() else 0
        }
    
    def _get_khl_features(self, base_features: Dict) -> Dict[str, Any]:
        """КХЛ специфичные признаки"""
        return {
            'is_playoffs': 1 if 'плей-офф' in base_features.get('tournament', '').lower() else 0,
            'is_home_advantage': 0.5,  # Будет обновлено при анализе
            'overtime_probability': 0.3
        }
    
    def _get_default_features(self, match: Match) -> Dict[str, Any]:
        """Признаки по умолчанию"""
        return {
            'sport': match.sport,
            'tournament': 'Unknown',
            'importance': 5,
            'team1_winrate': 50.0,
            'team2_winrate': 50.0,
            'winrate_diff': 0.0,
            'h2h_team1_advantage': 0.5,
            'hours_until_match': 2.0,
            'is_weekend': 0,
            'is_prime_time': 0
        }
    
    async def update_all_matches_features(self):
        """Обновление признаков для всех матчей"""
        try:
            logger.info("🔧 Updating features for all matches")
            
            # Получаем все матчи
            matches = await db_manager.get_matches(limit=500)
            
            updated_count = 0
            for match in matches:
                try:
                    # Создаем признаки
                    features = await self.create_match_features(match)
                    
                    # Обновляем матч в базе данных
                    await db_manager.update_match_features(match.id, features)
                    updated_count += 1
                    
                    if updated_count % 50 == 0:
                        logger.info(f"🔧 Updated features for {updated_count} matches")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error updating features for match {match.id}: {e}")
                    continue
            
            logger.info(f"✅ Updated features for {updated_count} matches")
            return updated_count
            
        except Exception as e:
            logger.error(f"❌ Error updating match features: {e}")
            return 0
    
    def get_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """Получение вектора признаков для ML"""
        try:
            # Основные признаки для ML
            feature_columns = [
                'importance',
                'team1_winrate', 'team2_winrate',
                'team1_avg_goals', 'team2_avg_goals',
                'team1_avg_conceded', 'team2_avg_conceded',
                'team1_last_5_form', 'team2_last_5_form',
                'team1_momentum', 'team2_momentum',
                'h2h_team1_advantage',
                'winrate_diff', 'goals_diff', 'form_diff', 'momentum_diff',
                'hours_until_match', 'is_weekend', 'is_prime_time'
            ]
            
            vector = []
            for col in feature_columns:
                value = features.get(col, 0)
                if isinstance(value, bool):
                    value = 1 if value else 0
                elif value is None:
                    value = 0
                vector.append(float(value))
            
            return np.array(vector)
            
        except Exception as e:
            logger.error(f"❌ Error creating feature vector: {e}")
            return np.zeros(18)  # Возвращаем нулевой вектор

# Глобальный экземпляр
feature_engineering = FeatureEngineering()
