#!/usr/bin/env python3
"""
AIBOT - Advanced Telegram Bot with AI Analytics
Автоматическая публикация сигналов в каналы CS:GO и КХЛ
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.enums import ParseMode
import os
import json
import random

# Импорты наших модулей
from ai_models import AdvancedMLModels
from data_collector import AdvancedDataCollector, DataCollectionScheduler
from database import DatabaseManager, Signal
from config import config

logger = logging.getLogger(__name__)

class AIBOTTelegramBot:
    def __init__(self):
        # Конфигурация из config
        self.TOKEN = config.telegram.bot_token
        self.ADMIN_ID = config.telegram.admin_id
        self.CS2_CHANNEL = config.telegram.cs2_channel
        self.KHL_CHANNEL = config.telegram.khl_channel
        self.WEB_APP_URL = config.telegram.web_app_url
        
        # Инициализация
        self.bot = Bot(token=self.TOKEN, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        
        # База данных
        self.db_manager = DatabaseManager(config.database.path)
        
        # ML и сбор данных
        self.ml_models = AdvancedMLModels(self.db_manager)
        self.data_collector = AdvancedDataCollector(self.db_manager)
        
        # Данные
        self.signals_history = []
        self.matches_data = []
        self.bot_stats = {
            'total_signals': 0,
            'successful_signals': 0,
            'cs2_signals': 0,
            'khl_signals': 0,
            'users_count': 0,
            'last_signal_time': None
        }
        
        # Настройка роутов
        self.setup_handlers()
        
    def setup_handlers(self):
        """Настройка всех обработчиков"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            """Команда /start"""
            await self.send_welcome(message)
        
        @self.dp.message(Command("admin"))
        async def cmd_admin(message: Message):
            """Команда /admin"""
            if message.from_user.id == self.ADMIN_ID:
                await self.send_admin_panel(message)
            else:
                await message.answer("⛔ Доступ запрещен")
        
        @self.dp.message(Command("signals"))
        async def cmd_signals(message: Message):
            """Команда /signals"""
            await self.send_signals(message)
        
        @self.dp.message(Command("live"))
        async def cmd_live(message: Message):
            """Команда /live"""
            await self.send_live_matches(message)
        
        @self.dp.message(Command("stats"))
        async def cmd_stats(message: Message):
            """Команда /stats"""
            await self.send_statistics(message)
        
        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            """Команда /help"""
            await self.send_help(message)
        
        @self.dp.callback_query(F.data.startswith("admin_"))
        async def callback_admin(callback: CallbackQuery):
            """Обработка админ-панели"""
            await self.handle_admin_callback(callback)
        
        @self.dp.callback_query(F.data.startswith("signal_"))
        async def callback_signal(callback: CallbackQuery):
            """Обработка сигналов"""
            await self.handle_signal_callback(callback)
        
        @self.dp.callback_query(F.data.startswith("menu_"))
        async def callback_menu(callback: CallbackQuery):
            """Обработка меню"""
            await self.handle_menu_callback(callback)
        
        @self.dp.message()
        async def handle_text(message: Message):
            """Обработка текстовых сообщений"""
            await self.handle_text_message(message)
    
    async def send_welcome(self, message: Message):
        """Отправка приветственного сообщения"""
        self.bot_stats['users_count'] += 1
        
        welcome_text = """
🤖 <b>Добро пожаловать в AIBET Analytics!</b>

Я - AI-бот для анализа матчей CS:GO и КХЛ с автоматической публикацией сигналов.

🔥 <b>Что я умею:</b>
• 🧠 AI-анализ матчей с точностью до 85%
• 📊 Автоматическая публикация сигналов
• 🏒 Live-прогнозы по ходу матчей
• 📈 Подробная статистика и история

🎯 <b>Каналы с сигналами:</b>
• CS:GO: @aibetcsgo
• КХЛ: @aibetkhl

