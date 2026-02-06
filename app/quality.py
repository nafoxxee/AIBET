"""
AIBET Analytics Platform - Data Quality Assessment
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.schemas import LeagueMatch, OddsInfo

logger = logging.getLogger(__name__)


class DataQualityAssessor:
    """Data quality assessment for matches and odds"""
    
    def __init__(self):
        self.quality_thresholds = {
            "fresh_data_hours": 24,  # Data is fresh if less than 24 hours old
            "min_odds": 1.01,  # Minimum odds value
            "max_odds": 1000,  # Maximum odds value
            "min_team_name_length": 2,
            "max_team_name_length": 50
        }
    
    async def assess_match_quality(self, match: LeagueMatch) -> str:
        """Assess match data quality"""
        quality_score = 0
        max_score = 5
        
        # Check data freshness
        if self._is_data_fresh(match.start_time):
            quality_score += 1
        else:
            logger.debug(f"Stale data for match {match.global_match_id}")
        
        # Check team names
        if self._validate_team_names(match.teams):
            quality_score += 1
        else:
            logger.debug(f"Invalid team names for match {match.global_match_id}")
        
        # Check odds if present
        if match.odds and self._validate_odds(match.odds):
            quality_score += 1
        else:
            logger.debug(f"Invalid odds for match {match.global_match_id}")
        
        # Check match status consistency
        if self._validate_status_consistency(match):
            quality_score += 1
        else:
            logger.debug(f"Inconsistent status for match {match.global_match_id}")
        
        # Check confidence scores
        if self._validate_confidence_scores(match):
            quality_score += 1
        else:
            logger.debug(f"Invalid confidence scores for match {match.global_match_id}")
        
        # Determine quality level
        quality_ratio = quality_score / max_score
        if quality_ratio >= 0.8:
            return "high"
        elif quality_ratio >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _is_data_fresh(self, start_time: datetime) -> bool:
        """Check if data is fresh"""
        now = datetime.utcnow()
        age = now - start_time
        return age.total_seconds() < (self.quality_thresholds["fresh_data_hours"] * 3600)
    
    def _validate_team_names(self, teams: List[str]) -> bool:
        """Validate team names"""
        if len(teams) != 2:
            return False
        
        for team in teams:
            length = len(team.strip())
            if not (self.quality_thresholds["min_team_name_length"] <= length <= self.quality_thresholds["max_team_name_length"]):
                return False
        
        return True
    
    def _validate_odds(self, odds_list: List[OddsInfo]) -> bool:
        """Validate odds information"""
        if not odds_list:
            return True  # No odds is valid
        
        for odds_info in odds_list:
            for odds_value in odds_info.odds.values():
                if not (self.quality_thresholds["min_odds"] <= odds_value <= self.quality_thresholds["max_odds"]):
                    return False
        
        return True
    
    def _validate_status_consistency(self, match: LeagueMatch) -> bool:
        """Validate match status consistency"""
        now = datetime.utcnow()
        
        # Check status vs start time
        if match.status == "scheduled" and match.start_time > now:
            return True
        elif match.status == "live" and match.start_time <= now:
            return True
        elif match.status == "finished":
            return True
        elif match.status == "archived":
            return True
        
        return False
    
    def _validate_confidence_scores(self, match: LeagueMatch) -> bool:
        """Validate confidence scores"""
        return (
            0.0 <= match.confidence_score <= 1.0 and
            0.0 <= match.value_score <= 1.0
        )
    
    async def filter_bad_data(self, matches: List[LeagueMatch]) -> List[LeagueMatch]:
        """Filter out matches with bad data"""
        filtered_matches = []
        
        for match in matches:
            quality = await self.assess_match_quality(match)
            
            # Only filter out very low quality data
            if quality != "low":
                match.data_quality = quality
                filtered_matches.append(match)
            else:
                logger.warning(f"Filtered out low quality match: {match.global_match_id}")
        
        return filtered_matches
    
    async def update_quality_from_source(self, match: LeagueMatch, source_reliability: float):
        """Update match quality based on source reliability"""
        current_quality = match.data_quality or "medium"
        
        # Adjust quality based on source reliability
        if source_reliability > 0.8 and current_quality == "medium":
            match.data_quality = "high"
        elif source_reliability < 0.5 and current_quality == "high":
            match.data_quality = "medium"
        elif source_reliability < 0.3:
            match.data_quality = "low"


# Global quality assessor
quality_assessor = DataQualityAssessor()
