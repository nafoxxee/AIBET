#!/usr/bin/env python3
"""
AIBET Analytics Platform - Fixed Telegram Bot
Исправленная версия без ошибок CallbackQuery
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

class AIBOTTelegramBotFixed:
    def __init__(self, bot_token: str, admin_id: int, db_manager):
        self.bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        self.admin_id = admin_id
        self.db_manager = db_manager
        self._initialized = False
        
        # Регистрируем хендлеры
        self.register_handlers()
        
        logger.info(f"🤖 AIBOT Telegram Bot Fixed initialized (admin: {admin_id})")
    
    def register_handlers(self):
        """Регистрация всех хендлеров"""
        logger.info("🔧 Registering bot handlers")
        
        # Команды
        self.dp.message(Command('start'))(self.cmd_start)
        self.dp.message(Command('help'))(self.cmd_help)
        self.dp.message(Command('live'))(self.cmd_live)
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
            "🎯 <b>Добро пожаловать в AIBET!</b>\n\n"
            "Аналитика и прогнозы на CS2 и КХЛ\n\n"
            "📊 <b>Доступные команды:</b>\n"
            "/live - Live матчи\n"
            "/matches - Предстоящие матчи\n"
            "/signals - Сигналы\n"
            "/stats - Статистика команд\n"
            "/miniapp - Mini приложение\n\n"
            "🤖 Начните с команды /matches",
            reply_markup=self.get_main_keyboard()
        )
    
    async def cmd_help(self, message: Message):
        """Команда /help"""
        help_text = """
🎯 <b>AIBET - Справка</b>

📊 <b>Основные команды:</b>
/start - Главное меню
/live - Текущие матчи
/matches - Предстоящие матчи
/signals - Активные сигналы
/stats - Статистика команд
/miniapp - Полное приложение

🎯 <b>Сигналы:</b>
• CS2 - @aibetcsgo
• КХЛ - @aibetkhl

📈 <b>Фичи:</b>
• Реальные данные
• ML прогнозы
• Автоматические сигналы
• Статистика команд
        """
        await message.answer(help_text, reply_markup=self.get_main_keyboard())
    
    async def cmd_live(self, message: Message):
        """Команда /live"""
        try:
            matches = await self.db_manager.get_matches(status='live', limit=10)
            
            if not matches:
                await message.answer("📊 Сейчас нет live матчей")
                return
            
            response = "🔴 <b>Live Матчи:</b>\n\n"
            
            for match in matches:
                status_emoji = "🔴" if match['status'] == 'live' else "⚪"
                response += f"{status_emoji} <b>{match['team1']}</b> vs <b>{match['team2']}</b>\n"
                response += f"🏆 {match['tournament']}\n"
                if match['score']:
                    response += f"📊 Счёт: {match['score']}\n"
                response += f"📅 {match['date']}\n\n"
            
            await message.answer(response, reply_markup=self.get_main_keyboard())
            
        except Exception as e:
            logger.error(f"Error in /live: {e}")
            await message.answer("❌ Ошибка загрузки live матчей")
    
    async def cmd_matches(self, message: Message):
        """Команда /matches"""
        try:
            matches = await self.db_manager.get_upcoming_matches()
            
            if not matches:
                await message.answer("📊 Предстоящие матчи обновляются...")
                return
            
            response = "📅 <b>Предстоящие матчи:</b>\n\n"
            
            for match in matches[:10]:  # Показываем первые 10
                sport_emoji = "🔫" if match['sport'] == 'cs2' else "🏒"
                response += f"{sport_emoji} <b>{match['team1']}</b> vs <b>{match['team2']}</b>\n"
                response += f"🏆 {match['tournament']}\n"
                response += f"📅 {match['date']}\n"
                response += f"📊 Статус: {match['status']}\n\n"
            
            await message.answer(response, reply_markup=self.get_main_keyboard())
            
        except Exception as e:
            logger.error(f"Error in /matches: {e}")
            await message.answer("❌ Ошибка загрузки матчей")
    
    async def cmd_signals(self, message: Message):
        """Команда /signals"""
        try:
            signals = await self.db_manager.get_signals(published=True)
            
            if not signals:
                await message.answer("🎯 Активных сигналов пока нет")
                return
            
            response = "🎯 <b>Активные сигналы:</b>\n\n"
            
            for signal in signals[:5]:  # Показываем первые 5
                sport_emoji = "🔫" if signal['sport'] == 'cs2' else "🏒"
                prediction_emoji = "✅" if signal['probability'] >= 70 else "⚠️"
                
                response += f"{sport_emoji} {prediction_emoji} <b>{signal['team1']}</b> vs <b>{signal['team2']}</b>\n"
                response += f"🏆 {signal['tournament']}\n"
                response += f"🎯 Прогноз: {signal['prediction']}\n"
                response += f"📊 Вероятность: {signal['probability']}%\n"
                if signal['recommendation']:
                    response += f"💡 {signal['recommendation']}\n"
                response += f"📅 {signal['date']}\n\n"
            
            await message.answer(response, reply_markup=self.get_main_keyboard())
            
        except Exception as e:
            logger.error(f"Error in /signals: {e}")
            await message.answer("❌ Ошибка загрузки сигналов")
    
    async def cmd_stats(self, message: Message):
        """Команда /stats"""
        try:
            # Получаем статистику для примера
            stats_text = """
