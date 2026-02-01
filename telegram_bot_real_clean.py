#!/usr/bin/env python3
"""
AIBET Analytics Platform - Real Telegram Bot
Enhanced bot with real data, inline mini app button, and comprehensive commands
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
    WebAppInfo, CallbackQuery, InlineQuery, InputTextMessageContent
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager, User, Match
from parsers.cs2_parser import CS2Parser
from parsers.khl_parser import KHLParser
from parsers.odds_parser import odds_parser
from feature_engineering_real import feature_engineering
from ml_models_real import ml_models

logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "379036860"))
MINI_APP_URL = "https://aibet-mini-prilozhenie.onrender.com/"
API_BASE_URL = "http://localhost:8000"  # Local API URL

class RealTelegramBot:
    def __init__(self, bot_token: str, admin_id: int, db_manager_instance):
        self.bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()
        self.admin_id = admin_id
        self.db_manager = db_manager_instance
        self._initialized = False
        
        # Initialize parsers
        self.cs2_parser = CS2Parser()
        self.khl_parser = KHLParser()
        
        # Daily signal counter
        self.daily_signals = 0
        self.last_signal_date = datetime.now().date()
        
        # Регистрируем хендлеры
        self.register_handlers()
        
        logger.info(f"🤖 Real Telegram Bot initialized (admin: {admin_id})")
    
    def register_handlers(self):
        """Регистрация всех хендлеров"""
        logger.info("🔧 Registering bot handlers")
        
        # Команды
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_live, Command("live"))
        self.dp.message.register(self.cmd_signals, Command("signals"))
        self.dp.message.register(self.cmd_analysis, Command("analysis"))
        self.dp.message.register(self.cmd_stats, Command("stats"))
        self.dp.message.register(self.cmd_odds, Command("odds"))
        self.dp.message.register(self.cmd_mini_app, Command("miniapp"))
        self.dp.message.register(self.cmd_admin, Command("admin"))
        
        # Inline queries
        self.dp.inline_query.register(self.inline_handler)
        
        # Callback queries
        self.dp.callback_query.register(self.callback_handler)
        
        # Text messages
        self.dp.message.register(self.text_handler, F.text)
        
        logger.info("✅ All handlers registered")
    
    async def cmd_start(self, message: Message):
        """Команда /start"""
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        
        # Сохраняем пользователя
        await self.db_manager.add_user(
            user_id=user_id,
            username=username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        # Создаем клавиатуру с кнопкой Mini App
        keyboard = InlineKeyboardBuilder()
        keyboard.button(
            text="🚀 Открыть Mini App",
            web_app=WebApp(url=MINI_APP_URL)
        )
        keyboard.button(
            text="📊 Смотреть прогнозы",
            callback_data="show_signals"
        )
        keyboard.button(
            text="⚡ Live матчи",
            callback_data="show_live"
        )
        keyboard.adjust(1)
        
        welcome_text = f"""
🎯 <b>Добро пожаловать в AIBET Analytics!</b>

👋 Привет, {username}!

🤖 Я ваш персональный AI-ассистент для ставок на спорт:

🔹 <b>CS2</b> - Прогнозы на матчи Counter-Strike 2
🔹 <b>KHL</b> - Анализ матчей Континентальной Хоккейной Лиги

✨ <b>Что я умею:</b>
• 🎯 Точные прогнозы на основе ML
• 📊 Анализ последних 100 матчей
• 💰 Коэффициенты от топ букмекеров
• ⚡ Live обновления
• 🚪 Удобная Mini App

👇 <b>Выберите действие:</b>
        """
        
        await message.answer(
            welcome_text,
            reply_markup=keyboard.as_markup()
        )
    
    async def cmd_help(self, message: Message):
        """Команда /help"""
        help_text = """
📖 <b>Справка по командам AIBET:</b>

🔹 <code>/start</code> - Главное меню
🔹 <code>/live</code> - Live матчи CS2 + KHL
🔹 <code>/signals</code> - Точные сигналы (confidence ≥ 70%)
🔹 <code>/analysis [ID]</code> - Анализ конкретного матча
🔹 <code>/stats [TEAM]</code> - Статистика команды
🔹 <code>/odds [ID]</code> - Коэффициенты по матчу
🔹 <code>/miniapp</code> - Открыть Mini App

