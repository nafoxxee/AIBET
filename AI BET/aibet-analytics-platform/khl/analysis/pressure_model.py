import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PressureEvent:
    team: str
    pressure_type: str
    intensity: float
    duration: int  # seconds
    timestamp: datetime
    outcome: str  # 'goal', 'save', 'miss', 'penalty'


class KHLPressureModel:
    """Analyze pressure patterns in KHL matches"""
    
    def __init__(self):
        self.pressure_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
        self.pressure_events = []
        self.pressure_zones = {
            'offensive_zone': 1.0,
            'neutral_zone': 0.5,
            'defensive_zone': 0.2
        }
    
    def analyze_match_pressure(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pressure patterns throughout the match"""
        analysis = {
            'team1_pressure_profile': {},
            'team2_pressure_profile': {},
            'pressure_battles': [],
            'critical_pressure_moments': [],
            'pressure_efficiency': {},
            'comeback_pressure': {},
            'recommendation': '',
            'confidence': 0.0
        }
        
        try:
            # Get match data
            live_data = match_data.get('live_data', {})
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            current_period = match_data.get('current_period', 1)
            time_in_period = match_data.get('time_in_period', 0)
            
            # Analyze team pressure profiles
            analysis['team1_pressure_profile'] = self._analyze_team_pressure(match_data, 'team1')
            analysis['team2_pressure_profile'] = self._analyze_team_pressure(match_data, 'team2')
            
            # Identify pressure battles
            analysis['pressure_battles'] = self._identify_pressure_battles(match_data)
            
            # Find critical pressure moments
            analysis['critical_pressure_moments'] = self._find_critical_pressure_moments(match_data)
            
            # Calculate pressure efficiency
            analysis['pressure_efficiency'] = self._calculate_pressure_efficiency(match_data)
            
            # Analyze comeback pressure
            analysis['comeback_pressure'] = self._analyze_comeback_pressure(match_data)
            
            # Generate recommendation
            analysis['recommendation'] = self._generate_pressure_recommendation(analysis)
            analysis['confidence'] = self._calculate_pressure_confidence(analysis)
            
        except Exception as e:
            logger.warning(f"Error analyzing match pressure: {e}")
        
        return analysis
    
    def _analyze_team_pressure(self, match_data: Dict[str, Any], team: str) -> Dict[str, Any]:
        """Analyze pressure profile for a specific team"""
        profile = {
            'overall_pressure': 0.0,
            'pressure_by_period': {},
            'shot_pressure': 0.0,
            'score_pressure': 0.0,
            'time_pressure': 0.0,
            'power_play_pressure': 0.0,
            'pressure_consistency': 0.0,
            'pressure_peaks': []
        }
        
        try:
            live_data = match_data.get('live_data', {})
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            current_period = match_data.get('current_period', 1)
            time_in_period = match_data.get('time_in_period', 0)
            
            # Calculate shot pressure
            total_shots = shots['team1'] + shots['team2']
            if total_shots > 0:
                profile['shot_pressure'] = shots[team] / total_shots
            
            # Calculate score pressure
            if team == 'team1':
                score_diff = score['team1'] - score['team2']
            else:
                score_diff = score['team2'] - score['team1']
            
            if score_diff > 0:
                profile['score_pressure'] = min(0.8, 0.5 + score_diff * 0.1)
            elif score_diff < 0:
                profile['score_pressure'] = max(0.2, 0.5 + score_diff * 0.1)
            else:
                profile['score_pressure'] = 0.5
            
            # Calculate time pressure
            if current_period == 3:
                time_pressure_factor = time_in_period / 1200.0  # Normalize to period length
                profile['time_pressure'] = min(0.9, time_pressure_factor * 1.2)
            else:
                profile['time_pressure'] = 0.3
            
            # Calculate power play pressure
            power_play = live_data.get('power_play', {})
            if power_play and power_play.get('team') == team:
                remaining_time = power_play.get('time_remaining', 0)
                profile['power_play_pressure'] = min(0.9, remaining_time / 120.0)
            
            # Calculate overall pressure
            pressure_components = [
                profile['shot_pressure'],
                profile['score_pressure'],
                profile['time_pressure'],
                profile['power_play_pressure']
            ]
            profile['overall_pressure'] = sum(pressure_components) / len(pressure_components)
            
            # Identify pressure peaks
            profile['pressure_peaks'] = self._identify_pressure_peaks(match_data, team)
            
            # Calculate pressure consistency
            profile['pressure_consistency'] = self._calculate_pressure_consistency(profile)
            
        except Exception as e:
            logger.warning(f"Error analyzing {team} pressure: {e}")
        
        return profile
    
    def _identify_pressure_peaks(self, match_data: Dict[str, Any], team: str) -> List[Dict[str, Any]]:
        """Identify moments of peak pressure for a team"""
        peaks = []
        
        try:
            live_data = match_data.get('live_data', {})
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            current_period = match_data.get('current_period', 1)
            time_in_period = match_data.get('time_in_period', 0)
            
            # Power play opportunities
            power_play = live_data.get('power_play', {})
            if power_play and power_play.get('team') == team:
                peaks.append({
                    'type': 'power_play',
                    'intensity': 0.8,
                    'period': current_period,
                    'time': time_in_period,
                    'description': f'Power play opportunity for {team}'
                })
            
            # Late period pressure
            if current_period == 3 and time_in_period > 900:
                score_diff = abs(score['team1'] - score['team2'])
                if score_diff <= 1:
                    peaks.append({
                        'type': 'late_game_pressure',
                        'intensity': 0.9,
                        'period': current_period,
                        'time': time_in_period,
                        'description': f'Late game pressure for {team}'
                    })
            
            # Shot pressure buildup
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            total_shots = shots['team1'] + shots['team2']
            if total_shots > 0:
                shot_ratio = shots[team] / total_shots
                if shot_ratio > 0.65:
                    peaks.append({
                        'type': 'shot_pressure',
                        'intensity': 0.7,
                        'period': current_period,
                        'time': time_in_period,
                        'description': f'High shot pressure from {team}'
                    })
            
        except Exception as e:
            logger.warning(f"Error identifying pressure peaks: {e}")
        
        return peaks
    
    def _calculate_pressure_consistency(self, profile: Dict[str, Any]) -> float:
        """Calculate how consistent a team's pressure is"""
        try:
            pressure_values = [
                profile['shot_pressure'],
                profile['score_pressure'],
                profile['time_pressure'],
                profile['power_play_pressure']
            ]
            
            if len(pressure_values) == 0:
                return 0.5
            
            # Calculate standard deviation
            mean_pressure = sum(pressure_values) / len(pressure_values)
            variance = sum((p - mean_pressure) ** 2 for p in pressure_values) / len(pressure_values)
            std_dev = np.sqrt(variance)
            
            # Lower standard deviation = more consistent
            consistency = max(0.0, 1.0 - std_dev)
            return consistency
            
        except Exception as e:
            logger.warning(f"Error calculating pressure consistency: {e}")
            return 0.5
    
    def _identify_pressure_battles(self, match_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify periods where both teams are applying pressure"""
        battles = []
        
        try:
            live_data = match_data.get('live_data', {})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            current_period = match_data.get('current_period', 1)
            time_in_period = match_data.get('time_in_period', 0)
            
            total_shots = shots['team1'] + shots['team2']
            
            # High shot volume from both teams
            if total_shots > 25:
                shot_balance = abs(shots['team1'] - shots['team2']) / total_shots
                
                if shot_balance < 0.3:  # Relatively balanced
                    battles.append({
                        'type': 'shot_battle',
                        'intensity': min(0.9, total_shots / 30.0),
                        'period': current_period,
                        'time': time_in_period,
                        'description': f'Intense shot battle: {shots["team1"]}-{shots["team2"]}'
                    })
            
            # Score pressure battle
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            if score['team1'] == score['team2'] and current_period >= 2:
                battles.append({
                    'type': 'score_battle',
                    'intensity': 0.7,
                    'period': current_period,
                    'time': time_in_period,
                    'description': 'Scoreless pressure battle'
                })
            
        except Exception as e:
            logger.warning(f"Error identifying pressure battles: {e}")
        
        return battles
    
    def _find_critical_pressure_moments(self, match_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find critical moments where pressure led to outcomes"""
        moments = []
        
        try:
            live_data = match_data.get('live_data', {})
            goal_scorers = live_data.get('goal_scorers', [])
            penalties = live_data.get('penalties', {})
            current_period = match_data.get('current_period', 1)
            
            # Goals after sustained pressure
            for goal in goal_scorers[-3:]:  # Last 3 goals
                moments.append({
                    'type': 'pressure_goal',
                    'team': goal.get('team', ''),
                    'period': goal.get('period', 1),
                    'time': goal.get('time', ''),
                    'description': f'Goal by {goal.get("player", "Unknown")} after pressure'
                })
            
            # Penalty kills under pressure
            all_penalties = penalties.get('team1', []) + penalties.get('team2', [])
            for penalty in all_penalties[-2:]:  # Recent penalties
                moments.append({
                    'type': 'penalty_pressure',
                    'team': penalty.get('team', ''),
                    'period': current_period,
                    'time': penalty.get('time', ''),
                    'description': f'Penalty to {penalty.get("player", "Unknown")} creating pressure'
                })
            
        except Exception as e:
            logger.warning(f"Error finding critical pressure moments: {e}")
        
        return moments
    
    def _calculate_pressure_efficiency(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate how efficiently teams convert pressure to goals"""
        efficiency = {
            'team1': {'pressure_conversion': 0.0, 'shot_conversion': 0.0},
            'team2': {'pressure_conversion': 0.0, 'shot_conversion': 0.0}
        }
        
        try:
            live_data = match_data.get('live_data', {})
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            goal_scorers = live_data.get('goal_scorers', [])
            
            # Count goals by team
            team1_goals = sum(1 for g in goal_scorers if g.get('team') == 'team1')
            team2_goals = sum(1 for g in goal_scorers if g.get('team') == 'team2')
            
            # Calculate shot conversion
            if shots['team1'] > 0:
                efficiency['team1']['shot_conversion'] = team1_goals / shots['team1']
            if shots['team2'] > 0:
                efficiency['team2']['shot_conversion'] = team2_goals / shots['team2']
            
            # Calculate pressure conversion (simplified)
            total_pressure = shots['team1'] + shots['team2']
            if total_pressure > 0:
                efficiency['team1']['pressure_conversion'] = (team1_goals / total_pressure) * 2
                efficiency['team2']['pressure_conversion'] = (team2_goals / total_pressure) * 2
            
        except Exception as e:
            logger.warning(f"Error calculating pressure efficiency: {e}")
        
        return efficiency
    
    def _analyze_comeback_pressure(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pressure in comeback situations"""
        comeback = {
            'potential_comeback': False,
            'pressing_team': '',
            'pressure_intensity': 0.0,
            'time_window': 0,
            'success_probability': 0.0
        }
        
        try:
            score = match_data.get('score', {'team1': 0, 'team2': 0})
            live_data = match_data.get('live_data', {})
            shots = live_data.get('shots', {'team1': 0, 'team2': 0})
            current_period = match_data.get('current_period', 1)
            time_in_period = match_data.get('time_in_period', 0)
            
            # Determine if comeback is possible
            score_diff = abs(score['team1'] - score['team2'])
            
            if score_diff >= 2 and current_period >= 2:
                # Identify trailing team
                if score['team1'] > score['team2']:
                    trailing_team = 'team2'
                else:
                    trailing_team = 'team1'
                
                # Check if trailing team is generating pressure
                leading_shots = shots['team1'] if trailing_team == 'team2' else shots['team2']
                trailing_shots = shots['team2'] if trailing_team == 'team2' else shots['team1']
                
                if trailing_shots > leading_shots + 5:
                    comeback['potential_comeback'] = True
                    comeback['pressing_team'] = trailing_team
                    comeback['pressure_intensity'] = min(0.9, (trailing_shots - leading_shots) / 15.0)
                    
                    # Calculate time window
                    if current_period == 3:
                        comeback['time_window'] = max(0, 1200 - time_in_period)
                    else:
                        comeback['time_window'] = (3 - current_period) * 1200 + (1200 - time_in_period)
                    
                    # Calculate success probability
                    base_prob = 0.2
                    pressure_bonus = comeback['pressure_intensity'] * 0.3
                    time_bonus = min(0.2, comeback['time_window'] / 3600.0)
                    comeback['success_probability'] = min(0.8, base_prob + pressure_bonus + time_bonus)
            
        except Exception as e:
            logger.warning(f"Error analyzing comeback pressure: {e}")
        
        return comeback
    
    def _generate_pressure_recommendation(self, analysis: Dict[str, Any]) -> str:
        """Generate recommendation based on pressure analysis"""
        try:
            comeback = analysis.get('comeback_pressure', {})
            efficiency = analysis.get('pressure_efficiency', {})
            battles = analysis.get('pressure_battles', [])
            
            # Priority scenarios
            if comeback.get('potential_comeback'):
                pressing_team = comeback['pressing_team']
                prob = comeback['success_probability']
                return f"Watch {pressing_team} comeback pressure ({prob:.1%} probability)"
            
            if battles:
                intense_battle = max(battles, key=lambda x: x.get('intensity', 0))
                if intense_battle['intensity'] > 0.7:
                    return f"Intense {intense_battle['type']} battle detected"
            
            # Check efficiency
            team1_eff = efficiency.get('team1', {}).get('shot_conversion', 0)
            team2_eff = efficiency.get('team2', {}).get('shot_conversion', 0)
            
            if abs(team1_eff - team2_eff) > 0.1:
                more_efficient = 'team1' if team1_eff > team2_eff else 'team2'
                return f"{more_efficient} more efficient at converting pressure"
            
            return "Pressure patterns normal, monitor for developments"
            
        except Exception as e:
            logger.warning(f"Error generating pressure recommendation: {e}")
            return "Unable to generate pressure recommendation"
    
    def _calculate_pressure_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence in pressure analysis"""
        try:
            confidence_factors = []
            
            # Comeback confidence
            comeback = analysis.get('comeback_pressure', {})
            if comeback.get('potential_comeback'):
                confidence_factors.append(comeback.get('success_probability', 0))
            
            # Battle confidence
            battles = analysis.get('pressure_battles', [])
            if battles:
                max_battle_intensity = max(b.get('intensity', 0) for b in battles)
                confidence_factors.append(max_battle_intensity)
            
            # Efficiency confidence
            efficiency = analysis.get('pressure_efficiency', {})
            team1_eff = efficiency.get('team1', {}).get('shot_conversion', 0)
            team2_eff = efficiency.get('team2', {}).get('shot_conversion', 0)
            if team1_eff > 0 or team2_eff > 0:
                confidence_factors.append(0.6)
            
            if confidence_factors:
                return sum(confidence_factors) / len(confidence_factors)
            
            return 0.5
            
        except Exception as e:
            logger.warning(f"Error calculating pressure confidence: {e}")
            return 0.0


async def analyze_khl_pressure(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze pressure patterns for KHL matches"""
    analyzer = KHLPressureModel()
    analyzed_matches = []
    
    for match in matches:
        if match.get('status') == 'live':
            pressure_analysis = analyzer.analyze_match_pressure(match)
            match['pressure_analysis'] = pressure_analysis
            analyzed_matches.append(match)
    
    return analyzed_matches


async def khl_pressure_analysis_task():
    """KHL pressure analysis task"""
    logger.info("Starting KHL pressure analysis")
    
    try:
        # Get live matches
        from storage.database import get_live_khl_matches
        matches = await get_live_khl_matches()
        
        if matches:
            analyzed_matches = await analyze_khl_pressure(matches)
            
            # Store analysis results
            from storage.database import store_khl_pressure_analysis
            await store_khl_pressure_analysis(analyzed_matches)
            
            # Check for high-pressure scenarios
            high_pressure_matches = [
                m for m in analyzed_matches 
                if m.get('pressure_analysis', {}).get('confidence', 0) >= 0.7
            ]
            
            if high_pressure_matches:
                from app.main import telegram_sender
                for match in high_pressure_matches[:2]:  # Top 2 matches
                    pressure = match['pressure_analysis']
                    await telegram_sender.send_khl_analysis({
                        'match': match,
                        'scenarios': [{
                            'name': 'Pressure Model Analysis',
                            'confidence': pressure['confidence'],
                            'description': pressure['recommendation'],
                            'factors': [battle['description'] for battle in pressure.get('pressure_battles', [])[:2]],
                            'recommendation': pressure['recommendation']
                        }],
                        'recommendation': {
                            'text': pressure['recommendation'],
                            'confidence': pressure['confidence']
                        }
                    })
            
            logger.info(f"Pressure analysis completed for {len(matches)} matches")
        
    except Exception as e:
        logger.error(f"KHL pressure analysis task failed: {e}")


def setup_khl_pressure_tasks(scheduler):
    """Setup KHL pressure analysis tasks"""
    scheduler.add_task('khl_pressure_analysis', khl_pressure_analysis_task, 120)  # Every 2 minutes
    logger.info("KHL pressure analysis tasks setup complete")
