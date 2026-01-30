// AI BET Telegram Mini App
class AIBetApp {
    constructor() {
        this.telegram = null;
        this.userData = null;
        this.isAdmin = false;
        this.currentScreen = 'main-screen';
        this.apiBase = '/api'; // Будет настроено при деплое
        this.refreshInterval = null;
        this.wsConnection = null;
        this.currentFilters = {
            cs2: { tournament: 'all', confidence: 'all' },
            khl: { tournament: 'all', confidence: 'all' }
        };
        this.currentTab = {
            cs2: 'matches',
            khl: 'matches'
        };
        this.currentStatsTab = 'overview';
        this.currentTimeFilter = 3;
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
            
            // Скрываем экран загрузки
            this.hideLoadingScreen();
            
            console.log('AI BET App initialized successfully');
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('Ошибка инициализации приложения');
        }
    }

    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        const mainScreen = document.getElementById('main-screen');
        
        if (loadingScreen) {
            loadingScreen.classList.remove('active');
        }
        if (mainScreen) {
            mainScreen.classList.add('active');
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
            case 'main-screen':
                await this.loadMainData();
                break;
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
            this.loadMainData(),
            this.loadLiveData()
        ]);
    }

    async loadMainData() {
        try {
            const stats = await this.apiCall('/stats/general');
            
            // Обновляем быстрые статистики
            document.getElementById('total-signals').textContent = stats.total_signals || 0;
            document.getElementById('accuracy').textContent = `${(stats.accuracy || 0).toFixed(1)}%`;
            document.getElementById('active-analyses').textContent = stats.active_analyses || 0;
            
            // Обновляем счетчики на кнопках
            document.getElementById('cs2-count').textContent = stats.cs2_matches || 0;
            document.getElementById('khl-count').textContent = stats.khl_matches || 0;
            document.getElementById('live-count').textContent = stats.live_matches || 0;
            
        } catch (error) {
            console.error('Error loading main data:', error);
        }
    }

    async loadCS2Data() {
        try {
            const tab = this.currentTab.cs2;
            
            if (tab === 'matches') {
                await this.loadCS2Matches();
            } else if (tab === 'signals') {
                await this.loadCS2Signals();
            } else if (tab === 'analytics') {
                await this.loadCS2Analytics();
            }
        } catch (error) {
            console.error('Error loading CS2 data:', error);
            this.showError('Ошибка загрузки данных CS2');
        }
    }

    async loadCS2Matches() {
        try {
            this.showLoading('cs2-matches');
            const data = await this.apiCall('/cs2/matches', this.currentFilters.cs2);
            this.renderMatches(data, 'cs2-matches');
        } catch (error) {
            this.showError('Ошибка загрузки матчей CS2', 'cs2-matches');
        }
    }

    async loadCS2Signals() {
        try {
            this.showLoading('cs2-matches');
            const data = await this.apiCall('/cs2/signals', this.currentFilters.cs2);
            this.renderSignals(data, 'cs2-matches');
        } catch (error) {
            this.showError('Ошибка загрузки сигналов CS2', 'cs2-matches');
        }
    }

    async loadCS2Analytics() {
        try {
            this.showLoading('cs2-matches');
            const data = await this.apiCall('/cs2/analytics');
            this.renderAnalytics(data, 'cs2-matches');
        } catch (error) {
            this.showError('Ошибка загрузки аналитики CS2', 'cs2-matches');
        }
    }

    async loadKHLData() {
        try {
            const tab = this.currentTab.khl;
            
            if (tab === 'matches') {
                await this.loadKHLMatches();
            } else if (tab === 'signals') {
                await this.loadKHLSignals();
            } else if (tab === 'analytics') {
                await this.loadKHLAnalytics();
            }
        } catch (error) {
            console.error('Error loading KHL data:', error);
            this.showError('Ошибка загрузки данных КХЛ');
        }
    }

    async loadKHLMatches() {
        try {
            this.showLoading('khl-matches');
            const data = await this.apiCall('/khl/matches', this.currentFilters.khl);
            this.renderMatches(data, 'khl-matches');
        } catch (error) {
            this.showError('Ошибка загрузки матчей КХЛ', 'khl-matches');
        }
    }

    async loadKHLSignals() {
        try {
            this.showLoading('khl-matches');
            const data = await this.apiCall('/khl/signals', this.currentFilters.khl);
            this.renderSignals(data, 'khl-matches');
        } catch (error) {
            this.showError('Ошибка загрузки сигналов КХЛ', 'khl-matches');
        }
    }

    async loadKHLAnalytics() {
        try {
            this.showLoading('khl-matches');
            const data = await this.apiCall('/khl/analytics');
            this.renderAnalytics(data, 'khl-matches');
        } catch (error) {
            this.showError('Ошибка загрузки аналитики КХЛ', 'khl-matches');
        }
    }

    async loadLiveData() {
        try {
            const data = await this.apiCall('/live/matches');
            this.renderLiveMatches(data);
            this.updateLiveStats(data);
        } catch (error) {
            console.error('Error loading live data:', error);
        }
    }

    async loadPrematchData() {
        try {
            this.showLoading('prematch-matches');
            const data = await this.apiCall(`/prematch/matches?hours=${this.currentTimeFilter}`);
            this.renderMatches(data, 'prematch-matches');
        } catch (error) {
            this.showError('Ошибка загрузки предматчевых данных', 'prematch-matches');
        }
    }

    async loadHistory() {
        try {
            this.showLoading('history-list');
            const sportFilter = document.getElementById('history-sport-filter')?.value || 'all';
            const resultFilter = document.getElementById('history-result-filter')?.value || 'all';
            
            const data = await this.apiCall('/history/signals', {
                sport: sportFilter,
                result: resultFilter
            });
            
            this.renderHistory(data);
            this.updateHistoryStats(data);
        } catch (error) {
            this.showError('Ошибка загрузки истории', 'history-list');
        }
    }

    async loadStats() {
        try {
            this.showLoading('stats-content');
            
            let endpoint = '/stats/overview';
            if (this.currentStatsTab === 'cs2') {
                endpoint = '/stats/cs2';
            } else if (this.currentStatsTab === 'khl') {
                endpoint = '/stats/khl';
            } else if (this.currentStatsTab === 'scenarios') {
                endpoint = '/stats/scenarios';
            }
            
            const data = await this.apiCall(endpoint);
            this.renderStats(data);
        } catch (error) {
            this.showError('Ошибка загрузки статистики', 'stats-content');
        }
    }

    async loadConfidence() {
        try {
            this.showLoading('confidence-list');
            const data = await this.apiCall('/confidence/ratings');
            this.renderConfidence(data);
        } catch (error) {
            this.showError('Ошибка загрузки рейтингов уверенности', 'confidence-list');
        }
    }

    async loadStatus() {
        try {
            const data = await this.apiCall('/system/status');
            this.renderSystemStatus(data);
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

    // Методы отрисовки
    renderMatches(matches, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        if (!matches || matches.length === 0) {
            container.innerHTML = '<div class="loading">Нет доступных матчей</div>';
            return;
        }
        
        container.innerHTML = matches.map(match => this.renderMatchCard(match)).join('');
    }

    renderMatchCard(match) {
        const confidenceClass = match.confidence ? match.confidence.toLowerCase() : '';
        const confidenceBadge = match.confidence || 'MEDIUM';
        const sportClass = match.sport || '';
        
        return `
            <div class="match-card ${sportClass} ${confidenceClass}">
                <div class="match-header">
                    <div class="match-teams">${match.team1} vs ${match.team2}</div>
                    <div class="match-time">${new Date(match.match_time).toLocaleString('ru-RU')}</div>
                </div>
                <div class="match-tournament">${match.tournament}</div>
                ${match.score1 !== undefined && match.score2 !== undefined ? 
                    `<div class="match-score">${match.score1} - ${match.score2}</div>` : ''}
                <div class="match-odds">
                    <div class="odds-item">${match.team1}: ${match.odds1}</div>
                    <div class="odds-item">${match.team2}: ${match.odds2}</div>
                    ${match.odds_draw ? `<div class="odds-item">Ничья: ${match.odds_draw}</div>` : ''}
                </div>
                ${match.scenario ? `
                    <div class="match-scenario">
                        <div class="scenario-name">${match.scenario}</div>
                        <div class="scenario-description">${match.explanation || 'Нет описания'}</div>
                    </div>
                ` : ''}
                <div class="match-actions">
                    ${match.confidence ? `<span class="confidence-badge ${confidenceClass}">${confidenceBadge}</span>` : ''}
                    <button class="action-btn primary" onclick="app.viewMatchDetails('${match.id}')">
                        Подробнее
                    </button>
                    <button class="action-btn secondary" onclick="app.shareMatch('${match.id}')">
                        Поделиться
                    </button>
                </div>
            </div>
        `;
    }

    renderSignals(signals, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        if (!signals || signals.length === 0) {
            container.innerHTML = '<div class="loading">Нет доступных сигналов</div>';
            return;
        }
        
        container.innerHTML = signals.map(signal => this.renderSignalCard(signal)).join('');
    }

    renderSignalCard(signal) {
        const confidenceClass = signal.confidence.toLowerCase();
        const resultEmoji = {
            'win': '✅',
            'lose': '❌',
            'pending': '⏳'
        }[signal.result] || '⏳';
        
        return `
            <div class="match-card ${confidenceClass}">
                <div class="match-header">
                    <div class="match-teams">${signal.match}</div>
                    <div class="match-time">${resultEmoji} ${signal.result || 'pending'}</div>
                </div>
                <div class="match-tournament">${signal.tournament}</div>
                <div class="match-scenario">
                    <div class="scenario-name">${signal.scenario}</div>
                    <div class="scenario-description">${signal.explanation}</div>
                </div>
                <div class="match-odds">
                    <div class="odds-item">Коэффициент: ${signal.odds_at_signal}</div>
                    <div class="odds-item">Вероятность: ${(signal.probability * 100).toFixed(1)}%</div>
                </div>
                <div class="match-actions">
                    <span class="confidence-badge ${confidenceClass}">${signal.confidence}</span>
                    <button class="action-btn primary" onclick="app.viewSignalDetails('${signal.id}')">
                        Подробнее
                    </button>
                </div>
            </div>
        `;
    }

    renderAnalytics(analytics, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        let html = '<div class="analytics-container">';
        
        if (analytics.stats) {
            html += '<div class="analytics-section">';
            html += '<h3>Статистика</h3>';
            html += `<p>Всего анализов: ${analytics.stats.total_analyses}</p>`;
            html += `<p>Точность: ${analytics.stats.accuracy?.toFixed(1)}%</p>`;
            html += `<p>Успешных сценариев: ${analytics.stats.successful_scenarios}</p>`;
            html += '</div>';
        }
        
        if (analytics.scenarios) {
            html += '<div class="analytics-section">';
            html += '<h3>Сценарии</h3>';
            Object.entries(analytics.scenarios).forEach(([scenario, data]) => {
                html += `<div class="scenario-stat">`;
                html += `<strong>${scenario}:</strong> ${data.success_rate?.toFixed(1)}% (${data.count} случаев)`;
                html += `</div>`;
            });
            html += '</div>';
        }
        
        html += '</div>';
        container.innerHTML = html;
    }

    renderLiveMatches(data) {
        const container = document.getElementById('live-matches');
        if (!container) return;
        
        const allMatches = [...(data.cs2 || []), ...(data.khl || [])];
        
        if (allMatches.length === 0) {
            container.innerHTML = '<div class="loading">Нет live матчей</div>';
            return;
        }
        
        container.innerHTML = allMatches.map(match => {
            const sportClass = match.sport || '';
            return `
                <div class="match-card live-match ${sportClass}">
                    <div class="match-header">
                        <div class="match-teams">${match.team1} vs ${match.team2}</div>
                        <div class="match-time">🔴 LIVE</div>
                    </div>
                    <div class="match-score">${match.score1} - ${match.score2}</div>
                    <div class="match-tournament">${match.tournament}</div>
                    ${match.scenario ? `
                        <div class="match-scenario">
                            <div class="scenario-name">${match.scenario}</div>
                            <div class="scenario-description">${match.explanation}</div>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    renderHistory(signals) {
        const container = document.getElementById('history-list');
        if (!container) return;
        
        if (!signals || signals.length === 0) {
            container.innerHTML = '<div class="loading">Нет истории сигналов</div>';
            return;
        }
        
        container.innerHTML = signals.map(signal => {
            const resultClass = signal.result || 'pending';
            const resultEmoji = {
                'win': '✅',
                'lose': '❌',
                'pending': '⏳'
            }[signal.result] || '⏳';
            
            return `
                <div class="history-item ${resultClass}">
                    <div class="history-header">
                        <div class="history-match">${signal.match}</div>
                        <div class="history-result ${resultClass}">${resultEmoji} ${signal.result || 'pending'}</div>
                    </div>
                    <div class="history-details">
                        <div>Сценарий: ${signal.scenario}</div>
                        <div>Уверенность: ${signal.confidence}</div>
                        <div>Вероятность: ${(signal.probability * 100).toFixed(1)}%</div>
                        <div>Дата: ${new Date(signal.published_at).toLocaleString('ru-RU')}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderStats(stats) {
        const container = document.getElementById('stats-content');
        if (!container) return;
        
        let html = '<div class="stats-grid">';
        
        if (this.currentStatsTab === 'overview') {
            html += `
                <div class="stat-item">
                    <div class="stat-label">Всего сигналов</div>
                    <div class="stat-value">${stats.total_signals || 0}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Общая точность</div>
                    <div class="stat-value">${(stats.overall_accuracy || 0).toFixed(1)}%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">CS2 точность</div>
                    <div class="stat-value">${(stats.cs2_accuracy || 0).toFixed(1)}%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">КХЛ точность</div>
                    <div class="stat-value">${(stats.khl_accuracy || 0).toFixed(1)}%</div>
                </div>
            `;
        } else {
            Object.entries(stats).forEach(([key, value]) => {
                if (typeof value === 'number') {
                    html += `
                        <div class="stat-item">
                            <div class="stat-label">${key}</div>
                            <div class="stat-value">${value}</div>
                        </div>
                    `;
                }
            });
        }
        
        html += '</div>';
        container.innerHTML = html;
    }

    renderConfidence(ratings) {
        const container = document.getElementById('confidence-list');
        if (!container) return;
        
        if (!ratings || ratings.length === 0) {
            container.innerHTML = '<div class="loading">Нет данных об уверенности</div>';
            return;
        }
        
        container.innerHTML = ratings.map(rating => {
            const confidenceClass = rating.confidence.toLowerCase();
            const confidenceLevel = {
                'HIGH': 'ВЫСОКАЯ',
                'MEDIUM': 'СРЕДНЯЯ',
                'LOW': 'НИЗКАЯ'
            }[rating.confidence] || rating.confidence;
            
            return `
                <div class="confidence-item">
                    <div class="confidence-header">
                        <div class="confidence-match">${rating.match}</div>
                        <div class="confidence-level ${confidenceClass}">${confidenceLevel}</div>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill ${confidenceClass}" style="width: ${rating.confidence_percentage || 0}%"></div>
                    </div>
                    <div class="confidence-details">
                        <div>Сценарий: ${rating.scenario}</div>
                        <div>ML вероятность: ${(rating.ml_probability * 100).toFixed(1)}%</div>
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
        this.updateStatusItem('cs2-ml-status', status.ml?.cs2?.status || 'offline');
        this.updateStatusItem('khl-ml-status', status.ml?.khl?.status || 'offline');
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
        const totalSignals = document.getElementById('history-total');
        const accuracy = document.getElementById('history-accuracy');
        const streak = document.getElementById('history-streak');
        
        if (totalSignals) totalSignals.textContent = data.length || 0;
        
        if (accuracy && data.length > 0) {
            const successful = data.filter(s => s.result === 'win').length;
            const resolved = data.filter(s => s.result && s.result !== 'pending').length;
            const rate = resolved > 0 ? (successful / resolved * 100) : 0;
            accuracy.textContent = `${rate.toFixed(1)}%`;
        }
        
        if (streak) {
            streak.textContent = this.calculateStreak(data);
        }
    }

    calculateStreak(signals) {
        if (!signals || signals.length === 0) return 0;
        
        let streak = 0;
        for (let i = signals.length - 1; i >= 0; i--) {
            if (signals[i].result === 'win') {
                streak++;
            } else if (signals[i].result === 'lose') {
                break;
            }
        }
        return streak;
    }

    // API методы
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
            } else if (data && method === 'GET') {
                const params = new URLSearchParams(data);
                endpoint += `?${params.toString()}`;
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

    // Публичные методы для вызова из HTML
    async viewMatchDetails(matchId) {
        try {
            const details = await this.apiCall(`/matches/${matchId}`);
            this.showMatchDetailsModal(details);
        } catch (error) {
            this.showError('Ошибка загрузки деталей матча');
        }
    }

    async viewSignalDetails(signalId) {
        try {
            const details = await this.apiCall(`/signals/${signalId}`);
            this.showSignalDetailsModal(details);
        } catch (error) {
            this.showError('Ошибка загрузки деталей сигнала');
        }
    }

    async shareMatch(matchId) {
        try {
            const match = await this.apiCall(`/matches/${matchId}`);
            const shareText = `AI BET Analytics: ${match.team1} vs ${match.team2}\nСценарий: ${match.scenario}\nУверенность: ${match.confidence}`;
            
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
        const modal = document.getElementById('modal');
        const title = document.getElementById('modal-title');
        const body = document.getElementById('modal-body');
        
        title.textContent = `${match.team1} vs ${match.team2}`;
        body.innerHTML = `
            <div class="match-details">
                <p><strong>Турнир:</strong> ${match.tournament}</p>
                <p><strong>Время:</strong> ${new Date(match.match_time).toLocaleString('ru-RU')}</p>
                <p><strong>Коэффициенты:</strong> ${match.team1}: ${match.odds1}, ${match.team2}: ${match.odds2}</p>
                ${match.scenario ? `
                    <p><strong>Сценарий:</strong> ${match.scenario}</p>
                    <p>${match.explanation}</p>
                ` : ''}
                <p><strong>Уверенность:</strong> ${match.confidence}</p>
            </div>
        `;
        
        modal.classList.add('active');
    }

    showSignalDetailsModal(signal) {
        const modal = document.getElementById('modal');
        const title = document.getElementById('modal-title');
        const body = document.getElementById('modal-body');
        
        title.textContent = `Сигнал: ${signal.scenario}`;
        body.innerHTML = `
            <div class="signal-details">
                <p><strong>Матч:</strong> ${signal.match}</p>
                <p><strong>Сценарий:</strong> ${signal.scenario}</p>
                <p><strong>Уверенность:</strong> ${signal.confidence}</p>
                <p><strong>Вероятность:</strong> ${(signal.probability * 100).toFixed(1)}%</p>
                <p><strong>Коэффициент:</strong> ${signal.odds_at_signal}</p>
                <p><strong>Объяснение:</strong> ${signal.explanation}</p>
                <p><strong>Факторы:</strong> ${signal.factors?.join(', ') || 'Нет данных'}</p>
                <p><strong>Результат:</strong> ${signal.result || 'Ожидание'}</p>
                <p><strong>Дата:</strong> ${new Date(signal.published_at).toLocaleString('ru-RU')}</p>
            </div>
        `;
        
        modal.classList.add('active');
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
}

// Глобальные функции для вызова из HTML
let app;

function showScreen(screenId) {
    app.showScreen(screenId);
}

function switchTab(sport, tab) {
    app.currentTab[sport] = tab;
    
    // Обновляем активную кнопку
    const container = document.getElementById(`${sport}-content`);
    const buttons = container.parentElement.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Загружаем данные для вкладки
    app.loadScreenData(`${sport}-screen`);
}

function switchStatsTab(tab) {
    app.currentStatsTab = tab;
    
    // Обновляем активную кнопку
    const buttons = document.querySelectorAll('.stats-tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Загружаем статистику
    app.loadStats();
}

function applyFilters(sport) {
    const tournamentFilter = document.getElementById(`${sport}-tournament-filter`).value;
    const confidenceFilter = document.getElementById(`${sport}-confidence-filter`).value;
    
    app.currentFilters[sport] = {
        tournament: tournamentFilter,
        confidence: confidenceFilter
    };
    
    // Перезагружаем данные
    app.loadScreenData(`${sport}-screen`);
}

function filterByTime(hours) {
    app.currentTimeFilter = hours;
    
    // Обновляем активную кнопку
    const buttons = document.querySelectorAll('.time-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Перезагружаем предматчи
    app.loadPrematchData();
}

function filterHistory() {
    app.loadHistory();
}

function closeModal() {
    const modal = document.getElementById('modal');
    modal.classList.remove('active');
}

// Функции обновления данных
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
    
    // Закрытие модального окна при клике вне его
    document.getElementById('modal').addEventListener('click', (e) => {
        if (e.target.id === 'modal') {
            closeModal();
        }
    });
});

// Очистка при закрытии приложения
window.addEventListener('beforeunload', () => {
    if (app) {
        app.stopAutoRefresh();
    }
});