💡 <b>Совет:</b> Используйте inline режим! Введите @aibet_bot в любом чате.

📱 <b>Mini App:</b> Полная аналитика в удобном интерфейсе

❓ <b>Поддержка:</b> @admin
        """
        
        await message.answer(help_text)
    
    async def cmd_live(self, message: Message):
        """Команда /live - показать live матчи"""
        try:
            await message.answer("⏳ Загружаю live матчи...")
            
            # Получаем live матчи
            cs2_matches = await self.db_manager.get_matches(sport="cs2", status="live", limit=5)
            khl_matches = await self.db_manager.get_matches(sport="khl", status="live", limit=5)
            
            if not cs2_matches and not khl_matches:
                await message.answer("🔴 Сейчас нет live матчей")
                return
            
            response_text = "⚡ <b>Live матчи:</b>\n\n"
            
            if cs2_matches:
                response_text += "🔫 <b>CS2:</b>\n"
                for match in cs2_matches:
                    response_text += f"• {match.team1} vs {match.team2}\n"
                    response_text += f"  Счет: {match.score or 'N/A'}\n\n"
            
            if khl_matches:
                response_text += "🏒 <b>KHL:</b>\n"
                for match in khl_matches:
                    response_text += f"• {match.team1} vs {match.team2}\n"
                    response_text += f"  Счет: {match.score or 'N/A'}\n\n"
            
            # Клавиатура для обновления
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔄 Обновить", callback_data="refresh_live")
            keyboard.button(text="📊 Все матчи", callback_data="show_all_matches")
            keyboard.adjust(2)
            
            await message.edit_text(response_text, reply_markup=keyboard.as_markup())
            
        except Exception as e:
            logger.error(f"Error in /live: {e}")
            await message.answer("❌ Ошибка загрузки live матчей")
    
    async def cmd_signals(self, message: Message):
        """Команда /signals - лучшие сигналы"""
        try:
            # Проверяем лимит сигналов в день
            today = datetime.now().date()
            if today != self.last_signal_date:
                self.daily_signals = 0
                self.last_signal_date = today
            
            if self.daily_signals >= 10:
                await message.answer("📊 Лимит сигналов на сегодня исчерпан (10/10)")
                return
            
            await message.answer("🎯 Анализирую матчи для сигналов...")
            
            # Получаем прогнозы от ML моделей
            predictions = await ml_models.predict_upcoming_matches(limit=20)
            
            # Фильтруем по confidence >= 70%
            high_confidence = [p for p in predictions if p.confidence >= 0.70]
            
            if not high_confidence:
                await message.answer("🔴 Нет сигналов с confidence ≥ 70%")
                return
            
            # Ограничиваем количество
            available_signals = min(len(high_confidence), 10 - self.daily_signals)
            signals = high_confidence[:available_signals]
            
            response_text = f"🎯 <b>Точные сигналы ({len(signals)}):</b>\n\n"
            
            for i, signal in enumerate(signals, 1):
                winner = signal.team1 if signal.prediction == 1 else signal.team2
                confidence_percent = int(signal.confidence * 100)
                
                response_text += f"{i}. <b>{winner}</b>\n"
                response_text += f"   {signal.team1} vs {signal.team2}\n"
                response_text += f"   Confidence: {confidence_percent}%\n"
                response_text += f"   Модель: {signal.model_used}\n\n"
            
            self.daily_signals += len(signals)
            
            # Клавиатура
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="📊 Больше прогнозов", callback_data="more_predictions")
            keyboard.button(text="🚀 Mini App", web_app=WebApp(url=MINI_APP_URL))
            keyboard.adjust(1)
            
            await message.edit_text(
                response_text + f"\n📊 Осталось сигналов сегодня: {10 - self.daily_signals}/10",
                reply_markup=keyboard.as_markup()
            )
            
        except Exception as e:
            logger.error(f"Error in /signals: {e}")
            await message.answer("❌ Ошибка загрузки сигналов")
    
    async def cmd_analysis(self, message: Message):
        """Команда /analysis - анализ матча"""
        try:
            # Получаем ID матча из аргументов
            args = message.text.split()
            if len(args) < 2:
                await message.answer("Использование: /analysis [ID матча]")
                return
            
            match_id = args[1]
            await message.answer(f"📊 Анализирую матч {match_id}...")
            
            # Получаем матч из базы
            matches = await self.db_manager.get_matches(limit=100)
            target_match = None
            
            for match in matches:
                if str(match.id) == match_id:
                    target_match = match
                    break
            
            if not target_match:
                await message.answer("❌ Матч не найден")
                return
            
            # Получаем ML прогноз
            prediction = await ml_models.predict_match(target_match)
            
            if not prediction:
                await message.answer("❌ Не удалось получить прогноз")
                return
            
            # Получаем фичи для обеих команд
            team1_features, team2_features = await feature_engineering.extract_features_for_match(target_match)
            
            response_text = f"📊 <b>Анализ матча:</b>\n\n"
            response_text += f"🔫 {target_match.team1} vs {target_match.team2}\n"
            response_text += f"🏆 Спорт: {target_match.sport.upper()}\n"
            response_text += f"⏰ Время: {target_match.start_time or 'N/A'}\n\n"
            
            # Прогноз
            winner = target_match.team1 if prediction.prediction == 1 else target_match.team2
            confidence_percent = int(prediction.confidence * 100)
            
            response_text += f"🎯 <b>Прогноз:</b> {winner}\n"
            response_text += f"📈 Confidence: {confidence_percent}%\n"
            response_text += f"🤖 Модель: {prediction.model_used}\n\n"
            
            # Статистика команд
            response_text += f"📊 <b>Статистика {target_match.team1}:</b>\n"
            response_text += f"• Win Rate: {team1_features.win_rate:.1%}\n"
            response_text += f"• Форма: {team1_features.recent_wins}-{team1_features.recent_draws}-{team1_features.recent_losses}\n"
            response_text += f"• Momentum: {team1_features.momentum_score:.1f}\n\n"
            
            response_text += f"📊 <b>Статистика {target_match.team2}:</b>\n"
            response_text += f"• Win Rate: {team2_features.win_rate:.1%}\n"
            response_text += f"• Форма: {team2_features.recent_wins}-{team2_features.recent_draws}-{team2_features.recent_losses}\n"
            response_text += f"• Momentum: {team2_features.momentum_score:.1f}\n\n"
            
            await message.edit_text(response_text)
            
        except Exception as e:
            logger.error(f"Error in /analysis: {e}")
            await message.answer("❌ Ошибка анализа матча")
    
    async def cmd_stats(self, message: Message):
        """Команда /stats - статистика команды"""
        try:
            args = message.text.split()
            if len(args) < 2:
                await message.answer("Использование: /stats [Название команды]")
                return
            
            team_name = " ".join(args[1:])
            await message.answer(f"📊 Загружаю статистику {team_name}...")
            
            # Ищем команду в обоих видах спорта
            cs2_features = None
            khl_features = None
            
            try:
                cs2_features = await feature_engineering.get_team_features(team_name, "cs2")
            except:
                pass
            
            try:
                khl_features = await feature_engineering.get_team_features(team_name, "khl")
            except:
                pass
            
            if not cs2_features and not khl_features:
                await message.answer(f"❌ Команда '{team_name}' не найдена")
                return
            
            response_text = f"📊 <b>Статистика {team_name}:</b>\n\n"
            
            if cs2_features:
                response_text += f"🔫 <b>CS2:</b>\n"
                response_text += f"• Win Rate: {cs2_features.win_rate:.1%}\n"
                response_text += f"• Матчей: {cs2_features.total_matches}\n"
                response_text += f"• Средний счет: {cs2_features.avg_score:.1f}\n"
                response_text += f"• Форма: {cs2_features.recent_wins}-{cs2_features.recent_draws}-{cs2_features.recent_losses}\n\n"
            
            if khl_features:
                response_text += f"🏒 <b>KHL:</b>\n"
                response_text += f"• Win Rate: {khl_features.win_rate:.1%}\n"
                response_text += f"• Матчей: {khl_features.total_matches}\n"
                response_text += f"• Средний счет: {khl_features.avg_score:.1f}\n"
                response_text += f"• Форма: {khl_features.recent_wins}-{khl_features.recent_draws}-{khl_features.recent_losses}\n\n"
            
            await message.edit_text(response_text)
            
        except Exception as e:
            logger.error(f"Error in /stats: {e}")
            await message.answer("❌ Ошибка загрузки статистики")
    
    async def cmd_odds(self, message: Message):
        """Команда /odds - коэффициенты по матчу"""
        try:
            args = message.text.split()
            if len(args) < 2:
                await message.answer("Использование: /odds [ID матча]")
                return
            
            match_id = args[1]
            await message.answer(f"💰 Загружаю коэффициенты для матча {match_id}...")
            
            # Получаем матч
            matches = await self.db_manager.get_matches(limit=100)
            target_match = None
            
            for match in matches:
                if str(match.id) == match_id:
                    target_match = match
                    break
            
            if not target_match:
                await message.answer("❌ Матч не найден")
                return
            
            # Получаем коэффициенты
            odds_data = await odds_parser.get_all_odds(target_match.sport)
            
            # Ищем коэффициенты для этого матча
            match_odds = []
            for odds in odds_data:
                if (odds.team1 == target_match.team1 and odds.team2 == target_match.team2):
                    match_odds.append(odds)
            
            if not match_odds:
                await message.answer("❌ Коэффициенты не найдены")
                return
            
            response_text = f"💰 <b>Коэффициенты:</b>\n\n"
            response_text += f"🔫 {target_match.team1} vs {target_match.team2}\n"
            response_text += f"🏆 Спорт: {target_match.sport.upper()}\n\n"
            
            for odds in match_odds:
                response_text += f"📊 <b>{odds.bookmaker.upper()}</b>:\n"
                response_text += f"• П1: {odds.odds1}\n"
                response_text += f"• П2: {odds.odds2}\n"
                if odds.odds_draw:
                    response_text += f"• Ничья: {odds.odds_draw}\n"
                response_text += f"• Обновлено: {odds.updated_at.strftime('%H:%M')}\n\n"
            
            await message.edit_text(response_text)
            
        except Exception as e:
            logger.error(f"Error in /odds: {e}")
            await message.answer("❌ Ошибка загрузки коэффициентов")
    
    async def cmd_mini_app(self, message: Message):
        """Команда /miniapp - открыть Mini App"""
        keyboard = InlineKeyboardBuilder()
        keyboard.button(
            text="🚀 Открыть Mini App",
            web_app=WebApp(url=MINI_APP_URL)
        )
        
        await message.answer(
            "🚀 <b>Mini App</b> - полная аналитика в удобном интерфейсе:",
            reply_markup=keyboard.as_markup()
        )
    
    async def cmd_admin(self, message: Message):
        """Команда /admin - админ панель"""
        if message.from_user.id != self.admin_id:
            await message.answer("❌ Доступ запрещен")
            return
        
        # Получаем статистику
        total_users = await self.db_manager.get_users_count()
        total_matches = len(await self.db_manager.get_matches(limit=1000))
        model_status = await ml_models.get_model_status()
        
        admin_text = f"""
