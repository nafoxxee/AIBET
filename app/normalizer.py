"""
AIBET Analytics Platform - Data Normalization
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.schemas import LeagueMatch, OddsInfo, TeamScore, MatchScore

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Data normalization for different sources"""
    
    def __init__(self):
        self.team_name_mappings = {
            # NHL team name normalization
            "TOR": "Toronto Maple Leafs",
            "MTL": "Montreal Canadiens",
            "NYR": "New York Rangers",
            "NYI": "New York Islanders",
            "NJD": "New Jersey Devils",
            "NYB": "New Jersey Devils",  # Legacy mapping
            
            # KHL team name normalization
            "CSKA": "CSKA Moscow",
            "SKA": "SKA Saint Petersburg",
            "AK BARS": "Ak Bars Kazan",
            "METALLURG MG": "Metallurg Magnitogorsk",
            "LOKO": "Lokomotiv Yaroslavl",
            
            # CS2 team name normalization
            "NAVI": "Natus Vincere",
            "FAZE": "FaZe Clan",
            "G2": "G2 Esports",
            "VITALITY": "Team Vitality",
            "ASTRALIS": "Astralis"
        }
        
        self.status_mappings = {
            "scheduled": "scheduled",
            "upcoming": "upcoming", 
            "live": "live",
            "in_progress": "live",
            "finished": "finished",
            "completed": "finished",
            "ended": "finished",
            "archived": "archived",
            "postponed": "archived",
            "cancelled": "archived"
        }
    
    async def normalize_match(self, raw_match: Dict[str, Any], league: str) -> LeagueMatch:
        """Normalize match data from any source"""
        try:
            # Generate global match ID
            global_match_id = self._generate_global_id(raw_match, league)
            
            # Normalize teams
            teams = self._normalize_teams(raw_match.get("teams", []))
            
            # Normalize start time
            start_time = self._normalize_datetime(raw_match.get("start_time"))
            
            # Normalize status
            status = self._normalize_status(raw_match.get("status", "scheduled"))
            
            # Normalize score
            score = self._normalize_score(raw_match.get("score"))
            
            # Normalize odds
            odds = self._normalize_odds(raw_match.get("odds", []))
            
            # Determine lifecycle state
            lifecycle_state = self._determine_lifecycle_state(status, start_time)
            
            # Create normalized match
            normalized_match = LeagueMatch(
                global_match_id=global_match_id,
                league=league,
                teams=teams,
                start_time=start_time,
                status=status,
                score=score,
                best_of=raw_match.get("best_of", 1),
                odds=odds,
                confidence_score=0.0,  # Will be calculated later
                value_score=0.0,      # Will be calculated later
                lifecycle_state=lifecycle_state,
                source_confidence=[],
                data_quality="medium"  # Will be assessed later
            )
            
            logger.debug(f"Normalized match {global_match_id} for {league}")
            return normalized_match
            
        except Exception as e:
            logger.error(f"Error normalizing match: {e}")
            raise
    
    def _generate_global_id(self, raw_match: Dict[str, Any], league: str) -> str:
        """Generate global match ID"""
        from app.schemas import GlobalMatchID
        
        teams = raw_match.get("teams", [])
        if len(teams) >= 2:
            team_a, team_b = teams[0], teams[1]
        else:
            team_a, team_b = "unknown", "unknown"
        
        start_time = self._normalize_datetime(raw_match.get("start_time"))
        
        return GlobalMatchID.generate(league, team_a, team_b, start_time)
    
    def _normalize_teams(self, teams: List[str]) -> List[str]:
        """Normalize team names"""
        normalized_teams = []
        
        for team in teams:
            if isinstance(team, str):
                # Apply team name mappings
                normalized = self.team_name_mappings.get(team.upper(), team.strip())
                normalized_teams.append(normalized)
            elif isinstance(team, dict):
                # Handle team objects
                team_name = team.get("name", team.get("short_name", ""))
                normalized = self.team_name_mappings.get(team_name.upper(), team_name.strip())
                normalized_teams.append(normalized)
        
        return normalized_teams
    
    def _normalize_datetime(self, datetime_value: Any) -> datetime:
        """Normalize datetime from various formats"""
        if isinstance(datetime_value, datetime):
            return datetime_value
        
        if isinstance(datetime_value, str):
            # Try common datetime formats
            formats = [
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d.%m.%Y %H:%M",
                "%d.%m.%Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(datetime_value, fmt)
                except ValueError:
                    continue
        
        # Default to current time
        logger.warning(f"Could not parse datetime: {datetime_value}, using current time")
        return datetime.utcnow()
    
    def _normalize_status(self, status: str) -> str:
        """Normalize match status"""
        if not status:
            return "scheduled"
        
        normalized = self.status_mappings.get(status.lower().strip(), status.lower().strip())
        
        # Validate normalized status
        valid_statuses = ["scheduled", "upcoming", "live", "finished", "archived"]
        return normalized if normalized in valid_statuses else "scheduled"
    
    def _normalize_score(self, score_data: Any) -> Optional[MatchScore]:
        """Normalize score information"""
        if not score_data:
            return None
        
        try:
            if isinstance(score_data, dict):
                # Handle different score formats
                current = score_data.get("current")
                periods = score_data.get("periods")
                final = score_data.get("final")
                
                return MatchScore(
                    current=current,
                    periods=periods,
                    final=final
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error normalizing score: {e}")
            return None
    
    def _normalize_odds(self, odds_data: Any) -> Optional[List[OddsInfo]]:
        """Normalize odds information"""
        if not odds_data:
            return None
        
        try:
            normalized_odds = []
            
            if isinstance(odds_data, list):
                for odds_item in odds_data:
                    if isinstance(odds_item, dict):
                        normalized_odds.append(OddsInfo(
                            source=odds_item.get("source", "unknown"),
                            odds=odds_item.get("odds", {}),
                            timestamp=self._normalize_datetime(odds_item.get("timestamp")),
                            movement=odds_item.get("movement")
                        ))
            
            return normalized_odds if normalized_odds else None
            
        except Exception as e:
            logger.error(f"Error normalizing odds: {e}")
            return None
    
    def _determine_lifecycle_state(self, status: str, start_time: datetime) -> str:
        """Determine lifecycle state from status and start time"""
        now = datetime.utcnow()
        
        if status == "scheduled" and start_time > now:
            return "UPCOMING"
        elif status == "upcoming":
            return "UPCOMING"
        elif status == "live":
            return "LIVE"
        elif status == "finished":
            return "FINISHED"
        elif status == "archived":
            return "ARCHIVED"
        else:
            return "UPCOMING"


# Global normalizer
data_normalizer = DataNormalizer()
