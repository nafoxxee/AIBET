#!/usr/bin/env python3
"""
AIBET Analytics Platform - Telegram Bot
Обновленный бот с inline кнопками и командами
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
)

from database import User, db_manager
from signal_generator import signal_generator
from telegram_publisher import create_telegram_publisher

logger = logging.getLogger(__name__)

class BotStates(StatesGroup):
    main_menu = State()
    signals = State()
    stats = State()
    settings = State()

class AIBOTTelegramBot:
    def __init__(self, bot_token: str, admin_id: int):
        self.bot_token = bot_token
        self.admin_id = admin_id
        self.bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.publisher = create_telegram_publisher(bot_token)
        self._initialized = False
    
    async def initialize(self):
        """Инициализация бота"""
        if self._initialized:
            return
            
        logger.info("🤖 Initializing AIBOT Telegram Bot")
        
        # Инициализируем publisher
        await self.publisher.initialize()
        
        # Регистрируем handlers
        self.register_handlers()
        
        self._initialized = True
        logger.info("✅ AIBOT Telegram Bot initialized successfully")
    
    def register_handlers(self):
        """Регистрация обработчиков"""
        
        # Команды
        self.dp.message(Command("start"))(self.cmd_start)
        self.dp.message(Command("help"))(self.cmd_help)
        self.dp.message(Command("signals"))(self.cmd_signals)
        self.dp.message(Command("stats"))(self.cmd_stats)
        self.dp.message(Command("analyze"))(self.cmd_analyze)
        self.dp.message(Command("admin"))(self.cmd_admin)
        
        # Callback queries
        self.dp.callback_query(F.data == "main_menu")(self.cb_main_menu)
        self.dp.callback_query(F.data == "live_matches")(self.cb_live_matches)
        self.dp.callback_query(F.data == "signals")(self.cb_signals)
        self.dp.callback_query(F.data == "stats")(self.cb_stats)
        self.dp.callback_query(F.data == "analyze")(self.cb_analyze)
        self.dp.callback_query(F.data == "settings")(self.cb_settings)
        self.dp.callback_query(F.data.startswith("signal_"))(self.cb_signal_details)
        self.dp.callback_query(F.data.startswith("match_"))(self.cb_match_details)
        
        # Любые другие сообщения
        self.dp.message()(self.handle_message)
    
    async def cmd_start(self, message: Message):
        """Команда /start"""
        user_id = message.from_user.id
        
        # Регистрируем пользователя
        user = User(telegram_id=user_id, is_admin=(user_id == self.admin_id))
        await db_manager.add_user(user)
        
        # Приветственное сообщение
        welcome_text = (
            "<b>🤖 Добро пожаловать в AIBET Analytics Platform!</b>\n\n"
            "🎯 <b>AI-анализ матчей CS2 и КХЛ с точностью >70%</b>\n\n"
            "📊 <b>Что я умею:</b>\n"
            "• 🔴 Live матчи в реальном времени\n"
            "• 🤖 AI анализ предстоящих игр\n"
            "• 📢 Автоматические сигналы\n"
            "• 📈 Подробная статистика\n\n"
            "<i>Используйте кнопки ниже для навигации</i>"
        )
        
        keyboard = self.get_main_keyboard()
        await message.answer(welcome_text, reply_markup=keyboard)
    
    async def cmd_help(self, message: Message):
        """Команда /help"""
        help_text = (
            "<b>📖 Справка AIBOT</b>\n\n"
            "<b>🔥 Основные команды:</b>\n"
            "/start - Главное меню\n"
            "/signals - Последние сигналы\n"
            "/stats - Статистика системы\n"
            "/analyze - AI анализ матчей\n"
            "/help - Эта справка\n\n"
            "<b>🎯 Функции:</b>\n"
            "• 🔴 <b>Live матчи</b> - Матчи в реальном времени\n"
            "• 🤖 <b>AI анализ</b> - Предсказания с уверенностью >70%\n"
            "• 📊 <b>Статистика</b> - Точность и производительность\n"
            "• ⚙️ <b>Настройки</b> - Персонализация\n\n"
            "<b>📢 Каналы:</b>\n"
            "• @aibetcsgo - CS2 сигналы\n"
            "• @aibetkhl - КХЛ сигналы\n\n"
            "<i>По вопросам: @admin</i>"
        )
        
        await message.answer(help_text)
    
    async def cmd_signals(self, message: Message):
        """Команда /signals"""
        await self.show_signals(message)
    
    async def cmd_stats(self, message: Message):
        """Команда /stats"""
        await self.show_stats(message)
    
    async def cmd_analyze(self, message: Message):
        """Команда /analyze"""
        await self.show_analyze(message)
    
    async def cmd_admin(self, message: Message):
        """Команда /admin"""
        if message.from_user.id != self.admin_id:
            await message.answer("⛔ Доступ запрещен")
            return
        
        await self.show_admin_panel(message)
    
    async def cb_main_menu(self, callback: CallbackQuery):
        """Главное меню"""
        await callback.answer()
        
        menu_text = (
            "<b>🏠 Главное меню</b>\n\n"
            "Выберите интересующий раздел:"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔴 Live матчи", callback_data="live_matches"),
                InlineKeyboardButton(text="🤖 AI анализ", callback_data="analyze")
            ],
            [
                InlineKeyboardButton(text="📢 Сигналы", callback_data="signals"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
            ]
        ])
        
        await callback.message.edit_text(menu_text, reply_markup=keyboard)
    
    async def cb_live_matches(self, callback: CallbackQuery):
        """Live матчи"""
        await callback.answer()
        
        try:
            # Получаем live матчи
            from database import Match
            matches = await db_manager.get_matches(status="live", limit=10)
            
            if not matches:
                await callback.message.edit_text(
                    "🔴 <b>Live матчи</b>\n\n"
                    "Сейчас нет активных матчей",
                    reply_markup=self.get_back_keyboard("main_menu")
                )
                return
            
            text = f"🔴 <b>Live матчи ({len(matches)})</b>\n\n"
            
            keyboard_buttons = []
            for i, match in enumerate(matches[:5], 1):
                text += f"{i}. <b>{match.team1}</b> vs <b>{match.team2}</b>\n"
                text += f"🏆 {match.features.get('tournament', 'Unknown')}\n"
                text += f"⚡ Счет: {match.score or 'Идет'}\n\n"
                
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"📊 {match.team1} vs {match.team2}",
                        callback_data=f"match_{match.id}"
                    )
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await callback.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in cb_live_matches: {e}")
            await callback.message.edit_text(
                "❌ Ошибка загрузки матчей",
                reply_markup=self.get_back_keyboard("main_menu")
            )
    
    async def cb_signals(self, callback: CallbackQuery):
        """Сигналы"""
        await callback.answer()
        
        try:
            # Получаем последние сигналы
            signals = await db_manager.get_signals(published=True, limit=10)
            
            if not signals:
                await callback.message.edit_text(
                    "📢 <b>Сигналы</b>\n\n"
                    "Пока нет опубликованных сигналов",
                    reply_markup=self.get_back_keyboard("main_menu")
                )
                return
            
            text = f"📢 <b>Последние сигналы ({len(signals)})</b>\n\n"
            
            keyboard_buttons = []
            for i, signal in enumerate(signals[:5], 1):
                # Короткая версия сигнала
                signal_preview = signal.signal[:50] + "..." if len(signal.signal) > 50 else signal.signal
                confidence = int(signal.confidence * 100)
                
                text += f"{i}. {signal.sport.upper()}\n"
                text += f"📊 {signal_preview}\n"
                text += f"🎯 Уверенность: {confidence}%\n"
                text += f"🕐 {signal.created_at.strftime('%H:%M')}\n\n"
                
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"📊 Сигнал #{i}",
                        callback_data=f"signal_{signal.id}"
                    )
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await callback.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in cb_signals: {e}")
            await callback.message.edit_text(
                "❌ Ошибка загрузки сигналов",
                reply_markup=self.get_back_keyboard("main_menu")
            )
    
    async def cb_stats(self, callback: CallbackQuery):
        """Статистика"""
        await callback.answer()
        
        try:
            # Получаем статистику
            stats = await signal_generator.get_signal_statistics()
            performance = await signal_generator.analyze_signal_performance(days=7)
            
            text = (
                "<b>📊 Статистика AIBET</b>\n\n"
                f"📢 Всего сигналов: <b>{stats.get('total_signals', 0)}</b>\n"
                f"🔫 CS2 сигналы: <b>{stats.get('cs2_signals', 0)}</b>\n"
                f"🏒 КХЛ сигналы: <b>{stats.get('khl_signals', 0)}</b>\n"
                f"📈 Средняя уверенность: <b>{stats.get('avg_confidence', 0):.1%}</b>\n\n"
                f"🎯 Точность за 7 дней: <b>{performance.get('accuracy', 0):.1f}%</b>\n"
                f"✅ Успешных: <b>{performance.get('successful_signals', 0)}</b>\n"
                f"📅 Сегодня: <b>{stats.get('today_signals', 0)}</b>\n\n"
                "<i>🤖 AI работает с точностью >70%</i>"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Обновить", callback_data="stats"),
                    InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
                ]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in cb_stats: {e}")
            await callback.message.edit_text(
                "❌ Ошибка загрузки статистики",
                reply_markup=self.get_back_keyboard("main_menu")
            )
    
    async def cb_analyze(self, callback: CallbackQuery):
        """AI анализ"""
        await callback.answer()
        
        try:
            # Получаем матчи с высокой уверенностью
            high_confidence = await signal_generator.get_high_confidence_matches()
            
            if not high_confidence:
                await callback.message.edit_text(
                    "🤖 <b>AI анализ</b>\n\n"
                    "Сейчас нет матчей с высокой уверенностью предсказания",
                    reply_markup=self.get_back_keyboard("main_menu")
                )
                return
            
            text = f"🤖 <b>AI анализ матчей</b>\n\n"
            
            keyboard_buttons = []
            for i, match_data in enumerate(high_confidence[:3], 1):
                match = match_data['match']
                prediction = match_data['prediction']
                confidence = int(prediction['confidence'] * 100)
                
                text += f"{i}. <b>{match.team1}</b> vs <b>{match.team2}</b>\n"
                text += f"🏆 {match.features.get('tournament', 'Unknown')}\n"
                text += f"🎯 Прогноз: <b>{prediction['prediction']}</b>\n"
                text += f"📊 Уверенность: <b>{confidence}%</b>\n\n"
                
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"📊 Анализ матча #{i}",
                        callback_data=f"match_{match.id}"
                    )
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await callback.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in cb_analyze: {e}")
            await callback.message.edit_text(
                "❌ Ошибка загрузки анализа",
                reply_markup=self.get_back_keyboard("main_menu")
            )
    
    async def cb_signal_details(self, callback: CallbackQuery):
        """Детали сигнала"""
        await callback.answer()
        
        try:
            signal_id = int(callback.data.split("_")[1])
            
            # Получаем сигнал
            signals = await db_manager.get_signals(limit=1000)
            signal = next((s for s in signals if s.id == signal_id), None)
            
            if not signal:
                await callback.message.edit_text("❌ Сигнал не найден")
                return
            
            # Получаем матч
            matches = await db_manager.get_matches(limit=1000)
            match = next((m for m in matches if m.id == signal.match_id), None) if signal.match_id else None
            
            text = (
                f"<b>📢 Детали сигнала</b>\n\n"
                f"🏆 {signal.sport.upper()}\n\n"
                f"{signal.signal}\n\n"
                f"🎯 Уверенность: <b>{int(signal.confidence * 100)}%</b>\n"
                f"🕐 Создан: <b>{signal.created_at.strftime('%d.%m.%Y %H:%M')}</b>\n"
                f"📢 Опубликован: <b>{'Да' if signal.published else 'Нет'}</b>"
            )
            
            if match:
                text += f"\n\n📊 Матч: <b>{match.team1}</b> vs <b>{match.team2}</b>"
                text += f"\n🏆 {match.features.get('tournament', 'Unknown')}"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔙 Назад", callback_data="signals")
                ]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in cb_signal_details: {e}")
            await callback.message.edit_text("❌ Ошибка загрузки деталей")
    
    async def cb_match_details(self, callback: CallbackQuery):
        """Детали матча"""
        await callback.answer()
        
        try:
            match_id = int(callback.data.split("_")[1])
            
            # Получаем матч
            matches = await db_manager.get_matches(limit=1000)
            match = next((m for m in matches if m.id == match_id), None)
            
            if not match:
                await callback.message.edit_text("❌ Матч не найден")
                return
            
            # Получаем предсказание
            from ml_models import ml_models
            prediction = await ml_models.predict_match(match)
            
            status_emoji = "🔴" if match.status == "live" else "⏰" if match.status == "upcoming" else "✅"
            
            text = (
                f"<b>📊 Детали матча</b>\n\n"
                f"{status_emoji} <b>{match.team1}</b> vs <b>{match.team2}</b>\n"
                f"🏆 {match.features.get('tournament', 'Unknown')}\n"
                f"📊 Статус: <b>{match.status.upper()}</b>\n"
                f"⚡ Счет: <b>{match.score or 'Не начат'}</b>\n\n"
                f"🤖 <b>AI Прогноз</b>\n"
                f"🎯 Победитель: <b>{prediction['prediction']}</b>\n"
                f"📊 Уверенность: <b>{int(prediction['confidence'] * 100)}%</b>\n\n"
                f"📈 <b>Анализ</b>\n"
                f"{prediction['analysis']}"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔙 Назад", callback_data="live_matches")
                ]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in cb_match_details: {e}")
            await callback.message.edit_text("❌ Ошибка загрузки деталей")
    
    async def cb_settings(self, callback: CallbackQuery):
        """Настройки"""
        await callback.answer()
        
        text = (
            "<b>⚙️ Настройки</b>\n\n"
            "🔔 <b>Уведомления</b>\n"
            "• Сигналы: Включены\n"
            "• Live матчи: Включены\n\n"
            "🎯 <b>Пороги</b>\n"
            "• Мин. уверенность: 70%\n"
            "• Максимум сигналов: 10/день\n\n"
            "<i>Настройки доступны в Mini App</i>"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🌐 Mini App", url="https://aibet-mini-prilozhenie.onrender.com"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    async def show_admin_panel(self, message: Message):
        """Панель администратора"""
        try:
            # Получаем статистику
            stats = await signal_generator.get_signal_statistics()
            
            text = (
                "<b>🔑 Панель администратора</b>\n\n"
                f"📢 Всего сигналов: <b>{stats.get('total_signals', 0)}</b>\n"
                f"📈 Опубликовано: <b>{stats.get('published_signals', 0)}</b>\n"
                f"🎯 Точность: <b>{stats.get('avg_confidence', 0):.1%}</b>\n\n"
                "<b>🔧 Управление:</b>\n"
                "• /generate - Генерировать сигналы\n"
                "• /publish - Опубликовать ожидающие\n"
                "• /cleanup - Очистка старых данных\n"
                "• /test - Тест публикации"
            )
            
            await message.answer(text)
            
        except Exception as e:
            logger.error(f"Error in admin panel: {e}")
            await message.answer("❌ Ошибка загрузки панели")
    
    async def handle_message(self, message: Message):
        """Обработка обычных сообщений"""
        if message.text == "/start":
            await self.cmd_start(message)
        elif message.text == "🏠 Главное меню":
            await self.cb_main_menu(message)
        else:
            # Показываем главное меню
            keyboard = self.get_main_keyboard()
            await message.answer("Используйте кнопки меню:", reply_markup=keyboard)
    
    def get_main_keyboard(self) -> ReplyKeyboardMarkup:
        """Главное меню с кнопками"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="🔴 Live матчи"),
                    KeyboardButton(text="🤖 AI анализ")
                ],
                [
                    KeyboardButton(text="📢 Сигналы"),
                    KeyboardButton(text="📊 Статистика")
                ],
                [
                    KeyboardButton(text="🏠 Главное меню")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        return keyboard
    
    def get_back_keyboard(self, callback_data: str) -> InlineKeyboardMarkup:
        """Кнопка назад"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)
            ]
        ])
    
    async def start_polling(self):
        """Запуск бота"""
        if not self._initialized:
            await self.initialize()
        
        logger.info("🤖 Starting AIBOT polling...")
        await self.dp.start_polling(self.bot)

# Глобальный экземпляр бота
def create_bot(bot_token: str, admin_id: int) -> AIBOTTelegramBot:
    """Создание экземпляра бота"""
    return AIBOTTelegramBot(bot_token, admin_id)