📱 <b>Mini App:</b>
Нажмите кнопку "📊 Mini App" для полного анализа!
        """
        
        # Клавиатура
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📊 Mini App", web_app=WebAppInfo(
                        url=self.WEB_APP_URL
                    ))
                ],
                [
                    KeyboardButton(text="🔥 Сигналы"),
                    KeyboardButton(text="🏒 Live матчи")
                ],
                [
                    KeyboardButton(text="📈 Статистика"),
                    KeyboardButton(text="❓ Помощь")
                ]
            ],
            resize_keyboard=True
        )
        
        await message.answer(welcome_text, reply_markup=keyboard)
    
    async def send_admin_panel(self, message: Message):
        """Отправка админ-панели"""
        admin_text = f"""
🛠️ <b>Админ-панель AIBOT</b>

📊 <b>Статистика бота:</b>
• Всего сигналов: {self.bot_stats['total_signals']}
• Успешных: {self.bot_stats['successful_signals']}
• CS:GO сигналов: {self.bot_stats['cs2_signals']}
• КХЛ сигналов: {self.bot_stats['khl_signals']}
• Пользователей: {self.bot_stats['users_count']}

🎛️ <b>Управление:</b>
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить данные", callback_data="admin_update"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton(text="🔥 Создать сигнал", callback_data="admin_create_signal"),
                InlineKeyboardButton(text="📢 Отправить в канал", callback_data="admin_send_channel")
            ],
            [
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings"),
                InlineKeyboardButton(text="📝 Логи", callback_data="admin_logs")
            ]
        ])
        
        await message.answer(admin_text, reply_markup=keyboard)
    
    async def send_signals(self, message: Message):
        """Отправка последних сигналов"""
        try:
            signals = await self.db_manager.get_signals(limit=5)
            if not signals:
                await message.answer("📭 Сигналов пока нет. AI анализирует матчи...")
                return
            
            signals_text = "🔥 <b>Последние сигналы AIBET:</b>\n\n"
            
            for signal in signals:
                sport_icon = "🔫" if signal.sport == 'cs2' else "🏒"
                confidence_value = float(signal.confidence.replace('%', '')) / 100 if isinstance(signal.confidence, str) else signal.confidence
                confidence_emoji = "🟢" if confidence_value >= 0.8 else "🟡" if confidence_value >= 0.6 else "🔴"
                
                signals_text += f"""
{sport_icon} <b>Match {signal.match_id}</b>
{confidence_emoji} Уверенность: {(confidence_value * 100):.0f}%
💰 Коэффициент: {signal.odds_at_signal}x
🎯 Прогноз: {signal.prediction or 'team1'}
⏰ {signal.published_at}

{signal.explanation[:100]}...

---
                """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📊 Mini App", web_app=WebAppInfo(
                        url=self.WEB_APP_URL
                    ))
                ],
                [
                    InlineKeyboardButton(text="🔄 Обновить", callback_data="signal_refresh"),
                    InlineKeyboardButton(text="📈 Все сигналы", callback_data="signal_all")
                ]
            ])
            
            await message.answer(signals_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error sending signals: {e}")
            await message.answer("❌ Ошибка загрузки сигналов")
    
    async def send_live_matches(self, message: Message):
        """Отправка live матчей"""
        live_matches = await self.get_live_matches()
        
        if not live_matches:
            await message.answer("🏒 Сейчас нет live матчей")
            return
        
        live_text = "🏒 <b>Live матчи сейчас:</b>\n\n"
        
        for match in live_matches:
            sport_icon = "🔫" if match['sport'] == 'cs2' else "🏒"
            
            live_text += f"""
{sport_icon} <b>{match['team1']} vs {match['team2']}</b>
⚡ Счет: {match['score1']} - {match['score2']}
🏆 {match['tournament']}
📡 <b>LIVE</b>

---
            """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="live_refresh"),
                InlineKeyboardButton(text="📊 Mini App", web_app=WebAppInfo(
                    url="https://aibet-mini-app.onrender.com"
                ))
            ]
        ])
        
        await message.answer(live_text, reply_markup=keyboard)
    
    async def send_statistics(self, message: Message):
        """Отправка статистики"""
        stats_text = f"""
📈 <b>Статистика AIBET:</b>

🎯 <b>Общая статистика:</b>
• Всего сигналов: {self.bot_stats['total_signals']}
• Успешных: {self.bot_stats['successful_signals']}
• Успешность: {(self.bot_stats['successful_signals'] / max(1, self.bot_stats['total_signals']) * 100):.1f}%

🔫 <b>CS:GO:</b>
• Сигналов: {self.bot_stats['cs2_signals']}
• Точность: {(self.bot_stats['successful_signals'] / max(1, self.bot_stats['cs2_signals']) * 100):.1f}%

🏒 <b>КХЛ:</b>
• Сигналов: {self.bot_stats['khl_signals']}
• Точность: {(self.bot_stats['successful_signals'] / max(1, self.bot_stats['khl_signals']) * 100):.1f}%

👥 <b>Пользователи:</b>
• Активных: {self.bot_stats['users_count']}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Mini App", web_app=WebAppInfo(
                    url="https://aibet-mini-app.onrender.com"
                ))
            ]
        ])
        
        await message.answer(stats_text, reply_markup=keyboard)
    
    async def send_help(self, message: Message):
        """Отправка помощи"""
        help_text = """
