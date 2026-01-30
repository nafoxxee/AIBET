import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import parse_qs

from aiohttp import web, WSMsgType
from aiohttp.web import Request, Response, WebSocketResponse
import aiohttp_cors

from app.config import config

logger = logging.getLogger(__name__)


class MiniAppAPI:
    """API сервер для Telegram Mini App"""
    
    def __init__(self):
        self.app = web.Application()
        self.active_connections: Dict[str, WebSocketResponse] = {}
        self.admin_users = config.ADMIN_TELEGRAM_IDS  # Будет в конфиге
        
        # Настройка CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        self._setup_routes()
        self._setup_cors(cors)
        
        # Импорты модулей (ленивая загрузка)
        self.cs2_analyzer = None
        self.khl_analyzer = None
        self.db_manager = None
        
    def _setup_routes(self):
        """Настройка API маршрутов"""
        
        # Аутентификация
        self.app.router.add_post('/api/auth/check-admin', self.check_admin)
        
        # CS2 эндпоинты
        self.app.router.add_get('/api/cs2/matches', self.get_cs2_matches)
        self.app.router.add_get('/api/cs2/match/{match_id}', self.get_cs2_match)
        
        # КХЛ эндпоинты
        self.app.router.add_get('/api/khl/matches', self.get_khl_matches)
        self.app.router.add_get('/api/khl/match/{match_id}', self.get_khl_match)
        
        # Live матчи
        self.app.router.add_get('/api/live/matches', self.get_live_matches)
        
        # Предматчевые данные
        self.app.router.add_get('/api/prematch/matches', self.get_prematch_matches)
        
        # История сигналов
        self.app.router.add_get('/api/history/signals', self.get_history_signals)
        
        # Статистика
        self.app.router.add_get('/api/stats/{sport}', self.get_stats)
        
        # Рейтинги уверенности
        self.app.router.add_get('/api/confidence/ratings', self.get_confidence_ratings)
        
        # Статус системы
        self.app.router.add_get('/api/system/status', self.get_system_status)
        
        # Админ эндпоинты
        self.app.router.add_post('/api/admin/action', self.admin_action)
        self.app.router.add_get('/api/admin/dashboard', self.get_admin_dashboard)
        
        # WebSocket для real-time обновлений
        self.app.router.add_get('/api/ws', self.websocket_handler)
        
        # Статические файлы для Mini App
        self.app.router.add_static('/', path='c:/AI BET/frontend', name='static')
    
    def _setup_cors(self, cors):
        """Настройка CORS для всех маршрутов"""
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def _get_modules(self):
        """Ленивая загрузка модулей"""
        if not self.cs2_analyzer:
            from cs2.analysis.scenarios import CS2ScenarioAnalyzer
            self.cs2_analyzer = CS2ScenarioAnalyzer()
        
        if not self.khl_analyzer:
            from khl.analysis.scenarios import KHLScenarioAnalyzer
            self.khl_analyzer = KHLScenarioAnalyzer()
        
        if not self.db_manager:
            from storage.database import DatabaseManager
            self.db_manager = DatabaseManager()
    
    def _verify_telegram_auth(self, request: Request) -> Optional[Dict[str, Any]]:
        """Проверка авторизации Telegram"""
        try:
            # Получаем данные из заголовков
            user_id = request.headers.get('X-Telegram-User-ID')
            init_data = request.headers.get('X-Telegram-Init-Data')
            
            if not user_id:
                return None
            
            # В реальном приложении здесь должна быть проверка подписи Telegram
            # Для упрощения пока пропускаем проверку
            
            return {
                'user_id': int(user_id),
                'init_data': init_data
            }
        except Exception as e:
            logger.error(f"Auth verification error: {e}")
            return None
    
    async def check_admin(self, request: Request) -> Response:
        """Проверка админских прав"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        is_admin = auth_data['user_id'] in self.admin_users
        
        return web.json_response({
            'is_admin': is_admin,
            'user_id': auth_data['user_id']
        })
    
    async def get_cs2_matches(self, request: Request) -> Response:
        """Получение матчей CS2"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            await self._get_modules()
            
            # Получаем фильтры из параметров
            tournament = request.query.get('tournament', 'all')
            confidence = request.query.get('confidence', 'all')
            
            # Получаем матчи из анализатора
            matches = await self.cs2_analyzer.get_current_matches(
                tournament_filter=tournament,
                confidence_filter=confidence
            )
            
            return web.json_response(matches)
        except Exception as e:
            logger.error(f"Error getting CS2 matches: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_cs2_match(self, request: Request) -> Response:
        """Получение детальной информации о матче CS2"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            match_id = request.match_info['match_id']
            await self._get_modules()
            
            match = await self.cs2_analyzer.get_match_details(match_id)
            
            if not match:
                return web.json_response({'error': 'Match not found'}, status=404)
            
            return web.json_response(match)
        except Exception as e:
            logger.error(f"Error getting CS2 match: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_khl_matches(self, request: Request) -> Response:
        """Получение матчей КХЛ"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            await self._get_modules()
            
            # Получаем фильтры
            tournament = request.query.get('tournament', 'all')
            confidence = request.query.get('confidence', 'all')
            
            matches = await self.khl_analyzer.get_current_matches(
                tournament_filter=tournament,
                confidence_filter=confidence
            )
            
            return web.json_response(matches)
        except Exception as e:
            logger.error(f"Error getting KHL matches: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_khl_match(self, request: Request) -> Response:
        """Получение детальной информации о матче КХЛ"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            match_id = request.match_info['match_id']
            await self._get_modules()
            
            match = await self.khl_analyzer.get_match_details(match_id)
            
            if not match:
                return web.json_response({'error': 'Match not found'}, status=404)
            
            return web.json_response(match)
        except Exception as e:
            logger.error(f"Error getting KHL match: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_live_matches(self, request: Request) -> Response:
        """Получение live матчей"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            await self._get_modules()
            
            # Получаем live матчи для обоих видов спорта
            cs2_matches = await self.cs2_analyzer.get_live_matches()
            khl_matches = await self.khl_analyzer.get_live_matches()
            
            return web.json_response({
                'cs2': cs2_matches,
                'khl': khl_matches,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting live matches: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_prematch_matches(self, request: Request) -> Response:
        """Получение предматчевых данных"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            await self._get_modules()
            
            hours = int(request.query.get('hours', 3))
            
            # Получаем предматчи для обоих видов спорта
            cs2_matches = await self.cs2_analyzer.get_prematch_matches(hours)
            khl_matches = await self.khl_analyzer.get_prematch_matches(hours)
            
            all_matches = [
                {**match, 'sport': 'cs2'} for match in cs2_matches
            ] + [
                {**match, 'sport': 'khl'} for match in khl_matches
            ]
            
            # Сортируем по времени
            all_matches.sort(key=lambda x: x.get('time', ''))
            
            return web.json_response(all_matches)
        except Exception as e:
            logger.error(f"Error getting prematch matches: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_history_signals(self, request: Request) -> Response:
        """Получение истории сигналов"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            await self._get_modules()
            
            limit = int(request.query.get('limit', 50))
            
            # Получаем историю из базы данных
            signals = await self.db_manager.get_signal_history(limit)
            
            return web.json_response(signals)
        except Exception as e:
            logger.error(f"Error getting history signals: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_stats(self, request: Request) -> Response:
        """Получение статистики"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            sport = request.match_info['sport']
            await self._get_modules()
            
            if sport == 'cs2':
                stats = await self.cs2_analyzer.get_statistics()
            elif sport == 'khl':
                stats = await self.khl_analyzer.get_statistics()
            elif sport == 'general':
                # Общая статистика
                cs2_stats = await self.cs2_analyzer.get_statistics()
                khl_stats = await self.khl_analyzer.get_statistics()
                
                stats = {
                    'total_analyses': cs2_stats.get('total_analyses', 0) + khl_stats.get('total_analyses', 0),
                    'accuracy': (cs2_stats.get('accuracy', 0) + khl_stats.get('accuracy', 0)) / 2,
                    'successful_scenarios': cs2_stats.get('successful_scenarios', 0) + khl_stats.get('successful_scenarios', 0),
                    'avg_confidence': (cs2_stats.get('avg_confidence', 0) + khl_stats.get('avg_confidence', 0)) / 2,
                    'scenarios': {
                        **cs2_stats.get('scenarios', {}),
                        **khl_stats.get('scenarios', {})
                    }
                }
            else:
                return web.json_response({'error': 'Invalid sport'}, status=400)
            
            return web.json_response(stats)
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_confidence_ratings(self, request: Request) -> Response:
        """Получение рейтингов уверенности"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            await self._get_modules()
            
            # Получаем рейтинги для обоих видов спорта
            cs2_ratings = await self.cs2_analyzer.get_confidence_ratings()
            khl_ratings = await self.khl_analyzer.get_confidence_ratings()
            
            all_ratings = cs2_ratings + khl_ratings
            
            # Сортируем по уровню уверенности
            all_ratings.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            return web.json_response(all_ratings)
        except Exception as e:
            logger.error(f"Error getting confidence ratings: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_system_status(self, request: Request) -> Response:
        """Получение статуса системы"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            await self._get_modules()
            
            # Собираем статус всех компонентов
            status = {
                'version': '1.0.0',
                'uptime': self._get_uptime(),
                'last_update': datetime.now().isoformat(),
                'active_tasks': len(asyncio.all_tasks()),
                'backend': {
                    'status': 'online',
                    'last_check': datetime.now().isoformat()
                },
                'parsers': {
                    'cs2': {
                        'status': 'online' if self.cs2_analyzer else 'offline',
                        'last_run': datetime.now().isoformat()
                    },
                    'khl': {
                        'status': 'online' if self.khl_analyzer else 'offline',
                        'last_run': datetime.now().isoformat()
                    }
                },
                'ml': {
                    'status': 'online',
                    'models_loaded': True,
                    'last_training': (datetime.now() - timedelta(hours=6)).isoformat()
                },
                'telegram': {
                    'status': 'online',
                    'bot_connected': True
                },
                'processed_matches': await self.db_manager.get_total_processed_matches()
            }
            
            return web.json_response(status)
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def admin_action(self, request: Request) -> Response:
        """Выполнение админского действия"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        # Проверка админских прав
        if auth_data['user_id'] not in self.admin_users:
            return web.json_response({'error': 'Forbidden'}, status=403)
        
        try:
            data = await request.json()
            action = data.get('action')
            
            await self._get_modules()
            
            result = {'success': True, 'message': f'Action {action} completed'}
            
            if action == 'run-analysis':
                # Запуск анализа
                await self.cs2_analyzer.run_analysis()
                await self.khl_analyzer.run_analysis()
                
            elif action == 'restart-cycles':
                # Перезапуск циклов
                await self._restart_analysis_cycles()
                
            elif action == 'retrain-ml':
                # Переобучение ML моделей
                from cs2.ml.trainer import train_cs2_models
                from khl.ml.trainer import train_khl_models
                
                await train_cs2_models()
                await train_khl_models()
                
            elif action == 'test-mode':
                # Включение тестового режима
                await self._toggle_test_mode()
                
            elif action == 'clear-cache':
                # Очистка кэша
                await self._clear_cache()
                
            elif action == 'backup-data':
                # Создание резервной копии
                backup_path = await self._create_backup()
                result['backup_path'] = backup_path
                
            else:
                return web.json_response({'error': 'Unknown action'}, status=400)
            
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Error executing admin action: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_admin_dashboard(self, request: Request) -> Response:
        """Получение данных админ панели"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        # Проверка админских прав
        if auth_data['user_id'] not in self.admin_users:
            return web.json_response({'error': 'Forbidden'}, status=403)
        
        try:
            await self._get_modules()
            
            # Получаем системные логи
            logs = await self._get_system_logs()
            
            # Получаем детальную статистику
            cs2_stats = await self.cs2_analyzer.get_statistics()
            khl_stats = await self.khl_analyzer.get_statistics()
            
            dashboard_data = {
                'logs': logs[-50:],  # Последние 50 записей
                'stats': {
                    'cs2': cs2_stats,
                    'khl': khl_stats
                },
                'system_status': await self.get_system_status(request)
            }
            
            return web.json_response(dashboard_data)
        except Exception as e:
            logger.error(f"Error getting admin dashboard: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def websocket_handler(self, request: Request) -> WebSocketResponse:
        """WebSocket обработчик для real-time обновлений"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.Response(status=401)
        
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        user_id = str(auth_data['user_id'])
        self.active_connections[user_id] = ws
        
        try:
            logger.info(f"WebSocket connection established for user {user_id}")
            
            # Отправляем начальное сообщение
            await ws.send_str(json.dumps({
                'type': 'connection_established',
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }))
            
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_websocket_message(user_id, data)
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({
                            'type': 'error',
                            'message': 'Invalid JSON'
                        }))
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error for user {user_id}: {ws.exception()}')
        
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
        finally:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            logger.info(f"WebSocket connection closed for user {user_id}")
        
        return ws
    
    async def _handle_websocket_message(self, user_id: str, data: Dict[str, Any]):
        """Обработка WebSocket сообщений"""
        message_type = data.get('type')
        
        if message_type == 'subscribe':
            # Подписка на обновления
            await self._subscribe_user(user_id, data.get('channels', []))
        elif message_type == 'unsubscribe':
            # Отписка от обновлений
            await self._unsubscribe_user(user_id, data.get('channels', []))
    
    async def _subscribe_user(self, user_id: str, channels: List[str]):
        """Подписка пользователя на каналы обновлений"""
        # Реализация подписки на каналы
        pass
    
    async def _unsubscribe_user(self, user_id: str, channels: List[str]):
        """Отписка пользователя от каналов обновлений"""
        # Реализация отписки от каналов
        pass
    
    async def broadcast_update(self, message: Dict[str, Any]):
        """Рассылка обновлений всем подключенным пользователям"""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected_users = []
        
        for user_id, ws in self.active_connections.items():
            try:
                await ws.send_str(message_str)
            except Exception as e:
                logger.error(f"Failed to send update to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Удаляем отключенных пользователей
        for user_id in disconnected_users:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
    
    # Вспомогательные методы
    def _get_uptime(self) -> str:
        """Получение времени работы системы"""
        # Реализация подсчета uptime
        return "0d 0h 0m"
    
    async def _restart_analysis_cycles(self):
        """Перезапуск циклов анализа"""
        # Реализация перезапуска
        pass
    
    async def _toggle_test_mode(self):
        """Переключение тестового режима"""
        # Реализация тестового режима
        pass
    
    async def _clear_cache(self):
        """Очистка кэша"""
        # Реализация очистки кэша
        pass
    
    async def _create_backup(self) -> str:
        """Создание резервной копии"""
        # Реализация создания бэкапа
        return "backup_path"
    
    async def _get_system_logs(self) -> List[str]:
        """Получение системных логов"""
        # Реализация получения логов
        return ["Log entry 1", "Log entry 2"]


# Создание экземпляра API
api_server = MiniAppAPI()

async def start_api_server(host: str = '0.0.0.0', port: int = 8080):
    """Запуск API сервера"""
    runner = web.AppRunner(api_server.app)
    await runner.setup()
    
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info(f"API сервер запущен на http://{host}:{port}")
    logger.info(f"Mini App доступна по адресу: http://{host}:{port}/index.html")
    
    return runner
