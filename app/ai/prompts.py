"""
AIBET Analytics Platform - AI Prompts and Templates
"""

from typing import Dict, Any, List
from datetime import datetime


class AIPromptTemplates:
    """AI prompt templates for different analysis types"""
    
    def __init__(self):
        self.base_context = """
You are an AI sports analytics assistant for the AIBET platform.
Your role is to provide educational analysis of sports matches using statistical data.
You MUST NOT provide betting predictions or gambling advice.
All analysis should be marked as educational and not predictive.
"""
        
        self.analysis_prompts = {
            "pre_match": """
Analyze the upcoming match between {team_a} and {team_b} in {league}.

Context:
- Match ID: {match_id}
- Start Time: {start_time}
- Recent Form: {form_data}
- Head-to-Head: {h2h_data}
- Odds Analysis: {odds_data}
- Data Quality: {data_quality}

Provide analysis covering:
1. Team form comparison
2. Historical matchup patterns
3. Market odds assessment
4. Key influencing factors
5. Risk level assessment

IMPORTANT: This is educational analysis only, not a prediction.
""",
            
            "value_analysis": """
Evaluate the value proposition in {team_a} vs {team_b} ({league}) match.

Odds Context:
- Average Odds: {avg_odds}
- Odds Spread: {odds_spread}
- Market Volatility: {volatility}
- Sources: {sources_count}

Form Context:
- Team A Form: {team_a_form}
- Team B Form: {team_b_form}
- Form Differential: {form_advantage}

Value Assessment:
1. Identify market inefficiencies
2. Compare odds vs form indicators
3. Assess risk/reward ratio
4. Highlight value opportunities

IMPORTANT: This is educational market analysis, not investment advice.
""",
            
            "risk_assessment": """
Assess risk factors for {team_a} vs {team_b} ({league}) match.

Risk Factors:
- Data Quality: {data_quality}
- Sample Size: {sample_size}
- Market Volatility: {volatility}
- Confidence Level: {confidence}
- Historical Reliability: {h2h_reliability}

Risk Categories:
1. Data reliability risks
2. Market volatility risks
3. Sample size limitations
4. Model confidence risks

IMPORTANT: This risk assessment is for educational purposes only.
"""
        }
        
        self.response_templates = {
            "educational_disclaimer": """
⚠️ EDUCATIONAL PURPOSE ONLY ⚠️
This analysis is provided for informational and educational purposes only.
It is not betting advice, investment advice, or a prediction of outcomes.
Sports betting involves significant risk and should only be done responsibly.
Past performance does not guarantee future results.
""",
            
            "confidence_explanation": """
Confidence Level: {level} ({percentage}%)
- High: Multiple strong indicators align
- Medium: Some conflicting signals present
- Low: Limited data or high uncertainty
""",
            
            "value_explanation": """
Value Assessment: {level}
- High: Market may undervalue true probability
- Medium: Some potential inefficiency detected
- Low: Odds appear fairly priced
"""
        }
    
    def get_prompt(self, analysis_type: str, context: Dict[str, Any]) -> str:
        """Get formatted prompt for analysis type"""
        try:
            if analysis_type not in self.analysis_prompts:
                return self.analysis_prompts["pre_match"]
            
            prompt = self.analysis_prompts[analysis_type]
            
            # Format with context
            return prompt.format(**context)
            
        except Exception as e:
            return f"Error formatting prompt: {str(e)}"
    
    def format_response(self, response_type: str, data: Dict[str, Any]) -> str:
        """Format response with template"""
        try:
            if response_type not in self.response_templates:
                return str(data)
            
            template = self.response_templates[response_type]
            return template.format(**data)
            
        except Exception as e:
            return f"Error formatting response: {str(e)}"
    
    def get_analysis_summary_structure(self) -> Dict[str, Any]:
        """Get standard structure for analysis summaries"""
        return {
            "match_info": {
                "teams": "Team names and league",
                "timing": "Start time and status"
            },
            "form_analysis": {
                "recent_performance": "Last 5-10 matches",
                "momentum": "Current form trends",
                "comparison": "Team vs team comparison"
            },
            "historical_analysis": {
                "head_to_head": "Historical matchup data",
                "patterns": "Repeated trends in encounters"
            },
            "market_analysis": {
                "odds_assessment": "Current market pricing",
                "value_detection": "Potential inefficiencies",
                "volatility": "Odds movement and stability"
            },
            "risk_assessment": {
                "confidence_level": "Analysis confidence",
                "data_quality": "Source reliability",
                "limiting_factors": "Constraints and uncertainties"
            },
            "educational_note": {
                "disclaimer": "Educational purpose statement",
                "responsible_gambling": "Betting risk warning"
            }
        }