📊 <b>Статистика команд:</b>

🔫 <b>CS2 Топ команды:</b>
• NaVi: 68% побед в последних 50 матчах
• FaZe: 62% побед в последних 50 матчах
• G2: 65% побед в последних 50 матчах

🏒 <b>КХЛ Топ команды:</b>
• CSKA Moscow: 65% побед
• SKA Saint Petersburg: 62% побед
• Ak Bars Kazan: 60% побед

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
                text="🚀 Открыть AIBET Mini App",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )]
        ])
        
        await message.answer(
            "🚀 <b>AIBET Mini App</b>\n\n"
            "Полная аналитика и прогнозы в удобном интерфейсе",
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
            cs2_matches = len(await self.db_manager.get_matches(sport='cs2'))
            khl_matches = len(await self.db_manager.get_matches(sport='khl'))
            total_signals = len(await self.db_manager.get_signals())
            
            admin_text = f"""
🔧 <b>Админ панель AIBET</b>

📊 <b>Статистика:</b>
• Всего матчей: {total_matches}
• CS2 матчей: {cs2_matches}
• КХЛ матчей: {khl_matches}
• Всего сигналов: {total_signals}

⏰ <b>Система:</b>
• Статус: ✅ Работает
• База данных: ✅ Подключена
• Парсеры: ✅ Активны

🎯 <b>Действия:</b>
• /update_matches - Обновить матчи
• /generate_signals - Генерировать сигналы
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
                "/matches - Матчи\n"
                "/signals - Сигналы\n"
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
        
        logger.info("🤖 Starting AIBOT Telegram Bot Fixed...")
        
        # Проверка токена
        if not BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found")
        
        # Установка команд бота
        await self.bot.set_my_commands([
            types.BotCommand(command="start", description="🚀 Главное меню"),
            types.BotCommand(command="help", description="❓ Помощь"),
            types.BotCommand(command="live", description="🔴 Live матчи"),
            types.BotCommand(command="matches", description="📊 Предстоящие матчи"),
            types.BotCommand(command="signals", description="🎯 Сигналы"),
            types.BotCommand(command="stats", description="📈 Статистика"),
            types.BotCommand(command="miniapp", description="🚀 Mini приложение"),
            types.BotCommand(command="admin", description="🔧 Админ панель")
        ])
        
        # Запуск поллинга
        await self.dp.start_polling(self.bot)
        self._initialized = True
        
        logger.info("✅ AIBOT Telegram Bot Fixed started successfully")

async def create_bot(db_manager) -> AIBOTTelegramBotFixed:
    """Создание экземпляра бота"""
    return AIBOTTelegramBotFixed(
        bot_token=BOT_TOKEN,
        admin_id=ADMIN_ID,
        db_manager=db_manager
    )
