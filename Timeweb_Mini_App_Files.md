# AIBET Mini App - Timeweb Ready Files
# Полный код для загрузки на Timeweb

## 📁 Структура файлов

```
aibet-mini-app/
├── index.html          # Главная страница
├── style.css          # Стили
├── script.js          # JavaScript логика
└── assets/           # Изображения (опционально)
```

## 📄 index.html

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIBET - Educational Sports Analytics</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="app">
        <div class="header">
            <h1>🏒 AIBET Analytics</h1>
            <p>Образовательная спортивная аналитика</p>
        </div>
        
        <div class="league-selector">
            <h2>Выберите лигу:</h2>
            <div class="buttons">
                <button onclick="selectLeague('nhl')" class="btn nhl">🏒 NHL</button>
                <button onclick="selectLeague('khl')" class="btn khl">🏒 KHL</button>
                <button onclick="selectLeague('cs2')" class="btn cs2">🎮 CS2</button>
            </div>
        </div>
        
        <div id="content" class="content">
            <div class="welcome">
                <h3>📊 Добро пожаловать!</h3>
                <p>Выберите лигу для просмотра образовательной аналитики.</p>
                <p class="disclaimer">
                    ⚠️ <strong>Образовательная цель:</strong><br>
                    Этот анализ предоставляется только в образовательных целях.<br>
                    Никаких ставок, финансовых рекомендаций или прогнозов не дается.
                </p>
            </div>
        </div>
        
        <div class="footer">
            <p>🌐 <a href="https://aibet-analytics.com" target="_blank">AIBET Analytics</a></p>
            <p>📚 Образовательная платформа</p>
        </div>
    </div>
    
    <script src="script.js"></script>
</body>
</html>
```

## 🎨 style.css

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
}

#app {
    max-width: 400px;
    margin: 0 auto;
    padding: 20px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.header {
    text-align: center;
    margin-bottom: 30px;
    color: white;
}

.header h1 {
    font-size: 24px;
    margin-bottom: 10px;
}

.header p {
    opacity: 0.9;
    font-size: 14px;
}

.league-selector {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.0.1);
}

.league-selector h2 {
    text-align: center;
    margin-bottom: 20px;
    color: #333;
}

.buttons {
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
}

.btn {
    padding: 15px 20px;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    color: white;
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.0.15);
}

.btn.nhl {
    background: linear-gradient(45deg, #FF6B6B, #C92A2A);
}

.btn.khl {
    background: linear-gradient(45deg, #4ECDC4, #2A9D8F);
}

.btn.cs2 {
    background: linear-gradient(45deg, #FFD93D, #FCB045);
}

.content {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.0.1);
    flex: 1;
}

.welcome {
    text-align: center;
}

.welcome h3 {
    color: #333;
    margin-bottom: 15px;
}

.disclaimer {
    background: #FFF3CD;
    border: 1px solid #FFEAA7;
    border-radius: 8px;
    padding: 15px;
    margin-top: 20px;
    font-size: 12px;
    color: #856404;
}

.footer {
    text-align: center;
    color: white;
    opacity: 0.8;
    font-size: 12px;
}

.footer a {
    color: white;
    text-decoration: none;
}

.league-content {
    display: none;
}

.league-content.active {
    display: block;
}

.match-list {
    margin-top: 20px;
}

.match-item {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 10px;
    border-left: 4px solid #007bff;
}

.match-item h4 {
    color: #333;
    margin-bottom: 8px;
}

.match-item p {
    color: #666;
    font-size: 14px;
    margin-bottom: 5px;
}

.analysis-score {
    background: #e9ecef;
    border-radius: 6px;
    padding: 10px;
    margin-top: 10px;
    text-align: center;
}

.score-value {
    font-size: 18px;
    font-weight: bold;
    color: #007bff;
}

.risk-level {
    margin-top: 5px;
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 4px;
    display: inline-block;
}

.risk-low {
    background: #d4edda;
    color: #155724;
}

.risk-medium {
    background: #fff3cd;
    color: #856404;
}

.risk-high {
    background: #f8d7da;
    color: #721c24;
}

/* Telegram Web App optimizations */
@media (max-width: 480px) {
    #app {
        padding: 10px;
    }
    
    .header h1 {
        font-size: 20px;
    }
    
    .btn {
        padding: 12px 16px;
        font-size: 14px;
    }
}

/* Dark theme support */
@media (prefers-color-scheme: dark) {
    body {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    }
    
    .league-selector,
    .content {
        background: #2c3e50;
        color: #ecf0f1;
    }
    
    .league-selector h2,
    .welcome h3,
    .match-item h4 {
        color: #ecf0f1;
    }
    
    .match-item {
        background: #34495e;
        border-left-color: #3498db;
    }
    
    .analysis-score {
        background: #2c3e50;
    }
    
    .score-value {
        color: #3498db;
    }
}
```

