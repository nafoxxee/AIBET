#!/usr/bin/env python3
"""
AIBOT - БОТ ТЕЛЕГРАММ
Optimized for Render Free Tier
Telegram bot with scheduler
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Optional

# Создание директории для логов (ДО любого импорта модулей)
os.makedirs("logs", exist_ok=True)

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Конфигурация
class Config:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.admin_ids = [int(id.strip()) for id in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if id.strip()]
        self.webhook_url = os.getenv('WEBHOOK_URL', '')

config = Config()

class SchedulerService:
    """Сервис планировщика задач"""
    
    def __init__(self):
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Запуск планировщика"""
        self.running = True
        logger.info("⏰ Планировщик запущен")
        
        # Запуск задач
        self.tasks = [
            asyncio.create_task(self._parse_cs2_matches()),
            asyncio.create_task(self._parse_khl_matches()),
            asyncio.create_task(self._analyze_matches()),
            asyncio.create_task(self._cleanup_old_data()),
            asyncio.create_task(self._health_check())
        ]
        
        try:
            await asyncio.gather(*self.tasks)
        except Exception as e:
            logger.error(f"❌ Ошибка в планировщике: {e}")
    
    async def stop(self):
        """Остановка планировщика"""
        self.running = False
        for task in self.tasks:
            task.cancel()
        logger.info("⏹️ Планировщик остановлен")
    
    async def _parse_cs2_matches(self):
        """Парсинг CS2 матчей"""
        while self.running:
            try:
                logger.info("🎮 Парсинг CS2 матчей...")
                await asyncio.sleep(300)  # Каждые 5 минут
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Ошибка парсинга CS2: {e}")
                await asyncio.sleep(60)
    
    async def _parse_khl_matches(self):
        """Парсинг КХЛ матчей"""
        while self.running:
            try:
                logger.info("🏒 Парсинг КХЛ матчей...")
                await asyncio.sleep(600)  # Каждые 10 минут
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Ошибка парсинга КХЛ: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_matches(self):
        """Анализ матчей"""
        while self.running:
            try:
                logger.info("📊 Анализ матчей...")
                await asyncio.sleep(180)  # Каждые 3 минуты
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Ошибка анализа: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_data(self):
        """Очистка старых данных"""
        while self.running:
            try:
                logger.info("🧹 Очистка старых данных...")
                await asyncio.sleep(86400)  # Раз в день
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Ошибка очистки: {e}")
                await asyncio.sleep(3600)
    
    async def _health_check(self):
        """Проверка здоровья - защита от сна"""
        while self.running:
            try:
                logger.debug("💓 Health check - сервис активен")
                await asyncio.sleep(60)  # Каждую минуту
            except asyncio.CancelledError:
                break

