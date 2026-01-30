import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FilterCriteria:
    min_odds: float = 1.10
    max_odds: float = 5.00
    min_public_bias: float = 0.0
    max_public_bias: float = 100.0
    required_tiers: Set[str] = None
    exclude_stand_ins: bool = False
    min_market_efficiency: float = 0.3


class CS2MatchFilter:
    """Filter CS2 matches based on various criteria"""
    
    def __init__(self):
        self.default_criteria = FilterCriteria()
        self.excluded_tournaments = {
            'showmatch', 'fun cup', 'charity', 'exhibition'
        }
    
    def filter_matches(self, matches: List[Dict[str, Any]], 
                       criteria: Optional[FilterCriteria] = None) -> List[Dict[str, Any]]:
        """Filter matches based on criteria"""
        if criteria is None:
            criteria = self.default_criteria
        
        filtered_matches = []
        
        for match in matches:
            if self._passes_all_filters(match, criteria):
                filtered_matches.append(match)
        
        logger.info(f"Filtered {len(matches)} matches down to {len(filtered_matches)}")
        return filtered_matches
    
    def _passes_all_filters(self, match: Dict[str, Any], criteria: FilterCriteria) -> bool:
        """Check if match passes all filters"""
        try:
            # Odds filter
            if not self._passes_odds_filter(match, criteria):
                return False
            
            # Public bias filter
            if not self._passes_bias_filter(match, criteria):
                return False
            
            # Tournament tier filter
            if not self._passes_tier_filter(match, criteria):
                return False
            
            # Stand-in filter
            if not self._passes_stand_in_filter(match, criteria):
                return False
            
            # Market efficiency filter
            if not self._passes_efficiency_filter(match, criteria):
                return False
            
            # Tournament type filter
            if not self._passes_tournament_type_filter(match):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error filtering match {match.get('match_id', 'unknown')}: {e}")
            return False
    
    def _passes_odds_filter(self, match: Dict[str, Any], criteria: FilterCriteria) -> bool:
        """Check odds filter"""
        try:
            odds_data = match.get('odds', {})
            avg_odds = odds_data.get('average_odds', {})
            
            if not avg_odds:
                return True  # No odds data, pass by default
            
            team1_odds = avg_odds.get('team1', 0)
            team2_odds = avg_odds.get('team2', 0)
            
            # Check if any team is within odds range
            if team1_odds > 0:
                if not (criteria.min_odds <= team1_odds <= criteria.max_odds):
                    return False
            
            if team2_odds > 0:
                if not (criteria.min_odds <= team2_odds <= criteria.max_odds):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error in odds filter: {e}")
            return True
    
    def _passes_bias_filter(self, match: Dict[str, Any], criteria: FilterCriteria) -> bool:
        """Check public bias filter"""
        try:
            odds_data = match.get('odds', {})
            public_money = odds_data.get('public_money', {})
            
            if not public_money:
                return True  # No bias data, pass by default
            
            team1_pct = public_money.get('team1_percentage', 0)
            team2_pct = public_money.get('team2_percentage', 0)
            
            # Check if bias is within range
            if not (criteria.min_public_bias <= team1_pct <= criteria.max_public_bias):
                return False
            
            if not (criteria.min_public_bias <= team2_pct <= criteria.max_public_bias):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error in bias filter: {e}")
            return True
    
    def _passes_tier_filter(self, match: Dict[str, Any], criteria: FilterCriteria) -> bool:
        """Check tournament tier filter"""
        try:
            tier = match.get('tier', 'C')
            
            if criteria.required_tiers:
                return tier in criteria.required_tiers
            
            return True
            
        except Exception as e:
            logger.warning(f"Error in tier filter: {e}")
            return True
    
    def _passes_stand_in_filter(self, match: Dict[str, Any], criteria: FilterCriteria) -> bool:
        """Check stand-in filter"""
        try:
            if not criteria.exclude_stand_ins:
                return True
            
            match_info = match.get('match_info', {})
            stand_ins = match_info.get('stand_ins', {})
            
            # Exclude if any team has stand-ins
            if stand_ins.get('team1', False) or stand_ins.get('team2', False):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error in stand-in filter: {e}")
            return True
    
    def _passes_efficiency_filter(self, match: Dict[str, Any], criteria: FilterCriteria) -> bool:
        """Check market efficiency filter"""
        try:
            odds_data = match.get('odds', {})
            analysis = odds_data.get('analysis', {})
            
            if not analysis:
                return True  # No analysis data, pass by default
            
            efficiency = analysis.get('market_efficiency', 0)
            return efficiency >= criteria.min_market_efficiency
            
        except Exception as e:
            logger.warning(f"Error in efficiency filter: {e}")
            return True
    
    def _passes_tournament_type_filter(self, match: Dict[str, Any]) -> bool:
        """Check tournament type filter"""
        try:
            tournament = match.get('tournament', '').lower()
            
            # Exclude certain tournament types
            for excluded in self.excluded_tournaments:
                if excluded in tournament:
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error in tournament type filter: {e}")
            return True
    
    def create_favorite_filter(self) -> FilterCriteria:
        """Create filter for favorite scenarios (heavy favorites)"""
        return FilterCriteria(
            min_odds=1.10,
            max_odds=1.40,
            min_public_bias=70.0,
            max_public_bias=100.0,
            required_tiers={'S', 'A', 'B'},
            exclude_stand_ins=False,
            min_market_efficiency=0.4
        )
    
    def create_underdog_filter(self) -> FilterCriteria:
        """Create filter for underdog scenarios"""
        return FilterCriteria(
            min_odds=2.50,
            max_odds=5.00,
            min_public_bias=0.0,
            max_public_bias=40.0,
            required_tiers={'S', 'A'},
            exclude_stand_ins=True,
            min_market_efficiency=0.6
        )
    
    def create_value_bet_filter(self) -> FilterCriteria:
        """Create filter for value betting opportunities"""
        return FilterCriteria(
            min_odds=1.50,
            max_odds=3.00,
            min_public_bias=40.0,
            max_public_bias=80.0,
            required_tiers={'A', 'B'},
            exclude_stand_ins=False,
            min_market_efficiency=0.5
        )
    
    def create_high_volatility_filter(self) -> FilterCriteria:
        """Create filter for high volatility matches"""
        return FilterCriteria(
            min_odds=1.80,
            max_odds=4.00,
            min_public_bias=30.0,
            max_public_bias=70.0,
            required_tiers={'B', 'C'},
            exclude_stand_ins=False,  # Include stand-ins for volatility
            min_market_efficiency=0.2
        )


