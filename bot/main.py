"""
AIBET MVP Telegram Bot
Main bot implementation for displaying signals and statistics
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo
)

from database.connection import get_db_context
from ml.predictor import Predictor

logger = logging.getLogger(__name__)

class AIBOTBot:
    """AIBET MVP Telegram Bot"""
    
    def __init__(self, bot_token: str, admin_id: int):
        self.bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        self.admin_id = admin_id
        self._initialized = False
        
        # Register handlers
        self.register_handlers()
        
        logger.info(f"🤖 AIBOT Bot initialized (admin: {admin_id})")
    
    def register_handlers(self):
        """Register all bot handlers"""
        logger.info("🔧 Registering bot handlers")
        
        # Commands
        self.dp.message(Command('start'))(self.cmd_start)
        self.dp.message(Command('help'))(self.cmd_help)
        self.dp.message(Command('signals'))(self.cmd_signals)
        self.dp.message(Command('matches'))(self.cmd_matches)
        self.dp.message(Command('stats'))(self.cmd_stats)
        self.dp.message(Command('predict'))(self.cmd_predict)
        self.dp.message(Command('miniapp'))(self.cmd_miniapp)
        self.dp.message(Command('admin'))(self.cmd_admin)
        
        # Callback handlers
        self.dp.callback_query()(self.handle_callback)
        
        # Message handlers
        self.dp.message()(self.handle_message)
    
    async def cmd_start(self, message: Message):
        """Start command"""
        await message.answer(
            "🎯 <b>Добро пожаловать в AIBET MVP!</b>\n\n"
            "Аналитическая платформа ставок на CS2 и КХЛ\n"
            "<b>Без live-данных, только умный анализ</b>\n\n"
            "📊 <b>Доступные команды:</b>\n"
            "/signals - Активные сигналы\n"
            "/matches - Предстоящие матчи\n"
            "/stats - Статистика\n"
            "/predict - Прогноз матча\n"
            "/miniapp - Mini приложение\n\n"
            "🤖 Начните с команды /signals",
            reply_markup=self.get_main_keyboard()
        )
    
    async def cmd_help(self, message: Message):
        """Help command"""
        help_text = """
🎯 <b>AIBET MVP - Справка</b>

📊 <b>Основные команды:</b>
/start - Главное меню
/signals - Активные сигналы
/matches - Предстоящие матчи
/stats - Статистика команд
/predict - Прогноз матча
/miniapp - Mini приложение

🎯 <b>О сигналах:</b>
• Генерируются ИИ на истории
• Confidence ≥ 65%
• Value score ≥ 0.1
• С объяснением логики

📈 <b>Фичи:</b>
• ML модели (Logistic Regression, RF)
• Feature engineering
• Анализ формы, H2H, рейтингов
• Graceful fallbacks

