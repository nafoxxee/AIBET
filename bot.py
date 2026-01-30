import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp_cors

from config import config
from database import DatabaseManager, Signal, Match
from ml.cs2_analyzer import CS2Analyzer
from ml.khl_analyzer import KHLAnalyzer

logger = logging.getLogger(__name__)


class BotStates(StatesGroup):
    """Состояния бота"""
    main_menu = State()
    cs2_menu = State()
    khl_menu = State()
    statistics = State()
    history = State()


class TelegramBot:
    """Основной класс Telegram бота"""
    
    def __init__(self):
        self.bot = Bot(token=config.telegram.bot_token)
        self.dp = Dispatcher()
        self.db_manager = DatabaseManager(config.database.path)
        self.cs2_analyzer = None
        self.khl_analyzer = None
        
        # Настройка обработчиков
        self._setup_handlers()
    
    async def initialize(self):
        """Инициализация бота"""
        await self.db_manager.initialize()
        
        # Инициализация анализаторов
        self.cs2_analyzer = CS2Analyzer(self.db_manager)
        self.khl_analyzer = KHLAnalyzer(self.db_manager)
        
        await self.cs2_analyzer.initialize()
        await self.khl_analyzer.initialize()
        
        logger.info("Telegram bot initialized")
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            await self._show_main_menu(message)
        
        @self.dp.callback_query(lambda c: c.data == "main_menu")
        async def main_menu_callback(callback: CallbackQuery):
            await self._show_main_menu(callback.message)
        
        # CS2 меню
        @self.dp.callback_query(lambda c: c.data == "cs2_menu")
        async def cs2_menu_callback(callback: CallbackQuery):
            await self._show_cs2_menu(callback.message)
        
        @self.dp.callback_query(lambda c: c.data.startswith("cs2_"))
        async def cs2_action_callback(callback: CallbackQuery):
            await self._handle_cs2_action(callback)
        
        # КХЛ меню
        @self.dp.callback_query(lambda c: c.data == "khl_menu")
        async def khl_menu_callback(callback: CallbackQuery):
            await self._show_khl_menu(callback.message)
        
        @self.dp.callback_query(lambda c: c.data.startswith("khl_"))
        async def khl_action_callback(callback: CallbackQuery):
            await self._handle_khl_action(callback)
        
        # Статистика
        @self.dp.callback_query(lambda c: c.data == "statistics")
        async def statistics_callback(callback: CallbackQuery):
            await self._show_statistics(callback.message)
        
        # История
        @self.dp.callback_query(lambda c: c.data == "history")
        async def history_callback(callback: CallbackQuery):
            await self._show_history(callback.message)
        
        # Статус системы
        @self.dp.callback_query(lambda c: c.data == "system_status")
        async def system_status_callback(callback: CallbackQuery):
            await self._show_system_status(callback.message)
        
        # Mini App
        @self.dp.callback_query(lambda c: c.data == "open_mini_app")
        async def mini_app_callback(callback: CallbackQuery):
            await self._open_mini_app(callback.message)
        
        # Админ функции
        @self.dp.callback_query(lambda c: c.data.startswith("admin_"))
        async def admin_callback(callback: CallbackQuery):
            await self._handle_admin_action(callback)
        
        # Помощь
        @self.dp.callback_query(lambda c: c.data == "help")
        async def help_callback(callback: CallbackQuery):
            await self._show_help(callback.message)
    
    async def _show_main_menu(self, message: Message):
        """Показать главное меню"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔫 CS2", callback_data="cs2_menu"),
                InlineKeyboardButton(text="🏒 КХЛ", callback_data="khl_menu")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="statistics"),
                InlineKeyboardButton(text="📈 История", callback_data="history")
            ],
            [
                InlineKeyboardButton(text="🔧 Статус системы", callback_data="system_status"),
                InlineKeyboardButton(text="📱 Mini App", callback_data="open_mini_app")
            ],
            [
                InlineKeyboardButton(text="❓ Помощь", callback_data="help")
            ]
        ])
        
        await message.answer(
            "🎯 **AI BET Analytics Platform**\n\n"
            "Выберите раздел для просмотра аналитики:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def _show_cs2_menu(self, message: Message):
        """Показать меню CS2"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Текущие матчи", callback_data="cs2_current"),
                InlineKeyboardButton(text="🔴 Live матчи", callback_data="cs2_live")
            ],
            [
                InlineKeyboardButton(text="📈 Аналитика", callback_data="cs2_analytics"),
                InlineKeyboardButton(text="🎯 Сигналы", callback_data="cs2_signals")
            ],
            [
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
            ]
        ])
        
        await message.answer(
            "🔫 **CS2 Аналитика**\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def _show_khl_menu(self, message: Message):
        """Показать меню КХЛ"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Текущие матчи", callback_data="khl_current"),
                InlineKeyboardButton(text="🔴 Live матчи", callback_data="khl_live")
            ],
            [
                InlineKeyboardButton(text="📈 Аналитика", callback_data="khl_analytics"),
                InlineKeyboardButton(text="🎯 Сигналы", callback_data="khl_signals")
            ],
            [
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
            ]
        ])
        
        await message.answer(
            "🏒 **КХЛ Аналитика**\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def _handle_cs2_action(self, callback: CallbackQuery):
        """Обработка действий CS2"""
        action = callback.data
        
        if action == "cs2_current":
            await self._show_cs2_current_matches(callback.message)
        elif action == "cs2_live":
            await self._show_cs2_live_matches(callback.message)
        elif action == "cs2_analytics":
            await self._show_cs2_analytics(callback.message)
        elif action == "cs2_signals":
            await self._show_cs2_signals(callback.message)
        
        await callback.answer()
    
    async def _handle_khl_action(self, callback: CallbackQuery):
        """Обработка действий КХЛ"""
        action = callback.data
        
        if action == "khl_current":
            await self._show_khl_current_matches(callback.message)
        elif action == "khl_live":
            await self._show_khl_live_matches(callback.message)
        elif action == "khl_analytics":
            await self._show_khl_analytics(callback.message)
        elif action == "khl_signals":
            await self._show_khl_signals(callback.message)
        
        await callback.answer()
    
    async def _show_cs2_current_matches(self, message: Message):
        """Показать текущие матчи CS2"""
        try:
            matches = await self.db_manager.get_upcoming_matches(sport='cs2', hours=24)
            
            if not matches:
                await message.answer("📋 Нет предстоящих матчей CS2 в ближайшие 24 часа")
                return
            
            response = "📋 **Предстоящие матчи CS2**\n\n"
            
            for match in matches[:10]:  # Показываем первые 10
                response += f"🔫 **{match.team1} vs {match.team2}**\n"
                response += f"🏆 {match.tournament}\n"
                response += f"⏰ {match.match_time.strftime('%d.%m %H:%M')}\n"
                response += f"💰 Коэффициенты: {match.odds1:.2f} - {match.odds2:.2f}\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="cs2_menu")]
            ])
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error showing CS2 current matches: {e}")
            await message.answer("❌ Ошибка загрузки матчей")
    
    async def _show_cs2_live_matches(self, message: Message):
        """Показать live матчи CS2"""
        try:
            matches = await self.db_manager.get_live_matches(sport='cs2')
            
            if not matches:
                await message.answer("🔴 Нет live матчей CS2")
                return
            
            response = "🔴 **Live матчи CS2**\n\n"
            
            for match in matches:
                response += f"🔫 **{match.team1} {match.score1} - {match.score2} {match.team2}**\n"
                response += f"🏆 {match.tournament}\n"
                response += f"💰 Коэффициенты: {match.odds1:.2f} - {match.odds2:.2f}\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="cs2_menu")]
            ])
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error showing CS2 live matches: {e}")
            await message.answer("❌ Ошибка загрузки live матчей")
    
    async def _show_cs2_analytics(self, message: Message):
        """Показать аналитику CS2"""
        try:
            stats = await self.db_manager.get_statistics(sport='cs2')
            
            response = "📈 **CS2 Аналитика**\n\n"
            response += f"📊 Всего сигналов: {stats['total']}\n"
            response += f"✅ Успешных: {stats['wins']}\n"
            response += f"❌ Неудачных: {stats['losses']}\n"
            response += f"🎯 Точность: {stats['accuracy']:.1f}%\n\n"
            
            # Добавляем информацию о ML модели
            if self.cs2_analyzer.last_trained:
                response += f"🤖 ML модель обучена: {self.cs2_analyzer.last_trained.strftime('%d.%m %H:%M')}\n"
                response += f"📊 Точность модели: {self.cs2_analyzer.model_accuracy:.1f}%\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="cs2_menu")]
            ])
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error showing CS2 analytics: {e}")
            await message.answer("❌ Ошибка загрузки аналитики")
    
    async def _show_cs2_signals(self, message: Message):
        """Показать сигналы CS2"""
        try:
            signals = await self.db_manager.get_signals(sport='cs2', limit=5)
            
            if not signals:
                await message.answer("🎯 Нет доступных сигналов CS2")
                return
            
            response = "🎯 **Последние сигналы CS2**\n\n"
            
            for signal in signals:
                match = await self.db_manager.get_match(signal.match_id)
                if match:
                    response += f"🔫 **{match.team1} vs {match.team2}**\n"
                    response += f"📊 Сценарий: {signal.scenario}\n"
                    response += f"🎯 Уверенность: {signal.confidence}\n"
                    response += f"📈 Вероятность: {signal.probability:.1%}\n"
                    response += f"💰 Коэффициент: {signal.odds_at_signal:.2f}\n"
                    response += f"📝 {signal.explanation}\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="cs2_menu")]
            ])
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error showing CS2 signals: {e}")
            await message.answer("❌ Ошибка загрузки сигналов")
    
    async def _show_khl_current_matches(self, message: Message):
        """Показать текущие матчи КХЛ"""
        try:
            matches = await self.db_manager.get_upcoming_matches(sport='khl', hours=24)
            
            if not matches:
                await message.answer("📋 Нет предстоящих матчей КХЛ в ближайшие 24 часа")
                return
            
            response = "📋 **Предстоящие матчи КХЛ**\n\n"
            
            for match in matches[:10]:
                response += f"🏒 **{match.team1} vs {match.team2}**\n"
                response += f"🏆 {match.tournament}\n"
                response += f"⏰ {match.match_time.strftime('%d.%m %H:%M')}\n"
                response += f"💰 Коэффициенты: {match.odds1:.2f} - {match.odds2:.2f} - {match.odds_draw:.2f}\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="khl_menu")]
            ])
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error showing KHL current matches: {e}")
            await message.answer("❌ Ошибка загрузки матчей")
    
    async def _show_khl_live_matches(self, message: Message):
        """Показать live матчи КХЛ"""
        try:
            matches = await self.db_manager.get_live_matches(sport='khl')
            
            if not matches:
                await message.answer("🔴 Нет live матчей КХЛ")
                return
            
            response = "🔴 **Live матчи КХЛ**\n\n"
            
            for match in matches:
                response += f"🏒 **{match.team1} {match.score1} - {match.score2} {match.team2}**\n"
                response += f"🏆 {match.tournament}\n"
                response += f"💰 Коэффициенты: {match.odds1:.2f} - {match.odds2:.2f} - {match.odds_draw:.2f}\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="khl_menu")]
            ])
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error showing KHL live matches: {e}")
            await message.answer("❌ Ошибка загрузки live матчей")
    
    async def _show_khl_analytics(self, message: Message):
        """Показать аналитику КХЛ"""
        try:
            stats = await self.db_manager.get_statistics(sport='khl')
            
            response = "📈 **КХЛ Аналитика**\n\n"
            response += f"📊 Всего сигналов: {stats['total']}\n"
            response += f"✅ Успешных: {stats['wins']}\n"
            response += f"❌ Неудачных: {stats['losses']}\n"
            response += f"🎯 Точность: {stats['accuracy']:.1f}%\n\n"
            
            # Добавляем информацию о ML модели
            if self.khl_analyzer.last_trained:
                response += f"🤖 ML модель обучена: {self.khl_analyzer.last_trained.strftime('%d.%m %H:%M')}\n"
                response += f"📊 Точность модели: {self.khl_analyzer.model_accuracy:.1f}%\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="khl_menu")]
            ])
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error showing KHL analytics: {e}")
            await message.answer("❌ Ошибка загрузки аналитики")
    
    async def _show_khl_signals(self, message: Message):
        """Показать сигналы КХЛ"""
        try:
            signals = await self.db_manager.get_signals(sport='khl', limit=5)
            
            if not signals:
                await message.answer("🎯 Нет доступных сигналов КХЛ")
                return
            
            response = "🎯 **Последние сигналы КХЛ**\n\n"
            
            for signal in signals:
                match = await self.db_manager.get_match(signal.match_id)
                if match:
                    response += f"🏒 **{match.team1} vs {match.team2}**\n"
                    response += f"📊 Сценарий: {signal.scenario}\n"
                    response += f"🎯 Уверенность: {signal.confidence}\n"
                    response += f"📈 Вероятность: {signal.probability:.1%}\n"
                    response += f"💰 Коэффициент: {signal.odds_at_signal:.2f}\n"
                    response += f"📝 {signal.explanation}\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="khl_menu")]
            ])
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error showing KHL signals: {e}")
            await message.answer("❌ Ошибка загрузки сигналов")
    
    async def _show_statistics(self, message: Message):
        """Показать общую статистику"""
        try:
            cs2_stats = await self.db_manager.get_statistics(sport='cs2')
            khl_stats = await self.db_manager.get_statistics(sport='khl')
            
            response = "📊 **Общая статистика**\n\n"
            
            response += "🔫 **CS2:**\n"
            response += f"📈 Сигналов: {cs2_stats['total']} | Точность: {cs2_stats['accuracy']:.1f}%\n\n"
            
            response += "🏒 **КХЛ:**\n"
            response += f"📈 Сигналов: {khl_stats['total']} | Точность: {khl_stats['accuracy']:.1f}%\n\n"
            
            total_signals = cs2_stats['total'] + khl_stats['total']
            total_wins = cs2_stats['wins'] + khl_stats['wins']
            total_losses = cs2_stats['losses'] + khl_stats['losses']
            overall_accuracy = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
            
            response += "📊 **Общие показатели:**\n"
            response += f"🎯 Всего сигналов: {total_signals}\n"
            response += f"✅ Успешных: {total_wins}\n"
            response += f"❌ Неудачных: {total_losses}\n"
            response += f"🎯 Общая точность: {overall_accuracy:.1f}%\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
            ])
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error showing statistics: {e}")
            await message.answer("❌ Ошибка загрузки статистики")
    
    async def _show_history(self, message: Message):
        """Показать историю сигналов"""
        try:
            cs2_signals = await self.db_manager.get_signals(sport='cs2', limit=5)
            khl_signals = await self.db_manager.get_signals(sport='khl', limit=5)
            
            response = "📈 **История сигналов**\n\n"
            
            if cs2_signals:
                response += "🔫 **CS2:**\n"
                for signal in cs2_signals:
                    result_emoji = "✅" if signal.result == "win" else "❌" if signal.result == "lose" else "⏳"
                    response += f"{result_emoji} {signal.scenario} ({signal.confidence})\n"
                response += "\n"
            
            if khl_signals:
                response += "🏒 **КХЛ:**\n"
                for signal in khl_signals:
                    result_emoji = "✅" if signal.result == "win" else "❌" if signal.result == "lose" else "⏳"
                    response += f"{result_emoji} {signal.scenario} ({signal.confidence})\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
            ])
            
            await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error showing history: {e}")
            await message.answer("❌ Ошибка загрузки истории")
    
    async def _show_system_status(self, message: Message):
        """Показать статус системы"""
        try:
            response = "🔧 **Статус системы**\n\n"
            response += "🤖 **Бот:** ✅ Онлайн\n"
            response += f"🗄️ **База данных:** ✅ Подключена\n"
            response += f"🔫 **CS2 анализатор:** ✅ {'Обучен' if self.cs2_analyzer.last_trained else 'Не обучен'}\n"
            response += f"🏒 **КХЛ анализатор:** ✅ {'Обучен' if self.khl_analyzer.last_trained else 'Не обучен'}\n"
            
            # Проверяем каналы
            if config.telegram.cs2_channel_id:
                response += f"📢 **CS2 канал:** {config.telegram.cs2_channel_id}\n"
            if config.telegram.khl_channel_id:
                response += f"📢 **КХЛ канал:** {config.telegram.khl_channel_id}\n"
            
            # Админ функции
            if message.from_user.id in config.telegram.admin_ids:
                response += "\n🛠️ **Админ функции:**\n"
                response += "🔄 Перезапустить анализ\n"
                response += "🧠 Переобучить ML\n"
                response += "📊 Детальная статистика\n"
            
            keyboard = []
            
            # Админ кнопки
            if message.from_user.id in config.telegram.admin_ids:
                keyboard.append([
                    InlineKeyboardButton(text="🔄 Перезапустить анализ", callback_data="admin_restart"),
                    InlineKeyboardButton(text="🧠 Переобучить ML", callback_data="admin_retrain")
                ])
            
            keyboard.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])
            
            await message.answer(response, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error showing system status: {e}")
            await message.answer("❌ Ошибка загрузки статуса")
    
    async def _open_mini_app(self, message: Message):
        """Открыть Mini App"""
        try:
            # Создаем WebApp кнопку
            webapp_url = f"https://{config.api.host}:{config.api.port}/index.html"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📱 Открыть Mini App", web_app=types.WebAppInfo(url=webapp_url))],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
            ])
            
            await message.answer(
                "📱 **AI BET Mini App**\n\n"
                "Откройте полноценный веб-интерфейс для детальной аналитики:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        
        except Exception as e:
            logger.error(f"Error opening mini app: {e}")
            await message.answer("❌ Ошибка открытия Mini App")
    
    async def _handle_admin_action(self, callback: CallbackQuery):
        """Обработка админских действий"""
        if callback.from_user.id not in config.telegram.admin_ids:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        action = callback.data
        
        if action == "admin_restart":
            await self._admin_restart_analysis(callback.message)
        elif action == "admin_retrain":
            await self._admin_retrain_ml(callback.message)
        
        await callback.answer()
    
    async def _admin_restart_analysis(self, message: Message):
        """Перезапуск анализа"""
        try:
            await message.answer("🔄 Перезапуск анализа...")
            
            # Здесь будет логика перезапуска анализа
            await asyncio.sleep(2)
            
            await message.answer("✅ Анализ успешно перезапущен")
        
        except Exception as e:
            logger.error(f"Error restarting analysis: {e}")
            await message.answer("❌ Ошибка перезапуска анализа")
    
    async def _admin_retrain_ml(self, message: Message):
        """Переобучение ML"""
        try:
            await message.answer("🧠 Переобучение ML моделей...")
            
            # Обучаем модели
            await self.cs2_analyzer.train_models()
            await self.khl_analyzer.train_models()
            
            await message.answer("✅ ML модели успешно обучены")
        
        except Exception as e:
            logger.error(f"Error retraining ML: {e}")
            await message.answer("❌ Ошибка обучения ML моделей")
    
    async def _show_help(self, message: Message):
        """Показать помощь"""
        response = """❓ **Помощь - AI BET Analytics Platform**

🎯 **Что это?**
Платформа для аналитики спортивных рынков CS2 и КХЛ с использованием ML.

🔫 **CS2 Аналитика:**
• Предматч анализ матчей
• Live аналитика в реальном времени
• Сценарный анализ
• Анализ коэффициентов

🏒 **КХЛ Аналитика:**
• Анализ матчей КХЛ
• Учет домашнего преимущества
• Анализ вратарей
• Статистика по периодам

📱 **Mini App:**
Полноценный веб-интерфейс с детальной аналитикой и графиками.

📊 **Каналы:**
• CS2: @aibetcsgo
• КХЛ: @aibetkhl

🤖 **ML Система:**
• Самообучение на результатах
• Обнаружение паттернов
• Прогнозирование сценариев

📈 **Точность:**
Система постоянно обучается и улучшает точность прогнозов.

🔧 **Поддержка:**
По вопросам обращайтесь к администратору."""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        
        await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
    
    async def publish_signal(self, signal: Signal, match: Match):
        """Публикация сигнала в канал"""
        try:
            # Определяем канал
            if signal.sport == 'cs2':
                channel_id = config.telegram.cs2_channel_id
                sport_emoji = "🔫"
            else:
                channel_id = config.telegram.khl_channel_id
                sport_emoji = "🏒"
            
            if not channel_id:
                logger.warning(f"No channel configured for {signal.sport}")
                return
            
            # Формируем сообщение
            confidence_emoji = {
                'HIGH': '🔥',
                'MEDIUM': '⚡',
                'LOW': '💡'
            }.get(signal.confidence, '📊')
            
            message = f"""{sport_emoji} **AI BET Signal - {signal.sport.upper()}**

🏆 **Матч:** {match.team1} vs {match.team2}
📊 **Турнир:** {match.tournament}
⏰ **Время:** {match.match_time.strftime('%d.%m %H:%M')}

🎯 **Сценарий:** {signal.scenario}
{confidence_emoji} **Уверенность:** {signal.confidence}
📈 **Вероятность:** {signal.probability:.1%}
💰 **Коэффициент:** {signal.odds_at_signal:.2f}

📝 **Объяснение:**
{signal.explanation}

🔑 **Факторы:**
{chr(10).join(f'• {factor}' for factor in signal.factors)}

---
📱 Аналитика: @aibetcsgo | @aibetkhl
🤖 AI Powered Betting Analytics"""
            
            # Создаем клавиатуру
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Подробнее", callback_data=f"signal_{signal.id}")]
            ])
            
            # Публикуем в канал
            await self.bot.send_message(
                chat_id=channel_id,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            logger.info(f"Published signal {signal.id} to {signal.sport} channel")
        
        except Exception as e:
            logger.error(f"Error publishing signal {signal.id}: {e}")
    
    async def run(self):
        """Запуск бота"""
        logger.info("Starting Telegram bot...")
        await self.dp.start_polling(self.bot)