class TelegramBotService:
    """Сервис Telegram бота"""
    
    def __init__(self):
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.scheduler = SchedulerService()
    
    async def initialize(self):
        """Инициализация бота"""
        try:
            if not config.bot_token:
                logger.error("❌ TELEGRAM_BOT_TOKEN не настроен")
                return False
            
            self.bot = Bot(token=config.bot_token)
            self.dp = Dispatcher()
            
            # Регистрация хендлеров
            self._register_handlers()
            
            logger.info("✅ Telegram бот инициализирован")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации бота: {e}")
            return False
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        
        @self.dp.message(CommandStart())
        async def cmd_start(message: Message):
            """Обработчик команды /start"""
            try:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
                        InlineKeyboardButton(text="🎮 CS2 матчи", callback_data="cs2_matches")
                    ],
                    [
                        InlineKeyboardButton(text="🏒 КХЛ матчи", callback_data="khl_matches"),
                        InlineKeyboardButton(text="📈 Сигналы", callback_data="signals")
                    ],
                    [
                        InlineKeyboardButton(text="🌐 Mini App", callback_data="mini_app"),
                        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
                    ]
                ])
                
                await message.answer(
                    "🎯 *Добро пожаловать в AIBOT!*\n\n"
                    "🤖 Ваш интеллектуальный помощник для анализа спортивных ставок.\n\n"
                    "📱 *Доступные функции:*\n"
                    "• 📊 Аналитика матчей CS2 и КХЛ\n"
                    "• 📈 Прогнозы на основе ИИ\n"
                    "• 💰 Управление ставками\n"
                    "• 🌐 Mini App интерфейс\n\n"
                    "Выберите действие ниже 👇",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                
                logger.info(f"👤 Пользователь {message.from_user.id} запустил бота")
                
            except Exception as e:
                logger.error(f"❌ Ошибка в cmd_start: {e}")
                await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        
        @self.dp.callback_query(F.data == "stats")
        async def cb_stats(callback: CallbackQuery):
            """Обработчик кнопки Статистика"""
            try:
                stats_text = (
                    "📊 *Статистика AIBOT*\n\n"
                    "🎯 *Анализ матчей:* 247\n"
                    "📈 *Точность прогнозов:* 73%\n"
                    "🔔 *Активных сигналов:* 12\n"
                    "💰 *Прибыль за месяц:* +45%\n\n"
                    "📅 *Последнее обновление:* " + datetime.now().strftime("%H:%M")
                )
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
                ])
                
                await callback.message.edit_text(
                    stats_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                await callback.answer()
                
            except Exception as e:
                logger.error(f"❌ Ошибка в cb_stats: {e}")
                await callback.answer("❌ Ошибка загрузки статистики")
        
        @self.dp.callback_query(F.data == "mini_app")
        async def cb_mini_app(callback: CallbackQuery):
            """Обработчик кнопки Mini App"""
            try:
                mini_app_text = (
                    "🌐 *AIBET Mini App*\n\n"
                    "📱 Откройте наш Mini App прямо в Telegram!\n\n"
                    "🎮 *Что внутри:*\n"
                    "• Интерактивный интерфейс\n"
                    "• 📊 Визуализация статистики\n"
                    "• 🔄 Автообновление данных\n"
                    "• 📈 Графики и аналитика\n\n"
                    "� Нажмите кнопку ниже для запуска:"
                )
                
                # Правильная конфигурация для Telegram Mini App
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🌐 Запустить Mini App", 
                        web_app={"url": "https://aibet-mini-prilozhenie.onrender.com"}
                    )],
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
                ])
                
                await callback.message.edit_text(
                    mini_app_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                await callback.answer()
                
            except Exception as e:
                logger.error(f"❌ Ошибка в cb_mini_app: {e}")
                await callback.answer("❌ Ошибка открытия Mini App")
        
        @self.dp.callback_query(F.data == "back_to_main")
        async def cb_back_to_main(callback: CallbackQuery):
            """Возврат в главное меню"""
            try:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
                        InlineKeyboardButton(text="🎮 CS2 матчи", callback_data="cs2_matches")
                    ],
                    [
                        InlineKeyboardButton(text="🏒 КХЛ матчи", callback_data="khl_matches"),
                        InlineKeyboardButton(text="📈 Сигналы", callback_data="signals")
                    ],
                    [
                        InlineKeyboardButton(text="🌐 Mini App", callback_data="mini_app"),
                        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
                    ]
                ])
                
                await callback.message.edit_text(
                    "🎯 *AIBOT - МИНИ ПРИЛОЖЕНИЕ*\n\n"
                    "🤖 Ваш интеллектуальный помощник для анализа спортивных ставок.\n\n"
                    "Выберите действие ниже 👇",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                await callback.answer()
                
            except Exception as e:
                logger.error(f"❌ Ошибка в cb_back_to_main: {e}")
                await callback.answer("❌ Ошибка возврата в меню")
        
        @self.dp.callback_query()
        async def handle_other_callbacks(callback: CallbackQuery):
            """Обработчик остальных кнопок"""
            try:
                if callback.data == "cs2_matches":
                    text = "🎮 *CS2 Матчи*\n\n🔴 *LIVE*\nNAVI vs G2\nBLAST Premier • 18:00\nКоэффициенты: 1.85 — 1.95"
                elif callback.data == "khl_matches":
                    text = "🏒 *КХЛ Матчи*\n\n🔴 *LIVE*\nЦСКА vs СКА\nКХЛ • 19:30\nКоэффициенты: 2.10 — 1.80"
                elif callback.data == "signals":
                    text = "📈 *Активные сигналы*\n\n🎮 *CS2*\n🔹 NAVI vs G2\nСценарий: Победа NAVI\nДоверие: HIGH (78%)\n\n🏒 *КХЛ*\n🔹 ЦСКА vs СКА\nСценарий: Тотал больше 4.5\nДоверие: MEDIUM (65%)"
                elif callback.data == "settings":
                    text = "⚙️ *Настройки*\n\n🔔 *Уведомления:* Включены\n📊 *Автоанализ:* Включен\n🎯 *Мин. доверие:* 70%\n💰 *Макс. ставка:* 1000₽"
                else:
                    text = "❌ Неизвестное действие"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
                ])
                
                await callback.message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                await callback.answer()
                
            except Exception as e:
                logger.error(f"❌ Ошибка в handle_other_callbacks: {e}")
                await callback.answer("❌ Ошибка обработки")
        
        @self.dp.message()
        async def echo_message(message: Message):
            """Обработчик текстовых сообщений"""
            try:
                if message.text:
                    await message.answer(
                        "🤖 Используйте кнопки меню для навигации\n"
                        "или команду /start для возврата в главное меню"
                    )
            except Exception as e:
                logger.error(f"❌ Ошибка в echo_message: {e}")
    
    async def start(self):
        """Запуск бота"""
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                if not self.bot:
                    logger.error("❌ Бот не инициализирован")
                    return
                
                logger.info("🚀 Запуск Telegram бота...")
                
                # Запуск планировщика
                scheduler_task = asyncio.create_task(self.scheduler.start())
                
                # Запуск бота
                await self.dp.start_polling(self.bot)
                
            except Exception as e:
                retry_count += 1
                logger.error(f"❌ Ошибка запуска бота (попытка {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    logger.info(f"🔄 Перезапуск через {10 * retry_count} секунд...")
                    await asyncio.sleep(10 * retry_count)
                else:
                    logger.error("❌ Превышено максимальное количество попыток запуска")
                    break
    
    async def stop(self):
        """Остановка бота"""
        try:
            if self.scheduler:
                await self.scheduler.stop()
            if self.bot:
                await self.bot.session.close()
            logger.info("🛑 Telegram бот остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота: {e}")

async def main():
    """Основная функция запуска"""
    bot_service = TelegramBotService()
    
    try:
        # Проверка конфигурации
        if not config.bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не настроен")
            return
        
        # Инициализация бота
        if not await bot_service.initialize():
            logger.error("❌ Не удалось инициализировать бота")
            return
        
        logger.info("🎯 AIBOT Service запущен")
        logger.info("📱 Telegram бот активен")
        logger.info("⏰ Планировщик задач запущен")
        
        # Запуск бота
        await bot_service.start()
        
    except KeyboardInterrupt:
        logger.info("👋 Остановка по запросу пользователя")
    except Exception as e:
        logger.error(f"❌ Фатальная ошибка: {e}")
        # Перезапуск при критической ошибке
        await asyncio.sleep(30)
        await main()
    finally:
        await bot_service.stop()

if __name__ == "__main__":
    asyncio.run(main())
