// AI BET Telegram Mini App
class AIBetApp {
    constructor() {
        this.telegram = null;
        this.userData = null;
        this.isAdmin = false;
        this.currentScreen = 'main-screen';
        this.apiBase = '/api'; // Будет настроено при деплое
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        try {
            // Инициализация Telegram WebApp SDK
            this.telegram = window.Telegram.WebApp;
            this.telegram.ready();
            
            // Настройка темы
            this.telegram.expand();
            this.telegram.enableClosingConfirmation();
            
            // Получение данных пользователя
            this.userData = this.telegram.initDataUnsafe?.user;
            if (!this.userData) {
                // Для тестирования в браузере
                this.userData = {
                    id: 123456789,
                    first_name: 'Test',
                    last_name: 'User',
                    username: 'testuser'
                };
            }
            
            // Проверка админских прав
            await this.checkAdminStatus();
            
            // Инициализация интерфейса
            this.setupEventListeners();
            this.updateUserInfo();
            this.startAutoRefresh();
            
            // Загрузка начальных данных
            await this.loadInitialData();
            
            console.log('AI BET App initialized successfully');
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('Ошибка инициализации приложения');
        }
    }

    async checkAdminStatus() {
        try {
            const response = await this.apiCall('/auth/check-admin', {
                user_id: this.userData.id
            });
            
            this.isAdmin = response.is_admin;
            
            // Показать/скрыть админскую кнопку
            const adminBtn = document.querySelector('.admin-only');
            if (adminBtn) {
                adminBtn.style.display = this.isAdmin ? 'flex' : 'none';
            }
        } catch (error) {
            console.error('Failed to check admin status:', error);
        }
    }

    setupEventListeners() {
        // Обработка кнопки "назад" в Telegram
        this.telegram.onEvent('backButtonClicked', () => {
            if (this.currentScreen !== 'main-screen') {
                this.showScreen('main-screen');
            } else {
                this.telegram.close();
            }
        });

        // Обработка изменения темы
        this.telegram.onEvent('themeChanged', () => {
            this.applyTheme();
        });

        // Применяем тему при инициализации
        this.applyTheme();
    }

    applyTheme() {
        const theme = this.telegram.themeParams;
        if (theme.bg_color) {
            document.documentElement.style.setProperty('--tg-theme-bg-color', theme.bg_color);
        }
        if (theme.text_color) {
            document.documentElement.style.setProperty('--tg-theme-text-color', theme.text_color);
        }
        if (theme.hint_color) {
            document.documentElement.style.setProperty('--tg-theme-hint-color', theme.hint_color);
        }
        if (theme.link_color) {
            document.documentElement.style.setProperty('--tg-theme-link-color', theme.link_color);
        }
        if (theme.button_color) {
            document.documentElement.style.setProperty('--tg-theme-button-color', theme.button_color);
        }
        if (theme.button_text_color) {
            document.documentElement.style.setProperty('--tg-theme-button-text-color', theme.button_text_color);
        }
    }

    updateUserInfo() {
        const usernameEl = document.getElementById('username');
        if (usernameEl && this.userData) {
            const name = `${this.userData.first_name || ''} ${this.userData.last_name || ''}`.trim();
            usernameEl.textContent = name || this.userData.username || 'Пользователь';
        }
    }

    showScreen(screenId) {
        // Скрыть все экраны
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        
        // Показать выбранный экран
        const targetScreen = document.getElementById(screenId);
        if (targetScreen) {
            targetScreen.classList.add('active');
            this.currentScreen = screenId;
            
            // Показать/скрыть кнопку "назад"
            if (screenId === 'main-screen') {
                this.telegram.BackButton.hide();
            } else {
                this.telegram.BackButton.show();
            }
            
            // Загрузить данные для экрана
            this.loadScreenData(screenId);
        }
    }

    async loadScreenData(screenId) {
        switch (screenId) {
            case 'cs2-screen':
                await this.loadCS2Data();
                break;
            case 'khl-screen':
                await this.loadKHLData();
                break;
            case 'live-screen':
                await this.loadLiveData();
                break;
            case 'prematch-screen':
                await this.loadPrematchData();
                break;
            case 'history-screen':
                await this.loadHistory();
                break;
            case 'stats-screen':
                await this.loadStats();
                break;
            case 'confidence-screen':
                await this.loadConfidence();
                break;
            case 'status-screen':
                await this.loadStatus();
                break;
            case 'admin-screen':
                await this.loadAdminData();
                break;
        }
    }

