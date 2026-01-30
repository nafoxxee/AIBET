import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LineupChange:
    player_name: str
    change_type: str  # 'stand_in', 'removed', 'returned'
    reason: str
    impact_score: float


class LineupAnalyzer:
    """Analyze lineup changes and their impact"""
    
    def __init__(self):
        self.player_impact_cache = {}
        self.team_performance_history = {}
    
    def analyze_lineup_stability(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze lineup stability for both teams"""
        analysis = {
            'team1_stability': self._analyze_team_lineup(match_data, 'team1'),
            'team2_stability': self._analyze_team_lineup(match_data, 'team2'),
            'overall_stability_score': 0.0,
            'key_changes': [],
            'recommendation': '',
            'confidence': 0.0
        }
        
        try:
            # Calculate overall stability
            team1_score = analysis['team1_stability']['stability_score']
            team2_score = analysis['team2_stability']['stability_score']
            analysis['overall_stability_score'] = (team1_score + team2_score) / 2
            
            # Identify key changes
            analysis['key_changes'] = self._identify_key_changes(analysis)
            
            # Generate recommendation
            analysis['recommendation'] = self._generate_lineup_recommendation(analysis)
            analysis['confidence'] = self._calculate_lineup_confidence(analysis)
            
        except Exception as e:
            logger.warning(f"Error analyzing lineup stability: {e}")
        
        return analysis
    
    def _analyze_team_lineup(self, match_data: Dict, team_key: str) -> Dict[str, Any]:
        """Analyze individual team lineup"""
        stability = {
            'stability_score': 1.0,  # Start with perfect stability
            'has_stand_ins': False,
            'missing_players': 0,
            'recent_changes': [],
            'impact_assessment': 'stable'
        }
        
        try:
            match_info = match_data.get('match_info', {})
            lineups = match_info.get('lineups', {})
            stand_ins = match_info.get('stand_ins', {})
            
            team_lineup = lineups.get(team_key, [])
            has_stand_in = stand_ins.get(team_key, False)
            
            # Check for stand-ins
            if has_stand_in:
                stability['has_stand_ins'] = True
                stability['stability_score'] -= 0.3
                stability['recent_changes'].append({
                    'type': 'stand_in',
                    'impact': 0.3,
                    'description': f'{team_key} using stand-in player'
                })
            
            # Check lineup completeness
            if len(team_lineup) < 5:
                missing = 5 - len(team_lineup)
                stability['missing_players'] = missing
                stability['stability_score'] -= (missing * 0.2)
                stability['recent_changes'].append({
                    'type': 'missing_players',
                    'impact': missing * 0.2,
                    'description': f'{team_key} missing {missing} players'
                })
            
            # Analyze player quality (simplified)
            player_quality_score = self._analyze_player_quality(team_lineup)
            if player_quality_score < 0.7:
                stability['stability_score'] -= 0.2
                stability['recent_changes'].append({
                    'type': 'player_quality',
                    'impact': 0.2,
                    'description': f'{team_key} has lower quality lineup'
                })
            
            # Determine impact assessment
            if stability['stability_score'] >= 0.9:
                stability['impact_assessment'] = 'stable'
            elif stability['stability_score'] >= 0.7:
                stability['impact_assessment'] = 'minor_disruption'
            elif stability['stability_score'] >= 0.5:
                stability['impact_assessment'] = 'moderate_disruption'
            else:
                stability['impact_assessment'] = 'severe_disruption'
            
        except Exception as e:
            logger.warning(f"Error analyzing {team_key} lineup: {e}")
        
        return stability
    
    def _analyze_player_quality(self, lineup: List[Dict]) -> float:
        """Analyze player quality based on recognition"""
        try:
            if not lineup:
                return 0.0
            
            # Known high-level players (simplified list)
            top_players = {
                's1mple', 'zywoo', 'niko', 'dev1ce', 'shox', 'coldzera',
                'falleN', 'gla1ve', 'electronic', 'b1t', 'ax1le', 'hobbit',
                'jks', 'rain', 'karrigan', 'twistzz', 'ropz', 'broky'
            }
            
            quality_score = 0.0
            for player in lineup:
                player_name = player.get('name', '').lower()
                if any(top in player_name for top in top_players):
                    quality_score += 0.9
                elif len(player_name) > 3:  # Reasonable player name
                    quality_score += 0.6
                else:
                    quality_score += 0.3
            
            return min(quality_score / len(lineup), 1.0)
            
        except Exception as e:
            logger.warning(f"Error analyzing player quality: {e}")
            return 0.5
    
    def _identify_key_changes(self, analysis: Dict) -> List[Dict[str, Any]]:
        """Identify key lineup changes"""
        key_changes = []
        
        try:
            team1_changes = analysis['team1_stability']['recent_changes']
            team2_changes = analysis['team2_stability']['recent_changes']
            
            # Combine and sort by impact
            all_changes = team1_changes + team2_changes
            all_changes.sort(key=lambda x: x.get('impact', 0), reverse=True)
            
            # Get top 3 changes
            key_changes = all_changes[:3]
            
        except Exception as e:
            logger.warning(f"Error identifying key changes: {e}")
        
        return key_changes
    
    def _generate_lineup_recommendation(self, analysis: Dict) -> str:
        """Generate recommendation based on lineup analysis"""
        try:
            overall_score = analysis['overall_stability_score']
            team1_stability = analysis['team1_stability']['stability_score']
            team2_stability = analysis['team2_stability']['stability_score']
            
            if overall_score >= 0.9:
                return "Both teams stable - proceed with normal analysis"
            
            elif overall_score >= 0.7:
                if abs(team1_stability - team2_stability) > 0.3:
                    less_stable = 'team1' if team1_stability < team2_stability else 'team2'
                    return f"Consider betting against {less_stable} due to lineup issues"
                else:
                    return "Minor lineup disruptions - factor into odds assessment"
            
            elif overall_score >= 0.5:
                if team1_stability < 0.5 and team2_stability >= 0.7:
                    return "Strong consideration: bet against team1 due to lineup instability"
                elif team2_stability < 0.5 and team1_stability >= 0.7:
                    return "Strong consideration: bet against team2 due to lineup instability"
                else:
                    return "Both teams have lineup issues - consider skipping or betting on volatility"
            
            else:
                return "Severe lineup instability for both teams - high volatility expected"
        
        except Exception as e:
            logger.warning(f"Error generating lineup recommendation: {e}")
            return "Unable to generate lineup recommendation"
    
    def _calculate_lineup_confidence(self, analysis: Dict) -> float:
        """Calculate confidence in lineup analysis"""
        try:
            overall_score = analysis['overall_stability_score']
            
            # Higher confidence when stability is very high or very low
            if overall_score >= 0.9 or overall_score <= 0.4:
                base_confidence = 0.8
            elif overall_score >= 0.7 or overall_score <= 0.6:
                base_confidence = 0.6
            else:
                base_confidence = 0.4
            
            # Adjust based on number of key changes
            key_changes_count = len(analysis['key_changes'])
            if key_changes_count > 0:
                change_factor = min(key_changes_count * 0.1, 0.3)
                base_confidence += change_factor
            
            return min(base_confidence, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating lineup confidence: {e}")
            return 0.0
    
    def detect_stand_in_impact(self, stand_in_name: str, team_name: str) -> float:
        """Detect potential impact of stand-in player"""
        try:
            # Check if stand-in is known player
            known_players = {
                'Brehze', 'Jks', 'Rush', 'Swag', 'Daps', 'CeRq', 'Tarik',
                'Stanislaw', 'Yekindar', 'Flamie', 'Mir', 'Edward'
            }
            
            if stand_in_name in known_players:
                return 0.8  # High-quality stand-in
            elif len(stand_in_name) > 5:
                return 0.5  # Unknown but potentially decent
            else:
                return 0.2  # Likely low-quality stand-in
        
        except Exception as e:
            logger.warning(f"Error detecting stand-in impact: {e}")
            return 0.5


async def analyze_cs2_lineups(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze lineup changes for CS2 matches"""
    analyzer = LineupAnalyzer()
    analyzed_matches = []
    
    for match in matches:
        lineup_analysis = analyzer.analyze_lineup_stability(match)
        match['lineup_analysis'] = lineup_analysis
        analyzed_matches.append(match)
    
    return analyzed_matches


async def cs2_lineup_analysis_task():
    """CS2 lineup analysis task"""
    logger.info("Starting CS2 lineup analysis")
    
    try:
        # Get matches with lineup data
        from storage.database import get_cs2_matches_with_lineups
        matches = await get_cs2_matches_with_lineups()
        
        if matches:
            analyzed_matches = await analyze_cs2_lineups(matches)
            
            # Store analysis results
            from storage.database import store_cs2_lineup_analysis
            await store_cs2_lineup_analysis(analyzed_matches)
            
            # Check for significant lineup issues
            unstable_matches = [
                m for m in analyzed_matches 
                if m.get('lineup_analysis', {}).get('overall_stability_score', 1.0) < 0.7
            ]
            
            if unstable_matches:
                from app.main import telegram_sender
                for match in unstable_matches[:2]:  # Top 2 unstable matches
                    lineup = match['lineup_analysis']
                    await telegram_sender.send_cs2_analysis({
                        'match': match,
                        'scenarios': [{
                            'name': 'Lineup Instability',
                            'confidence': lineup['confidence'],
                            'description': f"Lineup stability score: {lineup['overall_stability_score']:.1%}",
                            'factors': [change['description'] for change in lineup['key_changes'][:2]],
                            'recommendation': lineup['recommendation']
                        }],
                        'recommendation': {
                            'text': lineup['recommendation'],
                            'confidence': lineup['confidence']
                        }
                    })
            
            logger.info(f"Lineup analysis completed for {len(matches)} matches")
        
    except Exception as e:
        logger.error(f"CS2 lineup analysis task failed: {e}")


def setup_cs2_lineup_tasks(scheduler):
    """Setup CS2 lineup analysis tasks"""
    scheduler.add_task('cs2_lineup_analysis', cs2_lineup_analysis_task, 900)  # Every 15 minutes
    logger.info("CS2 lineup analysis tasks setup complete")