⚡ <b>Режим:</b>
Pre-Match анализ без live данных
        """
        await message.answer(help_text, reply_markup=self.get_main_keyboard())
    
    async def cmd_signals(self, message: Message):
        """Show active signals"""
        try:
            with get_db_context() as db:
                from database.models import Signal, Match
                
                # Get active signals
                signals = db.query(Signal).filter(
                    Signal.is_active == True
                ).order_by(Signal.created_at.desc()).limit(10).all()
                
                if not signals:
                    await message.answer("🎯 Активных сигналов пока нет")
                    return
                
                response = "🎯 <b>Активные сигналы:</b>\n\n"
                
                for signal in signals:
                    confidence_emoji = "🔥" if signal.confidence >= 80 else "✅" if signal.confidence >= 70 else "⚠️"
                    
                    response += f"{confidence_emoji} <b>{signal.match.team1.name}</b> vs <b>{signal.match.team2.name}</b>\n"
                    response += f"🏆 {signal.sport.upper()}\n"
                    response += f"🎯 Прогноз: {signal.prediction.upper()}\n"
                    response += f"📊 Вероятность: {signal.probability:.1%}\n"
                    response += f"💪 Уверенность: {signal.confidence:.1f}%\n"
                    if signal.value_score:
                        response += f"💰 Value: {signal.value_score:.2f}\n"
                    if signal.explanation:
                        response += f"📝 {signal.explanation}\n"
                    response += f"📅 {signal.created_at.strftime('%d.%m %H:%M')}\n\n"
                
                # Split message if too long
                if len(response) > 4000:
                    parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
                    for part in parts:
                        await message.answer(part)
                else:
                    await message.answer(response)
                
        except Exception as e:
            logger.error(f"Error in /signals: {e}")
            await message.answer("❌ Ошибка загрузки сигналов")
    
    async def cmd_matches(self, message: Message):
        """Show upcoming matches"""
        try:
            with get_db_context() as db:
                from database.models import Match, Team
                
                # Get upcoming matches
                matches = db.query(Match).filter(
                    Match.is_upcoming == True
                ).order_by(Match.date).limit(10).all()
                
                if not matches:
                    await message.answer("📊 Предстоящих матчей нет")
                    return
                
                response = "📅 <b>Предстоящие матчи:</b>\n\n"
                
                for match in matches:
                    sport_emoji = "🔫" if match.sport == "cs2" else "🏒"
                    response += f"{sport_emoji} <b>{match.team1.name}</b> vs <b>{match.team2.name}</b>\n"
                    response += f"🏆 {match.tournament or 'Unknown'}\n"
                    response += f"📅 {match.date.strftime('%d.%m %H:%M')}\n"
                    response += f"📊 Рейтинг: {match.team1.rating} vs {match.team2.rating}\n\n"
                
                await message.answer(response, reply_markup=self.get_main_keyboard())
                
        except Exception as e:
            logger.error(f"Error in /matches: {e}")
            await message.answer("❌ Ошибка загрузки матчей")
    
    async def cmd_stats(self, message: Message):
        """Show statistics"""
        try:
            with get_db_context() as db:
                from database.models import Team, Match, Signal
                
                # Get statistics
                total_teams = db.query(Team).count()
                cs2_teams = db.query(Team).filter(Team.sport == 'cs2').count()
                khl_teams = db.query(Team).filter(Team.sport == 'khl').count()
                
                total_matches = db.query(Match).count()
                upcoming_matches = db.query(Match).filter(Match.is_upcoming == True).count()
                
                total_signals = db.query(Signal).count()
                active_signals = db.query(Signal).filter(Signal.is_active == True).count()
                
                stats_text = f"""
📊 <b>Статистика AIBET MVP:</b>

🏆 <b>Команды:</b>
• Всего: {total_teams}
• CS2: {cs2_teams}
• КХЛ: {khl_teams}

📅 <b>Матчи:</b>
• Всего: {total_matches}
• Предстоящие: {upcoming_matches}

🎯 <b>Сигналы:</b>
• Всего: {total_signals}
• Активные: {active_signals}

🤖 <b>ML модели:</b>
• Logistic Regression
• Random Forest
• Feature engineering

