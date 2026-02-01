#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real Feature Engineering
Feature engineering for last 100 matches statistics
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict, deque
import sqlite3
import json

from database import Match, db_manager

logger = logging.getLogger(__name__)

# Global instance
feature_engineering = RealFeatureEngineering()

@dataclass
class TeamFeatures:
    """Team features for ML models"""
    team_name: str
    sport: str
    
    # Basic statistics (last 100 matches)
    win_rate: float = 0.0
    avg_score: float = 0.0
    avg_conceded: float = 0.0
    form_trend: float = 0.0  # Last 10 matches trend
    
    # Home/Away performance
    home_win_rate: float = 0.0
    away_win_rate: float = 0.0
    
    # Recent form (last 10 matches)
    recent_wins: int = 0
    recent_draws: int = 0
    recent_losses: int = 0
    recent_goals_scored: float = 0.0
    recent_goals_conceded: float = 0.0
    
    # Head-to-head statistics
    h2h_win_rate: float = 0.0
    h2h_avg_goals: float = 0.0
    
    # Consistency metrics
    win_streak_max: int = 0
    loss_streak_max: int = 0
    consistency_score: float = 0.0  # Variance in performance
    
    # Advanced metrics
    strength_of_schedule: float = 0.0
    momentum_score: float = 0.0
    fatigue_factor: float = 0.0
    
    # Odds-related features
    avg_odds_won: float = 0.0
    upset_rate: float = 0.0
    
    # Metadata
    total_matches: int = 0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

