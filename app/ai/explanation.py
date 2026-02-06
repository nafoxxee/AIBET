"""
AIBET Analytics Platform - AI Explanation Generator
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from app.schemas import AIExplanation, LeagueMatch, AIScore
from app.ai.scoring import ai_scoring_engine
from app.logging import setup_logging

logger = setup_logging(__name__)


class AIExplanationGenerator:
    """Generate human-readable AI explanations"""
    
    def __init__(self):
        self.explanation_templates = {
            "high_confidence": {
                "opening": "Based on comprehensive analysis, I found strong indicators",
                "closing": "This analysis is supported by multiple data points"
            },
            "medium_confidence": {
                "opening": "My analysis suggests several factors to consider",
                "closing": "Consider these insights with normal caution"
            },
            "low_confidence": {
                "opening": "Limited data available, but here are some observations",
                "closing": "This analysis should be used for educational purposes only"
            },
            "value_detected": {
                "statement": "Market inefficiency detected",
                "explanation": "Current odds may not accurately reflect true probabilities"
            },
            "form_dominance": {
                "statement": "Recent performance shows clear advantage",
                "explanation": "One team demonstrates superior current form"
            },
            "historical_pattern": {
                "statement": "Historical matchup patterns identified",
                "explanation": "Previous encounters suggest predictable patterns"
            }
        }
    
    async def generate_explanation(self, match: LeagueMatch, features: Dict[str, Any], ai_score: AIScore) -> AIExplanation:
        """Generate comprehensive AI explanation"""
        try:
            # Generate explanation factors
            explanation_factors = await ai_scoring_engine.generate_explanation_factors(match, features)
            
            # Generate verdict
            verdict = await ai_scoring_engine.calculate_verdict(ai_score, features)
            
            # Build summary
            summary = await self._build_summary(match, features, ai_score, explanation_factors)
            
            # Create explanation
            explanation = AIExplanation(
                not_a_prediction=True,
                educational_purpose=True,
                global_match_id=match.global_match_id,
                summary=summary,
                positive_factors=explanation_factors["positive_factors"],
                negative_factors=explanation_factors["negative_factors"],
                verdict=verdict,
                ai_score=ai_score,
                explanation_timestamp=datetime.utcnow()
            )
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating AI explanation: {e}")
            return AIExplanation(
                not_a_prediction=True,
                educational_purpose=True,
                global_match_id=match.global_match_id,
                summary=f"Error generating explanation: {str(e)}",
                positive_factors=["Analysis error"],
                negative_factors=[str(e)],
                verdict="Unable to generate reliable analysis",
                ai_score=ai_score,
                explanation_timestamp=datetime.utcnow()
            )
    
    async def _build_summary(self, match: LeagueMatch, features: Dict[str, Any], ai_score: AIScore, factors: Dict[str, List[str]]) -> str:
        """Build explanation summary"""
        try:
            confidence = ai_score.confidence
            risk_level = ai_score.risk_level
            score = ai_score.ai_score
            
            # Start with confidence level
            if confidence > 0.8:
                summary = self.explanation_templates["high_confidence"]["opening"]
            elif confidence > 0.5:
                summary = self.explanation_templates["medium_confidence"]["opening"]
            else:
                summary = self.explanation_templates["low_confidence"]["opening"]
            
            # Add key insights
            key_insights = []
            
            # Form insights
            form_features = features.get("form", {})
            if form_features.get("available"):
                form_diff = form_features.get("form_differential", {})
                advantage = form_diff.get("advantage", "balanced")
                
                if advantage != "balanced":
                    key_insights.append(f"{advantage} shows better recent form")
            
            # H2H insights
            h2h_features = features.get("head_to_head", {})
            if h2h_features.get("available"):
                dominance = h2h_features.get("dominance", "competitive")
                if dominance in ["team_a_strong", "team_b_strong"]:
                    key_insights.append(f"Historical dominance detected")
            
            # Odds insights
            odds_features = features.get("odds", {})
            if odds_features.get("available"):
                volatility = odds_features.get("volatility", "low")
                avg_odds = odds_features.get("avg_odds", 2.0)
                
                if volatility == "low":
                    key_insights.append("Stable market pricing")
                elif avg_odds > 3.0:
                    key_insights.append("Potential market inefficiency")
            
            # Add insights to summary
            if key_insights:
                summary += ". Key factors: " + "; ".join(key_insights[:3])
            
            # Add risk assessment
            if risk_level == "low":
                summary += ". Risk level: Low - multiple confirming factors"
            elif risk_level == "medium":
                summary += ". Risk level: Medium - some conflicting signals"
            else:
                summary += ". Risk level: High - limited data or high volatility"
            
            # Add educational disclaimer
            summary += ". This is educational analysis - not a betting recommendation"
            
            # Add confidence closing
            if confidence > 0.8:
                summary += ". " + self.explanation_templates["high_confidence"]["closing"]
            elif confidence > 0.5:
                summary += ". " + self.explanation_templates["medium_confidence"]["closing"]
            else:
                summary += ". " + self.explanation_templates["low_confidence"]["closing"]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error building summary: {e}")
            return f"Error generating analysis summary: {str(e)}"
    
    async def format_explanation_for_display(self, explanation: AIExplanation) -> Dict[str, Any]:
        """Format explanation for different display formats"""
        try:
            formatted = {
                "summary": explanation.summary,
                "verdict": explanation.verdict,
                "confidence": explanation.ai_score.confidence,
                "risk_level": explanation.ai_score.risk_level,
                "ai_score": explanation.ai_score.ai_score,
                "factors": {
                    "positive": explanation.positive_factors,
                    "negative": explanation.negative_factors
                },
                "metadata": {
                    "global_match_id": explanation.global_match_id,
                    "explanation_timestamp": explanation.explanation_timestamp.isoformat(),
                    "not_a_prediction": explanation.not_a_prediction,
                    "educational_purpose": explanation.educational_purpose
                }
            }
            
            # Add display-specific formatting
            formatted["display"] = {
                "short_summary": self._create_short_summary(explanation),
                "risk_indicator": self._get_risk_indicator(explanation.ai_score.risk_level),
                "confidence_bar": self._get_confidence_bar(explanation.ai_score.confidence),
                "key_factors": self._highlight_key_factors(explanation)
            }
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting explanation: {e}")
            return {"error": str(e)}
    
    def _create_short_summary(self, explanation: AIExplanation) -> str:
        """Create short summary for quick display"""
        try:
            confidence = explanation.ai_score.confidence
            risk = explanation.ai_score.risk_level
            
            # Base summary
            if confidence > 0.8:
                base = "Strong analytical signal"
            elif confidence > 0.5:
                base = "Moderate analytical signal"
            else:
                base = "Weak analytical signal"
            
            # Add risk modifier
            if risk == "low":
                return f"{base} (Low Risk)"
            elif risk == "medium":
                return f"{base} (Medium Risk)"
            else:
                return f"{base} (High Risk)"
                
        except Exception as e:
            return "Analysis unavailable"
    
    def _get_risk_indicator(self, risk_level: str) -> Dict[str, Any]:
        """Get risk indicator for display"""
        indicators = {
            "low": {"color": "green", "icon": "✓", "level": 1},
            "medium": {"color": "yellow", "icon": "!", "level": 2},
            "high": {"color": "red", "icon": "⚠", "level": 3}
        }
        
        return indicators.get(risk_level, indicators["medium"])
    
    def _get_confidence_bar(self, confidence: float) -> Dict[str, Any]:
        """Get confidence bar for display"""
        return {
            "percentage": round(confidence * 100, 1),
            "fill_color": "green" if confidence > 0.7 else "yellow" if confidence > 0.4 else "red",
            "level": "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"
        }
    
    def _highlight_key_factors(self, explanation: AIExplanation) -> List[Dict[str, str]]:
        """Highlight most important factors"""
        try:
            # Combine and prioritize factors
            all_factors = explanation.positive_factors + explanation.negative_factors
            
            # Prioritize by importance (simplified)
            priority_keywords = [
                ("dominates", "strong", "high confidence"),
                ("value", "inefficiency", "opportunity"),
                ("momentum", "form", "recent"),
                ("historical", "head-to-head", "pattern")
            ]
            
            highlighted = []
            for factor in all_factors[:5]:  # Top 5 factors
                priority = "medium"
                for keywords, level in priority_keywords:
                    if any(keyword in factor.lower() for keyword in keywords):
                        priority = level
                        break
                
                highlighted.append({
                    "text": factor,
                    "priority": priority
                })
            
            return highlighted
            
        except Exception as e:
            return [{"text": "Error highlighting factors", "priority": "error"}]


# Global AI explanation generator
ai_explanation_generator = AIExplanationGenerator()