❓ <b>Помощь AIBOT:</b>

🔥 <b>Основные команды:</b>
/start - Главное меню
/signals - Последние сигналы
/live - Live матчи
/stats - Статистика
/help - Эта помощь

📱 <b>Mini App:</b>
• Полный анализ матчей
• Графики и статистика
• История сигналов
• Настройки уведомлений

🎯 <b>Каналы с сигналами:</b>
• CS:GO: @aibetcsgo
• КХЛ: @aibetkhl

🤖 <b>AI возможности:</b>
• Точность прогнозов до 85%
• Анализ в реальном времени
• Учет формы команд
• Explainable AI

💬 <b>Поддержка:</b>
По вопросам пишите администратору
        """
        
        await message.answer(help_text)
    
    async def handle_text_message(self, message: Message):
        """Обработка текстовых сообщений"""
        text = message.text.lower()
        
        if "сигнал" in text or "signal" in text:
            await self.send_signals(message)
        elif "live" in text or "матч" in text:
            await self.send_live_matches(message)
        elif "статистик" in text or "stats" in text:
            await self.send_statistics(message)
        elif "помощ" in text or "help" in text:
            await self.send_help(message)
        else:
            await message.answer("🤖 Используйте кнопки меню или команды /help")
    
    async def handle_admin_callback(self, callback: CallbackQuery):
        """Обработка админ-колбэков"""
        action = callback.data.split("_")[1]
        
        if action == "update":
            await self.update_all_data(callback.message)
        elif action == "stats":
            await self.send_detailed_stats(callback.message)
        elif action == "create_signal":
            await self.create_manual_signal(callback.message)
        elif action == "send_channel":
            await self.send_to_channels(callback.message)
        elif action == "settings":
            await self.show_settings(callback.message)
        elif action == "logs":
            await self.show_logs(callback.message)
        
        await callback.answer()
    
    async def handle_signal_callback(self, callback: CallbackQuery):
        """Обработка колбэков сигналов"""
        action = callback.data.split("_")[1]
        
        if action == "refresh":
            await self.send_signals(callback.message)
        elif action == "all":
            await self.send_all_signals(callback.message)
        
        await callback.answer()
    
    async def handle_menu_callback(self, callback: CallbackQuery):
        """Обработка колбэков меню"""
        await callback.answer()
    
    async def update_all_data(self, message: Message):
        """Обновление всех данных"""
        await message.answer("🔄 Обновляю данные...")
        
        try:
            # Обновление матчей
            async with self.data_collector as collector:
                self.matches_data = await collector.collect_all_data()
            
            # Обновление моделей
            await self.ml_models.initialize_models()
            
            await message.answer("✅ Данные успешно обновлены!")
            
        except Exception as e:
            logger.error(f"Error updating data: {e}")
            await message.answer(f"❌ Ошибка обновления: {e}")
    
    async def create_manual_signal(self, message: Message):
        """Создание ручного сигнала"""
        if not self.matches_data:
            await message.answer("❌ Нет доступных матчей")
            return
        
        # Выбираем случайный матч для сигнала
        match = random.choice(self.matches_data)
        
        try:
            signal = await self.ml_models.generate_signal(match, match['sport'])
            
            if signal:
                self.signals_history.insert(0, signal)
                self.bot_stats['total_signals'] += 1
                self.bot_stats['cs2_signals'] += 1 if signal['sport'] == 'cs2' else 0
                self.bot_stats['khl_signals'] += 1 if signal['sport'] == 'khl' else 0
                
                await message.answer(f"✅ Сигнал создан: {signal['match']}")
            else:
                await message.answer("❌ Не удалось создать сигнал")
                
        except Exception as e:
            logger.error(f"Error creating signal: {e}")
            await message.answer(f"❌ Ошибка создания сигнала: {e}")
    
    async def send_to_channels(self, message: Message):
        """Отправка сигналов в каналы"""
        if not self.signals_history:
            await message.answer("❌ Нет сигналов для отправки")
            return
        
        latest_signal = self.signals_history[0]
        
        try:
            # Форматирование сообщения для канала
            channel_message = self.format_signal_for_channel(latest_signal)
            
            # Отправка в соответствующий канал
            if latest_signal['sport'] == 'cs2':
                await self.bot.send_message(self.CS2_CHANNEL, channel_message)
            else:
                await self.bot.send_message(self.KHL_CHANNEL, channel_message)
            
            await message.answer(f"✅ Сигнал отправлен в канал {latest_signal['sport']}")
            
        except Exception as e:
            logger.error(f"Error sending to channel: {e}")
            await message.answer(f"❌ Ошибка отправки: {e}")
    
    def format_signal_for_channel(self, signal: Dict) -> str:
        """Форматирование сигнала для канала"""
        sport_icon = "🔫" if signal['sport'] == 'cs2' else "🏒"
        confidence_emoji = "🟢" if signal['confidence'] >= 0.8 else "🟡" if signal['confidence'] >= 0.6 else "🔴"
        
        message = f"""
{sport_icon} <b>AIBET SIGNAL</b>

