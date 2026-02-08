# AIBET Bot - Environment Variables for Mini App
# Ready to add to your Mini App environment

## 🌐 Mini App Environment Variables

Add these variables to your Mini App (Render/VPS/Hosting):

### Telegram Bot Integration
```bash
# Bot Configuration
TELEGRAM_BOT_TOKEN=8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4
TELEGRAM_BOT_USERNAME=@aibet_analytics_bot

# Web App Configuration
WEB_APP_URL=https://aibet-mini-app.onrender.com
API_URL=https://aibet-analytics.onrender.com

# Source Tracking
DEFAULT_SOURCE=telegram
DEFAULT_LEAGUE=nhl

# Educational Mode
EDUCATIONAL_MODE=true
ENABLE_BETTING=false
```

### Database/Storage (Optional)
```bash
# Database Configuration
DATABASE_URL=sqlite:///aibet.db
# or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:port/database

# Redis (Optional)
REDIS_URL=redis://localhost:6379
```

### API Configuration
```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# CORS Settings
ALLOWED_ORIGINS=https://t.me,https://web.telegram.org
```

### Logging Configuration
```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 🔧 Mini App URL Parameter Handling

Your Mini App should handle these URL parameters:

```javascript
// Example URL: https://aibet-mini-app.onrender.com?source=telegram&user_id=123456&league=nhl

const urlParams = new URLSearchParams(window.location.search);
const source = urlParams.get('source') || 'web';
const userId = urlParams.get('user_id');
const league = urlParams.get('league') || 'nhl';

// Store in session/localStorage
sessionStorage.setItem('source', source);
sessionStorage.setItem('user_id', userId);
sessionStorage.setItem('league', league);
```

## 📱 Telegram Web App Integration

### Initialize Web App
```javascript
// Initialize Telegram Web App
const webApp = window.Telegram.WebApp;

// Set theme and expand
webApp.ready();
webApp.expand();

// Get user data
const user = webApp.initDataUnsafe?.user;
const userId = user?.id;

// Send data back to bot
webApp.sendData(JSON.stringify({
  action: 'league_selected',
  league: league,
  user_id: userId
}));
```

### Back Button Handling
```javascript
// Handle back button
webApp.onEvent('backButtonClicked', () => {
  webApp.close();
});

// Show back button
webApp.BackButton.show();
```

## 🎯 User Flow Integration

### 1. Bot → Mini App
```
User clicks NHL button → Opens Mini App with:
- source=telegram
- user_id=123456
- league=nhl
```

### 2. Mini App → Bot
```
User selects match → Send data back:
{
  action: 'match_selected',
  match_id: 'nhl_2024_02_08_team1_vs_team2',
  league: 'nhl',
  user_id: 123456
}
```

### 3. Bot Response
```
Bot receives data → Shows educational analysis:
- Match details
- Educational insights
- Risk assessment
- Disclaimer
```

## 📊 Educational Compliance

### Required Disclaimers
```javascript
// Add to all analysis responses
const educationalDisclaimer = `
⚠️ Образовательная цель:
Этот анализ предоставляется только в образовательных целях.
Никаких ставок, финансовых рекомендаций или прогнозов не дается.
Спортивная аналитика сопряжена с неопределенностями.
`;

// Display with analysis
showAnalysis(analysisData + educationalDisclaimer);
```

### Risk Assessment
```javascript
// Educational risk levels
const riskLevels = {
  low: 'Низкий риск',
  medium: 'Средний риск',
  high: 'Высокий риск'
};

// Always include educational context
const educationalContext = `
📚 **Образовательный контекст:**
Этот анализ демонстрирует методы спортивной аналитики
и предназначен исключительно для учебных целей.
`;
```

## 🚀 Deployment Ready

### Environment Setup
```bash
# Create .env file
cat > .env << EOF
TELEGRAM_BOT_TOKEN=8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4
TELEGRAM_BOT_USERNAME=@aibet_analytics_bot
WEB_APP_URL=https://aibet-mini-app.onrender.com
EDUCATIONAL_MODE=true
ENABLE_BETTING=false
EOF
```

### Test Integration
```bash
# Test URL parameters
curl "https://aibet-mini-app.onrender.com?source=telegram&user_id=123456&league=nhl"

# Test bot commands
curl -X POST https://api.telegram.org/bot8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4/getMe
```

## ✅ Integration Checklist

### BotMother Configuration
- [ ] Token added: `8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4`
- [ ] Web app URL configured
- [ ] Parameters set correctly
- [ ] Educational disclaimers added

### Mini App Configuration
- [ ] Environment variables set
- [ ] URL parameter handling
- [ ] Telegram Web App initialized
- [ ] Educational compliance implemented

### Testing
- [ ] Bot responds to `/start`
- [ ] Buttons open Mini App
- [ ] URL parameters received correctly
- [ ] Data sent back to bot works
- [ ] Educational disclaimers visible

---

**Bot @aibet_analytics_bot is ready for full integration!** 🚀