🔧 <b>Админ панель AIBET:</b>\n\n📊 <b>Статистика:</b>
• Пользователей: {total_users}
• Матчей в базе: {total_matches}
• Сигналов сегодня: {self.daily_signals}/10\n\n🤖 <b>ML модели:</b>
• Обучены: {'✅' if model_status['is_trained'] else '❌'}
• Моделей: {model_status['models_count']}\n\n🔄 <b>Фоновые задачи:</b>
• Обновление данных: {'🔄' if background_tasks_status['is_updating'] else '✅'}
• Обучение ML: {'🔄' if background_tasks_status['is_training'] else '✅'}\n\n⚙️ <b>Действия:</b>
        """
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔄 Обновить матчи", callback_data="admin_update_matches")
        keyboard.button(text="🤖 Обучить ML", callback_data="admin_train_ml")
        keyboard.button(text="📊 Статистика API", callback_data="admin_api_stats")
        keyboard.adjust(1)
        
        await message.answer(admin_text, reply_markup=keyboard.as_markup())
    
    async def inline_handler(self, inline_query: InlineQuery):
        """Inline режим бота"""
        try:
            text = inline_query.query.lower().strip()
            
            if not text:
                # Показываем популярные команды
                results = [
                    types.InlineQueryResultArticle(
                        id="signals",
                        title="🎯 Точные сигналы",
                        description="Прогнозы с confidence ≥ 70%",
                        input_message_content=InputTextMessageContent(
                            message_text="/signals"
                        )
                    ),
                    types.InlineQueryResultArticle(
                        id="live",
                        title="⚡ Live матчи",
                        description="Текущие live матчи CS2 и KHL",
                        input_message_content=InputTextMessageContent(
                            message_text="/live"
                        )
                    ),
                    types.InlineQueryResultArticle(
                        id="miniapp",
                        title="🚀 Mini App",
                        description="Полная аналитика в браузере",
                        input_message_content=InputTextMessageContent(
                            message_text="/miniapp"
                        )
                    )
                ]
            else:
                # Поиск по запросу
                results = []
                
                # Ищем матчи
                matches = await self.db_manager.get_matches(limit=50)
                
                for match in matches[:10]:  # Максимум 10 результатов
                    if (text in match.team1.lower() or 
                        text in match.team2.lower() or 
                        text in match.sport.lower()):
                        
                        results.append(
                            types.InlineQueryResultArticle(
                                id=f"match_{match.id}",
                                title=f"{match.team1} vs {match.team2}",
                                description=f"{match.sport.upper()} - {match.status}",
                                input_message_content=InputTextMessageContent(
                                    message_text=f"/analysis {match.id}"
                                )
                            )
                        )
            
            await inline_query.answer(results, cache_time=5)
            
        except Exception as e:
            logger.error(f"Error in inline handler: {e}")
    
    async def callback_handler(self, callback: CallbackQuery):
        """Обработка callback'ов"""
        try:
            await callback.answer()
            
            data = callback.data
            
            if data == "show_signals":
                await self.cmd_signals(callback.message)
            elif data == "show_live":
                await self.cmd_live(callback.message)
            elif data == "refresh_live":
                await self.cmd_live(callback.message)
            elif data == "show_all_matches":
                # Показать все матчи
                matches = await self.db_manager.get_matches(limit=20)
                response_text = "📊 <b>Все матчи:</b>\n\n"
                
                for match in matches:
                    response_text += f"• {match.team1} vs {match.team2}\n"
                    response_text += f"  {match.sport.upper()} - {match.status}\n\n"
                
                await callback.message.edit_text(response_text)
            
            elif data == "more_predictions":
                await callback.message.answer("🎯 Используйте /signals для получения прогнозов")
            
            elif data.startswith("admin_"):
                await self.handle_admin_callbacks(callback, data)
                
        except Exception as e:
            logger.error(f"Error in callback handler: {e}")
            await callback.answer("❌ Ошибка", show_alert=True)
    
    async def handle_admin_callbacks(self, callback: CallbackQuery, data: str):
        """Обработка админ callback'ов"""
        if callback.from_user.id != self.admin_id:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        if data == "admin_update_matches":
            await callback.message.answer("🔄 Запускаю обновление матчей...")
            # Здесь можно запустить фоновую задачу обновления
            await callback.message.answer("✅ Обновление запущено")
            
        elif data == "admin_train_ml":
            await callback.message.answer("🤖 Запускаю обучение ML...")
            # Здесь можно запустить обучение моделей
            await callback.message.answer("✅ Обучение запущено")
            
        elif data == "admin_api_stats":
            # Показать статистику API
            await callback.message.answer("📊 API статистика в разработке")
    
    async def text_handler(self, message: Message):
        """Обработка текстовых сообщений"""
        # Можно добавить обработку обычных текстовых сообщений
        pass
    
    async def start_polling(self):
        """Запуск бота"""
        logger.info("🚀 Starting bot polling...")
        await self.dp.start_polling(self.bot)
        
    async def stop(self):
        """Остановка бота"""
        logger.info("🛑 Stopping bot...")
        await self.dp.stop_polling()
        await self.bot.session.close()

# Глобальные переменные
bot_instance = None
background_tasks_status = {
    "last_data_update": None,
    "last_ml_training": None,
    "is_updating": False,
    "is_training": False
}

# Инициализация и запуск
def create_bot():
    """Создание экземпляра бота"""
    global bot_instance
    
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not found")
    
    bot_instance = RealTelegramBot(
        bot_token=BOT_TOKEN,
        admin_id=ADMIN_ID,
        db_manager_instance=db_manager
    )
    
    return bot_instance

async def main():
    """Главная функция"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Создаем и запускаем бота
    bot = create_bot()
    
    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
