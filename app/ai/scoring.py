"""
AIBET Analytics Platform - AI Scoring Engine v1.3
Educational analysis with confidence and risk assessment
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json

from app.schemas import LeagueMatch, AIContext, AIFeatures
from app.logging import setup_logging

logger = setup_logging(__name__)


class AIScoringEngine:
    """AI scoring engine for educational analysis"""
    
    def __init__(self):
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
        
        self.risk_factors = {
            "data_quality": 0.3,
            "sample_size": 0.2,
            "volatility": 0.3,
            "time_factor": 0.2
        }
    
    async def calculate_ai_score(self, match: Optional[LeagueMatch], features: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate AI score with educational disclaimer"""
        try:
            # Base score calculation
            base_score = await self._calculate_base_score(features)
            
            # Confidence calculation
            confidence = await self._calculate_confidence(features)
            
            # Risk assessment
            risk_level = await self._assess_risk_level(features, confidence)
            
            # Value assessment
            value_score = await self._calculate_value_score(features)
            
            # Educational disclaimer
            educational_note = self._get_educational_disclaimer()
            
            result = {
                "ai_score": round(base_score, 3),
                "confidence": round(confidence, 3),
                "risk_level": risk_level,
                "value_score": round(value_score, 3),
                "not_a_prediction": True,
                "educational_purpose_only": True,
                "disclaimer": educational_note,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "factors": {
                    "form_analysis": features.get("form_score", 0),
                    "historical_data": features.get("h2h_score", 0),
                    "market_factors": features.get("odds_score", 0),
                    "league_factors": features.get("league_score", 0)
                },
                "confidence_breakdown": {
                    "data_quality": features.get("data_quality", 0.5),
                    "sample_size": features.get("sample_size", 0.5),
                    "market_stability": features.get("market_stability", 0.5)
                },
                "risk_factors": await self._identify_risk_factors(features)
            }
            
            logger.info(f"AI score calculated: {base_score:.3f} (confidence: {confidence:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating AI score: {e}")
            return self._get_fallback_score()
    
    async def _calculate_base_score(self, features: Dict[str, Any]) -> float:
        """Calculate base AI score"""
        try:
            # Weighted factors
            form_weight = 0.3
            h2h_weight = 0.25
            odds_weight = 0.25
            league_weight = 0.2
            
            form_score = features.get("form_score", 0.5)
            h2h_score = features.get("h2h_score", 0.5)
            odds_score = features.get("odds_score", 0.5)
            league_score = features.get("league_score", 0.5)
            
            base_score = (
                form_score * form_weight +
                h2h_score * h2h_weight +
                odds_score * odds_weight +
                league_score * league_weight
            )
            
            # Normalize to 0-1 range
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            logger.error(f"Error calculating base score: {e}")
            return 0.5
    
    async def _calculate_confidence(self, features: Dict[str, Any]) -> float:
        """Calculate confidence level"""
        try:
            # Data quality factors
            data_quality = features.get("data_quality", 0.5)
            sample_size = features.get("sample_size", 0.5)
            market_stability = features.get("market_stability", 0.5)
            
            # Weighted confidence
            confidence = (
                data_quality * 0.4 +
                sample_size * 0.3 +
                market_stability * 0.3
            )
            
            return max(0.0, min(1.0, confidence))
            if form_features.get("available"):
                form_advantage = form_features.get("form_differential", {}).get("advantage", "balanced")
                
                if form_advantage != "balanced":
                    if (form_advantage == "team_a" and avg_odds > 2.2) or \
                       (form_advantage == "team_b" and avg_odds < 1.8):
                        adjusted_value *= 1.2  # Strong mismatch = high value
                    elif (form_advantage == "team_a" and avg_odds > 2.5) or \
                         (form_advantage == "team_b" and avg_odds < 1.6):
                        adjusted_value *= 1.3  # Very strong mismatch = very high value
            
            # Time-based value
            situational_features = features.get("situational", {})
            if situational_features.get("available"):
                urgency = situational_features.get("urgency", "normal")
                if urgency == "imminent":
                    adjusted_value *= 1.05  # Last-minute analysis
                performance_factor = situational_features.get("performance_factor", "standard")
                if performance_factor == "enhanced":
                    adjusted_value *= 1.03
            
            # Ensure within bounds
            return max(0.1, min(1.0, adjusted_value))
            
        except Exception as e:
            logger.error(f"Error applying value adjustments: {e}")
            return base_value
    
    def _determine_risk_level(self, confidence: float, features: Dict[str, Any]) -> str:
        """Determine risk level based on confidence and other factors"""
        try:
            # Base risk from confidence
            if confidence > 0.8:
                base_risk = "low"
            elif confidence > 0.5:
                base_risk = "medium"
            else:
                base_risk = "high"
            
            # Risk adjustments
            risk_adjustments = []
            
            # Data quality risk
            data_quality = features.get("data_quality", "medium")
            if data_quality == "low":
                risk_adjustments.append(1)  # Increase risk
            
            # Sample size risk
            form_features = features.get("form", {})
            if form_features.get("available"):
                team_a_matches = form_features.get("team_a", {}).get("matches_played", 0)
                team_b_matches = form_features.get("team_b", {}).get("matches_played", 0)
                min_matches = min(team_a_matches, team_b_matches)
                
                if min_matches < 3:
                    risk_adjustments.append(1)
            
            # Odds volatility risk
            odds_features = features.get("odds", {})
            if odds_features.get("available"):
                volatility = odds_features.get("volatility", "low")
                if volatility == "high":
                    risk_adjustments.append(1)
            
            # League risk
            league_features = features.get("league_specific", {})
            if league_features.get("available"):
                league = league_features.get("league")
                if league == "CS2":
                    risk_adjustments.append(0.5)  # Esports = higher volatility
            
            # Apply risk adjustments
            if risk_adjustments and sum(risk_adjustments) >= 2:
                if base_risk == "low":
                    return "medium"
                elif base_risk == "medium":
                    return "high"
            
            return base_risk
            
        except Exception as e:
            logger.error(f"Error determining risk level: {e}")
            return "medium"
    
    async def generate_explanation_factors(self, match: LeagueMatch, features: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate explanation factors for AI analysis"""
        try:
            positive_factors = []
            negative_factors = []
            
            # Form analysis
            form_features = features.get("form", {})
            if form_features.get("available"):
                form_diff = form_features.get("form_differential", {})
                advantage = form_diff.get("advantage", "balanced")
                
                if advantage != "balanced":
                    positive_factors.append(f"{advantage} shows better recent form")
                
                team_a_momentum = form_features.get("team_a", {}).get("momentum", 0)
                team_b_momentum = form_features.get("team_b", {}).get("momentum", 0)
                
                if abs(team_a_momentum) > 0.5:
                    positive_factors.append("Team A has strong positive momentum")
                if abs(team_b_momentum) > 0.5:
                    positive_factors.append("Team B has strong positive momentum")
                if team_a_momentum < -0.5:
                    negative_factors.append("Team A showing negative momentum")
                if team_b_momentum < -0.5:
                    negative_factors.append("Team B showing negative momentum")
            
            # Head-to-head analysis
            h2h_features = features.get("head_to_head", {})
            if h2h_features.get("available"):
                dominance = h2h_features.get("dominance", "competitive")
                total_matches = h2h_features.get("total_matches", 0)
                
                if dominance == "team_a_strong":
                    positive_factors.append(f"Team A dominates historically ({h2h_features.get('team_a_win_rate', 0):.1%} win rate)")
                elif dominance == "team_b_strong":
                    positive_factors.append(f"Team B dominates historically ({h2h_features.get('team_b_win_rate', 0):.1%} win rate)")
                elif dominance == "balanced":
                    positive_factors.append("Historically balanced matchup")
                
                if total_matches >= 10:
                    positive_factors.append("Strong historical sample size")
                elif total_matches < 3:
                    negative_factors.append("Limited historical data")
            
            # Odds analysis
            odds_features = features.get("odds", {})
            if odds_features.get("available"):
                volatility = odds_features.get("volatility", "low")
                avg_odds = odds_features.get("avg_odds", 2.0)
                
                if volatility == "low":
                    positive_factors.append("Stable odds across bookmakers")
                elif volatility == "high":
                    negative_factors.append("High odds volatility detected")
                
                if avg_odds > 3.0:
                    positive_factors.append("High odds indicate potential value")
                elif avg_odds < 1.7:
                    negative_factors.append("Low odds suggest limited value")
            
            # Situational factors
            situational_features = features.get("situational", {})
            if situational_features.get("available"):
                performance_factor = situational_features.get("performance_factor", "standard")
                urgency = situational_features.get("urgency", "normal")
                
                if performance_factor == "enhanced":
                    positive_factors.append("Optimal timing conditions")
                if urgency == "imminent":
                    positive_factors.append("Match starting soon - fresh data")
            
            # Data quality factors
            data_quality = features.get("data_quality", "medium")
            if data_quality == "high":
                positive_factors.append("High quality data sources")
            elif data_quality == "low":
                negative_factors.append("Limited data quality")
            
            return {
                "positive_factors": positive_factors[:5],  # Limit to top 5
                "negative_factors": negative_factors[:5]   # Limit to top 5
            }
            
        except Exception as e:
            logger.error(f"Error generating explanation factors: {e}")
            return {
                "positive_factors": ["Error generating analysis"],
                "negative_factors": [str(e)]
            }
    
    async def calculate_verdict(self, ai_score: AIScore, features: Dict[str, Any]) -> str:
        """Generate verdict based on AI score"""
        try:
            score = ai_score.ai_score
            confidence = ai_score.confidence
            risk = ai_score.risk_level
            
            # High confidence, low risk
            if confidence > 0.8 and risk == "low":
                if score > 0.7:
                    return "Strong analytical signal with high confidence"
                elif score > 0.5:
                    return "Moderate analytical signal with good confidence"
                else:
                    return "Weak analytical signal despite high confidence"
            
            # High confidence, medium risk
            elif confidence > 0.8 and risk == "medium":
                return "Moderate confidence with some risk factors"
            
            # Medium confidence
            elif confidence > 0.5:
                if risk == "low":
                    return "Decent analytical signal with moderate confidence"
                elif risk == "medium":
                    return "Cautious analytical recommendation"
                else:
                    return "High risk - limited analytical value"
            
            # Low confidence
            else:
                if risk == "high":
                    return "Insufficient data for reliable analysis"
                else:
                    return "Low confidence - limited predictive value"
            
        except Exception as e:
            logger.error(f"Error calculating verdict: {e}")
            return "Unable to generate reliable verdict"


# Global AI scoring engine
ai_scoring_engine = AIScoringEngine()