## 📜 script.js

```javascript
// Инициализация Telegram Web App
const webApp = window.Telegram?.WebApp;

// Параметры из URL
const urlParams = new URLSearchParams(window.location.search);
const source = urlParams.get('source') || 'web';
const userId = urlParams.get('user_id');
const league = urlParams.get('league') || 'nhl';

// Глобальные переменные
let currentLeague = league;
let userData = null;

// Инициализация приложения
function initApp() {
    // Инициализация Telegram Web App
    if (webApp) {
        webApp.ready();
        webApp.expand();
        
        // Получение данных пользователя
        userData = webApp.initDataUnsafe?.user;
        console.log('Telegram User:', userData);
        
        // Настройка кнопки "Назад"
        webApp.BackButton.onClick(() => {
            showWelcome();
            webApp.BackButton.hide();
        });
    }
    
    // Показываем начальный контент
    if (league && league !== 'nhl') {
        selectLeague(league);
    } else {
        showWelcome();
    }
    
    console.log('App initialized with:', { source, userId, league });
}

// Показ приветственного экрана
function showWelcome() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="welcome">
            <h3>📊 Добро пожаловать!</h3>
            <p>Выберите лигу для просмотра образовательной аналитики.</p>
            <p class="disclaimer">
                ⚠️ <strong>Образовательная цель:</strong><br>
                Этот анализ предоставляется только в образовательных целях.<br>
                Никаких ставок, финансовых рекомендаций или прогнозов не дается.
            </p>
        </div>
    `;
    
    if (webApp) {
        webApp.BackButton.hide();
    }
}

