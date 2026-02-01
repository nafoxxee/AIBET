#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real Telegram Bot
Полнофункциональный бот с реальными данными и кнопкой Mini App
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, InlineKeyboardMarkup, 
    InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo, CallbackQuery
)

from database import db_manager, User
from signal_generator_real import real_signal_generator
from ml_real import real_ml_models

logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "379036860"))
MINI_APP_URL = "https://aibet-mini-prilozhenie.onrender.com/"

class RealTelegramBot:
    def __init__(self, bot_token: str, admin_id: int, db_manager_instance):
        self.bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        self.admin_id = admin_id
        self.db_manager = db_manager_instance
        self._initialized = False
        
        # Регистрируем хендлеры
        self.register_handlers()
        
        logger.info(f"🤖 Real Telegram Bot initialized (admin: {admin_id})")
    
    def register_handlers(self):
        """Регистрация всех хендлеров"""
        logger.info("🔧 Registering bot handlers")
        
        # Команды
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_signals, Command("signals"))
        self.dp.message.register(self.cmd_stats, Command("stats"))
        self.dp.message.register(self.cmd_analyze, Command("analyze"))
        self.dp.message.register(self.cmd_admin, Command("admin"))
        
        # Inline кнопки
        self.dp.callback_query.register(self.cb_main_menu, F.data == "main_menu")
        self.dp.callback_query.register(self.cb_live_matches, F.data == "live_matches")
        self.dp.callback_query.register(self.cb_signals, F.data == "signals")
        self.dp.callback_query.register(self.cb_stats, F.data == "stats")
        self.dp.callback_query.register(self.cb_analyze, F.data == "analyze")
        
        # Любые другие сообщения
        self.dp.message.register(self.handle_message)
        
        logger.info("✅ All handlers registered")
    
    async def initialize(self):
        """Инициализация бота"""
        if self._initialized:
            return
            
        logger.info("🤖 Initializing Real Telegram Bot")
        logger.info(f"🔑 Admin ID: {self.admin_id}")
        
        try:
            # Проверяем токен
            if not self.bot.token:
                raise ValueError("Bot token is empty")
            
            # Проверяем подключение к Telegram
            bot_info = await self.bot.get_me()
            logger.info(f"🤖 Connected to bot: @{bot_info.username} (ID: {bot_info.id})")
            
            self._initialized = True
            logger.info("🎉 Real Telegram Bot initialized successfully")
            
        except Exception as e:
            logger.exception(f"❌ Error initializing bot: {e}")
            raise
    
    async def cmd_start(self, message: Message):
        """Команда /start"""
        logger.info(f"🎯 /start command from user {message.from_user.id} (@{message.from_user.username})")
        
        try:
            # Регистрируем пользователя
            user = User(telegram_id=message.from_user.id, is_admin=(message.from_user.id == self.admin_id))
            await self.db_manager.add_user(user)
            
            logger.info(f"✅ User {message.from_user.id} registered (admin: {user.is_admin})")
            
            # Главное меню с кнопкой Mini App
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚀 Открыть AIBET Mini App", web_app=WebAppInfo(url=MINI_APP_URL))
                ],
                [
                    InlineKeyboardButton(text="📊 Анализ", callback_data="analyze"),
                    InlineKeyboardButton(text="🔴 Live", callback_data="live_matches")
                ],
                [
                    InlineKeyboardButton(text="🎯 Сигналы", callback_data="signals"),
                    InlineKeyboardButton(text="📈 Статистика", callback_data="stats")
                ]
            ])
            
            await message.answer(
                f"🎯 <b>Добро пожаловать в AIBET!</b>\n\n"
                f"🤖 AI-анализ матчей CS2 и КХЛ\n"
                f"📊 Точность прогнозов >70%\n"
                f"🎯 Автоматические сигналы\n\n"
                f"Выберите действие ниже:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.exception(f"❌ Error in cmd_start: {e}")
            await message.answer("❌ Ошибка загрузки меню")
    
    async def cmd_help(self, message: Message):
        """Команда /help"""
        logger.info(f"📖 /help command from user {message.from_user.id}")
        
        help_text = (
            "<b>📖 Справка AIBET</b>\n\n"
            "<b>🔥 Основные команды:</b>\n"
            "/start - Главное меню\n"
            "/signals - Последние сигналы\n"
            "/stats - Статистика системы\n"
            "/analyze - AI анализ матчей\n"
            "/help - Эта справка\n\n"
            "<b>📢 Каналы:</b>\n"
            "• @aibetcsgo - CS2 сигналы\n"
            "• @aibetkhl - КХЛ сигналы\n\n"
            "<b>🚀 Mini App:</b>\n"
            "Полная аналитика и статистика в веб-приложении\n\n"
            "<i>По вопросам: @admin</i>"
        )
        
        await message.answer(help_text)
        logger.info(f"✅ Help message sent to user {message.from_user.id}")
    
    async def cmd_signals(self, message: Message):
        """Команда /signals"""
        logger.info(f"📢 /signals command from user {message.from_user.id}")
        
        try:
            signals = await real_signal_generator.get_high_confidence_signals(min_confidence=0.70)
            
            if not signals:
                await message.answer("📢 Пока нет сигналов с высокой уверенностью")
                logger.info(f"📢 No high confidence signals for user {message.from_user.id}")
                return
            
            text = f"📢 <b>Последние сигналы ({len(signals)})</b>\n\n"
            
            for i, signal in enumerate(signals[:5], 1):
                confidence = int(signal.confidence * 100)
                text += f"{i}. <b>{signal.sport.upper()}</b>\n"
                text += f"📊 {signal.signal[:100]}...\n"
                text += f"🎯 Уверенность: {confidence}%\n"
                text += f"🕐 {signal.created_at.strftime('%H:%M')}\n\n"
            
            await message.answer(text)
            logger.info(f"✅ Signals list sent to user {message.from_user.id} ({len(signals)} signals)")
            
        except Exception as e:
            logger.exception(f"❌ Error in cmd_signals: {e}")
            await message.answer("❌ Ошибка загрузки сигналов")
    
    async def cmd_stats(self, message: Message):
        """Команда /stats"""
        logger.info(f"📊 /stats command from user {message.from_user.id}")
        
        try:
            # Получаем статистику сигналов
            signal_stats = await real_signal_generator.get_signal_statistics()
            
            # Получаем статистику ML моделей
            model_stats = real_ml_models.get_model_stats()
            
            # Получаем количество матчей
            total_matches = len(await self.db_manager.get_matches(limit=1000))
            live_matches = len(await self.db_manager.get_live_matches(limit=50))
            
            text = (
                "<b>📊 Статистика AIBET</b>\n\n"
                f"🎯 Всего сигналов за неделю: <b>{signal_stats.get('total_week_signals', 0)}</b>\n"
                f"🔫 CS2 сигналы: <b>{signal_stats.get('cs2_signals', 0)}</b>\n"
                f"🏒 КХЛ сигналы: <b>{signal_stats.get('khl_signals', 0)}</b>\n"
                f"📈 Средняя уверенность: <b>{signal_stats.get('avg_confidence', 0):.1%}</b>\n"
                f"🔥 Высокая уверенность: <b>{signal_stats.get('high_confidence_signals', 0)}</b>\n\n"
                f"🎮 Всего матчей: <b>{total_matches}</b>\n"
                f"🔴 Live матчи: <b>{live_matches}</b>\n\n"
                f"🤖 ML статус: <b>{'Обучена' if model_stats.get('trained') else 'Обучается'}</b>\n"
            )
            
            if model_stats.get('training_stats'):
                training = model_stats['training_stats']
                text += f"📈 Точность RF: <b>{training.get('rf_accuracy', 0):.1%}</b>\n"
                text += f"📈 Точность LR: <b>{training.get('lr_accuracy', 0):.1%}</b>\n"
            
            await message.answer(text)
            logger.info(f"✅ Statistics sent to user {message.from_user.id}")
            
        except Exception as e:
            logger.exception(f"❌ Error in cmd_stats: {e}")
            await message.answer("❌ Ошибка загрузки статистики")
    
    async def cmd_analyze(self, message: Message):
        """Команда /analyze"""
        logger.info(f"🤖 /analyze command from user {message.from_user.id}")
        
        try:
            # Проверяем доступность ML моделей
            if not real_ml_models._trained:
                await message.answer("🤖 ML модели еще не обучены. Анализ недоступен.")
                logger.info(f"🤖 ML not trained for user {message.from_user.id}")
                return
            
            # Получаем предстоящие матчи
            matches = await self.db_manager.get_upcoming_matches(limit=5)
            
            if not matches:
                await message.answer("🤖 Сейчас нет предстоящих матчей для анализа")
                logger.info(f"🤖 No upcoming matches for analysis for user {message.from_user.id}")
                return
            
            text = f"🤖 <b>AI анализ матчей</b>\n\n"
            
            for i, match in enumerate(matches[:3], 1):
                # Получаем предсказание
                prediction = await real_ml_models.predict_match(match)
                
                if not prediction:
                    text += f"{i}. <b>{match.team1}</b> vs <b>{match.team2}</b>\n"
                    text += f"🏆 {match.features.get('tournament', 'Unknown')}\n"
                    text += f"⚠️ Анализ недоступен\n\n"
                else:
                    confidence = int(prediction['confidence'] * 100)
                    text += f"{i}. <b>{match.team1}</b> vs <b>{match.team2}</b>\n"
                    text += f"🏆 {match.features.get('tournament', 'Unknown')}\n"
                    text += f"🎯 {prediction['prediction']}\n"
                    text += f"📊 Уверенность: {confidence}%\n"
                    text += f"🧠 {prediction.get('explanation', 'Статистический анализ')}\n\n"
            
            await message.answer(text)
            logger.info(f"✅ Analysis sent to user {message.from_user.id}")
            
        except Exception as e:
            logger.exception(f"❌ Error in cmd_analyze: {e}")
            await message.answer("❌ Ошибка анализа матчей")
    
    async def cmd_admin(self, message: Message):
        """Команда /admin"""
        logger.info(f"🔑 /admin command from user {message.from_user.id}")
        
        # Проверяем админа
        if message.from_user.id != self.admin_id:
            await message.answer("🚫 Доступ запрещен")
            return
        
        logger.info(f"✅ Admin access granted to user {message.from_user.id}")
        
        try:
            # Получаем статистику
            signal_stats = await real_signal_generator.get_signal_statistics()
            model_stats = real_ml_models.get_model_stats()
            
            text = (
                "<b>🔑 Панель администратора</b>\n\n"
                f"📢 Сигналов за неделю: <b>{signal_stats.get('total_week_signals', 0)}</b>\n"
                f"📈 Опубликовано: <b>{signal_stats.get('published_signals', 0)}</b>\n"
                f"🤖 ML обучена: <b>{'Да' if model_stats.get('trained') else 'Нет'}</b>\n\n"
                "<b>🔧 Управление:</b>\n"
                "• /train_models - Обучить ML модели\n"
                "• /generate_signals - Генерировать сигналы\n"
                "• /update_data - Обновить данные\n"
            )
            
            await message.answer(text)
            logger.info(f"✅ Admin panel sent to user {message.from_user.id}")
            
        except Exception as e:
            logger.exception(f"❌ Error in admin panel: {e}")
            await message.answer("❌ Ошибка загрузки панели")
    
    # Callback handlers
    async def cb_main_menu(self, callback: CallbackQuery):
        """Главное меню"""
        await callback.answer()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Открыть AIBET Mini App", web_app=WebAppInfo(url=MINI_APP_URL))
            ],
            [
                InlineKeyboardButton(text="📊 Анализ", callback_data="analyze"),
                InlineKeyboardButton(text="🔴 Live", callback_data="live_matches")
            ],
            [
                InlineKeyboardButton(text="🎯 Сигналы", callback_data="signals"),
                InlineKeyboardButton(text="📈 Статистика", callback_data="stats")
            ]
        ])
        
        menu_text = (
            "<b>🏠 Главное меню</b>\n\n"
            "Выберите интересующий раздел:"
        )
        
        await callback.message.edit_text(menu_text, reply_markup=keyboard)
    
    async def cb_live_matches(self, callback: CallbackQuery):
        """Live матчи"""
        await callback.answer()
        
        try:
            matches = await self.db_manager.get_live_matches(limit=10)
            
            if not matches:
                await callback.message.edit_text(
                    "🔴 <b>Live матчи</b>\n\n"
                    "Сейчас нет активных матчей",
                    reply_markup=self.get_back_keyboard("main_menu")
                )
                return
            
            text = f"🔴 <b>Live матчи ({len(matches)})</b>\n\n"
            
            for i, match in enumerate(matches[:5], 1):
                text += f"{i}. <b>{match.team1}</b> vs <b>{match.team2}</b>\n"
                text += f"🏆 {match.features.get('tournament', 'Unknown')}\n"
                text += f"⚡ Счет: {match.score or 'Идет'}\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.exception(f"❌ Error in cb_live_matches: {e}")
            await callback.message.edit_text("❌ Ошибка загрузки матчей")
    
    async def cb_signals(self, callback: CallbackQuery):
        """Сигналы"""
        await callback.answer()
        await self.cmd_signals(callback.message)
    
    async def cb_stats(self, callback: CallbackQuery):
        """Статистика"""
        await callback.answer()
        await self.cmd_stats(callback.message)
    
    async def cb_analyze(self, callback: CallbackQuery):
        """Анализ"""
        await callback.answer()
        await self.cmd_analyze(callback.message)
    
    async def handle_message(self, message: Message):
        """Обработка других сообщений"""
        if message.text and message.text.lower() in ['меню', 'start', '/start']:
            await self.cmd_start(message)
        else:
            await message.answer("🤖 Используйте /start для главного меню")
    
    def get_back_keyboard(self, callback_data: str) -> InlineKeyboardMarkup:
        """Кнопка назад"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
        ])
    
    async def start_polling(self):
        """Запуск бота"""
        logger.info("🚀 Starting Real Telegram Bot...")
        
        if not self._initialized:
            logger.info("🔧 Bot not initialized, initializing now...")
            await self.initialize()
        
        logger.info("🤖 Starting polling...")
        logger.info(f"📱 Bot will respond to commands: /start, /help, /signals, /stats, /analyze, /admin")
        logger.info(f"👤 Admin commands available for ID: {ADMIN_ID}")
        
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.exception(f"❌ Error in polling: {e}")
            raise

# Обязательная функция main для импорта
async def main():
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    # Создаем и запускаем бота
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_id = int(os.getenv("ADMIN_ID", "379036860"))
    
    # Импортируем db_manager
    from database import db_manager
    
    bot = RealTelegramBot(bot_token, admin_id, db_manager)
    await bot.initialize()
    await bot.dp.start_polling(bot.bot)

# Глобальный экземпляр
def create_bot():
    """Создание экземпляра бота"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_id = int(os.getenv("ADMIN_ID", "379036860"))
    from database import db_manager
    return RealTelegramBot(bot_token, admin_id, db_manager)
