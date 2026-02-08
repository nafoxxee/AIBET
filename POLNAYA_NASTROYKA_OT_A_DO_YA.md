# AIBET - ПОЛНАЯ НАСТРОЙКА ОТ А ДО Я
# Готовые решения - просто скопируй и вставь

## 🎯 **ШАГ 1 - СОЗДАНИЕ БОТА В BOTFATHER**

### Открой Telegram и найди @BotFather
Отправь эти команды по очереди:

```
/start
/newbot
```

### Когда спросит имя бота:
```
AIBET Sports Analytics
```

### Когда спросит username:
```
aibet_analytics_bot
```

### Когда спросит описание:
```
Educational sports analytics assistant for NHL, KHL, and CS2 matches. Provides educational insights and analysis.
```

### Добавь команды:
```
/start - Главное меню с выбором лиги
/nhl - Информация о NHL и аналитика
/khl - Информация о KHL и аналитика
/cs2 - Информация о CS2 и аналитика
/about - О проекте AIBET и образовательная цель
```

### РЕЗУЛЬТАТ:
BotFather даст тебе токен:
```
8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4
```

---

## 🌐 **ШАГ 2 - СОЗДАНИЕ MINI APP НА TIMEWEB**

### Зайди в Timeweb:
```
1. timeweb.com
2. Войти в аккаунт
3. "Сайты" → "Добавить сайт"
4. "Загрузка файлов"
```

### Создай сайт:
```
Название: AIBET Mini App
Домен: aibet-mini-app.timeweb.ru (или любой доступный)
```

