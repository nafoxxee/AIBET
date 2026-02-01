#!/usr/bin/env python3
"""
AIBET Mini App - Advanced Analytics Platform
5 разделов: Главная, Live матчи, История сигналов, Статистика, Настройки
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import random

# Импорты наших модулей
from ai_models import AdvancedMLModels
from data_collector import AdvancedDataCollector, DataCollectionScheduler
from database import DatabaseManager, Signal
from config import config

logger = logging.getLogger(__name__)

class AIBETMiniApp:
    def __init__(self):
        self.app = FastAPI(title="AIBET Analytics Platform", version="1.0.0")
        
        # Настройка CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Инициализация базы данных
        self.db_manager = DatabaseManager(config.database.path)
        
        # Инициализация данных
        self.ml_models = AdvancedMLModels(self.db_manager)
        self.data_collector = AdvancedDataCollector(self.db_manager)
        
        # Роуты
        self.setup_routes()
        
    def setup_routes(self):
        """Настройка всех роутов"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def main_page():
            """Главная страница Mini App"""
            return self.generate_main_html()
        
        @self.app.get("/api/signals")
        async def get_signals():
            """API для получения сигналов"""
            return JSONResponse(content=self.get_signals_data())
        
        @self.app.get("/api/matches")
        async def get_matches():
            """API для получения матчей"""
            return JSONResponse(content=self.get_matches_data())
        
        @self.app.get("/api/live-matches")
        async def get_live_matches():
            """API для получения live матчей"""
            return JSONResponse(content=self.get_live_matches_data())
        
        @self.app.get("/api/statistics")
        async def get_statistics():
            """API для получения статистики"""
            return JSONResponse(content=self.get_statistics_data())
        
        @self.app.get("/api/history")
        async def get_history():
            """API для получения истории"""
            return JSONResponse(content=self.get_history_data())
        
        @self.app.get("/api/health")
        async def health_check():
            """Health check для Render"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    def generate_main_html(self) -> str:
        """Генерация HTML для Mini App"""
        return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIBET Analytics Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .dark { background-color: #1a1a1a; color: #ffffff; }
        .dark .bg-white { background-color: #2d2d2d; }
        .dark .text-gray-900 { color: #ffffff; }
        .dark .text-gray-600 { color: #a0a0a0; }
        .signal-card { transition: all 0.3s ease; }
        .signal-card:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        .live-indicator { animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
        .tab-active { border-bottom: 3px solid #3b82f6; }
    </style>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg">
            <div class="container mx-auto px-4 py-4">
                <div class="flex justify-between items-center">
                    <div class="flex items-center space-x-3">
                        <i class="fas fa-chart-line text-2xl"></i>
                        <h1 class="text-2xl font-bold">AIBET Analytics</h1>
                    </div>
                    <div class="flex items-center space-x-4">
                        <button id="themeToggle" class="p-2 rounded-full hover:bg-white/20 transition">
                            <i class="fas fa-moon"></i>
                        </button>
                        <button id="refreshBtn" class="p-2 rounded-full hover:bg-white/20 transition">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="container mx-auto px-4 py-6">
            <!-- Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div class="bg-white rounded-lg shadow p-4">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">Всего сигналов</p>
                            <p class="text-2xl font-bold text-gray-900" id="totalSignals">0</p>
                        </div>
                        <i class="fas fa-signal text-blue-500 text-2xl"></i>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow p-4">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">Успешность</p>
                            <p class="text-2xl font-bold text-green-600" id="successRate">0%</p>
                        </div>
                        <i class="fas fa-check-circle text-green-500 text-2xl"></i>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow p-4">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">Live матчи</p>
                            <p class="text-2xl font-bold text-orange-600" id="liveMatches">0</p>
                        </div>
                        <i class="fas fa-broadcast-tower text-orange-500 text-2xl"></i>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow p-4">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">AI точность</p>
                            <p class="text-2xl font-bold text-purple-600" id="aiAccuracy">0%</p>
                        </div>
                        <i class="fas fa-brain text-purple-500 text-2xl"></i>
                    </div>
                </div>
            </div>

            <!-- Navigation Tabs -->
            <div class="bg-white rounded-lg shadow mb-6">
                <div class="border-b border-gray-200">
                    <nav class="flex space-x-8 px-4">
                        <button class="py-3 px-1 border-b-2 font-medium text-sm tab-active" data-tab="main">
                            <i class="fas fa-home mr-2"></i>Главная
                        </button>
                        <button class="py-3 px-1 border-b-2 font-medium text-sm text-gray-500 hover:text-gray-700" data-tab="live">
                            <i class="fas fa-broadcast-tower mr-2"></i>Live матчи
                        </button>
                        <button class="py-3 px-1 border-b-2 font-medium text-sm text-gray-500 hover:text-gray-700" data-tab="history">
                            <i class="fas fa-history mr-2"></i>История
                        </button>
                        <button class="py-3 px-1 border-b-2 font-medium text-sm text-gray-500 hover:text-gray-700" data-tab="statistics">
                            <i class="fas fa-chart-bar mr-2"></i>Статистика
                        </button>
                        <button class="py-3 px-1 border-b-2 font-medium text-sm text-gray-500 hover:text-gray-700" data-tab="settings">
                            <i class="fas fa-cog mr-2"></i>Настройки
                        </button>
                    </nav>
                </div>
            </div>

            <!-- Tab Content -->
            <div id="tabContent">
                <!-- Main Tab -->
                <div id="main" class="tab-content">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <!-- Recent Signals -->
                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-lg font-semibold mb-4">
                                <i class="fas fa-signal text-blue-500 mr-2"></i>Последние сигналы
                            </h3>
                            <div id="recentSignals" class="space-y-3">
                                <!-- Signals will be loaded here -->
                            </div>
                        </div>

                        <!-- Upcoming Matches -->
                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-lg font-semibold mb-4">
                                <i class="fas fa-calendar text-purple-500 mr-2"></i>Предстоящие матчи
                            </h3>
                            <div id="upcomingMatches" class="space-y-3">
                                <!-- Matches will be loaded here -->
                            </div>
                        </div>
                    </div>

                    <!-- Charts Section -->
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-lg font-semibold mb-4">
                                <i class="fas fa-chart-line text-green-500 mr-2"></i>График успешности
                            </h3>
                            <canvas id="successChart" width="400" height="200"></canvas>
                        </div>

                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-lg font-semibold mb-4">
                                <i class="fas fa-chart-pie text-orange-500 mr-2"></i>Распределение сигналов
                            </h3>
                            <canvas id="distributionChart" width="400" height="200"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Live Matches Tab -->
                <div id="live" class="tab-content hidden">
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-semibold mb-4">
                            <i class="fas fa-broadcast-tower text-red-500 mr-2 live-indicator"></i>Live матчи
                        </h3>
                        <div id="liveMatchesContent" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <!-- Live matches will be loaded here -->
                        </div>
                    </div>
                </div>

                <!-- History Tab -->
                <div id="history" class="tab-content hidden">
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-semibold mb-4">
                            <i class="fas fa-history text-blue-500 mr-2"></i>История сигналов
                        </h3>
                        <div id="historyContent" class="space-y-3">
                            <!-- History will be loaded here -->
                        </div>
                    </div>
                </div>

                <!-- Statistics Tab -->
                <div id="statistics" class="tab-content hidden">
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-lg font-semibold mb-4">
                                <i class="fas fa-trophy text-yellow-500 mr-2"></i>Топ команды
                            </h3>
                            <div id="topTeams" class="space-y-2">
                                <!-- Top teams will be loaded here -->
                            </div>
                        </div>

                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-lg font-semibold mb-4">
                                <i class="fas fa-percentage text-green-500 mr-2"></i>Успешность по видам спорта
                            </h3>
                            <canvas id="sportSuccessChart" width="300" height="200"></canvas>
                        </div>

                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-lg font-semibold mb-4">
                                <i class="fas fa-clock text-purple-500 mr-2"></i>Активность по времени
                            </h3>
                            <canvas id="activityChart" width="300" height="200"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Settings Tab -->
                <div id="settings" class="tab-content hidden">
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-semibold mb-4">
                            <i class="fas fa-cog text-gray-500 mr-2"></i>Настройки
                        </h3>
                        
                        <div class="space-y-6">
                            <div>
                                <h4 class="font-medium mb-3">Уведомления</h4>
                                <div class="space-y-2">
                                    <label class="flex items-center">
                                        <input type="checkbox" class="mr-2" checked>
                                        <span>Уведомления о новых сигналах</span>
                                    </label>
                                    <label class="flex items-center">
                                        <input type="checkbox" class="mr-2" checked>
                                        <span>Уведомления о live матчах</span>
                                    </label>
                                </div>
                            </div>

                            <div>
                                <h4 class="font-medium mb-3">Фильтры сигналов</h4>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label class="block text-sm font-medium mb-1">Минимальная уверенность</label>
                                        <select class="w-full px-3 py-2 border rounded-lg">
                                            <option value="0.5">50%</option>
                                            <option value="0.6">60%</option>
                                            <option value="0.7" selected>70%</option>
                                            <option value="0.8">80%</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium mb-1">Минимальная ценность</label>
                                        <select class="w-full px-3 py-2 border rounded-lg">
                                            <option value="0.05">5%</option>
                                            <option value="0.1" selected>10%</option>
                                            <option value="0.15">15%</option>
                                            <option value="0.2">20%</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        let currentTheme = 'light';
        let currentTab = 'main';
        let charts = {};

        document.addEventListener('DOMContentLoaded', function() {
            initializeApp();
            loadInitialData();
            startAutoRefresh();
        });

        function initializeApp() {
            document.querySelectorAll('[data-tab]').forEach(button => {
                button.addEventListener('click', function() {
                    switchTab(this.dataset.tab);
                });
            });

            document.getElementById('themeToggle').addEventListener('click', toggleTheme);
            document.getElementById('refreshBtn').addEventListener('click', refreshData);
        }

        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.add('hidden');
            });
            document.getElementById(tabName).classList.remove('hidden');

            document.querySelectorAll('[data-tab]').forEach(button => {
                button.classList.remove('tab-active', 'text-blue-600');
                button.classList.add('text-gray-500');
            });

            document.querySelector(`[data-tab="${tabName}"]`).classList.add('tab-active', 'text-blue-600');
            document.querySelector(`[data-tab="${tabName}"]`).classList.remove('text-gray-500');

            currentTab = tabName;
            loadTabData(tabName);
        }

        function toggleTheme() {
            currentTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.body.classList.toggle('dark');
            const icon = document.querySelector('#themeToggle i');
            icon.className = currentTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }

        async function loadInitialData() {
            await Promise.all([loadSignals(), loadMatches(), loadStatistics(), loadHistory()]);
            updateDashboard();
        }

        async function loadSignals() {
            try {
                const response = await fetch('/api/signals');
                const data = await response.json();
                displaySignals(data);
            } catch (error) {
                console.error('Error loading signals:', error);
            }
        }

        async function loadMatches() {
            try {
                const response = await fetch('/api/matches');
                const data = await response.json();
                displayMatches(data);
            } catch (error) {
                console.error('Error loading matches:', error);
            }
        }

        async function loadStatistics() {
            try {
                const response = await fetch('/api/statistics');
                const data = await response.json();
                updateStatisticsDisplay(data);
                createCharts(data);
            } catch (error) {
                console.error('Error loading statistics:', error);
            }
        }

        async function loadHistory() {
            try {
                const response = await fetch('/api/history');
                const data = await response.json();
                displayHistory(data);
            } catch (error) {
                console.error('Error loading history:', error);
            }
        }

        function displaySignals(signals) {
            const container = document.getElementById('recentSignals');
            container.innerHTML = '';
            signals.slice(0, 5).forEach(signal => {
                container.appendChild(createSignalCard(signal));
            });
        }

        function createSignalCard(signal) {
            const card = document.createElement('div');
            card.className = 'signal-card border rounded-lg p-3 hover:shadow-md';
            
            const confidenceColor = signal.confidence >= 0.8 ? 'green' : signal.confidence >= 0.6 ? 'yellow' : 'red';
            const sportIcon = signal.sport === 'cs2' ? '🔫' : '🏒';
            
            card.innerHTML = `
                <div class="flex justify-between items-start mb-2">
                    <div class="flex items-center">
                        <span class="text-xl mr-2">${sportIcon}</span>
                        <div>
                            <p class="font-medium text-sm">${signal.match}</p>
                            <p class="text-xs text-gray-500">${signal.timestamp}</p>
                        </div>
                    </div>
                    <span class="px-2 py-1 bg-${confidenceColor}-100 text-${confidenceColor}-800 text-xs rounded-full">
                        ${(signal.confidence * 100).toFixed(0)}%
                    </span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm font-medium">${signal.prediction === 'team1' ? 'Победа 1' : 'Победа 2'}</span>
                    <span class="text-sm text-gray-600">${signal.odds}x</span>
                </div>
            `;
            return card;
        }

        function displayMatches(matches) {
            const container = document.getElementById('upcomingMatches');
            container.innerHTML = '';
            matches.filter(m => m.status === 'upcoming').slice(0, 5).forEach(match => {
                container.appendChild(createMatchCard(match));
            });
        }

        function createMatchCard(match) {
            const card = document.createElement('div');
            card.className = 'border rounded-lg p-3 hover:shadow-md';
            const sportIcon = match.sport === 'cs2' ? '🔫' : '🏒';
            const time = new Date(match.match_time).toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'});
            
            card.innerHTML = `
                <div class="flex justify-between items-center mb-2">
                    <span class="text-lg">${sportIcon}</span>
                    <span class="text-xs text-gray-500">${time}</span>
                </div>
                <div class="text-sm">
                    <p class="font-medium">${match.team1} vs ${match.team2}</p>
                    <p class="text-xs text-gray-600">${match.tournament}</p>
                </div>
                <div class="flex justify-between mt-2">
                    <span class="text-xs">${match.odds1}</span>
                    <span class="text-xs">${match.odds2}</span>
                </div>
            `;
            return card;
        }

        function updateStatisticsDisplay(stats) {
            document.getElementById('totalSignals').textContent = stats.total_signals;
            document.getElementById('successRate').textContent = `${(stats.success_rate * 100).toFixed(1)}%`;
            document.getElementById('aiAccuracy').textContent = `${(stats.success_rate * 100).toFixed(1)}%`;
        }

        function createCharts(data) {
            const successCtx = document.getElementById('successChart').getContext('2d');
            if (charts.success) charts.success.destroy();
            
            charts.success = new Chart(successCtx, {
                type: 'line',
                data: {
                    labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
                    datasets: [{
                        label: 'Успешность',
                        data: [65, 70, 68, 75, 72, 78, 82],
                        borderColor: 'rgb(34, 197, 94)',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        tension: 0.4
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });

            const distributionCtx = document.getElementById('distributionChart').getContext('2d');
            if (charts.distribution) charts.distribution.destroy();
            
            charts.distribution = new Chart(distributionCtx, {
                type: 'doughnut',
                data: {
                    labels: ['CS:GO', 'КХЛ'],
                    datasets: [{
                        data: [data.cs2_signals, data.khl_signals],
                        backgroundColor: ['rgba(59, 130, 246, 0.8)', 'rgba(251, 146, 60, 0.8)']
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        function updateDashboard() {
            const liveCount = document.querySelectorAll('.live-match').length;
            document.getElementById('liveMatches').textContent = liveCount;
        }

        function startAutoRefresh() {
            setInterval(() => {
                if (currentTab === 'live') loadLiveMatches();
                refreshData();
            }, 30000);
        }

        async function refreshData() {
            const refreshBtn = document.getElementById('refreshBtn');
            const icon = refreshBtn.querySelector('i');
            icon.classList.add('fa-spin');
            try {
                await loadInitialData();
            } finally {
                icon.classList.remove('fa-spin');
            }
        }

        async function loadLiveMatches() {
            try {
                const response = await fetch('/api/live-matches');
                const data = await response.json();
                displayLiveMatches(data);
            } catch (error) {
                console.error('Error loading live matches:', error);
            }
        }

        function displayLiveMatches(matches) {
            const container = document.getElementById('liveMatchesContent');
            if (!container) return;
            container.innerHTML = '';
            matches.forEach(match => {
                container.appendChild(createLiveMatchCard(match));
            });
        }

        function createLiveMatchCard(match) {
            const card = document.createElement('div');
            card.className = 'live-match border rounded-lg p-4 bg-red-50 border-red-200';
            const sportIcon = match.sport === 'cs2' ? '🔫' : '🏒';
            
            card.innerHTML = `
                <div class="flex justify-between items-center mb-3">
                    <div class="flex items-center">
                        <span class="text-2xl mr-2">${sportIcon}</span>
                        <span class="live-indicator text-red-500 text-sm font-medium">LIVE</span>
                    </div>
                </div>
                <div class="text-center mb-3">
                    <p class="font-medium">${match.team1} vs ${match.team2}</p>
                    <p class="text-2xl font-bold text-gray-800">${match.score1} - ${match.score2}</p>
                </div>
            `;
            return card;
        }

        function displayHistory(history) {
            const container = document.getElementById('historyContent');
            if (!container) return;
            container.innerHTML = '';
            history.forEach(signal => {
                container.appendChild(createHistoryCard(signal));
            });
        }

        function createHistoryCard(signal) {
            const card = document.createElement('div');
            card.className = 'border rounded-lg p-3';
            const sportIcon = signal.sport === 'cs2' ? '🔫' : '🏒';
            
            card.innerHTML = `
                <div class="flex justify-between items-start">
                    <div class="flex items-center">
                        <span class="text-lg mr-2">${sportIcon}</span>
                        <div>
                            <p class="font-medium text-sm">${signal.match}</p>
                            <p class="text-xs text-gray-500">${signal.timestamp}</p>
                        </div>
                    </div>
                </div>
                <div class="mt-2 text-sm">
                    <span class="font-medium">${signal.prediction}</span>
                    <span class="text-gray-600 ml-2">${signal.odds}x</span>
                </div>
            `;
            return card;
        }

        function loadTabData(tabName) {
            switch(tabName) {
                case 'live': loadLiveMatches(); break;
                case 'statistics': loadStatistics(); break;
                case 'history': loadHistory(); break;
            }
        }
    </script>
</body>
</html>
        """
    
    async def get_signals_data(self) -> List[Dict]:
        """Получение данных сигналов"""
        try:
            signals = await self.db_manager.get_signals(limit=20)
            return [self.signal_to_dict(signal) for signal in signals]
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return self.get_sample_signals()
    
    def signal_to_dict(self, signal: Signal) -> Dict:
        """Конвертация Signal в Dict"""
        return {
            'id': signal.id,
            'sport': signal.sport,
            'match_id': signal.match_id,
            'match': f"Match {signal.match_id}",  # Будет получено из match data
            'prediction': signal.prediction or 'team1',
            'confidence': float(signal.confidence.replace('%', '')) / 100 if isinstance(signal.confidence, str) else signal.confidence,
            'probability': signal.probability,
            'expected_value': signal.expected_value or 0.0,
            'odds': signal.odds_at_signal,
            'explanation': signal.explanation,
            'factors': signal.factors,
            'prediction_type': signal.prediction_type or 'MEDIUM_CONFIDENCE',
            'timestamp': signal.published_at.isoformat(),
            'result': signal.result
        }
    
    def get_sample_signals(self) -> List[Dict]:
        """Получение примеров сигналов"""
        return [
            {
                'id': 'signal_1',
                'sport': 'cs2',
                'match': 'NAVI vs G2',
                'prediction': 'team1',
                'confidence': 0.85,
                'probability': 0.85,
                'expected_value': 0.25,
                'odds': 1.85,
                'explanation': '🤖 AI Прогноз: Победа первой команды с вероятностью 85.0%',
                'factors': ['Анализ коэффициентов', 'Текущая форма команд'],
                'prediction_type': 'HIGH_CONFIDENCE',
                'timestamp': datetime.now().isoformat(),
                'result': 'won'
            },
            {
                'id': 'signal_2',
                'sport': 'khl',
                'match': 'ЦСКА vs СКА',
                'prediction': 'team2',
                'confidence': 0.72,
                'probability': 0.72,
                'expected_value': 0.15,
                'odds': 2.10,
                'explanation': '🤖 AI Прогноз: Победа второй команды с вероятностью 72.0%',
                'factors': ['Анализ коэффициентов', 'Домашнее преимущество'],
                'prediction_type': 'MEDIUM_CONFIDENCE',
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'result': 'lost'
            }
        ]
    
    async def get_matches_data(self) -> List[Dict]:
        """Получение данных матчей"""
        try:
            matches = await self.db_manager.get_upcoming_matches(hours=24)
            return [self.match_to_dict(match) for match in matches]
        except Exception as e:
            logger.error(f"Error getting matches: {e}")
            return self.get_sample_matches()
    
    def match_to_dict(self, match) -> Dict:
        """Конвертация Match в Dict"""
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
            'team1_tier': 'T1',  # Будет получено из team stats
            'team2_tier': 'T1',
            'team1_form': 0.8,
            'team2_form': 0.7,
            'h2h_win_rate': 0.5,
            'betting_percentage1': 50,
            'betting_percentage2': 50
        }
    
    def get_sample_matches(self) -> List[Dict]:
        """Получение примеров матчей"""
        return [
            {
                'id': 'match_1',
                'sport': 'cs2',
                'team1': 'NAVI',
                'team2': 'G2',
                'tournament': 'BLAST Premier Spring Final',
                'match_time': (datetime.now() + timedelta(hours=3)).isoformat(),
                'odds1': 1.85,
                'odds2': 1.95,
                'status': 'upcoming',
                'team1_tier': 'T1',
                'team2_tier': 'T1',
                'team1_form': 0.85,
                'team2_form': 0.78,
                'h2h_win_rate': 0.55,
                'betting_percentage1': 52,
                'betting_percentage2': 48
            },
            {
                'id': 'match_2',
                'sport': 'khl',
                'team1': 'ЦСКА Москва',
                'team2': 'СКА Санкт-Петербург',
                'tournament': 'КХЛ Регулярный чемпионат',
                'match_time': (datetime.now() + timedelta(hours=5)).isoformat(),
                'odds1': 2.10,
                'odds2': 1.80,
                'odds_draw': 4.50,
                'status': 'upcoming',
                'team1_tier': 'T1',
                'team2_tier': 'T1',
                'team1_form': 0.82,
                'team2_form': 0.79,
                'h2h_win_rate': 0.51,
                'betting_percentage1': 45,
                'betting_percentage2': 48,
                'betting_percentage_draw': 7
            }
        ]
    
    async def get_live_matches_data(self) -> List[Dict]:
        """Получение live матчей"""
        try:
            matches = await self.db_manager.get_live_matches()
            return [self.match_to_dict(match) for match in matches]
        except Exception as e:
            logger.error(f"Error getting live matches: {e}")
            return self.get_sample_live_matches()
    
    def get_sample_live_matches(self) -> List[Dict]:
        """Получение примеров live матчей"""
        return [
            {
                'id': 'live_1',
                'sport': 'cs2',
                'team1': 'FaZe',
                'team2': 'Vitality',
                'tournament': 'IEM Katowice 2026',
                'status': 'live',
                'score1': 12,
                'score2': 8,
                'live_data': {
                    'current_map': 'Mirage',
                    'live_time': datetime.now().isoformat()
                }
            },
            {
                'id': 'live_2',
                'sport': 'khl',
                'team1': 'Ак Барс Казань',
                'team2': 'Локомотив Ярославль',
                'tournament': 'КХЛ Плей-офф',
                'status': 'live',
                'score1': 2,
                'score2': 1,
                'live_data': {
                    'period': 2,
                    'live_time': datetime.now().isoformat()
                }
            }
        ]
    
    async def get_statistics_data(self) -> Dict:
        """Получение статистики"""
        try:
            stats = await self.db_manager.get_statistics()
            signals = await self.db_manager.get_signals(limit=1000)
            
            cs2_count = len([s for s in signals if s.sport == 'cs2'])
            khl_count = len([s for s in signals if s.sport == 'khl'])
            
            high_conf = len([s for s in signals if s.confidence in ['HIGH', '0.8', '0.9']])
            medium_conf = len([s for s in signals if s.confidence in ['MEDIUM', '0.6', '0.7']])
            low_conf = len([s for s in signals if s.confidence in ['LOW', '0.4', '0.5']])
            
            return {
                'total_signals': stats['total'],
                'successful_signals': stats['wins'],
                'success_rate': stats['accuracy'] / 100,
                'cs2_signals': cs2_count,
                'khl_signals': khl_count,
                'high_confidence': high_conf,
                'medium_confidence': medium_conf,
                'low_confidence': low_conf
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return self.get_sample_statistics()
    
    def get_sample_statistics(self) -> Dict:
        """Получение примеров статистики"""
        return {
            'total_signals': 25,
            'successful_signals': 18,
            'success_rate': 0.72,
            'cs2_signals': 15,
            'khl_signals': 10,
            'high_confidence': 8,
            'medium_confidence': 12,
            'low_confidence': 5
        }
    
    async def get_history_data(self) -> List[Dict]:
        """Получение истории"""
        try:
            signals = await self.db_manager.get_signals(limit=50)
            return [self.signal_to_dict(signal) for signal in signals]
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return self.get_sample_signals()

# Запуск приложения
async def main():
    # Инициализация базы данных
    app_instance = AIBETMiniApp()
    await app_instance.db_manager.initialize()
    
    # Инициализация ML моделей
    await app_instance.ml_models.initialize_models()
    
    port = int(os.environ.get("PORT", 10000))
    
    config = uvicorn.Config(
        app_instance.app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    uvicorn.run("mini_app:main", host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
