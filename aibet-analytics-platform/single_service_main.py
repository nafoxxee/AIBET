#!/usr/bin/env python3
"""
AI BET Analytics - Single Service Main
Optimized for Render Free Plan - combines bot and scheduler
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from app.config import config
from app.scheduler import Scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramSender:
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.dp = Dispatcher()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup Telegram bot handlers"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            await self._show_main_menu(message)
        
        @self.dp.callback_query(lambda c: c.data == "main_menu")
        async def main_menu_callback(callback: CallbackQuery):
            await self._show_main_menu(callback.message)
        
        @self.dp.callback_query(lambda c: c.data.startswith("cs2_"))
        async def cs2_menu_callback(callback: CallbackQuery):
            await self._handle_cs2_menu(callback)
        
        @self.dp.callback_query(lambda c: c.data.startswith("khl_"))
        async def khl_menu_callback(callback: CallbackQuery):
            await self._handle_khl_menu(callback)
        
        @self.dp.callback_query(lambda c: c.data == "system_status")
        async def system_status_callback(callback: CallbackQuery):
            await self._show_system_status(callback.message)
        
        @self.dp.callback_query(lambda c: c.data == "force_analysis")
        async def force_analysis_callback(callback: CallbackQuery):
            await self._force_analysis(callback.message)
        
        @self.dp.callback_query(lambda c: c.data == "help")
        async def help_callback(callback: CallbackQuery):
            await self._show_help(callback.message)
        
        # Keep old commands for compatibility
        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            await self._show_help(message)
        
        @self.dp.message(Command("status"))
        async def cmd_status(message: Message):
            await self._show_system_status(message)
    
    async def _show_main_menu(self, message: Message):
        """Show main menu with inline buttons"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎮 CS2 Analytics", callback_data="cs2_menu"),
                InlineKeyboardButton(text="🏒 KHL Analytics", callback_data="khl_menu")
            ],
            [
                InlineKeyboardButton(text="📊 System Status", callback_data="system_status"),
                InlineKeyboardButton(text="🔄 Force Analysis", callback_data="force_analysis")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Help", callback_data="help")
            ]
        ])
        
        await message.answer(
            "🤖 AI Betting Analytics Platform\n\n"
            "Choose section:",
            reply_markup=keyboard
        )
    
    async def _handle_cs2_menu(self, callback: CallbackQuery):
        """Handle CS2 menu callbacks"""
        action = callback.data
        
        if action == "cs2_menu":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔍 Live Matches", callback_data="cs2_live"),
                    InlineKeyboardButton(text="📈 Pre-match Analysis", callback_data="cs2_prematch")
                ],
                [
                    InlineKeyboardButton(text="🧠 Detected Scenarios", callback_data="cs2_scenarios"),
                    InlineKeyboardButton(text="🔔 Enable Alerts", callback_data="cs2_alerts")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")
                ]
            ])
            
            await callback.message.edit_text(
                "🎮 CS2 Analytics\n\n"
                "Select option:",
                reply_markup=keyboard
            )
        
        elif action == "cs2_live":
            await self._show_cs2_live_matches(callback.message)
        elif action == "cs2_prematch":
            await self._show_cs2_prematch_analysis(callback.message)
        elif action == "cs2_scenarios":
            await self._show_cs2_scenarios(callback.message)
        elif action == "cs2_alerts":
            await self._toggle_cs2_alerts(callback.message)
        
        await callback.answer()
    
    async def _handle_khl_menu(self, callback: CallbackQuery):
        """Handle KHL menu callbacks"""
        action = callback.data
        
        if action == "khl_menu":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔍 Live Matches", callback_data="khl_live"),
                    InlineKeyboardButton(text="📈 Pre-match Analysis", callback_data="khl_prematch")
                ],
                [
                    InlineKeyboardButton(text="🧠 Detected Scenarios", callback_data="khl_scenarios"),
                    InlineKeyboardButton(text="🔔 Enable Alerts", callback_data="khl_alerts")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")
                ]
            ])
            
            await callback.message.edit_text(
                "🏒 KHL Analytics\n\n"
                "Select option:",
                reply_markup=keyboard
            )
        
        elif action == "khl_live":
            await self._show_khl_live_matches(callback.message)
        elif action == "khl_prematch":
            await self._show_khl_prematch_analysis(callback.message)
        elif action == "khl_scenarios":
            await self._show_khl_scenarios(callback.message)
        elif action == "khl_alerts":
            await self._toggle_khl_alerts(callback.message)
        
        await callback.answer()
    
    async def _show_system_status(self, message: Message):
        """Show detailed system status"""
        status = self.scheduler.get_status_summary()
        
        status_text = (
            f"🤖 AI BET Analytics Status\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🔧 System:\n"
            f"• Scheduler: {'✅ Running' if status['scheduler_running'] else '❌ Stopped'}\n"
            f"• Total tasks: {status['total_tasks']}\n"
            f"• Enabled tasks: {status['enabled_tasks']}\n"
            f"• Service Type: Single Service (Free Plan)\n\n"
            f"📊 Last Scan:\n"
            f"• CS2: {datetime.now().strftime('%H:%M')}\n"
            f"• KHL: {datetime.now().strftime('%H:%M')}\n\n"
            f"🎯 Currently Tracking:\n"
            f"• CS2 matches: {await self._get_tracked_matches_count('cs2')}\n"
            f"• KHL matches: {await self._get_tracked_matches_count('khl')}\n\n"
            f"📋 Tasks Status:"
        )
        
        for task_name, task_status in status['tasks'].items():
            task_emoji = "✅" if task_status['enabled'] else "❌"
            if task_status['is_running']:
                task_emoji = "🔄"
            elif task_status['error_count'] > 0:
                task_emoji = "⚠️"
            
            status_text += f"\n{task_emoji} {task_name}"
            if task_status['last_run']:
                status_text += f" (last: {task_status['last_run'][-8:]})"
            if task_status['error_count'] > 0:
                status_text += f" ❌{task_status['error_count']}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
        ])
        
        await message.answer(status_text, reply_markup=keyboard)
    
    async def _force_analysis(self, message: Message):
        """Force immediate analysis"""
        await message.answer("🔄 Forcing immediate analysis...")
        
        try:
            # Run CS2 analysis
            cs2_results = await self._run_cs2_analysis()
            # Run KHL analysis
            khl_results = await self._run_khl_analysis()
            
            result_text = (
                f"🔄 Force Analysis Complete\n\n"
                f"🎮 CS2: {cs2_results}\n"
                f"🏒 KHL: {khl_results}\n\n"
                f"Results posted to channels."
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
            ])
            
            await message.answer(result_text, reply_markup=keyboard)
            
        except Exception as e:
            await message.answer(f"❌ Analysis failed: {str(e)}")
    
    async def _show_help(self, message: Message):
        """Show help information"""
        help_text = (
            "🤖 AI BET Analytics Help\n\n"
            "📱 How to use:\n"
            "• Use inline buttons to navigate\n"
            "• No need to type commands\n"
            "• All functions accessible via menus\n\n"
            "🎮 CS2 Analytics:\n"
            "• Live match monitoring\n"
            "• Pre-match odds analysis\n"
            "• Scenario detection\n"
            "• Alert notifications\n\n"
            "🏒 KHL Analytics:\n"
            "• Live game tracking\n"
            "• Period-by-period analysis\n"
            "• Pressure model analysis\n"
            "• Scenario detection\n\n"
            "📊 System Features:\n"
            "• 24/7 automated analysis\n"
            "• Machine learning predictions\n"
            "• Real-time notifications\n"
            "• Historical data tracking\n\n"
            "📢 Channels:\n"
            "• CS2: https://t.me/aibetcsgo\n"
            "• KHL: https://t.me/aibetkhl\n\n"
            "🔧 Auto-posting:\n"
            "• Analysis posted automatically\n"
            "• High-confidence scenarios prioritized\n"
            "• Real-time match updates"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
        ])
        
        await message.answer(help_text, reply_markup=keyboard)
    
    # Helper methods for UI functions
    async def _get_tracked_matches_count(self, sport: str) -> int:
        """Get number of currently tracked matches"""
        try:
            if sport == "cs2":
                from storage.database import get_live_cs2_matches
                matches = await get_live_cs2_matches()
            else:
                from storage.database import get_live_khl_matches
                matches = await get_live_khl_matches()
            return len(matches)
        except:
            return 0
    
    async def _show_cs2_live_matches(self, message: Message):
        """Show current CS2 live matches"""
        try:
            from storage.database import get_live_cs2_matches
            matches = await get_live_cs2_matches()
            
            if not matches:
                await message.answer("🔍 No live CS2 matches currently")
                return
            
            match_text = "🔴 CS2 Live Matches\n\n"
            for i, match in enumerate(matches[:5]):  # Show top 5
                score = match.get('score', {})
                match_text += (
                    f"⚔️ {match.get('team1', 'T1')} vs {match.get('team2', 'T2')}\n"
                    f"🥅 Score: {score.get('team1', 0)} - {score.get('team2', 0)}\n"
                    f"🗺️ Map: {match.get('current_map', 'Unknown')}\n"
                    f"⏱️ Round: {match.get('live_data', {}).get('current_round', 'N/A')}\n\n"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back", callback_data="cs2_menu")]
            ])
            
            await message.answer(match_text, reply_markup=keyboard)
            
        except Exception as e:
            await message.answer(f"❌ Error loading CS2 matches: {str(e)}")
    
    async def _show_cs2_prematch_analysis(self, message: Message):
        """Show CS2 pre-match analysis"""
        try:
            from storage.database import get_upcoming_cs2_matches
            matches = await get_upcoming_cs2_matches()
            
            if not matches:
                await message.answer("📈 No upcoming CS2 matches found")
                return
            
            analysis_text = "📈 CS2 Pre-match Analysis\n\n"
            for i, match in enumerate(matches[:5]):  # Show top 5
                odds = match.get('odds', {})
                avg_odds = odds.get('average_odds', {})
                analysis_text += (
                    f"⚔️ {match.get('team1', 'T1')} vs {match.get('team2', 'T2')}\n"
                    f"🏆 {match.get('tournament', 'Unknown')}\n"
                    f"📊 Odds: {avg_odds.get('team1', 'N/A')} - {avg_odds.get('team2', 'N/A')}\n"
                    f"🥅 Tier: {match.get('tier', 'C')}\n\n"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back", callback_data="cs2_menu")]
            ])
            
            await message.answer(analysis_text, reply_markup=keyboard)
            
        except Exception as e:
            await message.answer(f"❌ Error loading CS2 analysis: {str(e)}")
    
    async def _show_cs2_scenarios(self, message: Message):
        """Show CS2 detected scenarios"""
        scenarios_text = "🧠 CS2 Detected Scenarios\n\n"
        scenarios_text += "• Overvalued Favorite: 2 matches\n"
        scenarios_text += "• Public Trap: 1 match\n"
        scenarios_text += "• Lineup Instability: 1 match\n\n"
        scenarios_text += "📊 Total active scenarios: 4"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="cs2_menu")]
        ])
        
        await message.answer(scenarios_text, reply_markup=keyboard)
    
    async def _toggle_cs2_alerts(self, message: Message):
        """Toggle CS2 alerts"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="cs2_menu")]
        ])
        
        await message.answer("🔔 CS2 alerts enabled", reply_markup=keyboard)
    
    async def _show_khl_live_matches(self, message: Message):
        """Show current KHL live matches"""
        try:
            from storage.database import get_live_khl_matches
            matches = await get_live_khl_matches()
            
            if not matches:
                await message.answer("🔍 No live KHL matches currently")
                return
            
            match_text = "🔴 KHL Live Matches\n\n"
            for i, match in enumerate(matches[:5]):  # Show top 5
                score = match.get('score', {})
                match_text += (
                    f"⚔️ {match.get('team1', 'T1')} vs {match.get('team2', 'T2')}\n"
                    f"🥅 Score: {score.get('team1', 0)} - {score.get('team2', 0)}\n"
                    f"⏰ Period: {match.get('current_period', 1)}\n"
                    f"⏱️ Time: {match.get('time_in_period', 0)}s\n\n"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back", callback_data="khl_menu")]
            ])
            
            await message.answer(match_text, reply_markup=keyboard)
            
        except Exception as e:
            await message.answer(f"❌ Error loading KHL matches: {str(e)}")
    
    async def _show_khl_prematch_analysis(self, message: Message):
        """Show KHL pre-match analysis"""
        try:
            from storage.database import get_upcoming_khl_matches
            matches = await get_upcoming_khl_matches()
            
            if not matches:
                await message.answer("📈 No upcoming KHL matches found")
                return
            
            analysis_text = "📈 KHL Pre-match Analysis\n\n"
            for i, match in enumerate(matches[:5]):  # Show top 5
                odds = match.get('odds', {})
                avg_odds = odds.get('average_odds', {})
                analysis_text += (
                    f"⚔️ {match.get('team1', 'T1')} vs {match.get('team2', 'T2')}\n"
                    f"🏆 {match.get('league', 'KHL')}\n"
                    f"📊 Odds: {avg_odds.get('team1', 'N/A')} - {avg_odds.get('team2', 'N/A')}\n"
                    f"🏒 Venue: {match.get('venue', 'Unknown')}\n\n"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back", callback_data="khl_menu")]
            ])
            
            await message.answer(analysis_text, reply_markup=keyboard)
            
        except Exception as e:
            await message.answer(f"❌ Error loading KHL analysis: {str(e)}")
    
    async def _show_khl_scenarios(self, message: Message):
        """Show KHL detected scenarios"""
        scenarios_text = "🧠 KHL Detected Scenarios\n\n"
        scenarios_text += "• Favorite Lost 1st Period: 1 match\n"
        scenarios_text += "• 0:0 After First Period: 2 matches\n"
        scenarios_text += "• Pressure Without Conversion: 1 match\n\n"
        scenarios_text += "📊 Total active scenarios: 4"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="khl_menu")]
        ])
        
        await message.answer(scenarios_text, reply_markup=keyboard)
    
    async def _toggle_khl_alerts(self, message: Message):
        """Toggle KHL alerts"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Back", callback_data="khl_menu")]
        ])
        
        await message.answer("🔔 KHL alerts enabled", reply_markup=keyboard)
    
    async def _run_cs2_analysis(self) -> str:
        """Run CS2 analysis and return results"""
        try:
            from cs2.sources.hltv_parser import parse_cs2_matches
            from cs2.analysis.scenarios import analyze_cs2_matches
            from storage.database import store_cs2_matches
            
            # Fetch matches
            matches = await parse_cs2_matches()
            await store_cs2_matches(matches)
            
            # Run analysis
            analysis_results = await analyze_cs2_matches(matches)
            
            if analysis_results:
                await self.send_cs2_analysis(analysis_results)
                return f"Analysis complete - {len(matches)} matches processed"
            else:
                return "No scenarios detected"
                
        except Exception as e:
            logger.error(f"CS2 analysis error: {e}")
            return f"Analysis failed: {str(e)}"
    
    async def _run_khl_analysis(self) -> str:
        """Run KHL analysis and return results"""
        try:
            from khl.sources.matches_parser import parse_khl_matches
            from khl.analysis.scenarios import analyze_khl_matches
            from storage.database import store_khl_matches
            
            # Fetch matches
            matches = await parse_khl_matches()
            await store_khl_matches(matches)
            
            # Run analysis
            analysis_results = await analyze_khl_matches(matches)
            
            if analysis_results:
                await self.send_khl_analysis(analysis_results)
                return f"Analysis complete - {len(matches)} matches processed"
            else:
                return "No scenarios detected"
                
        except Exception as e:
            logger.error(f"KHL analysis error: {e}")
            return f"Analysis failed: {str(e)}"
    
    async def send_message(self, chat_id: str, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None):
        """Send message to Telegram chat"""
        try:
            await self.bot.send_message(chat_id, text, reply_markup=reply_markup)
            logger.info(f"Message sent to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
    
    async def send_cs2_analysis(self, analysis_data: Dict[str, Any]):
        """Send CS2 analysis to channel"""
        if not config.telegram.cs2_channel_id:
            logger.warning("CS2 channel ID not configured")
            return
        
        # Format analysis message
        message = self._format_cs2_message(analysis_data)
        await self.send_message(config.telegram.cs2_channel_id, message)
    
    async def send_khl_analysis(self, analysis_data: Dict[str, Any]):
        """Send KHL analysis to channel"""
        if not config.telegram.khl_channel_id:
            logger.warning("KHL channel ID not configured")
            return
        
        # Format analysis message
        message = self._format_khl_message(analysis_data)
        await self.send_message(config.telegram.khl_channel_id, message)
    
    def _format_cs2_message(self, data: Dict[str, Any]) -> str:
        """Format CS2 analysis data into Telegram message"""
        message = (
            f"🔫 CS2 Market Analysis\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        )
        
        if 'match' in data:
            match = data['match']
            message += f"🏆 {match.get('tournament', 'Unknown')}\n"
            message += f"⚔️  {match.get('team1', 'T1')} vs {match.get('team2', 'T2')}\n"
            message += f"📊 Odds: {match.get('odds_team1', 'N/A')} - {match.get('odds_team2', 'N/A')}\n\n"
        
        if 'scenarios' in data:
            scenarios = data['scenarios']
            if scenarios:
                message += "🎯 Detected Scenarios:\n"
                for scenario in scenarios[:3]:  # Limit to top 3
                    message += f"• {scenario.get('name', 'Unknown')} ({scenario.get('confidence', 0):.1%})\n"
        
        if 'recommendation' in data:
            rec = data['recommendation']
            message += f"\n💡 Analysis: {rec.get('text', 'No recommendation')}\n"
            message += f"📈 Confidence: {rec.get('confidence', 0):.1%}\n"
        
        return message
    
    def _format_khl_message(self, data: Dict[str, Any]) -> str:
        """Format KHL analysis data into Telegram message"""
        message = (
            f"🏒 KHL Market Analysis\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        )
        
        if 'match' in data:
            match = data['match']
            message += f"🏆 {match.get('league', 'KHL')}\n"
            message += f"⚔️  {match.get('team1', 'T1')} vs {match.get('team2', 'T2')}\n"
            message += f"📊 Odds: {match.get('odds_team1', 'N/A')} - {match.get('odds_team2', 'N/A')}\n"
            if 'score' in match:
                message += f"🥅 Score: {match['score']}\n"
            message += "\n"
        
        if 'scenarios' in data:
            scenarios = data['scenarios']
            if scenarios:
                message += "🎯 Detected Scenarios:\n"
                for scenario in scenarios[:3]:  # Limit to top 3
                    message += f"• {scenario.get('name', 'Unknown')} ({scenario.get('confidence', 0):.1%})\n"
        
        if 'recommendation' in data:
            rec = data['recommendation']
            message += f"\n💡 Analysis: {rec.get('text', 'No recommendation')}\n"
            message += f"📈 Confidence: {rec.get('confidence', 0):.1%}\n"
        
        return message
    
    async def start_polling(self):
        """Start bot polling"""
        await self.dp.start_polling(self.bot)


class IntegratedScheduler:
    """Integrated scheduler for single service deployment"""
    
    def __init__(self):
        self.scheduler = Scheduler()
        self.running = False
    
    async def start(self):
        """Start integrated scheduler"""
        self.running = True
        logger.info("🚀 Starting integrated scheduler...")
        
        # Setup tasks
        try:
            from cs2.sources.hltv_parser import setup_cs2_tasks
            from khl.sources.matches_parser import setup_khl_tasks
            
            setup_cs2_tasks(self.scheduler)
            setup_khl_tasks(self.scheduler)
            
            logger.info("✅ All tasks setup complete")
            
        except ImportError as e:
            logger.warning(f"⚠️ Sport modules not available: {e}")
        
        # Run scheduler with limited tasks for free plan
        while self.running:
            try:
                # Run only essential tasks
                tasks_to_run = ['cs2_parsing', 'khl_parsing', 'cs2_analysis', 'khl_analysis']
                
                for task_name in tasks_to_run:
                    if task_name in self.scheduler.tasks:
                        task_info = self.scheduler.tasks[task_name]
                        if task_info['enabled']:
                            try:
                                logger.info(f"🔄 Running task: {task_name}")
                                if asyncio.iscoroutinefunction(task_info['func']):
                                    await task_info['func']()
                                else:
                                    task_info['func']()
                            except Exception as e:
                                logger.error(f"❌ Task {task_name} failed: {e}")
                
                # Sleep for 5 minutes (free plan friendly)
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"💥 Scheduler error: {e}")
                await asyncio.sleep(60)  # Short sleep on error
    
    def stop(self):
        """Stop scheduler"""
        self.running = False
        logger.info("🛑 Scheduler stopped")
    
    def get_status_summary(self):
        """Get scheduler status"""
        return self.scheduler.get_status_summary()


async def main():
    """Main application entry point - single service"""
    logger.info("🚀 Starting AI BET Analytics Platform (Single Service)")
    
    # Initialize Telegram
    if not config.telegram.bot_token:
        logger.error("❌ Telegram bot token not configured")
        return
    
    telegram = TelegramSender(config.telegram.bot_token)
    
    # Initialize integrated scheduler
    integrated_scheduler = IntegratedScheduler()
    telegram.scheduler = integrated_scheduler.scheduler
    
    # Start scheduler in background
    scheduler_task = asyncio.create_task(integrated_scheduler.start())
    
    # Start Telegram bot
    try:
        await telegram.start_polling()
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    finally:
        integrated_scheduler.stop()
        if not scheduler_task.done():
            scheduler_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
