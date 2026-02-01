"""
AIBET MVP Feature Engineering
Extract features from historical data for ML models
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Feature engineering for ML models"""
    
    def __init__(self, db: Session):
        self.db = db
        self.recent_matches = 10  # Last N matches for form
        self.h2h_limit = 5  # Last N head-to-head matches
        
    def extract_features(self, match_id: int) -> Dict[str, Any]:
        """Extract all features for a given match"""
        try:
            from database.models import Match, Team, TeamStats
            
            # Get match
            match = self.db.query(Match).filter(Match.id == match_id).first()
            if not match:
                return {}
            
            # Get teams
            team1 = self.db.query(Team).filter(Team.id == match.team1_id).first()
            team2 = self.db.query(Team).filter(Team.id == match.team2_id).first()
            
            if not team1 or not team2:
                return {}
            
            # Extract different feature groups
            features = {}
            
            # Basic features
            features.update(self._extract_basic_features(team1, team2, match))
            
            # Form features
            features.update(self._extract_form_features(team1, team2, match))
            
            # Head-to-head features
            features.update(self._extract_h2h_features(team1, team2, match))
            
            # Sport-specific features
            if match.sport == "cs2":
                features.update(self._extract_cs2_features(team1, team2, match))
            elif match.sport == "khl":
                features.update(self._extract_khl_features(team1, team2, match))
            
            # Advanced features
            features.update(self._extract_advanced_features(team1, team2, match))
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features for match {match_id}: {e}")
            return {}
    
    def _extract_basic_features(self, team1, team2, match) -> Dict[str, Any]:
        """Extract basic team features"""
        features = {}
        
        # Rating difference
        rating_diff = team1.rating - team2.rating
        features['team1_rating'] = team1.rating
        features['team2_rating'] = team2.rating
        features['rating_difference'] = rating_diff
        
        # Rating ratio
        features['rating_ratio'] = team1.rating / (team2.rating + 1)
        
        # Home advantage (simplified)
        if match.arena and 'home' in match.arena.lower():
            features['team1_is_home'] = 1
        else:
            features['team1_is_home'] = 0
            
        if match.arena and 'away' in match.arena.lower():
            features['team2_is_home'] = 1
        else:
            features['team2_is_home'] = 0
        
        return features
    
    def _extract_form_features(self, team1, team2, match) -> Dict[str, Any]:
        """Extract recent form features"""
        features = {}
        
        # Get recent matches for both teams
        team1_form = self._get_recent_form(team1.id, match.sport)
        team2_form = self._get_recent_form(team2.id, match.sport)
        
        # Team 1 form
        features['team1_recent_wins'] = team1_form.count('W')
        features['team1_recent_losses'] = team1_form.count('L')
        features['team1_recent_draws'] = team1_form.count('D')
        features['team1_recent_winrate'] = team1_form.count('W') / len(team1_form) if team1_form else 0
        
        # Team 2 form
        features['team2_recent_wins'] = team2_form.count('W')
        features['team2_recent_losses'] = team2_form.count('L')
        features['team2_recent_draws'] = team2_form.count('D')
        features['team2_recent_winrate'] = team2_form.count('W') / len(team2_form) if team2_form else 0
        
        # Form differences
        features['recent_wins_diff'] = features['team1_recent_wins'] - features['team2_recent_wins']
        features['recent_winrate_diff'] = features['team1_recent_winrate'] - features['team2_recent_winrate']
        
        return features
    
    def _extract_h2h_features(self, team1, team2, match) -> Dict[str, Any]:
        """Extract head-to-head features"""
        features = {}
        
        # Get H2H matches
        h2h_matches = self._get_h2h_matches(team1.id, team2.id, match.sport)
        
        if h2h_matches:
            team1_wins = sum(1 for m in h2h_matches if m.result == 'team1')
            team2_wins = sum(1 for m in h2h_matches if m.result == 'team2')
            draws = sum(1 for m in h2h_matches if m.result == 'draw')
            
            features['h2h_matches_played'] = len(h2h_matches)
            features['h2h_team1_wins'] = team1_wins
            features['h2h_team2_wins'] = team2_wins
            features['h2h_draws'] = draws
            features['h2h_team1_winrate'] = team1_wins / len(h2h_matches)
            features['h2h_team2_winrate'] = team2_wins / len(h2h_matches)
        else:
            # Default values if no H2H history
            features.update({
                'h2h_matches_played': 0,
                'h2h_team1_wins': 0,
                'h2h_team2_wins': 0,
                'h2h_draws': 0,
                'h2h_team1_winrate': 0.5,
                'h2h_team2_winrate': 0.5
            })
        
        return features
    
    def _extract_cs2_features(self, team1, team2, match) -> Dict[str, Any]:
        """Extract CS2-specific features"""
        features = {}
        
        # Map winrates (if available)
        team1_stats = self._get_team_stats(team1.id, 'cs2')
        team2_stats = self._get_team_stats(team2.id, 'cs2')
        
        if team1_stats and team2_stats:
            # Map-specific winrates
            map_name = match.map_name.lower() if match.map_name else ''
            
            team1_map_wr = team1_stats.cs2_map_winrate or {}
            team2_map_wr = team2_stats.cs2_map_winrate or {}
            
            features['team1_map_winrate'] = team1_map_wr.get(map_name, 0.5)
            features['team2_map_winrate'] = team2_map_wr.get(map_name, 0.5)
            features['map_winrate_diff'] = features['team1_map_winrate'] - features['team2_map_winrate']
            
            # Average scores
            features['team1_avg_score_for'] = team1_stats.avg_score_for
            features['team2_avg_score_for'] = team2_stats.avg_score_for
            features['team1_avg_score_against'] = team1_stats.avg_score_against
            features['team2_avg_score_against'] = team2_stats.avg_score_against
            
            # Score differentials
            features['avg_score_diff'] = (team1_stats.avg_score_for - team2_stats.avg_score_for)
            features['avg_defense_diff'] = (team2_stats.avg_score_against - team1_stats.avg_score_against)
        else:
            # Default values
            features.update({
                'team1_map_winrate': 0.5,
                'team2_map_winrate': 0.5,
                'map_winrate_diff': 0.0,
                'team1_avg_score_for': 16.0,
                'team2_avg_score_for': 16.0,
                'team1_avg_score_against': 16.0,
                'team2_avg_score_against': 16.0,
                'avg_score_diff': 0.0,
                'avg_defense_diff': 0.0
            })
        
        # Best of series
        features['best_of'] = match.best_of or 1
        features['is_bo3'] = 1 if match.best_of == 3 else 0
        features['is_bo5'] = 1 if match.best_of == 5 else 0
        
        return features
    
    def _extract_khl_features(self, team1, team2, match) -> Dict[str, Any]:
        """Extract KHL-specific features"""
        features = {}
        
        # Home/away performance
        team1_stats = self._get_team_stats(team1.id, 'khl')
        team2_stats = self._get_team_stats(team2.id, 'khl')
        
        if team1_stats and team2_stats:
            home_away = team1_stats.khl_home_away or {}
            home_away2 = team2_stats.khl_home_away or {}
            
            # Home advantage for team1
            team1_home = home_away.get('home', {})
            team1_away = home_away.get('away', {})
            team2_home = home_away2.get('home', {})
            team2_away = home_away2.get('away', {})
            
            # Assume team1 is home, team2 is away (simplified)
            features['team1_home_winrate'] = team1_home.get('wins', 0) / max(team1_home.get('wins', 0) + team1_home.get('losses', 0), 1)
            features['team2_away_winrate'] = team2_away.get('wins', 0) / max(team2_away.get('wins', 0) + team2_away.get('losses', 0), 1)
            
            # Average goals
            features['team1_avg_goals_for'] = team1_stats.avg_score_for
            features['team2_avg_goals_for'] = team2_stats.avg_score_for
            features['team1_avg_goals_against'] = team1_stats.avg_score_against
            features['team2_avg_goals_against'] = team2_stats.avg_score_against
            
            # Goal differentials
            features['avg_goals_diff'] = (team1_stats.avg_score_for - team2_stats.avg_score_for)
            features['avg_defense_diff'] = (team2_stats.avg_score_against - team1_stats.avg_score_against)
        else:
            # Default values
            features.update({
                'team1_home_winrate': 0.6,  # Home advantage
                'team2_away_winrate': 0.4,
                'team1_avg_goals_for': 3.0,
                'team2_avg_goals_for': 2.5,
                'team1_avg_goals_against': 2.0,
                'team2_avg_goals_against': 2.5,
                'avg_goals_diff': 0.5,
                'avg_defense_diff': 0.5
            })
        
        return features
    
    def _extract_advanced_features(self, team1, team2, match) -> Dict[str, Any]:
        """Extract advanced statistical features"""
        features = {}
        
        # Get team stats
        team1_stats = self._get_team_stats(team1.id, match.sport)
        team2_stats = self._get_team_stats(team2.id, match.sport)
        
        if team1_stats and team2_stats:
            # Overall winrates
            features['team1_overall_winrate'] = team1_stats.win_rate
            features['team2_overall_winrate'] = team2_stats.win_rate
            features['overall_winrate_diff'] = team1_stats.win_rate - team2_stats.win_rate
            
            # Experience (matches played)
            features['team1_experience'] = team1_stats.matches_played
            features['team2_experience'] = team2_stats.matches_played
            features['experience_diff'] = team1_stats.matches_played - team2_stats.matches_played
            
            # Win/loss ratios
            team1_wl_ratio = team1_stats.wins / max(team1_stats.losses, 1)
            team2_wl_ratio = team2_stats.wins / max(team2_stats.losses, 1)
            features['team1_wl_ratio'] = team1_wl_ratio
            features['team2_wl_ratio'] = team2_wl_ratio
            features['wl_ratio_diff'] = team1_wl_ratio - team2_wl_ratio
        else:
            # Default values
            features.update({
                'team1_overall_winrate': 0.5,
                'team2_overall_winrate': 0.5,
                'overall_winrate_diff': 0.0,
                'team1_experience': 50,
                'team2_experience': 50,
                'experience_diff': 0.0,
                'team1_wl_ratio': 1.0,
                'team2_wl_ratio': 1.0,
                'wl_ratio_diff': 0.0
            })
        
        # Time-based features
        if match.date:
            days_since_last_match1 = self._get_days_since_last_match(team1.id, match.date, match.sport)
            days_since_last_match2 = self._get_days_since_last_match(team2.id, match.date, match.sport)
            
            features['team1_days_rest'] = days_since_last_match1
            features['team2_days_rest'] = days_since_last_match2
            features['rest_diff'] = days_since_last_match1 - days_since_last_match2
        else:
            features.update({
                'team1_days_rest': 7,
                'team2_days_rest': 7,
                'rest_diff': 0
            })
        
        return features
    
    def _get_recent_form(self, team_id: int, sport: str) -> List[str]:
        """Get recent match results for a team"""
        try:
            from database.models import Match
            
            matches = self.db.query(Match).filter(
                Match.team1_id == team_id,
                Match.sport == sport,
                Match.result != 'upcoming',
                Match.date < datetime.now()
            ).order_by(Match.date.desc()).limit(self.recent_matches).all()
            
            form = []
            for match in matches:
                if match.result == 'team1':
                    form.append('W')
                elif match.result == 'draw':
                    form.append('D')
                else:
                    form.append('L')
            
            return form[:self.recent_matches]
            
        except Exception as e:
            logger.error(f"Error getting recent form for team {team_id}: {e}")
            return ['W', 'L', 'W', 'D', 'W']  # Default form
    
    def _get_h2h_matches(self, team1_id: int, team2_id: int, sport: str) -> List:
        """Get head-to-head matches between two teams"""
        try:
            from database.models import Match
            
            matches = self.db.query(Match).filter(
                ((Match.team1_id == team1_id) & (Match.team2_id == team2_id)) |
                ((Match.team1_id == team2_id) & (Match.team2_id == team1_id)),
                Match.sport == sport,
                Match.result != 'upcoming'
            ).order_by(Match.date.desc()).limit(self.h2h_limit).all()
            
            return matches
            
        except Exception as e:
            logger.error(f"Error getting H2H matches: {e}")
            return []
    
    def _get_team_stats(self, team_id: int, sport: str):
        """Get team statistics"""
        try:
            from database.models import TeamStats
            
            return self.db.query(TeamStats).filter(
                TeamStats.team_id == team_id,
                TeamStats.sport == sport
            ).first()
            
        except Exception as e:
            logger.error(f"Error getting team stats for team {team_id}: {e}")
            return None
    
    def _get_days_since_last_match(self, team_id: int, current_date: datetime, sport: str) -> int:
        """Get days since last match for a team"""
        try:
            from database.models import Match
            
            last_match = self.db.query(Match).filter(
                ((Match.team1_id == team_id) | (Match.team2_id == team_id)),
                Match.sport == sport,
                Match.date < current_date,
                Match.result != 'upcoming'
            ).order_by(Match.date.desc()).first()
            
            if last_match:
                return (current_date - last_match.date).days
            else:
                return 7  # Default rest days
                
        except Exception as e:
            logger.error(f"Error getting days since last match: {e}")
            return 7
