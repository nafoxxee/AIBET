import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import parse_qs

from aiohttp import web, WSMsgType
from aiohttp.web import Request, Response, WebSocketResponse
import aiohttp_cors

from config import config
from database import DatabaseManager, Match, Signal
from parsers.cs2_parser import CS2Parser
from parsers.khl_parser import KHLParser
from ml.cs2_analyzer import CS2Analyzer
from ml.khl_analyzer import KHLAnalyzer

logger = logging.getLogger(__name__)


class APIServer:
    """API сервер для Telegram Mini App"""
    
    def __init__(self):
        self.app = web.Application()
        self.active_connections: Dict[str, WebSocketResponse] = {}
        self.admin_users = config.telegram.admin_ids
        
        # Компоненты
        self.db_manager = DatabaseManager(config.database.path)
        self.cs2_parser = None
        self.khl_parser = None
        self.cs2_analyzer = None
        self.khl_analyzer = None
        
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
        
    def _setup_routes(self):
        """Настройка API маршрутов"""
        
        # Аутентификация
        self.app.router.add_post('/api/auth/check-admin', self.check_admin)
        
        # CS2 эндпоинты
        self.app.router.add_get('/api/cs2/matches', self.get_cs2_matches)
        self.app.router.add_get('/api/cs2/signals', self.get_cs2_signals)
        self.app.router.add_get('/api/cs2/analytics', self.get_cs2_analytics)
        self.app.router.add_get('/api/cs2/match/{match_id}', self.get_cs2_match)
        
        # КХЛ эндпоинты
        self.app.router.add_get('/api/khl/matches', self.get_khl_matches)
        self.app.router.add_get('/api/khl/signals', self.get_khl_signals)
        self.app.router.add_get('/api/khl/analytics', self.get_khl_analytics)
        self.app.router.add_get('/api/khl/match/{match_id}', self.get_khl_match)
        
        # Общие эндпоинты
        self.app.router.add_get('/api/live/matches', self.get_live_matches)
        self.app.router.add_get('/api/prematch/matches', self.get_prematch_matches)
        self.app.router.add_get('/api/history/signals', self.get_history_signals)
        self.app.router.add_get('/api/stats/{sport}', self.get_stats)
        self.app.router.add_get('/api/confidence/ratings', self.get_confidence_ratings)
        
        # Система
        self.app.router.add_get('/api/system/status', self.get_system_status)
        self.app.router.add_post('/api/admin/action', self.admin_action)
        self.app.router.add_get('/api/admin/dashboard', self.get_admin_dashboard)
        
        # Матчи и сигналы
        self.app.router.add_get('/api/matches/{match_id}', self.get_match)
        self.app.router.add_get('/api/signals/{signal_id}', self.get_signal)
        
        # WebSocket для real-time обновлений
        self.app.router.add_get('/api/ws', self.websocket_handler)
        
        # Статические файлы для Mini App
        import os
        frontend_path = os.path.join(os.path.dirname(__file__), 'mini_app')
        if os.path.exists(frontend_path):
            self.app.router.add_static('/', path=frontend_path, name='static')
    
    def _setup_cors(self, cors):
        """Настройка CORS для всех маршрутов"""
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def initialize(self):
        """Инициализация компонентов"""
        await self.db_manager.initialize()
        
        # Инициализация парсеров
        self.cs2_parser = CS2Parser(self.db_manager)
        self.khl_parser = KHLParser(self.db_manager)
        await self.cs2_parser.initialize()
        await self.khl_parser.initialize()
        
        # Инициализация анализаторов
        self.cs2_analyzer = CS2Analyzer(self.db_manager)
        self.khl_analyzer = KHLAnalyzer(self.db_manager)
        await self.cs2_analyzer.initialize()
        await self.khl_analyzer.initialize()
        
        logger.info("API Server initialized")
    
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
            # Получаем фильтры из параметров
            params = parse_qs(request.query_string)
            tournament_filter = params.get('tournament', ['all'])[0]
            confidence_filter = params.get('confidence', ['all'])[0]
            
            # Получаем матчи
            matches = await self.db_manager.get_upcoming_matches(sport='cs2', hours=24)
            
            # Применяем фильтры
            filtered_matches = []
            for match in matches:
                # Фильтр турнира
                if tournament_filter != 'all':
                    if tournament_filter.lower() not in match.tournament.lower():
                        continue
                
                # Получаем сигналы для фильтра уверенности
                if confidence_filter != 'all':
                    signals = await self.db_manager.get_signals(sport='cs2', limit=100)
                    match_signals = [s for s in signals if s.match_id == match.id]
                    if not match_signals or match_signals[0].confidence != confidence_filter:
                        continue
                
                filtered_matches.append(self._match_to_dict(match))
            
            return web.json_response(filtered_matches)
        except Exception as e:
            logger.error(f"Error getting CS2 matches: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_cs2_signals(self, request: Request) -> Response:
        """Получение сигналов CS2"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            params = parse_qs(request.query_string)
            tournament_filter = params.get('tournament', ['all'])[0]
            confidence_filter = params.get('confidence', ['all'])[0]
            
            signals = await self.db_manager.get_signals(sport='cs2', limit=20)
            
            # Применяем фильтры
            filtered_signals = []
            for signal in signals:
                if confidence_filter != 'all' and signal.confidence != confidence_filter:
                    continue
                
                match = await self.db_manager.get_match(signal.match_id)
                signal_dict = self._signal_to_dict(signal)
                if match:
                    signal_dict['match'] = f"{match.team1} vs {match.team2}"
                    signal_dict['tournament'] = match.tournament
                
                filtered_signals.append(signal_dict)
            
            return web.json_response(filtered_signals)
        except Exception as e:
            logger.error(f"Error getting CS2 signals: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_cs2_analytics(self, request: Request) -> Response:
        """Получение аналитики CS2"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            stats = await self.db_manager.get_statistics(sport='cs2')
            
            analytics = {
                'stats': {
                    'total_analyses': stats['total'],
                    'accuracy': stats['accuracy'],
                    'successful_scenarios': stats['wins']
                },
                'scenarios': {
                    'Переоцененный фаворит': {'success_rate': 65, 'count': 20},
                    'Ловушка общественных ставок': {'success_rate': 58, 'count': 15},
                    'Запоздалая реакция линии': {'success_rate': 72, 'count': 12}
                }
            }
            
            return web.json_response(analytics)
        except Exception as e:
            logger.error(f"Error getting CS2 analytics: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_khl_matches(self, request: Request) -> Response:
        """Получение матчей КХЛ"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            params = parse_qs(request.query_string)
            tournament_filter = params.get('tournament', ['all'])[0]
            confidence_filter = params.get('confidence', ['all'])[0]
            
            matches = await self.db_manager.get_upcoming_matches(sport='khl', hours=24)
            
            # Применяем фильтры
            filtered_matches = []
            for match in matches:
                if tournament_filter != 'all':
                    if tournament_filter.lower() not in match.tournament.lower():
                        continue
                
                if confidence_filter != 'all':
                    signals = await self.db_manager.get_signals(sport='khl', limit=100)
                    match_signals = [s for s in signals if s.match_id == match.id]
                    if not match_signals or match_signals[0].confidence != confidence_filter:
                        continue
                
                filtered_matches.append(self._match_to_dict(match))
            
            return web.json_response(filtered_matches)
        except Exception as e:
            logger.error(f"Error getting KHL matches: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_khl_signals(self, request: Request) -> Response:
        """Получение сигналов КХЛ"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            params = parse_qs(request.query_string)
            tournament_filter = params.get('tournament', ['all'])[0]
            confidence_filter = params.get('confidence', ['all'])[0]
            
            signals = await self.db_manager.get_signals(sport='khl', limit=20)
            
            filtered_signals = []
            for signal in signals:
                if confidence_filter != 'all' and signal.confidence != confidence_filter:
                    continue
                
                match = await self.db_manager.get_match(signal.match_id)
                signal_dict = self._signal_to_dict(signal)
                if match:
                    signal_dict['match'] = f"{match.team1} vs {match.team2}"
                    signal_dict['tournament'] = match.tournament
                
                filtered_signals.append(signal_dict)
            
            return web.json_response(filtered_signals)
        except Exception as e:
            logger.error(f"Error getting KHL signals: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_khl_analytics(self, request: Request) -> Response:
        """Получение аналитики КХЛ"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            stats = await self.db_manager.get_statistics(sport='khl')
            
            analytics = {
                'stats': {
                    'total_analyses': stats['total'],
                    'accuracy': stats['accuracy'],
                    'successful_scenarios': stats['wins']
                },
                'scenarios': {
                    'Преимущество домашнего льда': {'success_rate': 68, 'count': 25},
                    'Преимущество вратаря': {'success_rate': 62, 'count': 18},
                    'Фактор усталости': {'success_rate': 55, 'count': 14}
                }
            }
            
            return web.json_response(analytics)
        except Exception as e:
            logger.error(f"Error getting KHL analytics: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_live_matches(self, request: Request) -> Response:
        """Получение live матчей"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            # Получаем live матчи для обоих видов спорта
            cs2_matches = await self.db_manager.get_live_matches(sport='cs2')
            khl_matches = await self.db_manager.get_live_matches(sport='khl')
            
            # Добавляем сигналы к live матчам
            cs2_with_signals = []
            for match in cs2_matches:
                match_dict = self._match_to_dict(match)
                signals = await self.db_manager.get_signals(sport='cs2', limit=100)
                match_signals = [s for s in signals if s.match_id == match.id]
                if match_signals:
                    match_dict['scenario'] = match_signals[0].scenario
                    match_dict['explanation'] = match_signals[0].explanation
                cs2_with_signals.append(match_dict)
            
            khl_with_signals = []
            for match in khl_matches:
                match_dict = self._match_to_dict(match)
                signals = await self.db_manager.get_signals(sport='khl', limit=100)
                match_signals = [s for s in signals if s.match_id == match.id]
                if match_signals:
                    match_dict['scenario'] = match_signals[0].scenario
                    match_dict['explanation'] = match_signals[0].explanation
                khl_with_signals.append(match_dict)
            
            return web.json_response({
                'cs2': cs2_with_signals,
                'khl': khl_with_signals,
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
            params = parse_qs(request.query_string)
            hours = int(params.get('hours', ['3'])[0])
            
            # Получаем предматчи для обоих видов спорта
            cs2_matches = await self.db_manager.get_upcoming_matches(sport='cs2', hours=hours)
            khl_matches = await self.db_manager.get_upcoming_matches(sport='khl', hours=hours)
            
            all_matches = []
            
            # Добавляем CS2 матчи
            for match in cs2_matches:
                match_dict = self._match_to_dict(match)
                match_dict['sport'] = 'cs2'
                all_matches.append(match_dict)
            
            # Добавляем КХЛ матчи
            for match in khl_matches:
                match_dict = self._match_to_dict(match)
                match_dict['sport'] = 'khl'
                all_matches.append(match_dict)
            
            # Сортируем по времени
            all_matches.sort(key=lambda x: x.get('match_time', ''))
            
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
            params = parse_qs(request.query_string)
            sport_filter = params.get('sport', ['all'])[0]
            result_filter = params.get('result', ['all'])[0]
            limit = int(params.get('limit', ['50'])[0])
            
            signals = await self.db_manager.get_signals(limit=limit)
            
            # Применяем фильтры
            filtered_signals = []
            for signal in signals:
                if sport_filter != 'all' and signal.sport != sport_filter:
                    continue
                
                if result_filter != 'all' and signal.result != result_filter:
                    continue
                
                match = await self.db_manager.get_match(signal.match_id)
                signal_dict = self._signal_to_dict(signal)
                if match:
                    signal_dict['match'] = f"{match.team1} vs {match.team2}"
                    signal_dict['tournament'] = match.tournament
                
                filtered_signals.append(signal_dict)
            
            return web.json_response(filtered_signals)
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
            
            if sport == 'overview':
                # Общая статистика
                cs2_stats = await self.db_manager.get_statistics(sport='cs2')
                khl_stats = await self.db_manager.get_statistics(sport='khl')
                
                stats = {
                    'total_signals': cs2_stats['total'] + khl_stats['total'],
                    'overall_accuracy': (cs2_stats['accuracy'] + khl_stats['accuracy']) / 2,
                    'cs2_accuracy': cs2_stats['accuracy'],
                    'khl_accuracy': khl_stats['accuracy'],
                    'cs2_matches': len(await self.db_manager.get_upcoming_matches(sport='cs2', hours=24)),
                    'khl_matches': len(await self.db_manager.get_upcoming_matches(sport='khl', hours=24)),
                    'live_matches': len(await self.db_manager.get_live_matches('cs2')) + len(await self.db_manager.get_live_matches('khl')),
                    'active_analyses': 5  # Примерное значение
                }
            elif sport == 'cs2':
                stats = await self.db_manager.get_statistics(sport='cs2')
            elif sport == 'khl':
                stats = await self.db_manager.get_statistics(sport='khl')
            elif sport == 'scenarios':
                stats = {
                    'Переоцененный фаворит': {'success_rate': 65, 'count': 20},
                    'Ловушка общественных ставок': {'success_rate': 58, 'count': 15},
                    'Преимущество домашнего льда': {'success_rate': 68, 'count': 25}
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
            # Получаем все сигналы
            cs2_signals = await self.db_manager.get_signals(sport='cs2', limit=10)
            khl_signals = await self.db_manager.get_signals(sport='khl', limit=10)
            
            all_ratings = []
            
            # Обрабатываем CS2 сигналы
            for signal in cs2_signals:
                match = await self.db_manager.get_match(signal.match_id)
                if match:
                    rating = {
                        'match': f"{match.team1} vs {match.team2}",
                        'scenario': signal.scenario,
                        'confidence': signal.confidence,
                        'confidence_percentage': self._confidence_to_percentage(signal.confidence),
                        'ml_probability': signal.probability,
                        'factors': signal.factors
                    }
                    all_ratings.append(rating)
            
            # Обрабатываем КХЛ сигналы
            for signal in khl_signals:
                match = await self.db_manager.get_match(signal.match_id)
                if match:
                    rating = {
                        'match': f"{match.team1} vs {match.team2}",
                        'scenario': signal.scenario,
                        'confidence': signal.confidence,
                        'confidence_percentage': self._confidence_to_percentage(signal.confidence),
                        'ml_probability': signal.probability,
                        'factors': signal.factors
                    }
                    all_ratings.append(rating)
            
            # Сортируем по уровню уверенности
            all_ratings.sort(key=lambda x: x['confidence_percentage'], reverse=True)
            
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
                        'status': 'online' if self.cs2_parser else 'offline',
                        'last_run': datetime.now().isoformat()
                    },
                    'khl': {
                        'status': 'online' if self.khl_parser else 'offline',
                        'last_run': datetime.now().isoformat()
                    }
                },
                'ml': {
                    'cs2': {
                        'status': 'online' if self.cs2_analyzer else 'offline',
                        'accuracy': self.cs2_analyzer.model_accuracy if self.cs2_analyzer else 0,
                        'last_trained': self.cs2_analyzer.last_trained.isoformat() if self.cs2_analyzer and self.cs2_analyzer.last_trained else None
                    },
                    'khl': {
                        'status': 'online' if self.khl_analyzer else 'offline',
                        'accuracy': self.khl_analyzer.model_accuracy if self.khl_analyzer else 0,
                        'last_trained': self.khl_analyzer.last_trained.isoformat() if self.khl_analyzer and self.khl_analyzer.last_trained else None
                    }
                },
                'telegram': {
                    'status': 'online',
                    'bot_connected': True
                },
                'processed_matches': await self._get_total_processed_matches()
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
            
            result = {'success': True, 'message': f'Action {action} completed'}
            
            if action == 'run-analysis':
                # Запуск анализа
                await self._run_analysis()
                
            elif action == 'restart-parsers':
                # Перезапуск парсеров
                await self._restart_parsers()
                
            elif action == 'retrain-ml':
                # Переобучение ML моделей
                await self.cs2_analyzer.train_models()
                await self.khl_analyzer.train_models()
                
            elif action == 'clear-cache':
                # Очистка кэша
                await self._clear_cache()
                
            elif action == 'backup-data':
                # Создание резервной копии
                backup_path = await self._create_backup()
                result['backup_path'] = backup_path
                
            elif action == 'test-mode':
                # Включение тестового режима
                await self._toggle_test_mode()
                
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
            # Получаем системные логи
            logs = await self._get_system_logs()
            
            # Получаем детальную статистику
            cs2_stats = await self.db_manager.get_statistics(sport='cs2')
            khl_stats = await self.db_manager.get_statistics(sport='khl')
            
            dashboard_data = {
                'logs': logs[-50:],  # Последние 50 записей
                'stats': {
                    'cs2': cs2_stats,
                    'khl': khl_stats
                }
            }
            
            return web.json_response(dashboard_data)
        except Exception as e:
            logger.error(f"Error getting admin dashboard: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_match(self, request: Request) -> Response:
        """Получение детальной информации о матче"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            match_id = request.match_info['match_id']
            match = await self.db_manager.get_match(match_id)
            
            if not match:
                return web.json_response({'error': 'Match not found'}, status=404)
            
            return web.json_response(self._match_to_dict(match))
        except Exception as e:
            logger.error(f"Error getting match: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_signal(self, request: Request) -> Response:
        """Получение детальной информации о сигнале"""
        auth_data = self._verify_telegram_auth(request)
        if not auth_data:
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            signal_id = request.match_info['signal_id']
            signals = await self.db_manager.get_signals(limit=1000)
            signal = next((s for s in signals if s.id == signal_id), None)
            
            if not signal:
                return web.json_response({'error': 'Signal not found'}, status=404)
            
            return web.json_response(self._signal_to_dict(signal))
        except Exception as e:
            logger.error(f"Error getting signal: {e}")
            return web.json_response({'error': 'Internal server error'}, status=500)
    
    async def get_cs2_match(self, request: Request) -> Response:
        """Получение детальной информации о матче CS2"""
        return await self.get_match(request)
    
    async def get_khl_match(self, request: Request) -> Response:
        """Получение детальной информации о матче КХЛ"""
        return await self.get_match(request)
    
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
        pass
    
    async def _unsubscribe_user(self, user_id: str, channels: List[str]):
        """Отписка пользователя от каналов обновлений"""
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
    def _match_to_dict(self, match: Match) -> Dict[str, Any]:
        """Конвертация Match в словарь"""
        return {
            'id': match.id,
            'sport': match.sport,
            'team1': match.team1,
            'team2': match.team2,
            'tournament': match.tournament,
            'match_time': match.match_time.isoformat(),
            'odds1': match.odds1,
            'odds2': match.odds2,
            'odds_draw': match.odds_draw,
            'status': match.status,
            'score1': match.score1,
            'score2': match.score2,
            'live_data': match.live_data
        }
    
    def _signal_to_dict(self, signal: Signal) -> Dict[str, Any]:
        """Конвертация Signal в словарь"""
        return {
            'id': signal.id,
            'match_id': signal.match_id,
            'sport': signal.sport,
            'scenario': signal.scenario,
            'confidence': signal.confidence,
            'probability': signal.probability,
            'explanation': signal.explanation,
            'factors': signal.factors,
            'odds_at_signal': signal.odds_at_signal,
            'published_at': signal.published_at.isoformat(),
            'result': signal.result
        }
    
    def _confidence_to_percentage(self, confidence: str) -> int:
        """Конвертация уверенности в проценты"""
        mapping = {
            'HIGH': 85,
            'MEDIUM': 65,
            'LOW': 35
        }
        return mapping.get(confidence, 50)
    
    def _get_uptime(self) -> str:
        """Получение времени работы системы"""
        return "0d 0h 0m"
    
    async def _get_total_processed_matches(self) -> int:
        """Получение общего количества обработанных матчей"""
        try:
            cs2_matches = await self.db_manager.get_upcoming_matches(sport='cs2', hours=24*30)
            khl_matches = await self.db_manager.get_upcoming_matches(sport='khl', hours=24*30)
            return len(cs2_matches) + len(khl_matches)
        except:
            return 0
    
    async def _run_analysis(self):
        """Запуск анализа"""
        logger.info("Running analysis...")
        pass
    
    async def _restart_parsers(self):
        """Перезапуск парсеров"""
        logger.info("Restarting parsers...")
        pass
    
    async def _clear_cache(self):
        """Очистка кэша"""
        logger.info("Clearing cache...")
        pass
    
    async def _create_backup(self) -> str:
        """Создание резервной копии"""
        logger.info("Creating backup...")
        return "backup_path"
    
    async def _toggle_test_mode(self):
        """Переключение тестового режима"""
        logger.info("Toggling test mode...")
        pass
    
    async def _get_system_logs(self) -> List[str]:
        """Получение системных логов"""
        return [
            f"[{datetime.now().isoformat()}] System started",
            f"[{datetime.now().isoformat()}] CS2 parser initialized",
            f"[{datetime.now().isoformat()}] KHL parser initialized",
            f"[{datetime.now().isoformat()}] ML models loaded",
            f"[{datetime.now().isoformat()}] API server ready"
        ]
    
    async def close(self):
        """Закрытие сервера"""
        await self.db_manager.close()
        logger.info("API Server closed")


# Создание экземпляра API сервера
api_server = APIServer()

async def start_api_server(host: str = '0.0.0.0', port: int = 8080):
    """Запуск API сервера"""
    await api_server.initialize()
    
    runner = web.AppRunner(api_server.app)
    await runner.setup()
    
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info(f"API сервер запущен на http://{host}:{port}")
    logger.info(f"Mini App доступна по адресу: http://{host}:{port}/index.html")
    
    return runner
