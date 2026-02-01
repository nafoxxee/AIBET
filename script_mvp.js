// AIBET MVP - JavaScript Functionality
// Senior Full-Stack Implementation

// API Base URL
const API_BASE = window.location.origin;

// State Management
let currentSection = 'home';
let signals = [];
let matches = [];
let stats = {};

// Initialize App
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupNavigation();
    loadHomeStats();
    setupEventListeners();
}

function setupNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const section = this.dataset.section;
            switchSection(section);
        });
    });
}

function switchSection(section) {
    // Update navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-section="${section}"]`).classList.add('active');
    
    // Update sections
    document.querySelectorAll('.section').forEach(sec => {
        sec.classList.remove('active');
    });
    document.getElementById(section).classList.add('active');
    
    currentSection = section;
    
    // Load section data
    switch(section) {
        case 'home':
            loadHomeStats();
            break;
        case 'signals':
            loadSignals();
            break;
        case 'matches':
            loadMatches();
            break;
        case 'stats':
            loadStatistics();
            break;
    }
}

function setupEventListeners() {
    // Sport filter for signals
    document.getElementById('sportFilter')?.addEventListener('change', loadSignals);
    
    // Sport filter for matches
    document.getElementById('matchSportFilter')?.addEventListener('change', loadMatches);
}