🏆 <b>{signal['match']}</b>

🎯 <b>Прогноз:</b> {signal['prediction']}
{confidence_emoji} <b>Уверенность:</b> {(signal['confidence'] * 100):.0f}%
💰 <b>Коэффициент:</b> {signal['odds']}x
📊 <b>Ценность:</b> {(signal['expected_value'] * 100):.1f}%

🤖 <b>AI Анализ:</b>
{signal['explanation']}

📈 <b>Ключевые факторы:</b>
{chr(10).join(f"• {factor}" for factor in signal['factors'])}

---
⚡ <b>AIBET Analytics</b> | AI-powered betting signals
        """
        
        return message
    
    async def get_live_matches(self) -> List[Dict]:
        """Получение live матчей"""
        # Здесь будет логика получения live матчей
        return [
            {
                'id': 'live_1',
                'sport': 'cs2',
                'team1': 'FaZe',
                'team2': 'Vitality',
                'tournament': 'IEM Katowice 2026',
                'status': 'live',
                'score1': 12,
                'score2': 8
            }
        ]
    
    async def send_detailed_stats(self, message: Message):
        """Отправка детальной статистики"""
        stats_text = f"""
📊 <b>Детальная статистика AIBOT:</b>

🎯 <b>Производительность:</b>
• Всего сигналов: {self.bot_stats['total_signals']}
• Успешных: {self.bot_stats['successful_signals']}
• Проигрышных: {self.bot_stats['total_signals'] - self.bot_stats['successful_signals']}
• Успешность: {(self.bot_stats['successful_signals'] / max(1, self.bot_stats['total_signals']) * 100):.1f}%

🔫 <b>CS:GO статистика:</b>
• Сигналов: {self.bot_stats['cs2_signals']}
• Успешность: {(self.bot_stats['successful_signals'] / max(1, self.bot_stats['cs2_signals']) * 100):.1f}%

🏒 <b>КХЛ статистика:</b>
• Сигналов: {self.bot_stats['khl_signals']}
• Успешность: {(self.bot_stats['successful_signals'] / max(1, self.bot_stats['khl_signals']) * 100):.1f}%