⚡ <b>Режим:</b>
Pre-Match анализ без live данных
                """
                
                await message.answer(stats_text, reply_markup=self.get_main_keyboard())
                
        except Exception as e:
            logger.error(f"Error in /stats: {e}")
            await message.answer("❌ Ошибка загрузки статистики")
    
    async def cmd_predict(self, message: Message):
        """Predict match (interactive)"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔫 CS2", callback_data="predict_cs2")],
            [InlineKeyboardButton(text="🏒 КХЛ", callback_data="predict_khl")]
        ])
        
        await message.answer(
            "🎯 <b>Выберите спорт для прогноза:</b>",
            reply_markup=keyboard
        )
    
    async def cmd_miniapp(self, message: Message):
        """Open Mini App"""
        web_app_url = os.getenv("MINI_APP_URL", "https://aibet-mvp.onrender.com")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🚀 Открыть AIBET Mini App",
                web_app=WebAppInfo(url=web_app_url)
            )]
        ])
        
        await message.answer(
            "🚀 <b>AIBET Mini App</b>\n\n"
            "Полная аналитика и прогнозы в удобном интерфейсе",
            reply_markup=keyboard
        )
    
    async def cmd_admin(self, message: Message):
        """Admin commands"""
        if message.from_user.id != self.admin_id:
            await message.answer("❌ Доступ запрещен")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить модели", callback_data="admin_update_models")],
            [InlineKeyboardButton(text="🎯 Генерировать сигналы", callback_data="admin_generate_signals")],
            [InlineKeyboardButton(text="📊 Статистика системы", callback_data="admin_system_stats")]
        ])
        
        await message.answer(
            "🔧 <b>Админ панель AIBET MVP</b>",
            reply_markup=keyboard
        )
    
    async def handle_callback(self, callback: CallbackQuery):
        """Handle callback queries"""
        try:
            await callback.answer()
            
            data = callback.data
            
            if data == "predict_cs2":
                await self._show_matches_for_prediction(callback, "cs2")
            elif data == "predict_khl":
                await self._show_matches_for_prediction(callback, "khl")
            elif data.startswith("predict_match_"):
                match_id = int(data.split("_")[2])
                await self._predict_match(callback, match_id)
            elif data == "admin_update_models":
                await self._admin_update_models(callback)
            elif data == "admin_generate_signals":
                await self._admin_generate_signals(callback)
            elif data == "admin_system_stats":
                await self._admin_system_stats(callback)
            else:
                await callback.message.answer("❌ Неизвестное действие")
                
        except Exception as e:
            logger.error(f"Error in callback: {e}")
            await callback.answer("❌ Ошибка")
    
    async def _show_matches_for_prediction(self, callback: CallbackQuery, sport: str):
        """Show matches for prediction"""
        try:
            with get_db_context() as db:
                from database.models import Match
                
                matches = db.query(Match).filter(
                    Match.sport == sport,
                    Match.is_upcoming == True
                ).order_by(Match.date).limit(10).all()
                
                if not matches:
                    await callback.message.answer(f"📊 Предстоящих матчей {sport.upper()} нет")
                    return
                
                keyboard = []
                for match in matches:
                    keyboard.append([InlineKeyboardButton(
                        text=f"{match.team1.name} vs {match.team2.name}",
                        callback_data=f"predict_match_{match.id}"
                    )])
                
                await callback.message.answer(
                    f"🎯 <b>Выберите матч {sport.upper()}:</b>",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing matches for prediction: {e}")
            await callback.message.answer("❌ Ошибка загрузки матчей")
    
    async def _predict_match(self, callback: CallbackQuery, match_id: int):
        """Predict specific match"""
        try:
            with get_db_context() as db:
                predictor = Predictor(db)
                prediction = predictor.predict_match(match_id)
                
                if 'error' in prediction:
                    await callback.message.answer(f"❌ Ошибка прогноза: {prediction['error']}")
                    return
                
                confidence_emoji = "🔥" if prediction['confidence'] >= 80 else "✅" if prediction['confidence'] >= 70 else "⚠️"
                
                response = f"""
{confidence_emoji} <b>Прогноз матча:</b>

🏆 {prediction['team1']} vs {prediction['team2']}
📊 Спорт: {prediction['sport'].upper()}

🎯 <b>Прогноз:</b> {prediction['prediction'].upper()}
📊 <b>Вероятность:</b> {prediction['probabilities'][prediction['prediction']]:.1%}
💪 <b>Уверенность:</b> {prediction['confidence']:.1f}%
💰 <b>Value Score:</b> {prediction['value_score']:.2f}

📝 <b>Объяснение:</b>
{prediction['explanation']}

🤖 <b>Метод:</b> {prediction['method']}
                """
                
                await callback.message.answer(response)
                
        except Exception as e:
            logger.error(f"Error predicting match: {e}")
            await callback.message.answer("❌ Ошибка прогноза")
    
    async def _admin_update_models(self, callback: CallbackQuery):
        """Admin: Update models"""
        try:
            with get_db_context() as db:
                predictor = Predictor(db)
                
                # Initialize models for both sports
                cs2_success = predictor.initialize_models('cs2')
                khl_success = predictor.initialize_models('khl')
                
                await callback.message.answer(
                    f"🔄 <b>Обновление моделей:</b>\n"
                    f"CS2: {'✅ Успешно' if cs2_success else '❌ Ошибка'}\n"
                    f"КХЛ: {'✅ Успешно' if khl_success else '❌ Ошибка'}"
                )
                
        except Exception as e:
            logger.error(f"Error updating models: {e}")
            await callback.message.answer("❌ Ошибка обновления моделей")
    
    async def _admin_generate_signals(self, callback: CallbackQuery):
        """Admin: Generate signals"""
        try:
            with get_db_context() as db:
                predictor = Predictor(db)
                
                # Generate signals for both sports
                cs2_signals = predictor.generate_signals('cs2', limit=5)
                khl_signals = predictor.generate_signals('khl', limit=5)
                
                await callback.message.answer(
                    f"🎯 <b>Генерация сигналов:</b>\n"
                    f"CS2: {len(cs2_signals)} сигналов\n"
                    f"КХЛ: {len(khl_signals)} сигналов"
                )
                
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            await callback.message.answer("❌ Ошибка генерации сигналов")
    
    async def _admin_system_stats(self, callback: CallbackQuery):
        """Admin: System statistics"""
        try:
            with get_db_context() as db:
                from database.models import Team, Match, Signal, ModelMetrics
                
                teams = db.query(Team).count()
                matches = db.query(Match).count()
                signals = db.query(Signal).count()
                models = db.query(ModelMetrics).count()
                
                await callback.message.answer(
                    f"📊 <b>Статистика системы:</b>\n"
                    f"Команды: {teams}\n"
                    f"Матчи: {matches}\n"
                    f"Сигналы: {signals}\n"
                    f"ML модели: {models}"
                )
                
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            await callback.message.answer("❌ Ошибка получения статистики")
    
    async def handle_message(self, message: Message):
        """Handle regular messages"""
        text = message.text.lower() if message.text else ""
        
        if text in ['меню', 'start', 'главное']:
            await self.cmd_start(message)
        elif text in ['помощь', 'help']:
            await self.cmd_help(message)
        elif text in ['сигналы', 'signals']:
            await self.cmd_signals(message)
        elif text in ['матчи', 'matches']:
            await self.cmd_matches(message)
        elif text in ['статистика', 'stats']:
            await self.cmd_stats(message)
        else:
            await message.answer(
                "🤖 Используйте команды из меню:\n"
                "/signals - Сигналы\n"
                "/matches - Матчи\n"
                "/stats - Статистика\n"
                "/miniapp - Приложение",
                reply_markup=self.get_main_keyboard()
            )
    
    def get_main_keyboard(self) -> ReplyKeyboardMarkup:
        """Get main keyboard"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🎯 Сигналы"), KeyboardButton(text="📊 Матчи")],
                [KeyboardButton(text="📈 Статистика"), KeyboardButton(text="🚀 Mini App")],
                [KeyboardButton(text="❓ Помощь")]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        return keyboard
    
    async def start(self):
        """Start the bot"""
        if self._initialized:
            return
        
        logger.info("🤖 Starting AIBOT Bot...")
        
        # Set bot commands
        await self.bot.set_my_commands([
            types.BotCommand(command="start", description="🚀 Главное меню"),
            types.BotCommand(command="help", description="❓ Помощь"),
            types.BotCommand(command="signals", description="🎯 Активные сигналы"),
            types.BotCommand(command="matches", description="📊 Предстоящие матчи"),
            types.BotCommand(command="stats", description="📈 Статистика"),
            types.BotCommand(command="predict", description="🎯 Прогноз матча"),
            types.BotCommand(command="miniapp", description="🚀 Mini приложение"),
            types.BotCommand(command="admin", description="🔧 Админ панель")
        ])
        
        # Start polling
        await self.dp.start_polling(self.bot)
        self._initialized = True
        
        logger.info("✅ AIBOT Bot started successfully")

async def create_bot(bot_token: str, admin_id: int) -> AIBOTBot:
    """Create bot instance"""
    return AIBOTBot(bot_token, admin_id)