class RealFeatureEngineering:
    def __init__(self):
        self.name = "Real Feature Engineering"
        self.min_matches = 10  # Minimum matches for reliable stats
        self.max_matches = 100  # Maximum matches to consider
        self.recent_matches = 10  # Recent matches for form
        
        # Cache for team features
        self.team_cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        
    async def extract_features_for_match(self, match: Match) -> Tuple[TeamFeatures, TeamFeatures]:
        """Extract features for both teams in a match"""
        team1_features = await self.get_team_features(match.team1, match.sport)
        team2_features = await self.get_team_features(match.team2, match.sport)
        
        # Add head-to-head features
        await self._add_h2h_features(team1_features, team2_features, match.sport)
        
        return team1_features, team2_features
    
    async def get_team_features(self, team_name: str, sport: str) -> TeamFeatures:
        """Get or compute team features"""
        cache_key = f"{team_name}_{sport}"
        
        # Check cache
        if cache_key in self.team_cache:
            cached_features, timestamp = self.team_cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl:
                return cached_features
        
        # Compute features
        features = await self._compute_team_features(team_name, sport)
        
        # Cache result
        self.team_cache[cache_key] = (features, datetime.now())
        
        return features
    
    async def _compute_team_features(self, team_name: str, sport: str) -> TeamFeatures:
        """Compute comprehensive team features"""
        logger.info(f"🔧 Computing features for {team_name} ({sport})")
        
        try:
            # Get match history
            matches = await self._get_team_match_history(team_name, sport)
            
            if len(matches) < self.min_matches:
                logger.warning(f"⚠️ Insufficient matches for {team_name}: {len(matches)}")
                return self._create_default_features(team_name, sport)
            
            features = TeamFeatures(team_name=team_name, sport=sport, total_matches=len(matches))
            
            # Basic statistics
            features = await self._compute_basic_stats(features, matches)
            
            # Home/Away performance
            features = await self._compute_home_away_stats(features, matches)
            
            # Recent form
            features = await self._compute_recent_form(features, matches)
            
            # Consistency metrics
            features = await self._compute_consistency_metrics(features, matches)
            
            # Advanced metrics
            features = await self._compute_advanced_metrics(features, matches)
            
            # Odds-related features
            features = await self._compute_odds_features(features, matches)
            
            logger.info(f"✅ Computed features for {team_name}")
            return features
            
        except Exception as e:
            logger.error(f"❌ Error computing features for {team_name}: {e}")
            return self._create_default_features(team_name, sport)
    
    async def _get_team_match_history(self, team_name: str, sport: str) -> List[Match]:
        """Get team match history (last 100 matches)"""
        try:
            # Get matches where team is involved
            all_matches = await db_manager.get_matches(
                sport=sport, 
                limit=self.max_matches * 2  # Get more to filter
            )
            
            team_matches = []
            for match in all_matches:
                if match.team1 == team_name or match.team2 == team_name:
                    team_matches.append(match)
            
            # Sort by date (most recent first) and limit
            team_matches.sort(key=lambda x: x.start_time or datetime.min, reverse=True)
            return team_matches[:self.max_matches]
            
        except Exception as e:
            logger.error(f"Error getting match history for {team_name}: {e}")
            return []
    
    async def _compute_basic_stats(self, features: TeamFeatures, matches: List[Match]) -> TeamFeatures:
        """Compute basic win/loss statistics"""
        wins = 0
        total_goals_scored = 0
        total_goals_conceded = 0
        
        for match in matches:
            is_team1 = match.team1 == features.team_name
            opponent_score = 0
            team_score = 0
            
            # Parse score
            if match.score and match.score != '':
                try:
                    if '-' in match.score:
                        scores = match.score.split('-')
                        if is_team1:
                            team_score = int(scores[0].strip())
                            opponent_score = int(scores[1].strip())
                        else:
                            team_score = int(scores[1].strip())
                            opponent_score = int(scores[0].strip())
                except:
                    pass
            
            # Determine win/loss
            if match.status == 'finished':
                if team_score > opponent_score:
                    wins += 1
                
                total_goals_scored += team_score
                total_goals_conceded += opponent_score
        
        features.win_rate = wins / len(matches) if matches else 0.0
        features.avg_score = total_goals_scored / len(matches) if matches else 0.0
        features.avg_conceded = total_goals_conceded / len(matches) if matches else 0.0
        
        return features
    
    async def _compute_home_away_stats(self, features: TeamFeatures, matches: List[Match]) -> TeamFeatures:
        """Compute home/away performance"""
        home_wins = 0
        home_matches = 0
        away_wins = 0
        away_matches = 0
        
        for match in matches:
            is_team1 = match.team1 == features.team_name
            is_home = is_team1  # Assume team1 is home
            
            if match.status == 'finished':
                team_score = 0
                opponent_score = 0
                
                if match.score and match.score != '':
                    try:
                        if '-' in match.score:
                            scores = match.score.split('-')
                            if is_team1:
                                team_score = int(scores[0].strip())
                                opponent_score = int(scores[1].strip())
                            else:
                                team_score = int(scores[1].strip())
                                opponent_score = int(scores[0].strip())
                    except:
                        pass
                
                if is_home:
                    home_matches += 1
                    if team_score > opponent_score:
                        home_wins += 1
                else:
                    away_matches += 1
                    if team_score > opponent_score:
                        away_wins += 1
        
        features.home_win_rate = home_wins / home_matches if home_matches else 0.0
        features.away_win_rate = away_wins / away_matches if away_matches else 0.0
        
        return features
    
    async def _compute_recent_form(self, features: TeamFeatures, matches: List[Match]) -> TeamFeatures:
        """Compute recent form (last 10 matches)"""
        recent_matches = matches[:self.recent_matches]
        
        recent_wins = 0
        recent_draws = 0
        recent_losses = 0
        recent_goals_scored = 0
        recent_goals_conceded = 0
        
        for match in recent_matches:
            is_team1 = match.team1 == features.team_name
            team_score = 0
            opponent_score = 0
            
            if match.score and match.score != '':
                try:
                    if '-' in match.score:
                        scores = match.score.split('-')
                        if is_team1:
                            team_score = int(scores[0].strip())
                            opponent_score = int(scores[1].strip())
                        else:
                            team_score = int(scores[1].strip())
                            opponent_score = int(scores[0].strip())
                except:
                    pass
            
            if match.status == 'finished':
                if team_score > opponent_score:
                    recent_wins += 1
                elif team_score == opponent_score:
                    recent_draws += 1
                else:
                    recent_losses += 1
                
                recent_goals_scored += team_score
                recent_goals_conceded += opponent_score
        
        features.recent_wins = recent_wins
        features.recent_draws = recent_draws
        features.recent_losses = recent_losses
        features.recent_goals_scored = recent_goals_scored / len(recent_matches) if recent_matches else 0.0
        features.recent_goals_conceded = recent_goals_conceded / len(recent_matches) if recent_matches else 0.0
        
        # Form trend (improving or declining)
        if len(recent_matches) >= 5:
            early_matches = recent_matches[5:]
            late_matches = recent_matches[:5]
            
            early_points = await self._calculate_points(features.team_name, early_matches)
            late_points = await self._calculate_points(features.team_name, late_matches)
            
            features.form_trend = (late_points - early_points) / 5.0
        
        return features
    
    async def _calculate_points(self, team_name: str, matches: List[Match]) -> float:
        """Calculate points from matches"""
        points = 0
        for match in matches:
            is_team1 = match.team1 == team_name
            team_score = 0
            opponent_score = 0
            
            if match.score and match.score != '':
                try:
                    if '-' in match.score:
                        scores = match.score.split('-')
                        if is_team1:
                            team_score = int(scores[0].strip())
                            opponent_score = int(scores[1].strip())
                        else:
                            team_score = int(scores[1].strip())
                            opponent_score = int(scores[0].strip())
                except:
                    pass
            
            if match.status == 'finished':
                if team_score > opponent_score:
                    points += 3  # Win
                elif team_score == opponent_score:
                    points += 1  # Draw
        
        return points
    
    async def _compute_consistency_metrics(self, features: TeamFeatures, matches: List[Match]) -> TeamFeatures:
        """Compute consistency and streak metrics"""
        current_win_streak = 0
        current_loss_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        
        results = []  # 1 for win, 0 for draw, -1 for loss
        
        for match in matches:
            is_team1 = match.team1 == features.team_name
            team_score = 0
            opponent_score = 0
            
            if match.score and match.score != '':
                try:
                    if '-' in match.score:
                        scores = match.score.split('-')
                        if is_team1:
                            team_score = int(scores[0].strip())
                            opponent_score = int(scores[1].strip())
                        else:
                            team_score = int(scores[1].strip())
                            opponent_score = int(scores[0].strip())
                except:
                    pass
            
            if match.status == 'finished':
                if team_score > opponent_score:
                    results.append(1)
                    current_win_streak += 1
                    current_loss_streak = 0
                    max_win_streak = max(max_win_streak, current_win_streak)
                elif team_score == opponent_score:
                    results.append(0)
                    current_win_streak = 0
                    current_loss_streak = 0
                else:
                    results.append(-1)
                    current_loss_streak += 1
                    current_win_streak = 0
                    max_loss_streak = max(max_loss_streak, current_loss_streak)
        
        features.win_streak_max = max_win_streak
        features.loss_streak_max = max_loss_streak
        
        # Consistency score (inverse of variance)
        if results:
            variance = np.var(results)
            features.consistency_score = 1.0 / (1.0 + variance)
        
        return features
    
    async def _compute_advanced_metrics(self, features: TeamFeatures, matches: List[Match]) -> TeamFeatures:
        """Compute advanced metrics like strength of schedule, momentum"""
        # Strength of schedule (average opponent win rate)
        opponent_win_rates = []
        
        for match in matches:
            opponent = match.team2 if match.team1 == features.team_name else match.team1
            opponent_features = await self.get_team_features(opponent, features.sport)
            opponent_win_rates.append(opponent_features.win_rate)
        
        if opponent_win_rates:
            features.strength_of_schedule = np.mean(opponent_win_rates)
        
        # Momentum score (weighted recent performance)
        recent_matches = matches[:10]
        momentum_score = 0
        weights = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
        
        for i, match in enumerate(recent_matches):
            if i < len(weights):
                is_team1 = match.team1 == features.team_name
                team_score = 0
                opponent_score = 0
                
                if match.score and match.score != '':
                    try:
                        if '-' in match.score:
                            scores = match.score.split('-')
                            if is_team1:
                                team_score = int(scores[0].strip())
                                opponent_score = int(scores[1].strip())
                            else:
                                team_score = int(scores[1].strip())
                                opponent_score = int(scores[0].strip())
                    except:
                        pass
                
                if match.status == 'finished':
                    if team_score > opponent_score:
                        momentum_score += weights[i] * 3
                    elif team_score == opponent_score:
                        momentum_score += weights[i] * 1
        
        features.momentum_score = momentum_score
        
        # Fatigue factor (matches in last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_matches_count = sum(1 for match in matches 
                                if match.start_time and match.start_time > seven_days_ago)
        features.fatigue_factor = recent_matches_count / 7.0  # Matches per day
        
        return features
    
    async def _compute_odds_features(self, features: TeamFeatures, matches: List[Match]) -> TeamFeatures:
        """Compute odds-related features"""
        odds_won = []
        upsets = 0
        total_odds_matches = 0
        
        for match in matches:
            # Check if odds data is available
            if hasattr(match, 'features') and match.features:
                odds1 = match.features.get('odds1')
                odds2 = match.features.get('odds2')
                
                if odds1 and odds2:
                    total_odds_matches += 1
                    is_team1 = match.team1 == features.team_name
                    team_odds = odds1 if is_team1 else odds2
                    
                    # Determine if team won
                    team_score = 0
                    opponent_score = 0
                    
                    if match.score and match.score != '':
                        try:
                            if '-' in match.score:
                                scores = match.score.split('-')
                                if is_team1:
                                    team_score = int(scores[0].strip())
                                    opponent_score = int(scores[1].strip())
                                else:
                                    team_score = int(scores[1].strip())
                                    opponent_score = int(scores[0].strip())
                        except:
                            pass
                    
                    if match.status == 'finished':
                        if team_score > opponent_score:
                            odds_won.append(team_odds)
                            
                            # Check if it was an upset (underdog won)
                            if team_odds > 2.0:  # Underdog threshold
                                upsets += 1
        
        if odds_won:
            features.avg_odds_won = np.mean(odds_won)
        
        if total_odds_matches > 0:
            features.upset_rate = upsets / total_odds_matches
        
        return features
    
    async def _add_h2h_features(self, team1_features: TeamFeatures, team2_features: TeamFeatures, sport: str):
        """Add head-to-head features between two teams"""
        try:
            # Get head-to-head matches
            h2h_matches = await self._get_h2h_matches(team1_features.team_name, team2_features.team_name, sport)
            
            if len(h2h_matches) < 2:
                return
            
            team1_wins = 0
            total_goals_team1 = 0
            total_goals_team2 = 0
            
            for match in h2h_matches:
                is_team1_home = match.team1 == team1_features.team_name
                team1_score = 0
                team2_score = 0
                
                if match.score and match.score != '':
                    try:
                        if '-' in match.score:
                            scores = match.score.split('-')
                            if is_team1_home:
                                team1_score = int(scores[0].strip())
                                team2_score = int(scores[1].strip())
                            else:
                                team1_score = int(scores[1].strip())
                                team2_score = int(scores[0].strip())
                    except:
                        pass
                
                if match.status == 'finished':
                    if team1_score > team2_score:
                        team1_wins += 1
                    
                    total_goals_team1 += team1_score
                    total_goals_team2 += team2_score
            
            team1_features.h2h_win_rate = team1_wins / len(h2h_matches) if h2h_matches else 0.0
            team2_features.h2h_win_rate = (len(h2h_matches) - team1_wins) / len(h2h_matches) if h2h_matches else 0.0
            
            avg_goals = (total_goals_team1 + total_goals_team2) / (2 * len(h2h_matches)) if h2h_matches else 0.0
            team1_features.h2h_avg_goals = avg_goals
            team2_features.h2h_avg_goals = avg_goals
            
        except Exception as e:
            logger.error(f"Error adding H2H features: {e}")
    
    async def _get_h2h_matches(self, team1: str, team2: str, sport: str) -> List[Match]:
        """Get head-to-head matches between two teams"""
        try:
            all_matches = await db_manager.get_matches(sport=sport, limit=200)
            
            h2h_matches = []
            for match in all_matches:
                if (match.team1 == team1 and match.team2 == team2) or \
                   (match.team1 == team2 and match.team2 == team1):
                    h2h_matches.append(match)
            
            # Sort by date (most recent first)
            h2h_matches.sort(key=lambda x: x.start_time or datetime.min, reverse=True)
            return h2h_matches[:20]  # Last 20 H2H matches
            
        except Exception as e:
            logger.error(f"Error getting H2H matches: {e}")
            return []
    
    def _create_default_features(self, team_name: str, sport: str) -> TeamFeatures:
        """Create default features for teams with insufficient data"""
        return TeamFeatures(
            team_name=team_name,
            sport=sport,
            win_rate=0.5,
            avg_score=0.0,
            avg_conceded=0.0,
            form_trend=0.0,
            home_win_rate=0.5,
            away_win_rate=0.5,
            recent_wins=0,
            recent_draws=0,
            recent_losses=0,
            recent_goals_scored=0.0,
            recent_goals_conceded=0.0,
            h2h_win_rate=0.5,
            h2h_avg_goals=0.0,
            win_streak_max=0,
            loss_streak_max=0,
            consistency_score=0.0,
            strength_of_schedule=0.5,
            momentum_score=0.0,
            fatigue_factor=0.0,
            avg_odds_won=0.0,
            upset_rate=0.0,
            total_matches=0,
            last_updated=datetime.now()
        )
    
    def features_to_dict(self, features: TeamFeatures) -> Dict[str, Any]:
        """Convert features to dictionary for ML models"""
        return {
            'win_rate': features.win_rate,
            'avg_score': features.avg_score,
            'avg_conceded': features.avg_conceded,
            'form_trend': features.form_trend,
            'home_win_rate': features.home_win_rate,
            'away_win_rate': features.away_win_rate,
            'recent_wins': features.recent_wins,
            'recent_draws': features.recent_draws,
            'recent_losses': features.recent_losses,
            'recent_goals_scored': features.recent_goals_scored,
            'recent_goals_conceded': features.recent_goals_conceded,
            'h2h_win_rate': features.h2h_win_rate,
            'h2h_avg_goals': features.h2h_avg_goals,
            'win_streak_max': features.win_streak_max,
            'loss_streak_max': features.loss_streak_max,
            'consistency_score': features.consistency_score,
            'strength_of_schedule': features.strength_of_schedule,
            'momentum_score': features.momentum_score,
            'fatigue_factor': features.fatigue_factor,
            'avg_odds_won': features.avg_odds_won,
            'upset_rate': features.upset_rate,
            'total_matches': features.total_matches
        }
    
    async def get_training_data(self, sport: str, limit: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """Get training data for ML models"""
        try:
            matches = await db_manager.get_matches(sport=sport, limit=limit)
            
            X = []
            y = []
            
            for match in matches:
                if match.status == 'finished' and match.score:
                    # Get features for both teams
                    team1_features, team2_features = await self.extract_features_for_match(match)
                    
                    # Combine features
                    team1_dict = self.features_to_dict(team1_features)
                    team2_dict = self.features_to_dict(team2_features)
                    
                    # Create feature vector
                    feature_vector = []
                    for key in team1_dict.keys():
                        feature_vector.append(team1_dict[key])
                        feature_vector.append(team2_dict[key])
                    
                    # Determine target (1 if team1 won, 0 otherwise)
                    is_team1_win = 0
                    if match.score and '-' in match.score:
                        try:
                            scores = match.score.split('-')
                            team1_score = int(scores[0].strip())
                            team2_score = int(scores[1].strip())
                            is_team1_win = 1 if team1_score > team2_score else 0
                        except:
                            pass
                    
                    X.append(feature_vector)
                    y.append(is_team1_win)
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return np.array([]), np.array([])

# Global instance
feature_engineering = RealFeatureEngineering()
