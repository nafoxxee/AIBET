import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics

logger = logging.getLogger(__name__)


class PublicBiasAnalyzer:
    """Analyze public betting bias and sentiment"""
    
    def __init__(self):
        self.historical_bias_data = []
        self.bias_thresholds = {
            'heavy_bias': 75.0,  # >75% on one team
            'extreme_bias': 85.0,  # >85% on one team
            'moderate_bias': 65.0  # >65% on one team
        }
    
    def analyze_public_bias(self, odds_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze public betting bias for a match"""
        analysis = {
            'bias_level': 'none',
            'bias_direction': '',
            'bias_strength': 0.0,
            'contrarian_signal': False,
            'market_efficiency': 0.0,
            'recommendation': '',
            'confidence': 0.0
        }
        
        try:
            public_money = odds_data.get('public_money', {})
            bookmakers = odds_data.get('bookmakers', [])
            movement_history = odds_data.get('movement_history', [])
            
            if not public_money:
                return analysis
            
            # Calculate bias percentages
            team1_pct = public_money.get('team1_percentage', 0)
            team2_pct = public_money.get('team2_percentage', 0)
            
            # Determine bias level and direction
            max_pct = max(team1_pct, team2_pct)
            
            if max_pct >= self.bias_thresholds['extreme_bias']:
                analysis['bias_level'] = 'extreme'
                analysis['bias_strength'] = min(1.0, (max_pct - 85) / 15)
            elif max_pct >= self.bias_thresholds['heavy_bias']:
                analysis['bias_level'] = 'heavy'
                analysis['bias_strength'] = min(1.0, (max_pct - 75) / 20)
            elif max_pct >= self.bias_thresholds['moderate_bias']:
                analysis['bias_level'] = 'moderate'
                analysis['bias_strength'] = min(1.0, (max_pct - 65) / 20)
            
            # Determine bias direction
            if team1_pct > team2_pct:
                analysis['bias_direction'] = 'team1'
            elif team2_pct > team1_pct:
                analysis['bias_direction'] = 'team2'
            
            # Check for contrarian signals
            analysis['contrarian_signal'] = self._detect_contrarian_signal(
                odds_data, analysis['bias_level']
            )
            
            # Calculate market efficiency
            analysis['market_efficiency'] = self._calculate_market_efficiency(
                bookmakers, movement_history
            )
            
            # Generate recommendation
            analysis['recommendation'] = self._generate_bias_recommendation(analysis)
            analysis['confidence'] = self._calculate_bias_confidence(analysis)
            
        except Exception as e:
            logger.warning(f"Error analyzing public bias: {e}")
        
        return analysis
    
    def _detect_contrarian_signal(self, odds_data: Dict, bias_level: str) -> bool:
        """Detect contrarian betting signals"""
        try:
            movement_history = odds_data.get('movement_history', [])
            avg_odds = odds_data.get('average_odds', {})
            
            if bias_level in ['heavy', 'extreme']:
                # Check if odds are moving against public money
                if len(movement_history) >= 2:
                    recent_odds = movement_history[-1]
                    previous_odds = movement_history[-2]
                    
                    # If public is heavy on team1 but team1 odds are increasing
                    if odds_data.get('public_money', {}).get('team1_percentage', 0) > 75:
                        team1_odds_change = recent_odds.get('team1_odds', 0) - previous_odds.get('team1_odds', 0)
                        return team1_odds_change > 0.02  # Odds drifting higher
            
            return False
            
        except Exception as e:
            logger.warning(f"Error detecting contrarian signal: {e}")
            return False
    
    def _calculate_market_efficiency(self, bookmakers: List[Dict], movement_history: List[Dict]) -> float:
        """Calculate market efficiency based on bookmaker diversity and odds stability"""
        try:
            # More bookmakers = more efficient market
            bookmaker_factor = min(len(bookmakers) / 5.0, 1.0)
            
            # Stable odds = efficient market
            stability_factor = 1.0
            if len(movement_history) >= 2:
                recent_odds = movement_history[-1]
                previous_odds = movement_history[-2]
                
                team1_change = abs(recent_odds.get('team1_odds', 0) - previous_odds.get('team1_odds', 0))
                team2_change = abs(recent_odds.get('team2_odds', 0) - previous_odds.get('team2_odds', 0))
                
                avg_change = (team1_change + team2_change) / 2
                stability_factor = max(0.2, 1.0 - (avg_change * 10))  # Less change = more stable
            
            return (bookmaker_factor + stability_factor) / 2
            
        except Exception as e:
            logger.warning(f"Error calculating market efficiency: {e}")
            return 0.5
    
    def _generate_bias_recommendation(self, analysis: Dict) -> str:
        """Generate recommendation based on bias analysis"""
        bias_level = analysis['bias_level']
        contrarian = analysis['contrarian_signal']
        efficiency = analysis['market_efficiency']
        
        if bias_level == 'extreme':
            if contrarian and efficiency > 0.6:
                return "STRONG contrarian play against public"
            else:
                return "AVOID - Extreme public bias with no contrarian signals"
        
        elif bias_level == 'heavy':
            if contrarian:
                return "Consider contrarian play against public"
            else:
                return "CAUTION - Heavy public bias, monitor for signals"
        
        elif bias_level == 'moderate':
            return "Monitor for developing bias patterns"
        
        else:
            return "No significant bias detected"
    
    def _calculate_bias_confidence(self, analysis: Dict) -> float:
        """Calculate confidence in bias analysis"""
        try:
            base_confidence = analysis['bias_strength']
            
            # Adjust for market efficiency
            efficiency_bonus = analysis['market_efficiency'] * 0.2
            
            # Adjust for contrarian signals
            contrarian_bonus = 0.15 if analysis['contrarian_signal'] else 0
            
            confidence = base_confidence + efficiency_bonus + contrarian_bonus
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating bias confidence: {e}")
            return 0.0
    
    def analyze_historical_bias_performance(self, historical_matches: List[Dict]) -> Dict[str, Any]:
        """Analyze historical performance of bias-based predictions"""
        performance = {
            'total_matches': len(historical_matches),
            'bias_accuracy': {},
            'roi_by_bias_level': {},
            'best_contrarian_scenarios': []
        }
        
        try:
            bias_results = {'none': [], 'moderate': [], 'heavy': [], 'extreme': []}
            
            for match in historical_matches:
                bias_analysis = match.get('bias_analysis', {})
                bias_level = bias_analysis.get('bias_level', 'none')
                result = match.get('result', {})  # Actual match result
                
                if bias_level in bias_results:
                    bias_results[bias_level].append({
                        'predicted': bias_analysis.get('recommendation', ''),
                        'actual': result.get('winner', ''),
                        'odds': match.get('odds', {}).get('average_odds', {})
                    })
            
            # Calculate accuracy for each bias level
            for bias_level, results in bias_results.items():
                if results:
                    correct = sum(1 for r in results if self._was_prediction_correct(r))
                    accuracy = correct / len(results)
                    performance['bias_accuracy'][bias_level] = accuracy
            
        except Exception as e:
            logger.warning(f"Error analyzing historical bias performance: {e}")
        
        return performance
    
    def _was_prediction_correct(self, prediction_data: Dict) -> bool:
        """Check if bias prediction was correct"""
        try:
            predicted = prediction_data.get('predicted', '')
            actual = prediction_data.get('actual', '')
            
            # Simplified correctness check
            if 'against public' in predicted.lower():
                # If predicted against public, check if underdog won
                return actual != 'favorite'  # Simplified
            
            return actual == 'favorite'  # Simplified
            
        except Exception:
            return False


async def analyze_cs2_public_bias(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze public bias for CS2 matches"""
    analyzer = PublicBiasAnalyzer()
    analyzed_matches = []
    
    for match in matches:
        if 'odds' in match:
            bias_analysis = analyzer.analyze_public_bias(match['odds'])
            match['bias_analysis'] = bias_analysis
            analyzed_matches.append(match)
    
    return analyzed_matches


async def cs2_bias_analysis_task():
    """CS2 public bias analysis task"""
    logger.info("Starting CS2 public bias analysis")
    
    try:
        # Get matches with odds data
        from storage.database import get_cs2_matches_with_odds
        matches = await get_cs2_matches_with_odds()
        
        if matches:
            analyzed_matches = await analyze_cs2_public_bias(matches)
            
            # Store analysis results
            from storage.database import store_cs2_bias_analysis
            await store_cs2_bias_analysis(analyzed_matches)
            
            # Check for strong bias signals
            strong_bias_matches = [
                m for m in analyzed_matches 
                if m.get('bias_analysis', {}).get('bias_level') in ['heavy', 'extreme']
            ]
            
            if strong_bias_matches:
                from app.main import telegram_sender
                for match in strong_bias_matches[:2]:  # Top 2 matches
                    bias = match['bias_analysis']
                    await telegram_sender.send_cs2_analysis({
                        'match': match,
                        'scenarios': [{
                            'name': f"Public Bias: {bias['bias_level'].title()}",
                            'confidence': bias['confidence'],
                            'description': f"Public bias {bias['bias_level']} on {bias['bias_direction']}",
                            'factors': [f"Bias strength: {bias['bias_strength']:.1%}"],
                            'recommendation': bias['recommendation']
                        }],
                        'recommendation': {
                            'text': bias['recommendation'],
                            'confidence': bias['confidence']
                        }
                    })
            
            logger.info(f"Public bias analysis completed for {len(matches)} matches")
        
    except Exception as e:
        logger.error(f"CS2 bias analysis task failed: {e}")


def setup_cs2_bias_tasks(scheduler):
    """Setup CS2 bias analysis tasks"""
    scheduler.add_task('cs2_bias_analysis', cs2_bias_analysis_task, 600)  # Every 10 minutes
    logger.info("CS2 bias analysis tasks setup complete")