// Выбор лиги
function selectLeague(selectedLeague) {
    currentLeague = selectedLeague;
    
    // Обновляем UI
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="league-content active">
            <h3>${getLeagueTitle(selectedLeague)}</h3>
            <p>${getLeagueDescription(selectedLeague)}</p>
            
            <div class="match-list">
                ${generateMockMatches(selectedLeague)}
            </div>
            
            <p class="disclaimer">
                ⚠️ <strong>Образовательная цель:</strong><br>
                Этот анализ предоставляется только в образовательных целях.<br>
                Никаких ставок, финансовых рекомендаций или прогнозов не дается.
            </p>
        </div>
    `;
    
    // Показываем кнопку "Назад" в Telegram
    if (webApp) {
        webApp.BackButton.show();
    }
    
    // Отправляем данные в бот
    if (webApp && userData) {
        webApp.sendData(JSON.stringify({
            action: 'league_selected',
            league: selectedLeague,
            user_id: userData.id,
            source: source
        }));
    }
}

// Получение заголовка лиги
function getLeagueTitle(league) {
    const titles = {
        'nhl': '🏒 NHL - Национальная Хоккейная Лига',
        'khl': '🏒 KHL - Континентальная Хоккейная Лига',
        'cs2': '🎮 CS2 - Counter-Strike 2 Киберспорт'
    };
    return titles[league] || '🏒 Спортивная аналитика';
}

// Получение описания лиги
function getLeagueDescription(league) {
    const descriptions = {
        'nhl': 'Просмотрите расписание матчей, статистику команд и образовательную аналитику для NHL.',
        'khl': 'Изучайте матчи, турнирную таблицу и образовательные инсайты для KHL.',
        'cs2': 'Анализируйте предстоящие турниры, результаты и образовательную статистику CS2.'
    };
    return descriptions[league] || 'Образовательная спортивная аналитика.';
}

// Генерация моковых матчей
function generateMockMatches(league) {
    const matches = {
        'nhl': [
            { teams: 'Boston Bruins vs Toronto Maple Leafs', time: '20:00', date: '2026-02-08' },
            { teams: 'Montreal Canadiens vs Ottawa Senators', time: '19:30', date: '2026-02-08' },
            { teams: 'Vancouver Canucks vs Edmonton Oilers', time: '22:00', date: '2026-02-08' }
        ],
        'khl': [
            { teams: 'SKA Saint Petersburg vs CSKA Moscow', time: '19:00', date: '2026-02-08' },
            { teams: 'Ak Bars Kazan vs Metallurg Magnitogorsk', time: '18:30', date: '2026-02-08' },
            { teams: 'Dinamo Moscow vs Spartak Moscow', time: '19:30', date: '2026-02-08' }
        ],
        'cs2': [
            { teams: 'NaVi vs FaZe Clan', time: '18:00', date: '2026-02-08' },
            { teams: 'G2 Esports vs Team Vitality', time: '20:00', date: '2026-02-08' },
            { teams: 'Astralis vs Heroic', time: '21:00', date: '2026-02-08' }
        ]
    };
    
    const leagueMatches = matches[league] || [];
    
    return leagueMatches.map((match, index) => `
        <div class="match-item">
            <h4>${match.teams}</h4>
            <p>📅 ${match.date} в ${match.time}</p>
            <div class="analysis-score">
                <div class="score-value">${(Math.random() * 0.5 + 0.5).toFixed(2)}</div>
                <div class="risk-level risk-${getRandomRisk()}">${getRiskText()}</div>
            </div>
        </div>
    `).join('');
}

// Получение случайного уровня риска
function getRandomRisk() {
    const risks = ['low', 'medium', 'high'];
    return risks[Math.floor(Math.random() * risks.length)];
}

// Получение текста риска
function getRiskText() {
    const riskTexts = {
        'low': 'Низкий риск',
        'medium': 'Средний риск',
        'high': 'Высокий риск'
    };
    return riskTexts[getRandomRisk()] || 'Средний риск';
}

// Запуск приложения
document.addEventListener('DOMContentLoaded', initApp);

// Обработка изменений в Telegram Web App
if (webApp) {
    webApp.onEvent('themeChanged', () => {
        console.log('Theme changed');
    });
    
    webApp.onEvent('viewportChanged', () => {
        console.log('Viewport changed');
    });
}
```

## 🚀 Инструкции по загрузке на Timeweb

### 1. Создание сайта на Timeweb
```
1. Войти в панель Timeweb
2. Перейти в "Сайты" → "Добавить сайт"
3. Выбрать "Загрузка файлов"
4. Назвать сайт: aibet-mini-app
5. Выбрать домен: aibet-mini-app.timeweb.ru
```

### 2. Загрузка файлов
```
1. Создать структуру папок
2. Загрузить index.html в корень
3. Загрузить style.css в корень
4. Загрузить script.js в корень
5. Проверить что index.html установлен как индексный
```

### 3. Настройка домена
```
Домен: aibet-mini-app.timeweb.ru
Тип: Перенаправление или статический сайт
Индексный файл: index.html
```

### 4. Тестирование
```
URL: https://aibet-mini-app.timeweb.ru
Проверить:
- Загрузка страницы
- Работающие кнопки
- Telegram Web App интеграция
- Educational disclaimers
```

## 🔗 Интеграция с ботом

### Обновление URL в боте
```
Старый: https://aibet-mini-app.onrender.com
Новый: https://aibet-mini-app.timeweb.ru
```

### Проверка параметров
```
Тест URL: https://aibet-mini-app.timeweb.ru?source=telegram&user_id=123456&league=nhl

Должно работать:
- Выбор лиги из URL
- Telegram Web App API
- Отправка данных в бот
```

---

**ГОТОВО К ЗАГРУЗКЕ НА TIMEWEB!** 🚀