// API Functions
async function apiCall(endpoint, options = {}) {
    try {
        showLoading();
        const response = await fetch(`${API_BASE}/api${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showError('Ошибка загрузки данных');
        return null;
    } finally {
        hideLoading();
    }
}

// Home Section
async function loadHomeStats() {
    const data = await apiCall('/statistics/home');
    if (data) {
        updateHomeStats(data);
    }
}

function updateHomeStats(data) {
    document.getElementById('totalSignals').textContent = data.quick_stats.active_signals;
    document.getElementById('totalMatches').textContent = data.quick_stats.matches;
    
    // Calculate average confidence from recent signals
    if (data.recent_signals && data.recent_signals.length > 0) {
        const avgConf = data.recent_signals.reduce((sum, s) => sum + s.confidence, 0) / data.recent_signals.length;
        document.getElementById('avgConfidence').textContent = `${avgConf.toFixed(1)}%`;
    }
}

// Signals Section
async function loadSignals() {
    const sportFilter = document.getElementById('sportFilter').value;
    const endpoint = sportFilter ? `/signals?sport=${sportFilter}` : '/signals';
    
    const data = await apiCall(endpoint);
    if (data) {
        signals = data;
        displaySignals(data);
    }
}

function displaySignals(signalsData) {
    const container = document.getElementById('signalsList');
    
    if (!signalsData || signalsData.length === 0) {
        container.innerHTML = '<div class="loading">Активных сигналов нет</div>';
        return;
    }
    
    const signalsHTML = signalsData.map(signal => createSignalCard(signal)).join('');
    container.innerHTML = signalsHTML;
}

function createSignalCard(signal) {
    const confidenceEmoji = getConfidenceEmoji(signal.confidence);
    const sportEmoji = signal.sport === 'cs2' ? '🔫' : '🏒';
    
    return `
        <div class="signal-card">
            <div class="signal-header">
                <div class="signal-teams">${sportEmoji} ${signal.team1} vs ${signal.team2}</div>
                <div class="signal-confidence">${confidenceEmoji} ${signal.confidence.toFixed(1)}%</div>
            </div>
            
            <div class="signal-details">
                <div class="signal-detail">
                    <strong>Прогноз:</strong> ${signal.prediction.toUpperCase()}
                </div>
                <div class="signal-detail">
                    <strong>Вероятность:</strong> ${(signal.probability * 100).toFixed(1)}%
                </div>
                <div class="signal-detail">
                    <strong>Value:</strong> ${signal.value_score.toFixed(2)}
                </div>
                <div class="signal-detail">
                    <strong>Спорт:</strong> ${signal.sport.toUpperCase()}
                </div>
            </div>
            
            ${signal.explanation ? `
                <div class="signal-explanation">
                    <strong>Объяснение:</strong> ${signal.explanation}
                </div>
            ` : ''}
            
            <div class="signal-detail" style="margin-top: 10px; font-size: 0.8rem; color: var(--text-secondary);">
                📅 ${new Date(signal.created_at).toLocaleString('ru-RU')}
            </div>
        </div>
    `;
}

// Matches Section
async function loadMatches() {
    const sportFilter = document.getElementById('matchSportFilter').value;
    const endpoint = sportFilter ? `/matches/upcoming?sport=${sportFilter}` : '/matches/upcoming';
    
    const data = await apiCall(endpoint);
    if (data) {
        matches = data;
        displayMatches(data);
    }
}

function displayMatches(matchesData) {
    const container = document.getElementById('matchesList');
    
    if (!matchesData || matchesData.length === 0) {
        container.innerHTML = '<div class="loading">Предстоящих матчей нет</div>';
        return;
    }
    
    const matchesHTML = matchesData.map(match => createMatchCard(match)).join('');
    container.innerHTML = matchesHTML;
}

function createMatchCard(match) {
    const sportEmoji = match.sport === 'cs2' ? '🔫' : '🏒';
    const matchDate = new Date(match.date);
    
    return `
        <div class="match-card">
            <div class="match-teams">
                ${sportEmoji} ${match.team1} vs ${match.team2}
            </div>
            
            <div class="match-details">
                <div>
                    <strong>Турнир:</strong> ${match.tournament || 'Unknown'}
                </div>
                <div>
                    <strong>Дата:</strong> ${matchDate.toLocaleString('ru-RU')}
                </div>
                <div class="match-rating">
                    <strong>Рейтинги:</strong> Получение...
                </div>
            </div>
        </div>
    `;
}

// Statistics Section
async function loadStatistics() {
    const [generalStats, teamStats] = await Promise.all([
        apiCall('/statistics'),
        apiCall('/statistics/teams?limit=10')
    ]);
    
    if (generalStats) {
        updateGeneralStats(generalStats);
    }
    
    if (teamStats) {
        displayTopTeams(teamStats);
    }
}

function updateGeneralStats(data) {
    document.getElementById('totalTeams').textContent = data.teams.total;
    document.getElementById('completedMatches').textContent = data.matches.completed;
    
    // Calculate win rate (placeholder - would come from performance data)
    document.getElementById('winRate').textContent = '68.5%';
    document.getElementById('avgValue').textContent = '0.15';
}

function displayTopTeams(teamsData) {
    const container = document.getElementById('topTeams');
    
    if (!teamsData || teamsData.length === 0) {
        container.innerHTML = '<div class="loading">Нет данных о командах</div>';
        return;
    }
    
    const teamsHTML = teamsData.map(team => createTeamItem(team)).join('');
    container.innerHTML = teamsHTML;
}

function createTeamItem(team) {
    const sportEmoji = team.sport === 'cs2' ? '🔫' : '🏒';
    
    return `
        <div class="team-item">
            <div class="team-name">${sportEmoji} ${team.name}</div>
            <div class="team-stats">
                <span>Рейтинг: ${team.rating}</span>
                <span>Win Rate: ${(team.win_rate * 100).toFixed(1)}%</span>
                <span>Матчи: ${team.matches_played}</span>
            </div>
        </div>
    `;
}

// Utility Functions
function getConfidenceEmoji(confidence) {
    if (confidence >= 80) return '🔥';
    if (confidence >= 70) return '✅';
    return '⚠️';
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

function showError(message) {
    // Create error toast
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-toast';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--error-color);
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 2000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 3000);
}

// Auto-refresh functionality
let refreshInterval;

function startAutoRefresh() {
    refreshInterval = setInterval(() => {
        switch(currentSection) {
            case 'home':
                loadHomeStats();
                break;
            case 'signals':
                loadSignals();
                break;
            case 'matches':
                loadMatches();
                break;
            case 'stats':
                loadStatistics();
                break;
        }
    }, 60000); // Refresh every minute
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
}

// Start auto-refresh when page is visible
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        startAutoRefresh();
    }
});

// Initial auto-refresh start
startAutoRefresh();
