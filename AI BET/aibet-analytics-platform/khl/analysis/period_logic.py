import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PeriodPattern:
    period: int
    pattern_type: str
    confidence: float
    description: str
    implications: List[str]


class KHLPeriodAnalyzer:
    """Analyze KHL period-specific patterns and logic"""
    
    def __init__(self):
        self.period_patterns = []
        self.period_statistics = {
            1: {'avg_goals': 1.8, 'scoring_frequency': 0.15},
            2: {'avg_goals': 2.1, 'scoring_frequency': 0.18},
            3: {'avg_goals': 2.3, 'scoring_frequency': 0.19}
        }
    
    def analyze_match_periods(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze period-by-period patterns for a match"""
        analysis = {
            'period_patterns': [],
            'period_predictions': {},
            'comeback_scenarios': [],
            'momentum_analysis': {},
            'recommendation': '',
            'confidence': 0.0
        }
        
        try:
            # Get match data
            live_data = match_data.get('live_data', {})
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            current_period = match_data.get('current_period', 1)
            
            # Analyze each period
            for period in [1, 2, 3]:
                pattern = self._analyze_period(match_data, period)
                if pattern:
                    analysis['period_patterns'].append(pattern)
            
            # Generate period predictions
            analysis['period_predictions'] = self._predict_period_outcomes(match_data)
            
            # Identify comeback scenarios
            analysis['comeback_scenarios'] = self._identify_comeback_scenarios(match_data)
            
            # Analyze momentum
            analysis['momentum_analysis'] = self._analyze_momentum(match_data)
            
            # Generate recommendation
            analysis['recommendation'] = self._generate_period_recommendation(analysis)
            analysis['confidence'] = self._calculate_period_confidence(analysis)
            
        except Exception as e:
            logger.warning(f"Error analyzing match periods: {e}")
        
        return analysis
    
    def _analyze_period(self, match_data: Dict[str, Any], period: int) -> Optional[PeriodPattern]:
        """Analyze specific period"""
        try:
            current_period = match_data.get('current_period', 1)
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            live_data = match_data.get('live_data', {})
            
            if period == 1:
                return self._analyze_first_period_patterns(match_data)
            elif period == 2:
                return self._analyze_second_period_patterns(match_data)
            elif period == 3:
                return self._analyze_third_period_patterns(match_data)
            
        except Exception as e:
            logger.warning(f"Error analyzing period {period}: {e}")
        
        return None
    
    def _analyze_first_period_patterns(self, match_data: Dict[str, Any]) -> PeriodPattern:
        """Analyze first period patterns"""
        try:
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            live_data = match_data.get('live_data', {})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            
            total_goals = score['team1'] + score['team2']
            shot_diff = shots['team1'] - shots['team2']
            
            # Determine pattern type
            if total_goals == 0 and shots['team1'] + shots['team2'] < 15:
                pattern_type = 'conservative_start'
                confidence = 0.7
                description = 'Both teams playing cautiously, low shot volume'
                implications = ['Expect second period to open up', 'Look for period 2 over bets']
            elif total_goals >= 3:
                pattern_type = 'explosive_start'
                confidence = 0.8
                description = 'High-scoring first period, defensive breakdowns'
                implications = ['Expect continued high scoring', 'Both teams may adjust defensively']
            elif abs(shot_diff) > 8:
                pattern_type = 'dominant_pressure'
                confidence = 0.6
                description = f'One team dominating shot differential ({shot_diff:+d})'
                implications = ['Pressure may convert soon', 'Watch for momentum shift']
            else:
                pattern_type = 'balanced_start'
                confidence = 0.5
                description = 'Evenly matched first period'
                implications = ['Match likely to remain competitive', 'Watch for special teams impact']
            
            return PeriodPattern(
                period=1,
                pattern_type=pattern_type,
                confidence=confidence,
                description=description,
                implications=implications
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing first period: {e}")
            return PeriodPattern(1, 'unknown', 0.0, 'Error analyzing', [])
    
    def _analyze_second_period_patterns(self, match_data: Dict[str, Any]) -> PeriodPattern:
        """Analyze second period patterns"""
        try:
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            live_data = match_data.get('live_data', {})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            
            total_goals = score['team1'] + score['team2']
            score_diff = abs(score['team1'] - score['team2'])
            
            # Determine pattern type
            if total_goals == 0:
                pattern_type = 'goalless_drought'
                confidence = 0.8
                description = 'No goals through first period, tension building'
                implications = ['High probability of goal in period 2', 'Teams may take more risks']
            elif score_diff >= 3:
                pattern_type = 'blowout_developing'
                confidence = 0.7
                description = f'Large score difference ({score_diff} goals)'
                implications = ['Leading team may conserve energy', 'Trailing team may press aggressively']
            elif total_goals >= 4:
                pattern_type = 'track_meet'
                confidence = 0.6
                description = 'High-scoring game developing'
                implications = ['Goalie performance may be factor', 'Special teams crucial']
            else:
                pattern_type = 'middle_game_adjustment'
                confidence = 0.5
                description = 'Teams making strategic adjustments'
                implications = ['Coaching adjustments key', 'Momentum shifts likely']
            
            return PeriodPattern(
                period=2,
                pattern_type=pattern_type,
                confidence=confidence,
                description=description,
                implications=implications
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing second period: {e}")
            return PeriodPattern(2, 'unknown', 0.0, 'Error analyzing', [])
    
    def _analyze_third_period_patterns(self, match_data: Dict[str, Any]) -> PeriodPattern:
        """Analyze third period patterns"""
        try:
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            score_diff = abs(score['team1'] - score['team2'])
            time_in_period = match_data.get('time_in_period', 0)
            
            # Determine pattern type
            if score_diff == 0:
                pattern_type = 'tight_finish'
                confidence = 0.8
                description = 'Scoreless game, playoff-like atmosphere'
                implications = ['Overtime probability high', 'Single mistake decisive']
            elif score_diff == 1:
                pattern_type = 'one_goal_game'
                confidence = 0.7
                description = 'One-goal game, maximum intensity'
                implications = ['Empty net strategy possible', 'Power play crucial']
            elif score_diff >= 4:
                pattern_type = 'garbage_time'
                confidence = 0.6
                description = 'Game decided, playing out the clock'
                implications = ['Lower intensity', 'Backup players may see time']
            elif time_in_period > 900 and score_diff <= 2:
                pattern_type = 'desperation_hockey'
                confidence = 0.8
                description = 'Late in close game, desperate measures'
                implications = ['Pull goalie possibility', 'High risk/reward plays']
            else:
                pattern_type = 'standard_finish'
                confidence = 0.5
                description = 'Normal third period progression'
                implications = ['Teams playing to situation', 'Clock management important']
            
            return PeriodPattern(
                period=3,
                pattern_type=pattern_type,
                confidence=confidence,
                description=description,
                implications=implications
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing third period: {e}")
            return PeriodPattern(3, 'unknown', 0.0, 'Error analyzing', [])
    
    def _predict_period_outcomes(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict outcomes for remaining periods"""
        predictions = {}
        
        try:
            current_period = match_data.get('current_period', 1)
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            live_data = match_data.get('live_data', {})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            
            # Predict for remaining periods
            for period in range(current_period, 4):
                period_stats = self.period_statistics.get(period, {'avg_goals': 2.0, 'scoring_frequency': 0.17})
                
                # Adjust predictions based on current game state
                base_goals = period_stats['avg_goals']
                
                # Adjust for fatigue (later periods = more goals)
                if period == 3:
                    base_goals *= 1.1
                
                # Adjust for shot pressure
                shot_pressure = (shots['team1'] + shots['team2']) / 40.0
                if shot_pressure > 1.2:
                    base_goals *= 1.15
                elif shot_pressure < 0.8:
                    base_goals *= 0.85
                
                # Adjust for score differential
                score_diff = abs(score['team1'] - score['team2'])
                if score_diff >= 3:
                    base_goals *= 0.9  # Teams may ease up
                
                predictions[f'period_{period}'] = {
                    'expected_goals': round(base_goals, 1),
                    'scoring_probability': period_stats['scoring_frequency'],
                    'overtime_probability': 0.15 if period == 3 and abs(score['team1'] - score['team2']) <= 1 else 0.05
                }
            
        except Exception as e:
            logger.warning(f"Error predicting period outcomes: {e}")
        
        return predictions
    
    def _identify_comeback_scenarios(self, match_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential comeback scenarios"""
        scenarios = []
        
        try:
            current_period = match_data.get('current_period', 1)
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            live_data = match_data.get('live_data', {})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            
            # Check for trailing team with pressure
            if score['team1'] > score['team2']:
                trailing_team = 'team2'
                leading_team = 'team1'
                score_diff = score['team1'] - score['team2']
            else:
                trailing_team = 'team1'
                leading_team = 'team2'
                score_diff = score['team2'] - score['team1']
            
            # Comeback scenario conditions
            if score_diff >= 2 and current_period >= 2:
                # Trailing team generating shots
                trailing_shots = shots[trailing_team]
                leading_shots = shots[leading_team]
                
                if trailing_shots > leading_shots + 5:
                    scenarios.append({
                        'type': 'pressure_comeback',
                        'team': trailing_team,
                        'confidence': 0.6,
                        'description': f'{trailing_team} generating pressure despite {score_diff} goal deficit',
                        'factors': [f'Shot advantage: {trailing_shots - leading_shots:+d}', f'Period: {current_period}']
                    })
            
            # Late game comeback
            if score_diff >= 1 and current_period == 3 and match_data.get('time_in_period', 0) > 900:
                scenarios.append({
                    'type': 'late_comeback',
                    'team': trailing_team,
                    'confidence': 0.4,
                    'description': f'Late game comeback potential for {trailing_team}',
                    'factors': ['Third period', 'Late in period', 'Desperation factor']
                })
            
        except Exception as e:
            logger.warning(f"Error identifying comeback scenarios: {e}")
        
        return scenarios
    
    def _analyze_momentum(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze game momentum"""
        momentum = {
            'team1_momentum': 0.5,
            'team2_momentum': 0.5,
            'momentum_shifts': [],
            'current_momentum': 'balanced'
        }
        
        try:
            live_data = match_data.get('live_data', {})
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            time_since_goal = live_data.get('time_since_last_goal', 0)
            
            # Calculate momentum based on shots and recent goals
            total_shots = shots['team1'] + shots['team2']
            if total_shots > 0:
                momentum['team1_momentum'] = shots['team1'] / total_shots
                momentum['team2_momentum'] = shots['team2'] / total_shots
            
            # Adjust for scoring
            if score['team1'] > score['team2']:
                momentum['team1_momentum'] += 0.1
            elif score['team2'] > score['team1']:
                momentum['team2_momentum'] += 0.1
            
            # Adjust for recent goal
            if time_since_goal < 120:  # Recent goal
                goal_scorers = live_data.get('goal_scorers', [])
                if goal_scorers:
                    last_scorer = goal_scorers[-1].get('team', '')
                    if last_scorer == 'team1':
                        momentum['team1_momentum'] += 0.15
                    else:
                        momentum['team2_momentum'] += 0.15
            
            # Normalize momentum
            total_momentum = momentum['team1_momentum'] + momentum['team2_momentum']
            if total_momentum > 0:
                momentum['team1_momentum'] /= total_momentum
                momentum['team2_momentum'] /= total_momentum
            
            # Determine current momentum
            if abs(momentum['team1_momentum'] - momentum['team2_momentum']) > 0.15:
                momentum['current_momentum'] = 'team1' if momentum['team1_momentum'] > momentum['team2_momentum'] else 'team2'
            else:
                momentum['current_momentum'] = 'balanced'
            
        except Exception as e:
            logger.warning(f"Error analyzing momentum: {e}")
        
        return momentum
    
    def _generate_period_recommendation(self, analysis: Dict[str, Any]) -> str:
        """Generate recommendation based on period analysis"""
        try:
            patterns = analysis.get('period_patterns', [])
            comebacks = analysis.get('comeback_scenarios', [])
            momentum = analysis.get('momentum_analysis', {})
            
            # Priority scenarios
            if comebacks:
                top_comeback = max(comebacks, key=lambda x: x.get('confidence', 0))
                return f"Watch for {top_comeback['team']} comeback scenario ({top_comeback['confidence']:.1%} confidence)"
            
            if patterns:
                high_confidence_patterns = [p for p in patterns if p.confidence >= 0.7]
                if high_confidence_patterns:
                    pattern = high_confidence_patterns[0]
                    return f"Strong {pattern.pattern_type} pattern detected in period {pattern.period}"
            
            current_momentum = momentum.get('current_momentum', 'balanced')
            if current_momentum != 'balanced':
                return f"Momentum favors {current_momentum}, expect continued pressure"
            
            return "Game developing normally, monitor for special teams impact"
            
        except Exception as e:
            logger.warning(f"Error generating period recommendation: {e}")
            return "Unable to generate period recommendation"
    
    def _calculate_period_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence in period analysis"""
        try:
            confidence_factors = []
            
            # Pattern confidence
            patterns = analysis.get('period_patterns', [])
            if patterns:
                avg_pattern_confidence = sum(p.confidence for p in patterns) / len(patterns)
                confidence_factors.append(avg_pattern_confidence)
            
            # Comeback scenario confidence
            comebacks = analysis.get('comeback_scenarios', [])
            if comebacks:
                max_comeback_confidence = max(c.get('confidence', 0) for c in comebacks)
                confidence_factors.append(max_comeback_confidence)
            
            # Momentum clarity
            momentum = analysis.get('momentum_analysis', {})
            current_momentum = momentum.get('current_momentum', 'balanced')
            if current_momentum != 'balanced':
                confidence_factors.append(0.7)
            
            if confidence_factors:
                return sum(confidence_factors) / len(confidence_factors)
            
            return 0.5
            
        except Exception as e:
            logger.warning(f"Error calculating period confidence: {e}")
            return 0.0


async def analyze_khl_periods(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze period patterns for KHL matches"""
    analyzer = KHLPeriodAnalyzer()
    analyzed_matches = []
    
    for match in matches:
        if match.get('status') == 'live':
            period_analysis = analyzer.analyze_match_periods(match)
            match['period_analysis'] = period_analysis
            analyzed_matches.append(match)
    
    return analyzed_matches


async def khl_period_analysis_task():
    """KHL period analysis task"""
    logger.info("Starting KHL period analysis")
    
    try:
        # Get live matches
        from storage.database import get_live_khl_matches
        matches = await get_live_khl_matches()
        
        if matches:
            analyzed_matches = await analyze_khl_periods(matches)
            
            # Store analysis results
            from storage.database import store_khl_period_analysis
            await store_khl_period_analysis(analyzed_matches)
            
            # Check for high-confidence scenarios
            high_confidence_matches = [
                m for m in analyzed_matches 
                if m.get('period_analysis', {}).get('confidence', 0) >= 0.7
            ]
            
            if high_confidence_matches:
                from app.main import telegram_sender
                for match in high_confidence_matches[:2]:  # Top 2 matches
                    period = match['period_analysis']
                    await telegram_sender.send_khl_analysis({
                        'match': match,
                        'scenarios': [{
                            'name': 'Period Pattern Analysis',
                            'confidence': period['confidence'],
                            'description': period['recommendation'],
                            'factors': [p.description for p in period.get('period_patterns', [])[:2]],
                            'recommendation': period['recommendation']
                        }],
                        'recommendation': {
                            'text': period['recommendation'],
                            'confidence': period['confidence']
                        }
                    })
            
            logger.info(f"Period analysis completed for {len(matches)} matches")
        
    except Exception as e:
        logger.error(f"KHL period analysis task failed: {e}")


def setup_khl_period_tasks(scheduler):
    """Setup KHL period analysis tasks"""
    scheduler.add_task('khl_period_analysis', khl_period_analysis_task, 180)  # Every 3 minutes
    logger.info("KHL period analysis tasks setup complete")