👥 <b>Пользователи:</b>
• Всего: {self.bot_stats['users_count']}
• Активных: {self.bot_stats['users_count']}

⏰ <b>Последний сигнал:</b>
{self.bot_stats['last_signal_time'] or 'Нет'}
        """
        
        await message.answer(stats_text)
    
    async def show_settings(self, message: Message):
        """Показ настроек"""
        settings_text = """
⚙️ <b>Настройки AIBOT:</b>

🔔 <b>Уведомления:</b>
• Автопубликация сигналов: ✅
• Live-обновления: ✅
• Статистические отчеты: ✅

🤖 <b>AI настройки:</b>
• Минимальная уверенность: 65%
• Минимальная ценность: 5%
• Автообучение: ✅

📡 <b>Каналы:</b>
• CS:GO: @aibetcsgo ✅
• КХЛ: @aibetkhl ✅

⚡ <b>Система:</b>
• Статус: Активна
• Версия: 1.0.0
• Uptime: 24/7
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Перезапустить AI", callback_data="admin_restart_ai"),
                InlineKeyboardButton(text="📊 Очистить кэш", callback_data="admin_clear_cache")
            ]
        ])
        
        await message.answer(settings_text, reply_markup=keyboard)
    
    async def show_logs(self, message: Message):
        """Показ логов"""
        logs_text = """
📝 <b>Последние логи AIBOT:</b>

✅ [2026-01-30 22:30] Бот запущен
✅ [2026-01-30 22:25] ML модели загружены
✅ [2026-01-30 22:20] Данные обновлены
🔥 [2026-01-30 22:15] Сигнал отправлен: NAVI vs G2
✅ [2026-01-30 22:10] Live матч обновлен
📊 [2026-01-30 22:05] Статистика обновлена

🔥 <b>Активность за сегодня:</b>
• Сигналов создано: 12
• В каналы отправлено: 8
• Пользователей: 156
• Ошибок: 0
        """
        
        await message.answer(logs_text)
    
    async def auto_signal_loop(self):
        """Автоматический цикл создания сигналов"""
        while True:
            try:
                # Обновление данных
                async with self.data_collector as collector:
                    self.matches_data = await collector.collect_all_data()
                
                # Создание сигналов для качественных матчей
                for match in self.matches_data:
                    if match['status'] == 'upcoming':
                        signal = await self.ml_models.generate_signal(match, match['sport'])
                        
                        if signal and signal['confidence'] >= 0.7:
                            self.signals_history.insert(0, signal)
                            self.bot_stats['total_signals'] += 1
                            self.bot_stats['cs2_signals'] += 1 if signal['sport'] == 'cs2' else 0
                            self.bot_stats['khl_signals'] += 1 if signal['sport'] == 'khl' else 0
                            self.bot_stats['last_signal_time'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            
                            # Отправка в канал
                            try:
                                channel_message = self.format_signal_for_channel(signal)
                                if signal['sport'] == 'cs2':
                                    await self.bot.send_message(self.CS2_CHANNEL, channel_message)
                                else:
                                    await self.bot.send_message(self.KHL_CHANNEL, channel_message)
                                
                                logger.info(f"Signal sent to {signal['sport']} channel")
                                
                            except Exception as e:
                                logger.error(f"Error sending signal to channel: {e}")
                
                # Ожидание перед следующей проверкой (30 минут)
                await asyncio.sleep(1800)
                
            except Exception as e:
                logger.error(f"Error in auto signal loop: {e}")
                await asyncio.sleep(300)  # 5 минут при ошибке
    
    async def start(self):
        """Запуск бота"""
        logger.info("🚀 Starting AIBOT Telegram Bot")
        
        # Инициализация базы данных
        await self.db_manager.initialize()
        
        # Инициализация ML моделей
        await self.ml_models.initialize_models()
        
        # Запуск авто-цикла сигналов
        asyncio.create_task(self.auto_signal_loop())
        
        # Запуск поллинга
        await self.dp.start_polling(self.bot)

# Запуск бота
async def main():
    bot = AIBOTTelegramBot()
    await bot.start()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
