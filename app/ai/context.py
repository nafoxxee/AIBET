"""
AIBET Analytics Platform - AI Context Builder
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.services import nhl_service, khl_service, cs2_service
from app.schemas import LeagueMatch, AIContext
from app.utils.ids import id_extractor
from app.utils.time import time_utils
from app.logging import setup_logging

logger = setup_logging(__name__)


class AIContextBuilder:
    """Build AI context for match analysis"""
    
    def __init__(self):
        self.context_cache = {}
        self.max_context_age_hours = 24
    
    async def build_match_context(self, global_match_id: str) -> AIContext:
        """Build comprehensive AI context for a match"""
        try:
            # Extract basic info from match ID
            context_data = {"global_match_id": global_match_id}
            
            # Try to find the match in all leagues
            match = await self._find_match_by_id(global_match_id)
            
            if not match:
                return AIContext(
                    global_match_id=global_match_id,
                    context_data={"error": "Match not found"},
                    analysis_timestamp=datetime.utcnow()
                )
            
            # Extract league
            league = match.league
            
            # Build context layers
            context_data.update({
                "league": league,
                "teams": match.teams,
                "start_time": match.start_time.isoformat(),
                "status": match.status,
                "score": match.score.dict() if match.score else None,
                "odds": [odds.dict() for odds in match.odds] if match.odds else [],
                "data_quality": match.data_quality
            })
            
            # Add historical context
            historical_data = await self._get_historical_context(match)
            context_data["historical"] = historical_data
            
            # Add recent form context
            form_data = await self._get_form_context(match)
            context_data["recent_form"] = form_data
            
            # Add odds movement context
            odds_context = await self._get_odds_context(match)
            context_data["odds_analysis"] = odds_context
            
            # Add league-specific context
            league_context = await self._get_league_context(match)
            context_data["league_specific"] = league_context
            
            # Add time-based context
            time_context = self._get_time_context(match)
            context_data["time_analysis"] = time_context
            
            return AIContext(
                global_match_id=global_match_id,
                context_data=context_data,
                analysis_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error building AI context for {global_match_id}: {e}")
            return AIContext(
                global_match_id=global_match_id,
                context_data={"error": str(e)},
                analysis_timestamp=datetime.utcnow()
            )
    
    async def _find_match_by_id(self, global_match_id: str) -> Optional[LeagueMatch]:
        """Find match by global ID across all leagues"""
        from app.config import settings
        
        # Search in each league
        if settings.ENABLE_NHL:
            nhl_matches = await nhl_service.get_schedule(limit=100)
            for match in nhl_matches:
                if match.global_match_id == global_match_id:
                    return match
        
        if settings.ENABLE_KHL:
            khl_matches = await khl_service.get_schedule(limit=100)
            for match in khl_matches:
                if match.global_match_id == global_match_id:
                    return match
        
        if settings.ENABLE_CS2:
            cs2_matches = await cs2_service.get_matches()
            for match in cs2_matches:
                if match.global_match_id == global_match_id:
                    return match
        
        return None
    
    async def _get_historical_context(self, match: LeagueMatch) -> Dict[str, Any]:
        """Get historical head-to-head context"""
        try:
            # Get recent matches for both teams
            team_a, team_b = match.teams[0], match.teams[1]
            
            historical_matches = []
            
            # Search for past matchups (simplified)
            all_matches = []
            from app.config import settings
            
            if settings.ENABLE_NHL:
                all_matches.extend(await nhl_service.get_schedule(limit=200))
            if settings.ENABLE_KHL:
                all_matches.extend(await khl_service.get_schedule(limit=200))
            if settings.ENABLE_CS2:
                all_matches.extend(await cs2_service.get_matches())
            
            # Find head-to-head matches
            for past_match in all_matches:
                if past_match.status == "finished":
                    past_teams = past_match.teams
                    if (team_a in past_teams and team_b in past_teams):
                        historical_matches.append(past_match)
            
            # Analyze historical data
            if historical_matches:
                total_matches = len(historical_matches)
                team_a_wins = sum(1 for m in historical_matches 
                                  if self._get_winner(m) == team_a)
                team_b_wins = sum(1 for m in historical_matches 
                                  if self._get_winner(m) == team_b)
                
                return {
                    "total_h2h_matches": total_matches,
                    "team_a_wins": team_a_wins,
                    "team_b_wins": team_b_wins,
                    "win_rate_a": team_a_wins / total_matches if total_matches > 0 else 0,
                    "win_rate_b": team_b_wins / total_matches if total_matches > 0 else 0,
                    "recent_trend": self._calculate_recent_trend(historical_matches)
                }
            
            return {"message": "No historical data available"}
            
        except Exception as e:
            logger.error(f"Error getting historical context: {e}")
            return {"error": str(e)}
    
    async def _get_form_context(self, match: LeagueMatch) -> Dict[str, Any]:
        """Get recent form context for teams"""
        try:
            team_a, team_b = match.teams[0], match.teams[1]
            
            # Get recent matches for each team (last 5)
            recent_matches = []
            all_matches = []
            
            from app.config import settings
            
            if settings.ENABLE_NHL:
                all_matches.extend(await nhl_service.get_schedule(limit=100))
            if settings.ENABLE_KHL:
                all_matches.extend(await khl_service.get_schedule(limit=100))
            if settings.ENABLE_CS2:
                all_matches.extend(await cs2_service.get_matches())
            
            # Filter recent finished matches
            recent_finished = [m for m in all_matches 
                             if m.status == "finished" and 
                             time_utils.is_past(m.start_time, hours=72)]
            
            # Sort by time
            recent_finished.sort(key=lambda x: x.start_time, reverse=True)
            
            # Get form for each team
            team_a_form = self._calculate_team_form(team_a, recent_finished[:10])
            team_b_form = self._calculate_team_form(team_b, recent_finished[:10])
            
            return {
                "team_a": {
                    "name": team_a,
                    "form": team_a_form,
                    "last_5_matches": team_a_form.get("last_5_results", [])
                },
                "team_b": {
                    "name": team_b,
                    "form": team_b_form,
                    "last_5_matches": team_b_form.get("last_5_results", [])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting form context: {e}")
            return {"error": str(e)}
    
    async def _get_odds_context(self, match: LeagueMatch) -> Dict[str, Any]:
        """Get odds analysis context"""
        try:
            if not match.odds:
                return {"message": "No odds data available"}
            
            # Analyze odds across sources
            all_odds = []
            for odds_info in match.odds:
                all_odds.extend(odds_info.odds.values())
            
            if all_odds:
                import statistics
                
                return {
                    "sources_count": len(match.odds),
                    "avg_odds": statistics.mean(all_odds),
                    "min_odds": min(all_odds),
                    "max_odds": max(all_odds),
                    "odds_spread": max(all_odds) - min(all_odds),
                    "movement_detected": any(
                        odds.movement and len(set(odds.movement)) > 1 
                        for odds in match.odds
                    )
                }
            
            return {"message": "No valid odds data"}
            
        except Exception as e:
            logger.error(f"Error getting odds context: {e}")
            return {"error": str(e)}
    
    async def _get_league_context(self, match: LeagueMatch) -> Dict[str, Any]:
        """Get league-specific context"""
        try:
            league = match.league
            
            if league == "NHL":
                return {
                    "season_type": "regular_season",
                    "conference_format": True,
                    "playoff_format": "best_of_7",
                    "overtime_rules": "5v5_15min",
                    "points_system": "2_1_0"
                }
            elif league == "KHL":
                return {
                    "season_type": "regular_season",
                    "conference_format": True,
                    "playoff_format": "best_of_7",
                    "overtime_rules": "4v4_20min",
                    "points_system": "3_2_1_0"
                }
            elif league == "CS2":
                return {
                    "format": match.best_of,
                    "game_type": "tactical_shooter",
                    "overtime_rules": "sudden_death",
                    "map_pool": ["mirage", "inferno", "dust2", "vertigo", "ancient"],
                    "economy_based": True
                }
            
            return {"message": "Unknown league context"}
            
        except Exception as e:
            logger.error(f"Error getting league context: {e}")
            return {"error": str(e)}
    
    def _get_time_context(self, match: LeagueMatch) -> Dict[str, Any]:
        """Get time-based analysis context"""
        try:
            now = datetime.utcnow()
            start_time = match.start_time
            
            return {
                "hours_until_match": (start_time - now).total_seconds() / 3600 if start_time > now else 0,
                "days_since_last_match": self._get_days_since_last_match(match),
                "time_of_day": start_time.hour,
                "day_of_week": start_time.strftime("%A"),
                "is_weekend": start_time.weekday() >= 5,
                "is_prime_time": 18 <= start_time.hour <= 22
            }
            
        except Exception as e:
            logger.error(f"Error getting time context: {e}")
            return {"error": str(e)}
    
    def _get_winner(self, match: LeagueMatch) -> Optional[str]:
        """Extract winner from finished match"""
        if not match.score or not match.score.final:
            return None
        
        final_score = match.score.final
        team_a, team_b = match.teams[0], match.teams[1]
        
        team_a_score = final_score.get(team_a, 0)
        team_b_score = final_score.get(team_b, 0)
        
        return team_a if team_a_score > team_b_score else team_b
    
    def _calculate_recent_trend(self, matches: List[LeagueMatch]) -> str:
        """Calculate recent trend for head-to-head"""
        if len(matches) < 3:
            return "insufficient_data"
        
        # Get last 3 matches
        recent_matches = matches[:3]
        team_a_wins = 0
        
        for match in recent_matches:
            winner = self._get_winner(match)
            if winner == match.teams[0]:  # team_a
                team_a_wins += 1
        
        if team_a_wins >= 2:
            return "team_a_dominant"
        elif team_a_wins == 1:
            return "balanced"
        else:
            return "team_b_dominant"
    
    def _calculate_team_form(self, team: str, matches: List[LeagueMatch]) -> Dict[str, Any]:
        """Calculate team form"""
        team_matches = [m for m in matches if team in m.teams]
        
        if not team_matches:
            return {"form": "no_data"}
        
        wins = 0
        losses = 0
        last_5_results = []
        
        for match in team_matches[:5]:
            winner = self._get_winner(match)
            if winner == team:
                wins += 1
                last_5_results.append("W")
            else:
                losses += 1
                last_5_results.append("L")
        
        win_rate = wins / len(team_matches) if team_matches else 0
        
        return {
            "matches_played": len(team_matches),
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "current_streak": self._get_current_streak(last_5_results),
            "last_5_results": last_5_results
        }
    
    def _get_current_streak(self, results: List[str]) -> str:
        """Get current win/loss streak"""
        if not results:
            return "no_data"
        
        streak = 1
        current_result = results[0]
        
        for result in results[1:]:
            if result == current_result:
                streak += 1
            else:
                break
        
        return f"{streak}_{current_result}"
    
    def _get_days_since_last_match(self, match: LeagueMatch) -> int:
        """Get days since last match for both teams"""
        # Simplified implementation
        return (datetime.utcnow() - match.start_time).days


# Global AI context builder
ai_context_builder = AIContextBuilder()