class MatchPrioritizer:
    """Prioritize matches for analysis"""
    
    def __init__(self):
        self.priority_weights = {
            'odds_quality': 0.3,
            'public_bias': 0.25,
            'tournament_importance': 0.2,
            'lineup_stability': 0.15,
            'market_efficiency': 0.1
        }
    
    def prioritize_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize matches based on multiple factors"""
        scored_matches = []
        
        for match in matches:
            score = self._calculate_priority_score(match)
            match['priority_score'] = score
            scored_matches.append(match)
        
        # Sort by priority score (descending)
        scored_matches.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        logger.info(f"Prioritized {len(matches)} matches")
        return scored_matches
    
    def _calculate_priority_score(self, match: Dict[str, Any]) -> float:
        """Calculate priority score for a match"""
        try:
            score = 0.0
            
            # Odds quality score
            odds_score = self._calculate_odds_score(match)
            score += odds_score * self.priority_weights['odds_quality']
            
            # Public bias score
            bias_score = self._calculate_bias_score(match)
            score += bias_score * self.priority_weights['public_bias']
            
            # Tournament importance score
            tier_score = self._calculate_tier_score(match)
            score += tier_score * self.priority_weights['tournament_importance']
            
            # Lineup stability score
            lineup_score = self._calculate_lineup_score(match)
            score += lineup_score * self.priority_weights['lineup_stability']
            
            # Market efficiency score
            efficiency_score = self._calculate_efficiency_score(match)
            score += efficiency_score * self.priority_weights['market_efficiency']
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating priority score: {e}")
            return 0.0
    
    def _calculate_odds_score(self, match: Dict[str, Any]) -> float:
        """Calculate odds quality score"""
        try:
            odds_data = match.get('odds', {})
            avg_odds = odds_data.get('average_odds', {})
            
            if not avg_odds:
                return 0.3  # No odds data
            
            team1_odds = avg_odds.get('team1', 0)
            team2_odds = avg_odds.get('team2', 0)
            
            # Prefer odds in sweet spot (1.20-3.00)
            if 1.20 <= min(team1_odds, team2_odds) <= 3.00:
                return 1.0
            elif 1.10 <= min(team1_odds, team2_odds) <= 4.00:
                return 0.7
            else:
                return 0.4
                
        except Exception:
            return 0.3
    
    def _calculate_bias_score(self, match: Dict[str, Any]) -> float:
        """Calculate public bias score"""
        try:
            odds_data = match.get('odds', {})
            public_money = odds_data.get('public_money', {})
            
            if not public_money:
                return 0.3
            
            team1_pct = public_money.get('team1_percentage', 50)
            team2_pct = public_money.get('team2_percentage', 50)
            
            # Higher score for significant bias (60-85% range)
            max_pct = max(team1_pct, team2_pct)
            
            if 70 <= max_pct <= 85:
                return 1.0
            elif 60 <= max_pct <= 90:
                return 0.7
            else:
                return 0.4
                
        except Exception:
            return 0.3
    
    def _calculate_tier_score(self, match: Dict[str, Any]) -> float:
        """Calculate tournament tier score"""
        try:
            tier = match.get('tier', 'C')
            
            tier_scores = {'S': 1.0, 'A': 0.8, 'B': 0.6, 'C': 0.4}
            return tier_scores.get(tier, 0.4)
            
        except Exception:
            return 0.4
    
    def _calculate_lineup_score(self, match: Dict[str, Any]) -> float:
        """Calculate lineup stability score"""
        try:
            lineup_analysis = match.get('lineup_analysis', {})
            stability = lineup_analysis.get('overall_stability_score', 1.0)
            
            # Higher score for stable lineups
            return stability
            
        except Exception:
            return 0.7
    
    def _calculate_efficiency_score(self, match: Dict[str, Any]) -> float:
        """Calculate market efficiency score"""
        try:
            odds_data = match.get('odds', {})
            analysis = odds_data.get('analysis', {})
            
            if not analysis:
                return 0.5
            
            return analysis.get('market_efficiency', 0.5)
            
        except Exception:
            return 0.5


async def filter_and_prioritize_cs2_matches(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter and prioritize CS2 matches"""
    try:
        # Apply filters
        match_filter = CS2MatchFilter()
        
        # Try different filter strategies
        favorite_filter = match_filter.create_favorite_filter()
        favorite_matches = match_filter.filter_matches(matches, favorite_filter)
        
        value_filter = match_filter.create_value_bet_filter()
        value_matches = match_filter.filter_matches(matches, value_filter)
        
        # Combine filtered matches
        filtered_matches = list({m['match_id']: m for m in favorite_matches + value_matches}.values())
        
        # Prioritize
        prioritizer = MatchPrioritizer()
        prioritized_matches = prioritizer.prioritize_matches(filtered_matches)
        
        return prioritized_matches[:10]  # Return top 10 matches
        
    except Exception as e:
        logger.error(f"Error filtering and prioritizing matches: {e}")
        return matches[:10]  # Fallback to first 10 matches


async def cs2_filtering_task():
    """CS2 match filtering and prioritization task"""
    logger.info("Starting CS2 match filtering")
    
    try:
        # Get all matches
        from storage.database import get_all_cs2_matches
        matches = await get_all_cs2_matches()
        
        if matches:
            prioritized_matches = await filter_and_prioritize_cs2_matches(matches)
            
            # Store prioritized matches
            from storage.database import store_prioritized_cs2_matches
            await store_prioritized_cs2_matches(prioritized_matches)
            
            logger.info(f"Filtered and prioritized {len(matches)} matches down to {len(prioritized_matches)}")
        
    except Exception as e:
        logger.error(f"CS2 filtering task failed: {e}")


def setup_cs2_filtering_tasks(scheduler):
    """Setup CS2 filtering tasks"""
    scheduler.add_task('cs2_filtering', cs2_filtering_task, 300)  # Every 5 minutes
    logger.info("CS2 filtering tasks setup complete")
