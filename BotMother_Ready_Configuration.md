# AIBET Telegram Bot - Ready for BotMother Configuration
# Bot Information and Token

## 🤖 Bot Details

**Bot Username:** @aibet_analytics_bot
**Bot Token:** `8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4`
**Bot Name:** AIBET Sports Analytics

## 🔧 BotMother Configuration Steps

### Step 1: Connect Bot to BotMother
1. Go to BotMother platform
2. Add new bot
3. Enter bot token: `8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4`
4. Import `BotMother_Config.yaml`

### Step 2: Configure Web App
1. Set Mini App URL: `https://aibet-mini-app.onrender.com`
2. Configure web app parameters:
   - `source=telegram`
   - `user_id={{user_id}}`
   - `league={{league}}`

### Step 3: Test Bot Commands
1. Send `/start` to @aibet_analytics_bot
2. Verify main menu appears
3. Test all inline buttons
4. Check web app integration

## 📋 BotMother Configuration File

Use this configuration in BotMother:

```yaml
name: AIBET Sports Analytics
token: 8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4
about: Educational sports analytics assistant for NHL, KHL, and CS2 matches.

commands:
  - command: /start
    description: Главное меню с выбором лиги
  - command: /nhl
    description: Информация о NHL
  - command: /khl
    description: Информация о KHL
  - command: /cs2
    description: Информация о CS2
  - command: /about
    description: О проекте AIBET

main_menu:
  title: "🏒 Выерите вид спорта:"
  buttons:
    - text: "🏒 NHL"
      web_app:
        url: https://aibet-mini-app.onrender.com
        parameters:
          source: telegram
          league: nhl
          user_id: "{{user_id}}"
    - text: "🏒 KHL"
      web_app:
        url: https://aibet-mini-app.onrender.com
        parameters:
          source: telegram
          league: khl
          user_id: "{{user_id}}"
    - text: "🎮 CS2"
      web_app:
        url: https://aibet-mini-app.onrender.com
        parameters:
          source: telegram
          league: cs2
          user_id: "{{user_id}}"
    - text: "🌐 Открыть Mini App"
      web_app:
        url: https://aibet-mini-app.onrender.com
        parameters:
          source: telegram
          user_id: "{{user_id}}"
    - text: "ℹ️ О проекте"
      text: |
        🏆 **AIBET - Образовательная аналитика**
        
        📖 **Наша миссия:**
        Предоставление качественной образовательной спортивной аналитики.
        
        🌐 **Платформа:**
        • Mini App: https://aibet-mini-app.onrender.com
        • Web API: https://aibet-analytics.onrender.com/docs
        
        🏒 **Виды спорта:**
        • 🏒 NHL - Национальная хоккейная лига
        • 🏒 KHL - Континентальная хоккейная лига
        • 🎮 CS2 - Киберспорт Counter-Strike 2
        
        ⚠️ **Важно:**
        Все данные предоставляются в образовательных целях.
        Никаких ставок или финансовых рекомендаций.
        
        📞 **Поддержка:**
        Технические вопросы через Mini App.

settings:
  language: ru
  inline_feedback: true
  auto_answer: false

disclaimer: |
  ⚠️ **Образовательная цель:**
  Этот бот предоставляет информацию только в образовательных целях.
  Никаких ставок, финансовых рекомендаций или прогнозов не дается.
  Спортивная аналитика сопряжена с неопределенностями.
  
  🌐 **Для полной аналитики:**
  Используйте нашу Mini App для детальной информации.
```

## 🚀 Quick Setup

### 1. BotMother Setup
```
1. Login to BotMother
2. Click "Add Bot"
3. Enter token: 8579178407:AAGr1hvHrApW7sgjg-SHbi_DpH53ZodS8-4
4. Upload configuration above
5. Set web app URL
```

### 2. Test Commands
```
/start - Главное меню
/nhl - Информация о NHL
/khl - Информация о KHL
/cs2 - Информация о CS2
/about - О проекте
```

### 3. Verify Web App
```
Click any league button → Should open Mini App
Check URL parameters → Should include user_id, source, league
```

## 📊 Expected Behavior

### Main Menu
```
🏒 Выерите вид спорта:
[🏒 NHL] [🏒 KHL] [🎮 CS2]
[🌐 Открыть Mini App] [ℹ️ О проекте]
```

### Web App URLs
```
NHL: https://aibet-mini-app.onrender.com?source=telegram&user_id=123456&league=nhl
KHL: https://aibet-mini-app.onrender.com?source=telegram&user_id=123456&league=khl
CS2: https://aibet-mini-app.onrender.com?source=telegram&user_id=123456&league=cs2
```

## ✅ Ready for Deployment

Bot is now ready for BotMother configuration with:
- ✅ Correct token
- ✅ Complete configuration
- ✅ Web app integration
- ✅ Educational disclaimers
- ✅ Russian language support

## 🎯 Next Steps

1. **Configure in BotMother** using the YAML above
2. **Test all commands** in Telegram
3. **Verify web app integration**
4. **Deploy Mini App** if not already done
5. **Monitor user interactions**

---

**Bot @aibet_analytics_bot is ready for BotMother deployment!** 🚀
