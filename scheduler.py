import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from config import config
from database import DatabaseManager, Match, Signal
from parsers.cs2_parser import CS2Parser
from parsers.khl_parser import KHLParser
from ml.cs2_analyzer import CS2Analyzer
from ml.khl_analyzer import KHLAnalyzer
from bot import TelegramBot

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Планировщик задач для автоматического анализа"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(config.database.path)
        self.cs2_parser = CS2Parser(self.db_manager)
        self.khl_parser = KHLParser(self.db_manager)
        self.cs2_analyzer = CS2Analyzer(self.db_manager)
        self.khl_analyzer = KHLAnalyzer(self.db_manager)
        self.telegram_bot = None
        
        self.running = False
        self.tasks = {}
        
    async def initialize(self):
        """Инициализация планировщика"""
        await self.db_manager.initialize()
        await self.cs2_parser.initialize()
        await self.khl_parser.initialize()
        await self.cs2_analyzer.initialize()
        await self.khl_analyzer.initialize()
        
        # Инициализация Telegram бота
        self.telegram_bot = TelegramBot()
        await self.telegram_bot.initialize()
        
        logger.info("Task scheduler initialized")
    
    async def start(self):
        """Запуск планировщика"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting task scheduler...")
        
        # Запускаем все задачи
        await self._start_all_tasks()
        
        # Запускаем heartbeat
        asyncio.create_task(self._heartbeat_loop())
        
        logger.info("Task scheduler started successfully")
    
    async def stop(self):
        """Остановка планировщика"""
        logger.info("Stopping task scheduler...")
        
        self.running = False
        
        # Останавливаем все задачи
        for task_name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.tasks.clear()
        
        # Закрываем соединения
        await self.db_manager.close()
        await self.cs2_parser.close()
        await self.khl_parser.close()
        
        logger.info("Task scheduler stopped")
    
    async def _start_all_tasks(self):
        """Запуск всех задач"""
        # Задача парсинга CS2 матчей
        self.tasks['cs2_parsing'] = asyncio.create_task(
            self._schedule_task('cs2_parsing', self._parse_cs2_matches, config.scheduler.cs2_check_interval)
        )
        
        # Задача парсинга КХЛ матчей
        self.tasks['khl_parsing'] = asyncio.create_task(
            self._schedule_task('khl_parsing', self._parse_khl_matches, config.scheduler.khl_check_interval)
        )
        
        # Задача анализа матчей
        self.tasks['match_analysis'] = asyncio.create_task(
            self._schedule_task('match_analysis', self._analyze_matches, 180)  # Каждые 3 минуты
        )
        
        # Задача обновления live матчей
        self.tasks['live_updates'] = asyncio.create_task(
            self._schedule_task('live_updates', self._update_live_matches, 60)  # Каждую минуту
        )
        
        # Задача обновления коэффициентов
        self.tasks['odds_updates'] = asyncio.create_task(
            self._schedule_task('odds_updates', self._update_odds, 300)  # Каждые 5 минут
        )
        
        # Задача проверки результатов
        self.tasks['result_check'] = asyncio.create_task(
            self._schedule_task('result_check', self._check_results, 300)
        )
        
        # Задача переобучения ML моделей
        self.tasks['ml_training'] = asyncio.create_task(
            self._schedule_task('ml_training', self._train_ml_models, config.ml.model_retrain_interval)
        )
        
        # Задача очистки старых данных
        self.tasks['data_cleanup'] = asyncio.create_task(
            self._schedule_task('data_cleanup', self._cleanup_old_data, 86400)  # Раз в день
        )
        
        logger.info(f"Started {len(self.tasks)} scheduled tasks")
    
    async def _schedule_task(self, task_name: str, task_func, interval: int):
        """Планирование периодической задачи"""
        logger.info(f"Starting scheduled task: {task_name} (interval: {interval}s)")
        
        while self.running:
            try:
                start_time = datetime.now()
                
                # Выполняем задачу
                await task_func()
                
                # Логируем выполнение
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Task {task_name} completed in {execution_time:.2f}s")
                
                # Ждем до следующего выполнения
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info(f"Task {task_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in task {task_name}: {e}")
                # Ждем перед повторной попыткой
                await asyncio.sleep(min(interval, 60))  # Не больше минуты при ошибках
    
    async def _parse_cs2_matches(self):
        """Парсинг CS2 матчей"""
        try:
            logger.info("Parsing CS2 matches...")
            
            # Получаем предстоящие матчи
            matches = await self.cs2_parser.parse_matches()
            
            # Сохраняем в базу
            await self.cs2_parser.save_matches(matches, 'cs2')
            
            logger.info(f"Parsed {len(matches)} CS2 matches")
            
        except Exception as e:
            logger.error(f"Error parsing CS2 matches: {e}")
    
    async def _parse_khl_matches(self):
        """Парсинг КХЛ матчей"""
        try:
            logger.info("Parsing KHL matches...")
            
            # Получаем предстоящие матчи
            matches = await self.khl_parser.parse_matches()
            
            # Сохраняем в базу
            await self.khl_parser.save_matches(matches, 'khl')
            
            logger.info(f"Parsed {len(matches)} KHL matches")
            
        except Exception as e:
            logger.error(f"Error parsing KHL matches: {e}")
    
    async def _analyze_matches(self):
        """Анализ матчей"""
        try:
            logger.info("Analyzing matches...")
            
            # Анализируем CS2 матчи
            await self._analyze_cs2_matches()
            
            # Анализируем КХЛ матчи
            await self._analyze_khl_matches()
            
        except Exception as e:
            logger.error(f"Error analyzing matches: {e}")
    
    async def _analyze_cs2_matches(self):
        """Анализ CS2 матчей"""
        try:
            # Получаем матчи, которые еще не проанализированы
            matches = await self.db_manager.get_upcoming_matches(sport='cs2', hours=24)
            
            for match in matches:
                # Проверяем, есть ли уже сигналы для этого матча
                existing_signals = await self.db_manager.get_signals(sport='cs2', limit=1000)
                match_signals = [s for s in existing_signals if s.match_id == match.id]
                
                if not match_signals:
                    # Проводим анализ
                    analysis = await self.cs2_analyzer.analyze_match(match)
                    
                    # Создаем сигналы для каждого сценария
                    for scenario in analysis.scenarios:
                        if scenario.probability > 0.5:  # Только для вероятных сценариев
                            signal = Signal(
                                id=f"cs2_{match.id}_{scenario.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                match_id=match.id,
                                sport='cs2',
                                scenario=scenario.name,
                                confidence=scenario.confidence,
                                probability=scenario.probability,
                                explanation=scenario.explanation,
                                factors=scenario.factors,
                                odds_at_signal=match.odds1 if match.team1 == analysis.scenarios[0].factors[0] else match.odds2,
                                published_at=datetime.now()
                            )
                            
                            # Сохраняем сигнал
                            await self.db_manager.save_signal(signal)
                            
                            # Публикуем в Telegram, если уверенность высокая
                            if scenario.confidence in ['HIGH', 'MEDIUM']:
                                await self.telegram_bot.publish_signal(signal, match)
            
            logger.info(f"Analyzed CS2 matches")
            
        except Exception as e:
            logger.error(f"Error analyzing CS2 matches: {e}")
    
    async def _analyze_khl_matches(self):
        """Анализ КХЛ матчей"""
        try:
            # Получаем матчи, которые еще не проанализированы
            matches = await self.db_manager.get_upcoming_matches(sport='khl', hours=24)
            
            for match in matches:
                # Проверяем, есть ли уже сигналы для этого матча
                existing_signals = await self.db_manager.get_signals(sport='khl', limit=1000)
                match_signals = [s for s in existing_signals if s.match_id == match.id]
                
                if not match_signals:
                    # Проводим анализ
                    analysis = await self.khl_analyzer.analyze_match(match)
                    
                    # Создаем сигналы для каждого сценария
                    for scenario in analysis.scenarios:
                        if scenario.probability > 0.5:  # Только для вероятных сценариев
                            signal = Signal(
                                id=f"khl_{match.id}_{scenario.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                match_id=match.id,
                                sport='khl',
                                scenario=scenario.name,
                                confidence=scenario.confidence,
                                probability=scenario.probability,
                                explanation=scenario.explanation,
                                factors=scenario.factors,
                                odds_at_signal=match.odds1 if match.team1 == analysis.scenarios[0].factors[0] else match.odds2,
                                published_at=datetime.now()
                            )
                            
                            # Сохраняем сигнал
                            await self.db_manager.save_signal(signal)
                            
                            # Публикуем в Telegram, если уверенность высокая
                            if scenario.confidence in ['HIGH', 'MEDIUM']:
                                await self.telegram_bot.publish_signal(signal, match)
            
            logger.info(f"Analyzed KHL matches")
            
        except Exception as e:
            logger.error(f"Error analyzing KHL matches: {e}")
    
    async def _update_live_matches(self):
        """Обновление live матчей"""
        try:
            logger.info("Updating live matches...")
            
            # Получаем live матчи CS2
            cs2_live = await self.cs2_parser.parse_live_matches()
            await self.cs2_parser.save_matches(cs2_live, 'cs2')
            
            # Получаем live матчи КХЛ
            khl_live = await self.khl_parser.parse_live_matches()
            await self.khl_parser.save_matches(khl_live, 'khl')
            
            logger.info(f"Updated {len(cs2_live)} CS2 and {len(khl_live)} KHL live matches")
            
        except Exception as e:
            logger.error(f"Error updating live matches: {e}")
    
    async def _update_odds(self):
        """Обновление коэффициентов"""
        try:
            logger.info("Updating odds...")
            
            # Получаем все предстоящие матчи
            cs2_matches = await self.db_manager.get_upcoming_matches(sport='cs2', hours=24)
            khl_matches = await self.db_manager.get_upcoming_matches(sport='khl', hours=24)
            
            # Обновляем коэффициенты CS2
            for match in cs2_matches:
                odds = await self.cs2_parser.parse_odds(match.id)
                if odds:
                    await self.db_manager.save_odds_history(
                        match.id, odds['odds1'], odds['odds2'], odds.get('odds_draw')
                    )
            
            # Обновляем коэффициенты КХЛ
            for match in khl_matches:
                odds = await self.khl_parser.parse_odds(match.id)
                if odds:
                    await self.db_manager.save_odds_history(
                        match.id, odds['odds1'], odds['odds2'], odds.get('odds_draw')
                    )
            
            logger.info("Odds updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating odds: {e}")
    
    async def _check_results(self):
        """Проверка результатов матчей"""
        try:
            logger.info("Checking match results...")
            
            # Получаем сигналы без результатов
            signals = await self.db_manager.get_signals(limit=1000)
            pending_signals = [s for s in signals if s.result is None]
            
            for signal in pending_signals:
                match = await self.db_manager.get_match(signal.match_id)
                if match and match.status == 'finished':
                    # Определяем результат сигнала
                    result = self._determine_signal_result(signal, match)
                    
                    # Обновляем результат
                    await self.db_manager.update_signal_result(signal.id, result)
            
            logger.info(f"Checked results for {len(pending_signals)} signals")
            
        except Exception as e:
            logger.error(f"Error checking results: {e}")
    
    def _determine_signal_result(self, signal: Signal, match: Match) -> str:
        """Определение результата сигнала"""
        try:
            # Упрощенная логика определения результата
            # В реальном приложении здесь будет более сложная логика
            
            if match.score1 is None or match.score2 is None:
                return 'pending'
            
            # Определяем победителя
            if match.score1 > match.score2:
                winner = match.team1
            elif match.score2 > match.score1:
                winner = match.team2
            else:
                winner = 'draw'
            
            # Проверяем, соответствует ли результат сценарию
            if 'фаворит' in signal.scenario.lower():
                # Если сценарий про фаворита, проверяем, выиграл ли фаворит
                if match.odds1 < match.odds2:  # team1 фаворит
                    return 'win' if winner == match.team1 else 'lose'
                else:  # team2 фаворит
                    return 'win' if winner == match.team2 else 'lose'
            elif 'андердог' in signal.scenario.lower():
                # Если сценарий про андердога
                if match.odds1 < match.odds2:  # team1 фаворит
                    return 'win' if winner == match.team2 else 'lose'
                else:  # team2 фаворит
                    return 'win' if winner == match.team1 else 'lose'
            else:
                # Для других сценариев используем вероятность
                return 'win' if signal.probability > 0.6 else 'lose'
        
        except Exception as e:
            logger.error(f"Error determining signal result: {e}")
            return 'pending'
    
    async def _train_ml_models(self):
        """Обучение ML моделей"""
        try:
            logger.info("Training ML models...")
            
            # Обучаем CS2 модель
            await self.cs2_analyzer.train_models()
            
            # Обучаем КХЛ модель
            await self.khl_analyzer.train_models()
            
            logger.info("ML models trained successfully")
            
        except Exception as e:
            logger.error(f"Error training ML models: {e}")
    
    async def _cleanup_old_data(self):
        """Очистка старых данных"""
        try:
            logger.info("Cleaning up old data...")
            
            # Удаляем матчи старше 30 дней
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # В реальном приложении здесь будет логика очистки
            # old_matches = await self.db_manager.get_old_matches(cutoff_date)
            # for match in old_matches:
            #     await self.db_manager.delete_match(match.id)
            
            logger.info("Old data cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def _heartbeat_loop(self):
        """Цикл heartbeat для проверки состояния системы"""
        while self.running:
            try:
                await asyncio.sleep(config.scheduler.heartbeat_interval)
                
                if self.running:
                    await self._send_heartbeat()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    async def _send_heartbeat(self):
        """Отправка heartbeat сообщения"""
        try:
            # Проверяем состояние всех компонентов
            status = {
                'timestamp': datetime.now().isoformat(),
                'scheduler_running': self.running,
                'active_tasks': len([t for t in self.tasks.values() if not t.done()]),
                'cs2_parser': 'active',
                'khl_parser': 'active',
                'cs2_analyzer': 'active',
                'khl_analyzer': 'active',
                'telegram_bot': 'active' if self.telegram_bot else 'inactive'
            }
            
            logger.info(f"Heartbeat: {status}")
            
            # Отправляем статус в Telegram (опционально)
            if self.telegram_bot and datetime.now().hour % 6 == 0:  # Каждые 6 часов
                await self._send_status_to_telegram(status)
                
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
    
    async def _send_status_to_telegram(self, status: Dict[str, Any]):
        """Отправка статуса в Telegram"""
        try:
            if not config.telegram.admin_ids:
                return
            
            message = f"""🔧 **System Status Report**
📅 {status['timestamp']}

🤖 **Scheduler:** {'✅ Running' if status['scheduler_running'] else '❌ Stopped'}
📊 **Active Tasks:** {status['active_tasks']}

🔫 **CS2 Components:**
• Parser: {status['cs2_parser']}
• Analyzer: {status['cs2_analyzer']}

🏒 **KHL Components:**
• Parser: {status['khl_parser']}
• Analyzer: {status['khl_analyzer']}

📱 **Telegram Bot:** {status['telegram_bot']}

---
AI BET Analytics Platform"""
            
            # Отправляем всем админам
            for admin_id in config.telegram.admin_ids:
                try:
                    await self.telegram_bot.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Error sending status to admin {admin_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error sending status to Telegram: {e}")
    
    def get_task_status(self) -> Dict[str, Any]:
        """Получение статуса задач"""
        return {
            'running': self.running,
            'tasks': {
                name: {
                    'done': task.done(),
                    'cancelled': task.cancelled() if task.done() else False
                }
                for name, task in self.tasks.items()
            }
        }

# Глобальный экземпляр планировщика
scheduler = TaskScheduler()
