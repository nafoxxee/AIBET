import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class KHLScenario:
    name: str
    confidence: float
    description: str
    factors: List[str]
    recommendation: str
    scenario_type: str  # 'period', 'pressure', 'comeback', 'late_game'


class KHLScenarioDetector:
    """Detect KHL betting market scenarios"""
    
    def __init__(self):
        self.scenarios = []
        self.period_thresholds = {
            'first_period_scoreless': 0.8,
            'favorite_lost_first': 0.7,
            'pressure_without_conversion': 0.6,
            'comeback_probability': 0.5,
            'late_goal_scenario': 0.6
        }
    
    def analyze_match(self, match_data: Dict[str, Any]) -> List[KHLScenario]:
        """Analyze match and detect KHL-specific scenarios"""
        scenarios = []
        
        try:
            # Get match data
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            current_period = match_data.get('current_period', 1)
            live_data = match_data.get('live_data', {})
            odds_data = match_data.get('odds', {})
            
            # Detect period-specific scenarios
            scenarios.extend(self._detect_period_scenarios(match_data))
            
            # Detect pressure scenarios
            scenarios.extend(self._detect_pressure_scenarios(match_data))
            
            # Detect comeback scenarios
            scenarios.extend(self._detect_comeback_scenarios(match_data))
            
            # Detect late game scenarios
            scenarios.extend(self._detect_late_game_scenarios(match_data))
            
            # Detect odds-based scenarios
            scenarios.extend(self._detect_odds_scenarios(match_data))
            
            # Sort by confidence
            scenarios.sort(key=lambda x: x.confidence, reverse=True)
            
        except Exception as e:
            logger.warning(f"Error analyzing KHL match scenarios: {e}")
        
        return scenarios[:5]  # Return top 5 scenarios
    
    def _detect_period_scenarios(self, match_data: Dict[str, Any]) -> List[KHLScenario]:
        """Detect period-specific scenarios"""
        scenarios = []
        
        try:
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            current_period = match_data.get('current_period', 1)
            time_in_period = match_data.get('time_in_period', 0)
            
            # 0:0 after first period
            if current_period >= 2 and score['team1'] == 0 and score['team2'] == 0:
                confidence = self.period_thresholds['first_period_scoreless']
                
                scenario = KHLScenario(
                    name="0:0 After First Period",
                    confidence=confidence,
                    description="Scoreless after first period indicates defensive battle",
                    factors=[
                        "Strong defensive positioning",
                        "Conservative coaching approach",
                        "Potential for opening up in later periods"
                    ],
                    recommendation="Consider live betting on goals in period 2",
                    scenario_type="period"
                )
                scenarios.append(scenario)
            
            # Favorite lost first period
            odds_data = match_data.get('odds', {})
            analysis = odds_data.get('analysis', {})
            favorite_team = analysis.get('favorite_team', '')
            
            if current_period >= 2 and favorite_team:
                if (favorite_team == 'team1' and score['team1'] < score['team2']) or \
                   (favorite_team == 'team2' and score['team2'] < score['team1']):
                    
                    confidence = self.period_thresholds['favorite_lost_first']
                    
                    scenario = KHLScenario(
                        name="Favorite Lost First Period",
                        confidence=confidence,
                        description=f"Pre-match favorite {favorite_team} lost first period",
                        factors=[
                            f"{favorite_team} trailing after period 1",
                            "Potential for tactical adjustments",
                            "Favorite likely to increase pressure"
                        ],
                        recommendation=f"Watch for {favorite_team} comeback in period 2",
                        scenario_type="period"
                    )
                    scenarios.append(scenario)
            
        except Exception as e:
            logger.warning(f"Error detecting period scenarios: {e}")
        
        return scenarios
    
    def _detect_pressure_scenarios(self, match_data: Dict[str, Any]) -> List[KHLScenario]:
        """Detect pressure-based scenarios"""
        scenarios = []
        
        try:
            live_data = match_data.get('live_data', {})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            
            # Pressure without conversion
            total_shots = shots['team1'] + shots['team2']
            total_goals = score['team1'] + score['team2']
            
            if total_shots > 30 and total_goals <= 1:
                # High shot volume but low scoring
                shot_efficiency = total_goals / total_shots if total_shots > 0 else 0
                
                if shot_efficiency < 0.05:  # Less than 5% conversion
                    confidence = self.period_thresholds['pressure_without_conversion']
                    
                    # Determine which team has more pressure
                    pressuring_team = 'team1' if shots['team1'] > shots['team2'] else 'team2'
                    shot_advantage = abs(shots['team1'] - shots['team2'])
                    
                    scenario = KHLScenario(
                        name="Pressure Without Conversion",
                        confidence=confidence,
                        description=f"High shot volume ({total_shots}) but low scoring ({total_goals} goals)",
                        factors=[
                            f"Shot advantage: {pressuring_team} (+{shot_advantage})",
                            "Strong goaltending performance",
                            "Potential for breakthrough goal"
                        ],
                        recommendation=f"Watch for {pressuring_team} to break through",
                        scenario_type="pressure"
                    )
                    scenarios.append(scenario)
            
        except Exception as e:
            logger.warning(f"Error detecting pressure scenarios: {e}")
        
        return scenarios
    
    def _detect_comeback_scenarios(self, match_data: Dict[str, Any]) -> List[KHLScenario]:
        """Detect comeback scenarios"""
        scenarios = []
        
        try:
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            current_period = match_data.get('current_period', 1)
            time_in_period = match_data.get('time_in_period', 0)
            live_data = match_data.get('live_data', {})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            
            # Determine comeback potential
            score_diff = abs(score['team1'] - score['team2'])
            
            if score_diff >= 2 and current_period >= 2:
                # Identify trailing and leading teams
                if score['team1'] > score['team2']:
                    trailing_team = 'team2'
                    leading_team = 'team1'
                else:
                    trailing_team = 'team1'
                    leading_team = 'team2'
                
                # Check if trailing team is generating pressure
                trailing_shots = shots[trailing_team]
                leading_shots = shots[leading_team]
                
                if trailing_shots > leading_shots + 6:
                    # Significant shot advantage for trailing team
                    shot_pressure_ratio = trailing_shots / leading_shots if leading_shots > 0 else 2.0
                    
                    # Calculate comeback probability
                    base_prob = 0.3
                    pressure_bonus = min(0.3, (shot_pressure_ratio - 1) * 0.2)
                    time_bonus = 0.1 if current_period == 3 else 0.05
                    
                    comeback_prob = base_prob + pressure_bonus + time_bonus
                    confidence = min(0.8, comeback_prob)
                    
                    scenario = KHLScenario(
                        name="Comeback Probability",
                        confidence=confidence,
                        description=f"{trailing_team} generating pressure despite {score_diff} goal deficit",
                        factors=[
                            f"Shot advantage: {trailing_team} (+{trailing_shots - leading_shots})",
                            f"Period: {current_period}, Time: {time_in_period}s",
                            "Momentum shifting to trailing team"
                        ],
                        recommendation=f"Watch {trailing_team} comeback attempt",
                        scenario_type="comeback"
                    )
                    scenarios.append(scenario)
            
        except Exception as e:
            logger.warning(f"Error detecting comeback scenarios: {e}")
        
        return scenarios
    
    def _detect_late_game_scenarios(self, match_data: Dict[str, Any]) -> List[KHLScenario]:
        """Detect late game scenarios"""
        scenarios = []
        
        try:
            current_period = match_data.get('current_period', 1)
            time_in_period = match_data.get('time_in_period', 0)
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            
            # Late goal scenario (last 5 minutes of third period)
            if current_period == 3 and time_in_period > 900:
                score_diff = abs(score['team1'] - score['team2'])
                
                if score_diff <= 1:  # Close game
                    confidence = self.period_thresholds['late_goal_scenario']
                    
                    # Determine if teams are playing cautiously or aggressively
                    live_data = match_data.get('live_data', {})
                    shots = live_data.get('shots', {'team1': 0, 'team2': 0})
                    total_shots = shots['team1'] + shots['team2']
                    
                    if total_shots < 20:  # Low shot volume
                        game_style = "cautious"
                        factors = [
                            "Low shot volume indicates cautious play",
                            "Teams playing for overtime possibility",
                            "Single mistake could be decisive"
                        ]
                    else:
                        game_style = "aggressive"
                        factors = [
                            "High shot volume indicates aggressive play",
                            "Teams pushing for late winner",
                            "Potential for empty net situation"
                        ]
                    
                    scenario = KHLScenario(
                        name="Late Goal Scenario",
                        confidence=confidence,
                        description=f"Close game in final minutes ({score_diff} goal difference)",
                        factors=factors,
                        recommendation=f"Watch for {game_style} late game developments",
                        scenario_type="late_game"
                    )
                    scenarios.append(scenario)
            
        except Exception as e:
            logger.warning(f"Error detecting late game scenarios: {e}")
        
        return scenarios
    
    def _detect_odds_scenarios(self, match_data: Dict[str, Any]) -> List[KHLScenario]:
        """Detect odds-based scenarios"""
        scenarios = []
        
        try:
            odds_data = match_data.get('odds', {})
            analysis = odds_data.get('analysis', {})
            movement_history = odds_data.get('movement_history', [])
            
            # Odds movement against public sentiment
            if len(movement_history) >= 2:
                recent_movement = movement_history[-1]['team1_odds'] - movement_history[-2]['team1_odds']
                
                if abs(recent_movement) > 0.03:  # Significant movement
                    movement_direction = 'team1_drifting' if recent_movement > 0 else 'team1_strengthening'
                    
                    confidence = min(0.7, abs(recent_movement) * 10)
                    
                    scenario = KHLScenario(
                        name="Significant Odds Movement",
                        confidence=confidence,
                        description=f"Odds {movement_direction.replace('_', ' ')}",
                        factors=[
                            f"Odds movement: {recent_movement:+.3f}",
                            "Market reacting to new information",
                            "Potential value opportunity"
                        ],
                        recommendation="Monitor for continued odds movement",
                        scenario_type="odds"
                    )
                    scenarios.append(scenario)
            
            # Close match odds
            avg_odds = odds_data.get('average_odds', {})
            team1_odds = avg_odds.get('team1', 0)
            team2_odds = avg_odds.get('team2', 0)
            
            if team1_odds > 0 and team2_odds > 0:
                odds_diff = abs(team1_odds - team2_odds)
                
                if odds_diff < 0.1:  # Very close odds
                    scenario = KHLScenario(
                        name="Evenly Matched Contest",
                        confidence=0.6,
                        description="Bookmakers see this as a very close match",
                        factors=[
                            f"Odds difference: {odds_diff:.3f}",
                            "No clear favorite",
                            "High probability of close game"
                        ],
                        recommendation="Consider overtime or shootout markets",
                        scenario_type="odds"
                    )
                    scenarios.append(scenario)
            
        except Exception as e:
            logger.warning(f"Error detecting odds scenarios: {e}")
        
        return scenarios