class AIConversationManager:
    """Manage AI conversation context and continuity"""
    
    def __init__(self):
        self.conversation_history = {}
        self.max_history_length = 10
    
    def add_to_history(self, session_id: str, user_input: str, ai_response: str):
        """Add interaction to conversation history"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": user_input,
            "ai_response": ai_response
        })
        
        # Trim history if too long
        if len(self.conversation_history[session_id]) > self.max_history_length:
            self.conversation_history[session_id] = self.conversation_history[session_id][-self.max_history_length:]
    
    def get_conversation_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation context for session"""
        return self.conversation_history.get(session_id, [])
    
    def clear_history(self, session_id: str):
        """Clear conversation history for session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
    
    def get_context_summary(self, session_id: str) -> str:
        """Get summary of conversation context"""
        history = self.get_conversation_context(session_id)
        
        if not history:
            return "No previous conversation"
        
        # Extract key topics
        topics = []
        for interaction in history[-3:]:  # Last 3 interactions
            user_input = interaction.get("user_input", "").lower()
            if "nhl" in user_input:
                topics.append("NHL analysis")
            elif "khl" in user_input:
                topics.append("KHL analysis")
            elif "cs2" in user_input:
                topics.append("CS2 analysis")
            elif "odds" in user_input:
                topics.append("Odds analysis")
            elif "value" in user_input:
                topics.append("Value assessment")
        
        if topics:
            return f"Previous topics: {', '.join(set(topics))}"
        
        return f"Previous interactions: {len(history)}"


class AIGuardrails:
    """AI response guardrails and safety"""
    
    def __init__(self):
        self.forbidden_patterns = [
            "bet on", "wager", "gamble", "stake",
            "guaranteed win", "sure thing", "lock",
            "prediction", "forecast", "will win",
            "insider information", "fixed match"
        ]
        
        self.required_disclaimers = [
            "educational purpose only",
            "not betting advice",
            "past performance not indicative",
            "responsible gambling"
        ]
    
    def validate_response(self, response: str) -> Dict[str, Any]:
        """Validate AI response for compliance"""
        validation = {
            "is_compliant": True,
            "violations": [],
            "missing_disclaimers": []
        }
        
        response_lower = response.lower()
        
        # Check for forbidden patterns
        for pattern in self.forbidden_patterns:
            if pattern in response_lower:
                validation["is_compliant"] = False
                validation["violations"].append(f"Contains forbidden pattern: {pattern}")
        
        # Check for required disclaimers
        for disclaimer in self.required_disclaimers:
            if disclaimer not in response_lower:
                validation["missing_disclaimers"].append(f"Missing disclaimer: {disclaimer}")
        
        # If violations or missing disclaimers, mark as non-compliant
        if validation["violations"] or validation["missing_disclaimers"]:
            validation["is_compliant"] = False
        
        return validation
    
    def sanitize_input(self, user_input: str) -> str:
        """Sanitize user input for safety"""
        # Remove potentially harmful instructions
        sanitized = user_input
        
        # Basic sanitization (in production, use more sophisticated methods)
        if "ignore previous instructions" in sanitized.lower():
            sanitized = "General sports analysis request"
        
        return sanitized


# Global instances
ai_prompt_templates = AIPromptTemplates()
ai_conversation_manager = AIConversationManager()
ai_guardrails = AIGuardrails()
