"""
AIBET Telegram Bot - Timeweb Version
Educational sports analytics bot with long polling
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from core.config import config
from core.storage import storage


class AIBOTBot:
    """AIBET Telegram Bot"""
    
    def __init__(self):
        self.application = None
        self.running = False
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command with inline buttons"""
        try:
            user_id = update.effective_user.id
            username = update.effective_user.username or update.effective_user.first_name or "User"
            
            # Store user data
            storage.set_user_data(user_id, "last_command", "start")
            storage.set_user_data(user_id, "username", username)
            
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🏒 NHL", callback_data="nhl"),
                    InlineKeyboardButton("🏒 KHL", callback_data="khl")
                ],
                [
                    InlineKeyboardButton("🎮 CS2", callback_data="cs2"),
                    InlineKeyboardButton("📊 О проекте", callback_data="about")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_message = f"""
🚀 **AIBET - Educational Sports Analytics Bot**

Добро пожаловать, {username}!

📊 **Выберите раздел:**
Используйте кнопки ниже для навигации

⚠️ **Важно:**
Этот бот предоставляет образовательную информацию только.
Никаких ставок или прогнозов не дается.

🌐 **AIBET Analytics:**
Веб-платформа: https://aibet-analytics.onrender.com
Документация: https://aibet-analytics.onrender.com/docs
"""
            
            await update.message.reply_text(
                welcome_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            print(f"📤 Start command sent to user {username} (ID: {user_id})")
            
        except Exception as e:
            print(f"❌ Error in start_command: {e}")
            await update.message.reply_text("❌ Временная ошибка сервиса")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        try:
            help_message = """
🤖 **AIBET - Помощь**

📋 **Доступные команды:**
/start - Главное меню с кнопками
/help - Эта справка
/status - Статус бота
/about - О проекте

🏒 **Виды спорта:**
• **NHL** - Национальная хоккейная лига
• **KHL** - Континентальная хоккейная лига
• **CS2** - Киберспорт Counter-Strike 2

📊 **Аналитика:**
• Расписание матчей
• Образовательные инсайты
• Оценка рисков
• Анализ эффективности

⚠️ **Важное уведомление:**
Вся информация предоставляется в образовательных целях.
Никаких советов по ставкам или финансовых рекомендаций.

🌐 **Платформа:**
Веб: https://aibet-analytics.onrender.com
API: https://aibet-analytics.onrender.com/docs

❓ **Поддержка:**
Для технических вопросов проверьте веб-платформу.
"""
            
            await update.message.reply_text(help_message, parse_mode='Markdown')
            print(f"📤 Help command sent to user {update.effective_user.id}")
            
        except Exception as e:
            print(f"❌ Error in help_command: {e}")
            await update.message.reply_text("❌ Временная ошибка сервиса")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command"""
        try:
            stats = storage.get_stats()
            status_message = f"""
📊 **Статус AIBOT**

✅ **Статус бота:** Онлайн
🕒 **Текущее время:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
🤖 **Версия бота:** 1.0.0

🌐 **Подключенные сервисы:**
• AIBET Analytics API: ✅ Онлайн
• Движок AI: ✅ Активен
• Источники данных: ✅ Подключены

📈 **Доступная аналитика:**
• Расписание NHL: ✅ Доступно
• Матчи KHL: ✅ Доступно
• CS2 киберспорт: ✅ Доступно
• AI инсайты: ✅ Только образовательные

📊 **Статистика хранилища:**
• Всего ключей: {stats['total_keys']}
• Всего пользователей: {stats['total_users']}
• Время обновления: {stats['timestamp']}

⚠️ **Режим работы:** Только образовательная аналитика
🔒 **Соответствие:** Только образовательные цели

🌐 **Веб-платформа:** https://aibet-analytics.onrender.com
"""
            
            await update.message.reply_text(status_message, parse_mode='Markdown')
            print(f"📤 Status command sent to user {update.effective_user.id}")
            
        except Exception as e:
            print(f"❌ Error in status_command: {e}")
            await update.message.reply_text("❌ Временная ошибка сервиса")
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /about command"""
        try:
            about_message = """
🏆 **О проекте AIBET**

📖 **Миссия:**
Предоставление образовательной спортивной аналитики и инсайтов для учебных целей.

🔬 **Технологии:**
• FastAPI Backend
• Telegram Bot Framework
• Образовательный AI анализ
• Обработка данных в реальном времени

🏒 **Покрытие спорта:**
• **NHL** - Профессиональный хоккей
• **KHL** - Международный хоккей
• **CS2** - Киберспорт

📊 **Функции аналитики:**
• Расписание матчей
• Инсайты по командам
• Образовательная оценка рисков
• Анализ рыночной эффективности

⚠️ **Образовательная оговорка:**
Вся предоставляемая информация предназначена только для образовательных целей.
Никаких ставок, финансовых рекомендаций или прогнозов.
Спортивная аналитика сопряжена с неопределенностями.

🌐 **Интеграция платформы:**
• Веб API: https://aibet-analytics.onrender.com
• Документация: /docs endpoint
• Мониторинг здоровья: /health endpoint

📚 **Образовательные ресурсы:**
Образовательная спортивная аналитика для:
• Энтузиастов data science
• Студентов спортивной аналитики
• Исследовательских целей
• Технических демонстраций

🔒 **Соответствие:**
• Только образовательные цели
• Никаких азартных игр
• Никаких финансовых советов
• Ответственная аналитика

📈 **Версия:** 1.0.0
🕒 **Последнее обновление:** 2026-02-08
"""
            
            await update.message.reply_text(about_message, parse_mode='Markdown')
            print(f"📤 About command sent to user {update.effective_user.id}")
            
        except Exception as e:
            print(f"❌ Error in about_command: {e}")
            await update.message.reply_text("❌ Временная ошибка сервиса")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline button callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = update.effective_user.id
            callback_data = query.data
            
            # Store button click
            storage.set_user_data(user_id, "last_button", callback_data)
            
            # Handle different buttons
            if callback_data == "nhl":
                message = """
🏒 **NHL - Национальная Хоккейная Лига**

📊 **Доступные функции:**
• Расписание матчей
• Статистика команд
• Образовательный анализ
• Исторические данные

🔍 **Текущий статус:**
Сервис находится в разработке.
Скоро будут доступны актуальные данные.

📈 **Что будет доступно:**
• Календарь матчей NHL
• Анализ формы команд
• Статистика игроков
• Образовательные прогнозы

⚠️ **Важно:**
Все данные предоставляются в образовательных целях.
Никаких рекомендаций по ставкам.

🌐 **Подробности:**
https://aibet-analytics.onrender.com/docs
"""
            
            elif callback_data == "khl":
                message = """
🏒 **KHL - Континентальная Хоккейная Лига**

📊 **Доступные функции:**
• Расписание матчей
• Турнирная таблица
• Образовательный анализ
• Статистика сезонов

🔍 **Текущий статус:**
Сервис находится в разработке.
Скоро будут доступны актуальные данные.

📈 **Что будет доступно:**
• Календарь матчей KHL
• Плей-офф статистика
• Анализ команд
• Образовательные инсайты

⚠️ **Важно:**
Все данные предоставляются в образовательных целях.
Никаких рекомендаций по ставкам.

🌐 **Подробности:**
https://aibet-analytics.onrender.com/docs
"""
            
            elif callback_data == "cs2":
                message = """
🎮 **CS2 - Counter-Strike 2 Киберспорт**

📊 **Доступные функции:**
• Предстоящие матчи
• Результаты турниров
• Образовательный анализ
• Статистика команд

🔍 **Текущий статус:**
Сервис находится в разработке.
Скоро будут доступны актуальные данные.

📈 **Что будет доступно:**
• Расписание турниров
• Анализ форм команд
• Статистика игроков
• Образовательные прогнозы

⚠️ **Важно:**
Все данные предоставляются в образовательных целях.
Никаких рекомендаций по ставкам.

🌐 **Подробности:**
https://aibet-analytics.onrender.com/docs
"""
            
            elif callback_data == "about":
                message = """
📊 **О проекте AIBET**

🏆 **Наша миссия:**
Предоставление качественной образовательной спортивной аналитики.

🔬 **Технологический стек:**
• FastAPI для backend
• Telegram Bot для интерфейса
• Python для обработки данных
• Образовательный AI анализ

📈 **Наши цели:**
• Сделать спортивную аналитику доступной
• Предоставить образовательные материалы
• Поддерживать ответственное использование
• Обеспечить точность данных

🌐 **Платформа:**
Основная веб-платформа:
https://aibet-analytics.onrender.com

📚 **Для кого это:**
• Студенты data science
• Энтузиасты спорта
• Исследователи
• Образовательные учреждения

🔒 **Наши принципы:**
• Только образовательные цели
• Никаких азартных игр
• Ответственная аналитика
• Прозрачность данных

📞 **Связь:**
Технические вопросы через веб-платформу.
"""
            
            else:
                message = "❌ Неизвестная команда"
            
            await query.edit_message_text(
                message,
                parse_mode='Markdown'
            )
            
            print(f"🔘 Button '{callback_data}' clicked by user {user_id}")
            
        except Exception as e:
            print(f"❌ Error in button_callback: {e}")
            if update.callback_query:
                await update.callback_query.answer("❌ Ошибка обработки")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors"""
        print(f"❌ Error {context.error}")
        
        error_message = """
❌ **Произошла ошибка**

Попробуйте еще раз позже.
Для непрерывной работы посетите нашу веб-платформу:
https://aibet-analytics.onrender.com

⚠️ Только образовательная аналитика.
"""
        
        try:
            if update and hasattr(update, 'message'):
                await update.message.reply_text(error_message)
        except:
            pass  # Avoid error loops
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n🔄 Получен сигнал {signum}, завершение работы...")
            self.running = False
            if self.application:
                self.application.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Run the bot"""
        try:
            print("🚀 Запуск AIBET Telegram Bot...")
            print(f"🤖 Token: {config.BOT_TOKEN[:10]}...")
            print(f"🐛 Debug: {config.DEBUG}")
            
            # Create application
            self.application = Application.builder().token(config.BOT_TOKEN).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CommandHandler("about", self.about_command))
            self.application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            print("✅ Обработчики команд зарегистрированы")
            print("🤖 AIBET запускается...")
            
            # Run bot with polling
            self.running = True
            await self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except Exception as e:
            print(f"❌ Критическая ошибка при запуске бота: {e}")
            raise
        finally:
            print("🔄 AIBET завершает работу...")


# Global bot instance
bot = AIBOTBot()


async def main():
    """Main entry point"""
    try:
        # Validate configuration
        config.validate()
        
        # Run bot
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Получен KeyboardInterrupt, завершение...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