async def analyze_khl_matches(matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Analyze KHL matches for scenarios"""
    if not matches:
        return None
    
    detector = KHLScenarioDetector()
    all_scenarios = []
    
    for match in matches:
        scenarios = detector.analyze_match(match)
        for scenario in scenarios:
            scenario.match_id = match.get('match_id', '')
            all_scenarios.append(scenario)
    
    if all_scenarios:
        # Get best scenario
        best_scenario = max(all_scenarios, key=lambda x: x.confidence)
        
        # Find the match for this scenario
        best_match = None
        for match in matches:
            if match.get('match_id') == best_scenario.match_id:
                best_match = match
                break
        
        if best_match:
            return {
                'match': best_match,
                'scenarios': [
                    {
                        'name': s.name,
                        'confidence': s.confidence,
                        'description': s.description,
                        'factors': s.factors,
                        'recommendation': s.recommendation,
                        'type': s.scenario_type
                    } for s in all_scenarios[:3]
                ],
                'recommendation': {
                    'text': best_scenario.recommendation,
                    'confidence': best_scenario.confidence
                },
                'analysis_time': datetime.now().isoformat()
            }
    
    return None


async def khl_analysis_task():
    """KHL analysis task for scheduler"""
    logger.info("Starting KHL scenario analysis")
    
    try:
        # Get matches with odds from database
        from storage.database import get_khl_matches_with_odds
        matches = await get_khl_matches_with_odds()
        
        if matches:
            analysis_result = await analyze_khl_matches(matches)
            
            if analysis_result:
                # Send to Telegram
                from app.main import telegram_sender
                await telegram_sender.send_khl_analysis(analysis_result)
                
                logger.info(f"KHL analysis completed. Found {len(analysis_result['scenarios'])} scenarios")
            else:
                logger.info("KHL analysis completed. No scenarios detected")
        
    except Exception as e:
        logger.error(f"KHL analysis task failed: {e}")


def setup_khl_analysis_tasks(scheduler):
    """Setup KHL analysis tasks in scheduler"""
    scheduler.add_task('khl_analysis', khl_analysis_task, 180)  # Every 3 minutes
    logger.info("KHL analysis tasks setup complete")