    async loadInitialData() {
        await Promise.all([
            this.loadLiveData(),
            this.loadHistory()
        ]);
    }

    async apiCall(endpoint, data = null, method = 'GET') {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-Telegram-User-ID': this.userData.id,
                    'X-Telegram-Init-Data': this.telegram.initData
                }
            };
            
            if (data && method !== 'GET') {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(`${this.apiBase}${endpoint}`, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API call failed for ${endpoint}:`, error);
            throw error;
        }
    }

    async loadCS2Data() {
        try {
            this.showLoading('cs2-matches');
            const data = await this.apiCall('/cs2/matches');
            this.renderCS2Matches(data);
            this.updateLastUpdateTime();
        } catch (error) {
            this.showError('Ошибка загрузки данных CS2', 'cs2-matches');
        }
    }

    async loadKHLData() {
        try {
            this.showLoading('khl-matches');
            const data = await this.apiCall('/khl/matches');
            this.renderKHLMatches(data);
            this.updateLastUpdateTime();
        } catch (error) {
            this.showError('Ошибка загрузки данных КХЛ', 'khl-matches');
        }
    }

    async loadLiveData() {
        try {
            const data = await this.apiCall('/live/matches');
            this.renderLiveMatches(data);
            this.updateLiveStats(data);
        } catch (error) {
            console.error('Failed to load live data:', error);
        }
    }

    async loadPrematchData() {
        try {
            const hours = document.querySelector('.time-btn.active')?.dataset.hours || 3;
            this.showLoading('prematch-matches');
            const data = await this.apiCall(`/prematch/matches?hours=${hours}`);
            this.renderPrematchMatches(data);
            this.updateLastUpdateTime();
        } catch (error) {
            this.showError('Ошибка загрузки предматчевых данных', 'prematch-matches');
        }
    }

    async loadHistory() {
        try {
            this.showLoading('history-list');
            const data = await this.apiCall('/history/signals');
            this.renderHistory(data);
            this.updateHistoryStats(data);
        } catch (error) {
            this.showError('Ошибка загрузки истории', 'history-list');
        }
    }

    async loadStats() {
        try {
            const activeTab = document.querySelector('.tab-btn.active')?.dataset.tab || 'cs2';
            this.showLoading('stats-content');
            const data = await this.apiCall(`/stats/${activeTab}`);
            this.renderStats(data);
            this.updateLastUpdateTime();
        } catch (error) {
            this.showError('Ошибка загрузки статистики', 'stats-content');
        }
    }

    async loadConfidence() {
        try {
            this.showLoading('confidence-list');
            const data = await this.apiCall('/confidence/ratings');
            this.renderConfidence(data);
            this.updateLastUpdateTime();
        } catch (error) {
            this.showError('Ошибка загрузки рейтингов уверенности', 'confidence-list');
        }
    }

    async loadStatus() {
        try {
            const data = await this.apiCall('/system/status');
            this.renderSystemStatus(data);
            this.updateLastUpdateTime();
        } catch (error) {
            this.showError('Ошибка загрузки статуса системы');
        }
    }

    async loadAdminData() {
        if (!this.isAdmin) {
            this.showError('Доступ запрещен');
            return;
        }
        
        try {
            const data = await this.apiCall('/admin/dashboard');
            this.renderAdminDashboard(data);
        } catch (error) {
            this.showError('Ошибка загрузки админ панели');
        }
    }

    renderCS2Matches(matches) {
        const container = document.getElementById('cs2-matches');
        if (!container) return;
        
        if (!matches || matches.length === 0) {
            container.innerHTML = '<div class="loading">Нет доступных матчей CS2</div>';
            return;
        }
        
        container.innerHTML = matches.map(match => this.renderMatchCard(match, 'cs2')).join('');
    }

    renderKHLMatches(matches) {
        const container = document.getElementById('khl-matches');
        if (!container) return;
        
        if (!matches || matches.length === 0) {
            container.innerHTML = '<div class="loading">Нет доступных матчей КХЛ</div>';
            return;
        }
        
        container.innerHTML = matches.map(match => this.renderMatchCard(match, 'khl')).join('');
    }

    renderMatchCard(match, sport) {
        const confidenceClass = this.getConfidenceClass(match.confidence);
        const confidenceBadge = this.getConfidenceBadge(match.confidence);
        
        return `
            <div class="match-card ${confidenceClass}">
                <div class="match-header">
                    <div class="match-teams">${match.team1} vs ${match.team2}</div>
                    <div class="match-time">${new Date(match.time).toLocaleString('ru-RU')}</div>
                </div>
                <div class="match-tournament">${match.tournament}</div>
                <div class="match-odds">
                    <div class="odds-item">${match.team1}: ${match.odds1}</div>
                    <div class="odds-item">${match.team2}: ${match.odds2}</div>
                </div>
                ${match.scenario ? `
                    <div class="match-scenario">
                        <div class="scenario-name">${match.scenario.name}</div>
                        <div class="scenario-description">${match.scenario.description}</div>
                    </div>
                ` : ''}
                <div class="match-actions">
                    <span class="confidence-badge ${confidenceClass}">${confidenceBadge}</span>
                    <button class="action-btn primary" onclick="app.viewMatchDetails('${match.id}', '${sport}')">
                        Подробнее
                    </button>
                    <button class="action-btn secondary" onclick="app.shareMatch('${match.id}', '${sport}')">
                        Поделиться
                    </button>
                </div>
            </div>
        `;
    }

    renderLiveMatches(data) {
        const container = document.getElementById('live-matches');
        if (!container) return;
        
        const allMatches = [...(data.cs2 || []), ...(data.khl || [])];
        
        if (allMatches.length === 0) {
            container.innerHTML = '<div class="loading">Нет live матчей</div>';
            return;
        }
        
        container.innerHTML = allMatches.map(match => `
            <div class="match-card live-match">
                <div class="match-header">
                    <div class="match-teams">${match.team1} vs ${match.team2}</div>
                    <div class="live-indicator">🔴 LIVE</div>
                </div>
                <div class="live-score">${match.score}</div>
                <div class="match-tournament">${match.tournament}</div>
                ${match.scenario ? `
                    <div class="match-scenario">
                        <div class="scenario-name">${match.scenario.name}</div>
                        <div class="scenario-description">${match.scenario.description}</div>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    renderPrematchMatches(matches) {
        const container = document.getElementById('prematch-matches');
        if (!container) return;
        
        if (!matches || matches.length === 0) {
            container.innerHTML = '<div class="loading">Нет предматчевых данных</div>';
            return;
        }
        
        container.innerHTML = matches.map(match => this.renderMatchCard(match, match.sport)).join('');
    }

    renderHistory(signals) {
        const container = document.getElementById('history-list');
        if (!container) return;
        
        if (!signals || signals.length === 0) {
            container.innerHTML = '<div class="loading">Нет истории сигналов</div>';
            return;
        }
        
        container.innerHTML = signals.map(signal => `
            <div class="history-item ${signal.result}">
                <div class="history-header">
                    <div class="history-match">${signal.match}</div>
                    <div class="history-result ${signal.result}">${signal.result === 'success' ? '✅ Успешно' : '❌ Неудачно'}</div>
                </div>
                <div class="history-details">
                    <div>Сценарий: ${signal.scenario}</div>
                    <div>Уверенность: ${signal.confidence}%</div>
                    <div>Дата: ${new Date(signal.date).toLocaleString('ru-RU')}</div>
                </div>
            </div>
        `).join('');
    }

    renderStats(stats) {
        const container = document.getElementById('stats-content');
        if (!container) return;
        
        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">Всего анализов</div>
                    <div class="stat-value">${stats.total_analyses || 0}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Точность прогнозов</div>
                    <div class="stat-value">${stats.accuracy || 0}%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Успешных сценариев</div>
                    <div class="stat-value">${stats.successful_scenarios || 0}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Средняя уверенность</div>
                    <div class="stat-value">${stats.avg_confidence || 0}%</div>
                </div>
            </div>
            <div class="scenarios-stats">
                <h3>Статистика сценариев</h3>
                ${stats.scenarios ? Object.entries(stats.scenarios).map(([scenario, data]) => `
                    <div class="scenario-stat">
                        <div class="scenario-name">${scenario}</div>
                        <div class="scenario-metrics">
                            <span>Успешность: ${data.success_rate}%</span>
                            <span>Количество: ${data.count}</span>
                        </div>
                    </div>
                `).join('') : ''}
            </div>
        `;
    }

    renderConfidence(ratings) {
        const container = document.getElementById('confidence-list');
        if (!container) return;
        
        if (!ratings || ratings.length === 0) {
            container.innerHTML = '<div class="loading">Нет данных об уверенности</div>';
            return;
        }
        
        container.innerHTML = ratings.map(rating => {
            const confidenceClass = this.getConfidenceClass(rating.confidence);
            const confidenceBadge = this.getConfidenceBadge(rating.confidence);
            
            return `
                <div class="confidence-item">
                    <div class="confidence-header">
                        <div class="confidence-match">${rating.match}</div>
                        <div class="confidence-level ${confidenceClass}">${confidenceBadge}</div>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill ${confidenceClass}" style="width: ${rating.confidence}%"></div>
                    </div>
                    <div class="confidence-details">
                        <div>Сценарий: ${rating.scenario}</div>
                        <div>ML вероятность: ${rating.ml_probability}%</div>
                        <div>Факторы: ${rating.factors?.join(', ') || 'Нет данных'}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderSystemStatus(status) {
        // Обновление статусов компонентов
        this.updateStatusItem('backend-status', status.backend?.status || 'offline');
        this.updateStatusItem('cs2-parser-status', status.parsers?.cs2?.status || 'offline');
        this.updateStatusItem('khl-parser-status', status.parsers?.khl?.status || 'offline');
        this.updateStatusItem('ml-status', status.ml?.status || 'offline');
        this.updateStatusItem('telegram-status', status.telegram?.status || 'offline');
        
        // Детальная информация
        const detailsContainer = document.getElementById('system-details');
        if (detailsContainer) {
            detailsContainer.innerHTML = `
                <div class="system-detail">
                    <strong>Версия:</strong> ${status.version || 'N/A'}
                </div>
                <div class="system-detail">
                    <strong>Uptime:</strong> ${status.uptime || 'N/A'}
                </div>
                <div class="system-detail">
                    <strong>Последнее обновление:</strong> ${status.last_update ? new Date(status.last_update).toLocaleString('ru-RU') : 'N/A'}
                </div>
                <div class="system-detail">
                    <strong>Активные задачи:</strong> ${status.active_tasks || 0}
                </div>
                <div class="system-detail">
                    <strong>Обработано матчей:</strong> ${status.processed_matches || 0}
                </div>
            `;
        }
    }

    renderAdminDashboard(data) {
        const logContainer = document.getElementById('admin-log-content');
        if (logContainer && data.logs) {
            logContainer.textContent = data.logs.join('\n');
        }
    }

    updateStatusItem(elementId, status) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = status === 'online' ? '🟢 Онлайн' : 
                                  status === 'offline' ? '🔴 Офлайн' : 
                                  '🟡 Предупреждение';
            element.className = `status-value ${status}`;
        }
    }

    updateLiveStats(data) {
        const cs2Count = document.getElementById('live-cs2-count');
        const khlCount = document.getElementById('live-khl-count');
        
        if (cs2Count) cs2Count.textContent = data.cs2?.length || 0;
        if (khlCount) khlCount.textContent = data.khl?.length || 0;
    }

    updateHistoryStats(data) {
        const totalSignals = document.getElementById('total-signals');
        const successRate = document.getElementById('success-rate');
        const currentStreak = document.getElementById('current-streak');
        
        if (totalSignals) totalSignals.textContent = data.length || 0;
        
        if (successRate && data.length > 0) {
            const successful = data.filter(s => s.result === 'success').length;
            const rate = Math.round((successful / data.length) * 100);
            successRate.textContent = `${rate}%`;
        }
        
        if (currentStreak) {
            currentStreak.textContent = this.calculateStreak(data);
        }
    }

    calculateStreak(signals) {
        if (!signals || signals.length === 0) return 0;
        
        let streak = 0;
        for (let i = signals.length - 1; i >= 0; i--) {
            if (signals[i].result === 'success') {
                streak++;
            } else {
                break;
            }
        }
        return streak;
    }

    getConfidenceClass(confidence) {
        if (confidence >= 80) return 'high-confidence';
        if (confidence >= 50) return 'medium-confidence';
        return 'low-confidence';
    }

    getConfidenceBadge(confidence) {
        if (confidence >= 80) return 'ВЫСОКАЯ';
        if (confidence >= 50) return 'СРЕДНЯЯ';
        return 'НИЗКАЯ';
    }

    showLoading(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<div class="loading">Загрузка...</div>';
        }
    }

    showError(message, containerId = null) {
        if (containerId) {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = `<div class="error">${message}</div>`;
            }
        } else {
            // Показать toast или alert
            this.telegram.showAlert(message);
        }
    }

    showSuccess(message) {
        this.telegram.showAlert(message);
    }

    updateLastUpdateTime() {
        const lastUpdateEl = document.getElementById('last-update');
        if (lastUpdateEl) {
            lastUpdateEl.textContent = `Обновлено: ${new Date().toLocaleTimeString('ru-RU')}`;
        }
    }

    startAutoRefresh() {
        // Обновление каждые 30 секунд
        this.refreshInterval = setInterval(() => {
            if (this.currentScreen !== 'main-screen') {
                this.loadScreenData(this.currentScreen);
            }
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // Публичные методы для вызова из HTML
    async viewMatchDetails(matchId, sport) {
        try {
            const details = await this.apiCall(`/${sport}/match/${matchId}`);
            // Показать детали матча в модальном окне
            this.showMatchDetailsModal(details);
        } catch (error) {
            this.showError('Ошибка загрузки деталей матча');
        }
    }

    async shareMatch(matchId, sport) {
        try {
            const match = await this.apiCall(`/${sport}/match/${matchId}`);
            const shareText = `AI BET Analytics: ${match.team1} vs ${match.team2}\nСценарий: ${match.scenario?.name}\nУверенность: ${match.confidence}%`;
            
            if (this.telegram.shareURL) {
                this.telegram.shareURL(shareText);
            } else {
                navigator.clipboard.writeText(shareText);
                this.showSuccess('Ссылка скопирована в буфер обмена');
            }
        } catch (error) {
            this.showError('Ошибка при поделении матчем');
        }
    }

    async adminAction(action) {
        if (!this.isAdmin) {
            this.showError('Доступ запрещен');
            return;
        }
        
        try {
            const result = await this.apiCall('/admin/action', { action }, 'POST');
            this.showSuccess(`Действие "${action}" выполнено успешно`);
            
            // Перезагрузить данные админ панели
            if (this.currentScreen === 'admin-screen') {
                await this.loadAdminData();
            }
        } catch (error) {
            this.showError(`Ошибка выполнения действия "${action}"`);
        }
    }

    showMatchDetailsModal(match) {
        // Реализация модального окна с деталями матча
        const modalHtml = `
            <div class="modal">
                <div class="modal-content">
                    <h3>${match.team1} vs ${match.team2}</h3>
                    <p><strong>Турнир:</strong> ${match.tournament}</p>
                    <p><strong>Время:</strong> ${new Date(match.time).toLocaleString('ru-RU')}</p>
                    <p><strong>Коэффициенты:</strong> ${match.team1}: ${match.odds1}, ${match.team2}: ${match.odds2}</p>
                    ${match.scenario ? `
                        <p><strong>Сценарий:</strong> ${match.scenario.name}</p>
                        <p>${match.scenario.description}</p>
                    ` : ''}
                    <p><strong>Уверенность:</strong> ${match.confidence}%</p>
                    <button onclick="this.closest('.modal').remove()">Закрыть</button>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }
}

// Глобальные функции для вызова из HTML
let app;

function showScreen(screenId) {
    app.showScreen(screenId);
}

async function refreshCS2Data() {
    await app.loadCS2Data();
}

async function refreshKHLData() {
    await app.loadKHLData();
}

async function refreshLiveData() {
    await app.loadLiveData();
}

async function refreshPrematchData() {
    await app.loadPrematchData();
}

async function refreshHistory() {
    await app.loadHistory();
}

async function refreshStats() {
    await app.loadStats();
}

async function refreshConfidence() {
    await app.loadConfidence();
}

async function refreshStatus() {
    await app.loadStatus();
}

async function adminAction(action) {
    await app.adminAction(action);
}

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    app = new AIBetApp();
    
    // Обработка вкладок статистики
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('tab-btn')) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            app.loadStats();
        }
    });
    
    // Обработка кнопок времени для предматчей
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('time-btn')) {
            document.querySelectorAll('.time-btn').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            app.loadPrematchData();
        }
    });
    
    // Обработка фильтров
    document.addEventListener('change', (e) => {
        if (e.target.id.includes('filter')) {
            // Применить фильтры
            if (app.currentScreen === 'cs2-screen') {
                app.loadCS2Data();
            } else if (app.currentScreen === 'khl-screen') {
                app.loadKHLData();
            }
        }
    });
});

// Очистка при закрытии приложения
window.addEventListener('beforeunload', () => {
    if (app) {
        app.stopAutoRefresh();
    }
});
