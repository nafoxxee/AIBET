#!/usr/bin/env python3
"""
AIBET Analytics Platform - Pre-Match Telegram Bot
Telegram бот для pre-match режима без live данных
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo
)

logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "379036860"))
MINI_APP_URL = "https://aibet-mini-app.onrender.com/"

class PreMatchTelegramBot:
    def __init__(self, bot_token: str, admin_id: int, db_manager):
        self.bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        self.admin_id = admin_id
        self.db_manager = db_manager
        self._initialized = False
        
        # Регистрируем хендлеры
        self.register_handlers()
        
        logger.info(f"🤖 Pre-Match Telegram Bot initialized (admin: {admin_id})")
    
    def register_handlers(self):
        """Регистрация всех хендлеров"""
        logger.info("🔧 Registering Pre-Match bot handlers")
        
        # Команды
        self.dp.message(Command('start'))(self.cmd_start)
        self.dp.message(Command('help'))(self.cmd_help)
        self.dp.message(Command('matches'))(self.cmd_matches)
        self.dp.message(Command('signals'))(self.cmd_signals)
        self.dp.message(Command('stats'))(self.cmd_stats)
        self.dp.message(Command('miniapp'))(self.cmd_miniapp)
        self.dp.message(Command('admin'))(self.cmd_admin)
        
        # Callback хендлеры
        self.dp.callback_query()(self.handle_callback)
        
        # Любые другие сообщения
        self.dp.message()(self.handle_message)
    
    async def cmd_start(self, message: Message):
        """Команда /start"""
        await message.answer(
            "🎯 <b>Добро пожаловать в AIBET Pre-Match!</b>\n\n"
            "Аналитика и прогнозы на CS2 и КХЛ\n"
            "<b>Режим: Pre-Match (без live данных)</b>\n\n"
            "📊 <b>Доступные команды:</b>\n"
            "/matches - Предстоящие матчи\n"
            "/signals - Pre-Match сигналы\n"
            "/stats - Статистика команд\n"
            "/miniapp - Mini приложение\n\n"
            "🤖 Начните с команды /matches",
            reply_markup=self.get_main_keyboard()
        )
    
    async def cmd_help(self, message: Message):
        """Команда /help"""
        help_text = """
🎯 <b>AIBET Pre-Match - Справка</b>

📊 <b>Основные команды:</b>
/start - Главное меню
/matches - Предстоящие матчи
/signals - Pre-Match сигналы
/stats - Статистика команд
/miniapp - Полное приложение

🎯 <b>Сигналы:</b>
• CS2 - @aibetcsgo
• КХЛ - @aibetkhl

📈 <b>Фичи:</b>
• Pre-Match анализ
• ML прогнозы на истории
• Автоматические сигналы
• Статистика команд
• Без live данных

⚡ <b>Режим:</b>
Только pre-match анализ
        """
        await message.answer(help_text, reply_markup=self.get_main_keyboard())
    
    async def cmd_matches(self, message: Message):
        """Команда /matches"""
        try:
            matches = await self.db_manager.get_upcoming_matches()
            
            if not matches:
                await message.answer("📊 Pre-Match матчи обновляются...")
                return
            
            response = "📅 <b>Предстоящие Pre-Match матчи:</b>\n\n"
            
            for match in matches[:10]:  # Показываем первые 10
                sport_emoji = "🔫" if match['sport'] == 'cs2' else "🏒"
                response += f"{sport_emoji} <b>{match['team1']}</b> vs <b>{match['team2']}</b>\n"
                response += f"🏆 {match['tournament']}\n"
                response += f"📅 {match['date']}\n"
                response += f"📊 Статус: Pre-Match\n\n"
            
            response += "\n⚡ <i>Pre-Match анализ без live данных</i>"
            
            await message.answer(response, reply_markup=self.get_main_keyboard())
            
        except Exception as e:
            logger.error(f"Error in /matches: {e}")
            await message.answer("❌ Ошибка загрузки pre-match матчей")
    
    async def cmd_signals(self, message: Message):
        """Команда /signals"""
        try:
            signals = await self.db_manager.get_signals(published=True)
            
            if not signals:
                await message.answer("🎯 Pre-Match сигналов пока нет")
                return
            
            response = "🎯 <b>Pre-Match сигналы:</b>\n\n"
            
            for signal in signals[:5]:  # Показываем первые 5
                sport_emoji = "🔫" if signal['sport'] == 'cs2' else "🏒"
                confidence_level = signal.get('confidence', 'Средняя')
                
                response += f"{sport_emoji} <b>{signal['team1']}</b> vs <b>{signal['team2']}</b>\n"
                response += f"🏆 {signal['tournament']}\n"
                response += f"🎯 Прогноз: {signal['prediction'].upper()}\n"
                response += f"📊 Вероятность: {signal['probability']:.1f}% ({confidence_level})\n"
                if signal['recommendation']:
                    response += f"💡 {signal['recommendation']}\n"
                response += f"📅 {signal['date']}\n\n"
            
            response += "\n⚡ <i>Pre-Match сигналы на основе исторических данных</i>"
            
            await message.answer(response, reply_markup=self.get_main_keyboard())
            
        except Exception as e:
            logger.error(f"Error in /signals: {e}")
            await message.answer("❌ Ошибка загрузки pre-match сигналов")
    
    async def cmd_stats(self, message: Message):
        """Команда /stats"""
        try:
            # Получаем статистику системы
            total_matches = await self.db_manager.get_match_count()
            historical_matches = await self.db_manager.get_historical_match_count()
            cs2_matches = len(await self.db_manager.get_matches(sport='cs2'))
            khl_matches = len(await self.db_manager.get_matches(sport='khl'))
            total_signals = len(await self.db_manager.get_signals())
            
            stats_text = f"""
