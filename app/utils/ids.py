"""
AIBET Analytics Platform - ID Generation and Validation
"""

import hashlib
import time
from datetime import datetime
from typing import Optional


class IDGenerator:
    """Deterministic ID generator"""
    
    @staticmethod
    def generate_match_id(league: str, team_a: str, team_b: str, start_time: datetime) -> str:
        """Generate deterministic global match ID"""
        # Create consistent string
        data = f"{league}_{team_a}_{team_b}_{start_time.isoformat()}"
        
        # Generate SHA256 hash
        hash_object = hashlib.sha256(data.encode('utf-8'))
        hash_hex = hash_object.hexdigest()
        
        # Return first 16 characters
        return hash_hex[:16]
    
    @staticmethod
    def generate_request_id() -> str:
        """Generate unique request ID"""
        timestamp = str(int(time.time() * 1000))
        random_data = str(time.time()).replace('.', '')
        
        data = f"{timestamp}_{random_data}"
        hash_object = hashlib.sha256(data.encode('utf-8'))
        
        return hash_object.hexdigest()[:12]
    
    @staticmethod
    def validate_global_match_id(match_id: str) -> bool:
        """Validate global match ID format"""
        if not match_id:
            return False
        
        # Should be 16 character hex string
        return len(match_id) == 16 and all(c in '0123456789abcdef' for c in match_id.lower())


class IDExtractor:
    """Extract components from IDs"""
    
    @staticmethod
    def extract_league_from_context(context_data: dict) -> Optional[str]:
        """Extract league from context data"""
        if "league" in context_data:
            return context_data["league"]
        
        if "teams" in context_data and len(context_data["teams"]) >= 2:
            # Try to infer league from team names
            teams = context_data["teams"]
            if any(team in ["Toronto Maple Leafs", "Montreal Canadiens"] for team in teams):
                return "NHL"
            elif any(team in ["CSKA Moscow", "SKA Saint Petersburg"] for team in teams):
                return "KHL"
            elif any(team in ["Natus Vincere", "FaZe Clan", "G2 Esports"] for team in teams):
                return "CS2"
        
        return None
    
    @staticmethod
    def extract_time_window(match_data: dict, hours: int = 24) -> tuple:
        """Extract time window for data queries"""
        start_time = match_data.get("start_time")
        if not start_time:
            return None, None
        
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        
        from datetime import timedelta
        
        window_start = start_time - timedelta(hours=hours)
        window_end = start_time + timedelta(hours=hours)
        
        return window_start, window_end


# Global instances
id_generator = IDGenerator()
id_extractor = IDExtractor()
