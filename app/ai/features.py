"""
AIBET Analytics Platform - AI Feature Engineering
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.schemas import LeagueMatch
from app.logging import setup_logging

logger = setup_logging(__name__)


class AIFeatureEngineer:
    """Feature engineering for AI analysis"""
    
    def __init__(self):
        self.feature_weights = {
            "recent_form": 0.3,
            "head_to_head": 0.25,
            "odds_analysis": 0.2,
            "home_advantage": 0.15,
            "time_factors": 0.1
        }
    
    async def extract_features(self, match: LeagueMatch, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract AI features from match and context"""
        try:
            features = {
                "match_id": match.global_match_id,
                "league": match.league,
                "teams": match.teams,
                "extraction_timestamp": datetime.utcnow().isoformat()
            }
            
            # Extract form features
            form_features = await self._extract_form_features(context)
            features["form"] = form_features
            
            # Extract head-to-head features
            h2h_features = await self._extract_h2h_features(context)
            features["head_to_head"] = h2h_features
            
            # Extract odds features
            odds_features = await self._extract_odds_features(match, context)
            features["odds"] = odds_features
            
            # Extract situational features
            situational_features = await self._extract_situational_features(match, context)
            features["situational"] = situational_features
            
            # Extract league-specific features
            league_features = await self._extract_league_features(match, context)
            features["league_specific"] = league_features
            
            # Calculate composite scores
            composite_scores = await self._calculate_composite_scores(features)
            features["composite_scores"] = composite_scores
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features for {match.global_match_id}: {e}")
            return {"error": str(e)}
    
    async def _extract_form_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract team form features"""
        try:
            recent_form = context.get("recent_form", {})
            
            if not recent_form or "error" in recent_form:
                return {"available": False}
            
            team_a_form = recent_form.get("team_a", {})
            team_b_form = recent_form.get("team_b", {})
            
            features = {
                "available": True,
                "team_a": {
                    "win_rate": team_a_form.get("form", {}).get("win_rate", 0),
                    "current_streak": team_a_form.get("form", {}).get("current_streak", "no_data"),
                    "last_5_wins": sum(1 for r in team_a_form.get("last_5_results", []) if r == "W"),
                    "momentum": self._calculate_momentum(team_a_form.get("last_5_results", []))
                },
                "team_b": {
                    "win_rate": team_b_form.get("form", {}).get("win_rate", 0),
                    "current_streak": team_b_form.get("form", {}).get("current_streak", "no_data"),
                    "last_5_wins": sum(1 for r in team_b_form.get("last_5_results", []) if r == "W"),
                    "momentum": self._calculate_momentum(team_b_form.get("last_5_results", []))
                }
            }
            
            # Calculate form differential
            features["form_differential"] = {
                "win_rate_diff": features["team_a"]["win_rate"] - features["team_b"]["win_rate"],
                "momentum_diff": features["team_a"]["momentum"] - features["team_b"]["momentum"],
                "advantage": "team_a" if features["team_a"]["win_rate"] > features["team_b"]["win_rate"] else "team_b"
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting form features: {e}")
            return {"available": False, "error": str(e)}
    
    async def _extract_h2h_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract head-to-head features"""
        try:
            historical = context.get("historical", {})
            
            if not historical or "error" in historical:
                return {"available": False}
            
            total_matches = historical.get("total_h2h_matches", 0)
            
            if total_matches == 0:
                return {"available": False}
            
            features = {
                "available": True,
                "total_matches": total_matches,
                "team_a_wins": historical.get("team_a_wins", 0),
                "team_b_wins": historical.get("team_b_wins", 0),
                "team_a_win_rate": historical.get("win_rate_a", 0),
                "team_b_win_rate": historical.get("win_rate_b", 0),
                "recent_trend": historical.get("recent_trend", "balanced")
            }
            
            # Calculate H2H dominance
            if features["team_a_win_rate"] > 0.7:
                features["dominance"] = "team_a_strong"
            elif features["team_b_win_rate"] > 0.7:
                features["dominance"] = "team_b_strong"
            elif abs(features["team_a_win_rate"] - features["team_b_win_rate"]) < 0.1:
                features["dominance"] = "balanced"
            else:
                features["dominance"] = "competitive"
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting H2H features: {e}")
            return {"available": False, "error": str(e)}
    
    async def _extract_odds_features(self, match: LeagueMatch, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract odds-related features"""
        try:
            odds_context = context.get("odds_analysis", {})
            
            if not match.odds or not odds_context or "error" in odds_context:
                return {"available": False}
            
            features = {
                "available": True,
                "sources_count": len(match.odds),
                "avg_odds": odds_context.get("avg_odds", 0),
                "min_odds": odds_context.get("min_odds", 0),
                "max_odds": odds_context.get("max_odds", 0),
                "odds_spread": odds_context.get("odds_spread", 0),
                "movement_detected": odds_context.get("movement_detected", False)
            }
            
            # Calculate odds signals
            if features["avg_odds"] > 0:
                # Value detection (simplified)
                if features["avg_odds"] > 2.5:
                    features["value_signal"] = "underdog_favored"
                elif features["avg_odds"] < 1.8:
                    features["value_signal"] = "favorite_favored"
                else:
                    features["value_signal"] = "neutral"
                
                # Volatility detection
                if features["odds_spread"] > 0.5:
                    features["volatility"] = "high"
                elif features["odds_spread"] > 0.2:
                    features["volatility"] = "medium"
                else:
                    features["volatility"] = "low"
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting odds features: {e}")
            return {"available": False, "error": str(e)}
    
    async def _extract_situational_features(self, match: LeagueMatch, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract situational features"""
        try:
            time_analysis = context.get("time_analysis", {})
            
            if not time_analysis or "error" in time_analysis:
                return {"available": False}
            
            features = {
                "available": True,
                "hours_until_match": time_analysis.get("hours_until_match", 0),
                "time_of_day": time_analysis.get("time_of_day", 12),
                "day_of_week": time_analysis.get("day_of_week", "Unknown"),
                "is_weekend": time_analysis.get("is_weekend", False),
                "is_prime_time": time_analysis.get("is_prime_time", False),
                "days_since_last_match": time_analysis.get("days_since_last_match", 0)
            }
            
            # Calculate situational factors
            if features["hours_until_match"] < 2:
                features["urgency"] = "imminent"
            elif features["hours_until_match"] < 6:
                features["urgency"] = "soon"
            else:
                features["urgency"] = "normal"
            
            # Time-based performance factors
            if features["is_prime_time"]:
                features["performance_factor"] = "enhanced"
            elif features["is_weekend"]:
                features["performance_factor"] = "weekend_effect"
            else:
                features["performance_factor"] = "standard"
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting situational features: {e}")
            return {"available": False, "error": str(e)}
    
    async def _extract_league_features(self, match: LeagueMatch, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract league-specific features"""
        try:
            league_context = context.get("league_specific", {})
            
            if not league_context or "error" in league_context:
                return {"available": False}
            
            league = match.league
            
            features = {
                "available": True,
                "league": league
            }
            
            if league == "NHL":
                features.update({
                    "season_format": "82_games",
                    "playoff_intensity": "high",
                    "travel_factor": "significant",
                    "rest_importance": "critical"
                })
            elif league == "KHL":
                features.update({
                    "season_format": "68_games",
                    "playoff_intensity": "medium",
                    "travel_factor": "moderate",
                    "rest_importance": "important"
                })
            elif league == "CS2":
                features.update({
                    "format": match.best_of,
                    "map_advantage": "map_pool_knowledge",
                    "economy_impact": "significant",
                    "team_coordination": "critical"
                })
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting league features: {e}")
            return {"available": False, "error": str(e)}
    
    async def _calculate_composite_scores(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate composite AI scores"""
        try:
            composite = {
                "confidence_score": 0.0,
                "value_score": 0.0,
                "risk_level": "medium"
            }
            
            # Form score (0-1)
            form_score = 0.0
            if features.get("form", {}).get("available"):
                form_diff = features["form"].get("form_differential", {})
                win_rate_diff = abs(form_diff.get("win_rate_diff", 0))
                form_score = max(0, 1 - win_rate_diff)
            
            # H2H score (0-1)
            h2h_score = 0.0
            if features.get("head_to_head", {}).get("available"):
                h2h_data = features["head_to_head"]
                if h2h_data.get("dominance") in ["team_a_strong", "team_b_strong"]:
                    h2h_score = 0.8
                elif h2h_data.get("dominance") == "balanced":
                    h2h_score = 0.5
                else:
                    h2h_score = 0.2
            
            # Odds score (0-1)
            odds_score = 0.0
            if features.get("odds", {}).get("available"):
                odds_data = features["odds"]
                # Higher score for stable odds
                if odds_data.get("volatility") == "low":
                    odds_score = 0.8
                elif odds_data.get("volatility") == "medium":
                    odds_score = 0.5
                else:
                    odds_score = 0.2
            
            # Situational score (0-1)
            situational_score = 0.0
            if features.get("situational", {}).get("available"):
                time_data = features["situational"]
                if time_data.get("performance_factor") == "enhanced":
                    situational_score = 0.8
                elif time_data.get("performance_factor") == "standard":
                    situational_score = 0.5
                else:
                    situational_score = 0.3
            
            # Calculate weighted composite scores
            composite["confidence_score"] = (
                form_score * self.feature_weights["recent_form"] +
                h2h_score * self.feature_weights["head_to_head"] +
                odds_score * self.feature_weights["odds_analysis"] +
                situational_score * self.feature_weights["time_factors"]
            )
            
            # Value score based on odds vs form
            if features.get("odds", {}).get("available") and features.get("form", {}).get("available"):
                odds_avg = features["odds"].get("avg_odds", 2.0)
                form_advantage = features["form"].get("form_differential", {}).get("advantage", "balanced")
                
                if form_advantage == "team_a" and odds_avg > 2.0:
                    composite["value_score"] = 0.8  # Team A undervalued
                elif form_advantage == "team_b" and odds_avg < 2.0:
                    composite["value_score"] = 0.8  # Team B undervalued
                elif odds_avg > 3.0:
                    composite["value_score"] = 0.6  # High odds = potential value
                else:
                    composite["value_score"] = 0.4
            
            # Risk level
            if composite["confidence_score"] > 0.8:
                composite["risk_level"] = "low"
            elif composite["confidence_score"] > 0.5:
                composite["risk_level"] = "medium"
            else:
                composite["risk_level"] = "high"
            
            return composite
            
        except Exception as e:
            logger.error(f"Error calculating composite scores: {e}")
            return {"confidence_score": 0.5, "value_score": 0.5, "risk_level": "medium"}
    
    def _calculate_momentum(self, results: List[str]) -> float:
        """Calculate momentum from recent results"""
        if not results:
            return 0.0
        
        momentum = 0.0
        weight = 1.0
        
        for result in results:
            if result == "W":
                momentum += weight
            elif result == "L":
                momentum -= weight * 0.5
            
            weight *= 0.8  # Decreasing weight for older matches
        
        # Normalize to -1 to 1 range
        return max(-1.0, min(1.0, momentum / len(results)))


# Global AI feature engineer
ai_feature_engineer = AIFeatureEngineer()