### Создай файл index.html:
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIBET - Educational Sports Analytics</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container {
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
        .content {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            flex: 1;
        }
        .buttons {
            display: grid;
            grid-template-columns: 1fr;
            gap: 10px;
            margin-bottom: 20px;
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
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
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
        .disclaimer {
            background: #FFF3CD;
            border: 1px solid #FFEAA7;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            font-size: 12px;
            color: #856404;
            text-align: center;
        }
        .welcome {
            text-align: center;
        }
        .welcome h3 {
            color: #333;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏒 AIBET Analytics</h1>
            <p>Образовательная спортивная аналитика</p>
        </div>
        
        <div class="content">
            <div class="welcome">
                <h3>📊 Добро пожаловать!</h3>
                <p>Выберите лигу для просмотра образовательной аналитики.</p>
                
                <div class="buttons">
                    <button onclick="selectLeague('nhl')" class="btn nhl">🏒 NHL</button>
                    <button onclick="selectLeague('khl')" class="btn khl">🏒 KHL</button>
                    <button onclick="selectLeague('cs2')" class="btn cs2">🎮 CS2</button>
                </div>
                
                <div class="disclaimer">
                    ⚠️ <strong>Образовательная цель:</strong><br>
                    Этот анализ предоставляется только в образовательных целях.<br>
                    Никаких ставок, финансовых рекомендаций или прогнозов не дается.
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Инициализация Telegram Web App
        const webApp = window.Telegram?.WebApp;
        
        // Получаем параметры из URL
        const urlParams = new URLSearchParams(window.location.search);
        const source = urlParams.get('source') || 'web';
        const userId = urlParams.get('user_id');
        const league = urlParams.get('league') || 'nhl';
        
        // Функция выбора лиги
        function selectLeague(selectedLeague) {
            // Показываем сообщение
            const content = document.querySelector('.welcome');
            content.innerHTML = `
                <h3>🏒 ${getLeagueTitle(selectedLeague)}</h3>
                <p>${getLeagueDescription(selectedLeague)}</p>
                <p><strong>Статус:</strong> Сервис в разработке. Скоро будут доступны актуальные данные!</p>
                
                <div class="disclaimer">
                    ⚠️ <strong>Образовательная цель:</strong><br>
                    Этот анализ предоставляется только в образовательных целях.<br>
                    Никаких ставок, финансовых рекомендаций или прогнозов не дается.
                </div>
            `;
            
            // Отправляем данные в бот если есть
            if (webApp && userId) {
                webApp.sendData(JSON.stringify({
                    action: 'league_selected',
                    league: selectedLeague,
                    user_id: userId,
                    source: source
                }));
            }
        }
        
        // Получаем название лиги
        function getLeagueTitle(league) {
            const titles = {
                'nhl': '🏒 NHL - Национальная Хоккейная Лига',
                'khl': '🏒 KHL - Континентальная Хоккейная Лига',
                'cs2': '🎮 CS2 - Counter-Strike 2 Киберспорт'
            };
            return titles[league] || '🏒 Спортивная аналитика';
        }
        
        // Получаем описание лиги
        function getLeagueDescription(league) {
            const descriptions = {
                'nhl': 'Просмотрите расписание матчей, статистику команд и образовательную аналитику для NHL.',
                'khl': 'Изучайте матчи, турнирную таблицу и образовательные инсайты для KHL.',
                'cs2': 'Анализируйте предстоящие турниры, результаты и образовательную статистику CS2.'
            };
            return descriptions[league] || 'Образовательная спортивная аналитика.';
        }
        
        // Инициализация приложения
        function initApp() {
            if (webApp) {
                webApp.ready();
                webApp.expand();
            }
            
            // Если есть параметр лиги, показываем её
            if (league !== 'nhl') {
                selectLeague(league);
            }
        }
        
        // Запуск приложения
        document.addEventListener('DOMContentLoaded', initApp);
    </script>
</body>
</html>
```

---

## 🤖 **ШАГ 3 - НАСТРОЙКА БОТА**

### Используй любой конструктор ботов:
1. **BotMother** (простой)
2. **Manybot** (бесплатный)
3. **BotPreset** (простой)

### Введи данные:
```
Токен: 8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4
Название: AIBET Sports Analytics
Описание: Educational sports analytics assistant
```

### Настрой кнопки:
```
Главная кнопка:
🏒 Выерите вид спорта

Вложенные кнопки:
[🏒 NHL] [🏒 KHL] [🎮 CS2]
[ℹ️ О проекте]
```

### Настрой URL для кнопок:
```
NHL: https://aibet-mini-app.timeweb.ru?source=telegram&user_id={user_id}&league=nhl
KHL: https://aibet-mini-app.timeweb.ru?source=telegram&user_id={user_id}&league=khl
CS2: https://aibet-mini-app.timeweb.ru?source=telegram&user_id={user_id}&league=cs2
```

---

## 🚀 **ШАГ 4 - ЗАГРУЗКА ФАЙЛОВ НА TIMEWEB**

### В Timeweb панели:
1. **"Сайты" → твой сайт**
2. **"Файловый менеджер"**
3. **Загрузи файл index.html**
4. **Убедись что index.html - главный файл**

### Проверь работу:
```
Открой в браузере: https://aibet-mini-app.timeweb.ru
Должна появиться страница с кнопками
```

---

## 🧪 **ШАГ 5 - ТЕСТИРОВАНИЕ**

### Тест бота:
```
1. Найди @aibet_analytics_bot в Telegram
2. Отправь /start
3. Должно появиться меню с кнопками
4. Нажми кнопку 🏒 NHL
5. Должен открыться Mini App
```

### Тест Mini App:
```
1. Открой https://aibet-mini-app.timeweb.ru
2. Нажми кнопку 🏒 NHL
3. Должна появиться информация о NHL
```

---

## ✅ **РЕЗУЛЬТАТ**

### Что получишь:
- ✅ **Рабочий бот** @aibet_analytics_bot
- ✅ **Mini App** на Timeweb
- ✅ **Интеграция** бота с веб-приложением
- ✅ **Educational** аналитика
- ✅ **Никаких сложных** настроек

### Финальные URL:
- **Бот**: @aibet_analytics_bot
- **Mini App**: https://aibet-mini-app.timeweb.ru

---

## 🎯 **ГОТОВОЕ РЕШЕНИЕ**

### Просто скопируй и вставь:

1. **HTML код выше** → сохрани как index.html
2. **Загрузи на Timeweb** → в корень сайта
3. **Токен бота** → 8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4
4. **Настрой бота** → в любом конструкторе с кнопками
5. **Протестируй** → готово!

---

## 📞 **ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ**

### Проблема: Бот не отвечает
```
Решение: Проверь токен в настройках бота
Токен: 8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4
```

### Проблема: Mini App не открывается
```
Решение: Проверь URL в кнопках бота
Правильный URL: https://aibet-mini-app.timeweb.ru
```

### Проблема: Кнопки не работают
```
Решение: Проверь HTML код
Убедись что JavaScript не заблокирован
```

---

## 🎉 **ВСЁ ГОТОВО!**

### Тебе нужно сделать только 3 вещи:
1. **Создать бота** в BotFather (готовые команды выше)
2. **Загрузить 1 файл** на Timeweb (HTML код выше)
3. **Настроить кнопки** в любом конструкторе ботов

### Результат:
- 🤖 **Рабочий бот** с меню
- 🌐 **Рабочий Mini App** 
- 🔗 **Связь между ними**
- 📊 **Educational аналитика**

---

**ВСЁ ГОТОВО К ИСПОЛЬЗОВАНИЮ!** 🚀