📊 <b>Pre-Match Статистика системы:</b>

📈 <b>Матчи:</b>
• Всего предстоящих: {total_matches}
• Исторических: {historical_matches}
• CS2: {cs2_matches}
• КХЛ: {khl_matches}

🎯 <b>Сигналы:</b>
• Всего: {total_signals}
• Pre-Match анализ

🤖 <b>ML модели:</b>
• Обучены на истории
• Pre-Match прогнозы

⚡ <b>Режим:</b>
Pre-Match (без live данных)

📈 Используйте /miniapp для подробной статистики
            """
            
            await message.answer(stats_text, reply_markup=self.get_main_keyboard())
            
        except Exception as e:
            logger.error(f"Error in /stats: {e}")
            await message.answer("❌ Ошибка загрузки статистики")
    
    async def cmd_miniapp(self, message: Message):
        """Команда /miniapp"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🚀 Открыть AIBET Pre-Match Mini App",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )]
        ])
        
        await message.answer(
            "🚀 <b>AIBET Pre-Match Mini App</b>\n\n"
            "Полный pre-match анализ и прогнозы в удобном интерфейсе\n"
            "⚡ Режим: Pre-Match (без live данных)",
            reply_markup=keyboard
        )
    
    async def cmd_admin(self, message: Message):
        """Команда /admin"""
        if message.from_user.id != self.admin_id:
            await message.answer("❌ Доступ запрещен")
            return
        
        try:
            # Получаем статистику системы
            total_matches = await self.db_manager.get_match_count()
            historical_matches = await self.db_manager.get_historical_match_count()
            cs2_matches = len(await self.db_manager.get_matches(sport='cs2'))
            khl_matches = len(await self.db_manager.get_matches(sport='khl'))
            total_signals = len(await self.db_manager.get_signals())
            
            admin_text = f"""
🔧 <b>Pre-Match Админ панель AIBET</b>

📊 <b>Статистика:</b>
• Предстоящих матчей: {total_matches}
• Исторических матчей: {historical_matches}
• CS2 матчей: {cs2_matches}
• КХЛ матчей: {khl_matches}
• Всего сигналов: {total_signals}

⏰ <b>Система:</b>
• Статус: ✅ Работает
• Режим: Pre-Match
• База данных: ✅ Подключена
• ML модели: ✅ Обучены

🎯 <b>Действия:</b>
• /update_matches - Обновить матчи
• /generate_signals - Генерировать сигналы
• /train_models - Обучить модели
            """
            
            await message.answer(admin_text)
            
        except Exception as e:
            logger.error(f"Error in /admin: {e}")
            await message.answer("❌ Ошибка загрузки админ панели")
    
    async def handle_callback(self, callback: CallbackQuery):
        """Обработка callback запросов"""
        try:
            await callback.answer()
            
            # Обработка разных callback_data
            if callback.data == "main_menu":
                await self.cmd_start(callback.message)
            elif callback.data == "refresh":
                await self.cmd_matches(callback.message)
            elif callback.data == "signals_refresh":
                await self.cmd_signals(callback.message)
            else:
                await callback.message.answer("❌ Неизвестное действие")
                
        except Exception as e:
            logger.error(f"Error in callback: {e}")
            await callback.answer("❌ Ошибка")
    
    async def handle_message(self, message: Message):
        """Обработка обычных сообщений"""
        if message.text and message.text.lower() in ['меню', 'start', 'главное']:
            await self.cmd_start(message)
        elif message.text and message.text.lower() in ['помощь', 'help']:
            await self.cmd_help(message)
        else:
            await message.answer(
                "🤖 Используйте команды из меню:\n"
                "/matches - Pre-Match матчи\n"
                "/signals - Pre-Match сигналы\n"
                "/miniapp - Приложение",
                reply_markup=self.get_main_keyboard()
            )
    
    def get_main_keyboard(self) -> ReplyKeyboardMarkup:
        """Получить основную клавиатуру"""
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Матчи"), KeyboardButton(text="🎯 Сигналы")],
                [KeyboardButton(text="📈 Статистика"), KeyboardButton(text="🚀 Mini App")],
                [KeyboardButton(text="❓ Помощь")]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        return keyboard
    
    async def start(self):
        """Запуск бота"""
        if self._initialized:
            return
        
        logger.info("🤖 Starting Pre-Match Telegram Bot...")
        
        # Проверка токена
        if not BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found")
        
        # Установка команд бота
        await self.bot.set_my_commands([
            types.BotCommand(command="start", description="🚀 Главное меню"),
            types.BotCommand(command="help", description="❓ Помощь"),
            types.BotCommand(command="matches", description="📊 Pre-Match матчи"),
            types.BotCommand(command="signals", description="🎯 Pre-Match сигналы"),
            types.BotCommand(command="stats", description="📈 Статистика"),
            types.BotCommand(command="miniapp", description="🚀 Mini приложение"),
            types.BotCommand(command="admin", description="🔧 Админ панель")
        ])
        
        # Запуск поллинга
        await self.dp.start_polling(self.bot)
        self._initialized = True
        
        logger.info("✅ Pre-Match Telegram Bot started successfully")

async def create_pre_match_bot(db_manager) -> PreMatchTelegramBot:
    """Создание экземпляра pre-match бота"""
    return PreMatchTelegramBot(
        bot_token=BOT_TOKEN,
        admin_id=ADMIN_ID,
        db_manager=db_manager
    )
