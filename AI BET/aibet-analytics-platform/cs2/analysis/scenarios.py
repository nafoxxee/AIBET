import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Scenario:
    name: str
    confidence: float
    description: str
    factors: List[str]
    recommendation: str


class CS2ScenarioDetector:
    """Detect CS2 betting market scenarios"""
    
    def __init__(self):
        self.scenarios = []
    
    def analyze_match(self, match_data: Dict[str, Any]) -> List[Scenario]:
        """Analyze match and detect scenarios"""
        scenarios = []
        
        # Get match components
        odds_data = match_data.get('odds', {})
        match_info = match_data.get('match_info', {})
        
        # Detect various scenarios
        scenarios.extend(self._detect_overvalued_favorite(odds_data, match_info))
        scenarios.extend(self._detect_public_trap(odds_data, match_info))
        scenarios.extend(self._detect_delayed_reaction(odds_data, match_info))
        scenarios.extend(self._detect_lineup_instability(match_info))
        scenarios.extend(self._detect_tournament_mismatch(odds_data, match_info))
        
        # Sort by confidence
        scenarios.sort(key=lambda x: x.confidence, reverse=True)
        
        return scenarios[:5]  # Return top 5 scenarios
    
    def _detect_overvalued_favorite(self, odds_data: Dict, match_info: Dict) -> List[Scenario]:
        """Detect overvalued favorite scenario"""
        scenarios = []
        
        try:
            analysis = odds_data.get('analysis', {})
            avg_odds = odds_data.get('average_odds', {})
            public_money = odds_data.get('public_money', {})
            
            # Check conditions
            is_heavy_favorite = analysis.get('is_heavy_favorite', False)
            public_bias = analysis.get('public_bias_detected', False)
            favorite_odds = analysis.get('favorite_odds', 0)
            
            if is_heavy_favorite and public_bias and favorite_odds < 1.30:
                # Additional checks
                team1_pct = public_money.get('team1_percentage', 0)
                team2_pct = public_money.get('team2_percentage', 0)
                
                if max(team1_pct, team2_pct) > 75:  # Very heavy public bias
                    confidence = min(0.8, (max(team1_pct, team2_pct) - 70) / 20)
                    
                    scenario = Scenario(
                        name="Overvalued Favorite",
                        confidence=confidence,
                        description="Heavy favorite with excessive public betting",
                        factors=[
                            f"Favorite odds: {favorite_odds:.2f}",
                            f"Public bias: {max(team1_pct, team2_pct):.1f}%",
                            "Market overreaction detected"
                        ],
                        recommendation="Consider betting against the favorite or skip"
                    )
                    scenarios.append(scenario)
        
        except Exception as e:
            logger.warning(f"Error detecting overvalued favorite: {e}")
        
        return scenarios
    
    def _detect_public_trap(self, odds_data: Dict, match_info: Dict) -> List[Scenario]:
        """Detect public trap scenario"""
        scenarios = []
        
        try:
            analysis = odds_data.get('analysis', {})
            movement = odds_data.get('movement_history', [])
            public_money = odds_data.get('public_money', {})
            
            # Check for odds movement against public sentiment
            public_bias = analysis.get('public_bias_detected', False)
            movement_trend = analysis.get('odds_movement_trend', '')
            
            if public_bias and movement_trend == 'favorite_drifting':
                # Odds drifting despite heavy public support
                team1_pct = public_money.get('team1_percentage', 0)
                team2_pct = public_money.get('team2_percentage', 0)
                
                confidence = min(0.7, (max(team1_pct, team2_pct) - 70) / 25)
                
                scenario = Scenario(
                    name="Public Trap",
                    confidence=confidence,
                    description="Odds moving against public money flow",
                    factors=[
                        f"Public bias: {max(team1_pct, team2_pct):.1f}%",
                        "Odds drifting against public",
                        "Smart money indicator"
                    ],
                    recommendation="Follow the odds movement, not the public"
                )
                scenarios.append(scenario)
        
        except Exception as e:
            logger.warning(f"Error detecting public trap: {e}")
        
        return scenarios
    
    def _detect_delayed_reaction(self, odds_data: Dict, match_info: Dict) -> List[Scenario]:
        """Detect delayed market reaction scenario"""
        scenarios = []
        
        try:
            lineups = match_info.get('lineups', {})
            stand_ins = match_info.get('stand_ins', {})
            
            # Check for lineup issues not reflected in odds
            team1_stand_in = stand_ins.get('team1', False)
            team2_stand_in = stand_ins.get('team2', False)
            
            if team1_stand_in or team2_stand_in:
                # Check if odds haven't adjusted for lineup changes
                avg_odds = odds_data.get('average_odds', {})
                favorite_odds = min(avg_odds.get('team1', 2), avg_odds.get('team2', 2))
                
                if favorite_odds < 1.35:  # Still heavy favorite despite lineup issues
                    confidence = 0.6
                    
                    affected_team = "Team 1" if team1_stand_in else "Team 2"
                    
                    scenario = Scenario(
                        name="Delayed Market Reaction",
                        confidence=confidence,
                        description="Lineup issues not reflected in odds",
                        factors=[
                            f"{affected_team} has stand-ins",
                            f"Odds still heavy favorite: {favorite_odds:.2f}",
                            "Market underreacting to roster changes"
                        ],
                        recommendation="Bet against the team with stand-ins"
                    )
                    scenarios.append(scenario)
        
        except Exception as e:
            logger.warning(f"Error detecting delayed reaction: {e}")
        
        return scenarios
    
    def _detect_lineup_instability(self, match_info: Dict) -> List[Scenario]:
        """Detect lineup instability scenario"""
        scenarios = []
        
        try:
            lineups = match_info.get('lineups', {})
            stand_ins = match_info.get('stand_ins', {})
            
            team1_players = len(lineups.get('team1', []))
            team2_players = len(lineups.get('team2', []))
            
            if team1_players < 5 or team2_players < 5:
                confidence = 0.5
                
                scenario = Scenario(
                    name="Lineup Instability",
                    confidence=confidence,
                    description="Teams not at full strength",
                    factors=[
                        f"Team 1 players: {team1_players}/5",
                        f"Team 2 players: {team2_players}/5",
                        "Roster instability affects performance"
                    ],
                    recommendation="Avoid betting or bet against weakened team"
                )
                scenarios.append(scenario)
        
        except Exception as e:
            logger.warning(f"Error detecting lineup instability: {e}")
        
        return scenarios
    
    def _detect_tournament_mismatch(self, odds_data: Dict, match_info: Dict) -> List[Scenario]:
        """Detect tournament tier mismatch scenario"""
        scenarios = []
        
        try:
            tier = match_info.get('tier', 'C')
            avg_odds = odds_data.get('average_odds', {})
            tournament = match_info.get('tournament', '')
            
            # Check if odds suggest major importance but tournament is low tier
            favorite_odds = min(avg_odds.get('team1', 2), avg_odds.get('team2', 2))
            
            if tier in ['C', 'B'] and favorite_odds < 1.25:
                # Very heavy favorite in low-tier tournament
                confidence = 0.4
                
                scenario = Scenario(
                    name="Tournament Mismatch",
                    confidence=confidence,
                    description="Heavy odds in low-importance match",
                    factors=[
                        f"Tournament tier: {tier}",
                        f"Favorite odds: {favorite_odds:.2f}",
                        "Low stakes may affect motivation"
                    ],
                    recommendation="Be cautious with heavy favorites in low-tier events"
                )
                scenarios.append(scenario)
        
        except Exception as e:
            logger.warning(f"Error detecting tournament mismatch: {e}")
        
        return scenarios


async def analyze_cs2_matches(matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Analyze CS2 matches for scenarios"""
    if not matches:
        return None
    
    detector = CS2ScenarioDetector()
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
                        'recommendation': s.recommendation
                    } for s in all_scenarios[:3]
                ],
                'recommendation': {
                    'text': best_scenario.recommendation,
                    'confidence': best_scenario.confidence
                },
                'analysis_time': datetime.now().isoformat()
            }
    
    return None


async def cs2_analysis_task():
    """CS2 analysis task for scheduler"""
    logger.info("Starting CS2 scenario analysis")
    
    try:
        # Get matches with odds from database
        from storage.database import get_cs2_matches_with_odds
        matches = await get_cs2_matches_with_odds()
        
        if matches:
            analysis_result = await analyze_cs2_matches(matches)
            
            if analysis_result:
                # Send to Telegram
                from app.main import telegram_sender
                await telegram_sender.send_cs2_analysis(analysis_result)
                
                logger.info(f"CS2 analysis completed. Found {len(analysis_result['scenarios'])} scenarios")
            else:
                logger.info("CS2 analysis completed. No scenarios detected")
        
    except Exception as e:
        logger.error(f"CS2 analysis task failed: {e}")


def setup_cs2_analysis_tasks(scheduler):
    """Setup CS2 analysis tasks in scheduler"""
    scheduler.add_task('cs2_analysis', cs2_analysis_task, 180)  # Every 3 minutes
    logger.info("CS2 analysis tasks setup complete")
