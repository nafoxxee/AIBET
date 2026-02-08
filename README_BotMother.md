# AIBET Telegram Bot - BotMother Complete Package

## 📦 Package Contents

This package contains everything needed to create a no-code Telegram bot for AIBET:

### Files Included:
1. **BotMother_Config.yaml** - Complete bot configuration
2. **BotMother_Setup_Guide.md** - Step-by-step setup instructions
3. **BotFather_Creation_Script.md** - Ready-to-copy BotFather commands

## 🚀 Quick Start

### Step 1: Create Bot with BotFather
1. Open Telegram and search for @BotFather
2. Copy commands from `BotFather_Creation_Script.md`
3. Send to @BotFather
4. Receive your bot token

### Step 2: Configure in BotMother
1. Go to BotMother platform
2. Import `BotMother_Config.yaml`
3. Set your Mini App URL
4. Configure web app integration

### Step 3: Test Integration
1. Send `/start` to your bot
2. Test all inline buttons
3. Verify Mini App opens correctly
4. Check URL parameters are passed

## 🤖 Bot Features

### Main Menu
```
🏒 Выерите вид спорта:
[🏒 NHL] [🏒 KHL] [🎮 CS2]
[🌐 Открыть Mini App] [ℹ️ О проекте]
```

### League Selection
- **NHL**: Opens Mini App with `league=nhl`
- **KHL**: Opens Mini App with `league=khl`
- **CS2**: Opens Mini App with `league=cs2`

### Web App Integration
- **URL**: `https://aibet-mini-app.onrender.com`
- **Parameters**: `source=telegram&user_id={id}&league={type}`
- **Purpose**: Educational analytics only

## 📋 Configuration Options

### Bot Settings
- **Language**: Russian (ru)
- **Inline Feedback**: Enabled
- **Auto Answer**: Disabled (manual control)
- **Educational Mode**: Enabled

### Web App Parameters
```javascript
// Mini App should receive:
{
  source: "telegram",
  user_id: "123456789",
  league: "nhl" | "khl" | "cs2"
}
```

## 🔧 Technical Implementation

### Button Actions
Each button sends different data to Mini App:

#### NHL Button
```yaml
text: "🏒 NHL"
web_app:
  url: https://aibet-mini-app.onrender.com
  parameters:
    source: telegram
    league: nhl
    user_id: "{{user_id}}"
```

#### KHL Button
```yaml
text: "🏒 KHL"
web_app:
  url: https://aibet-mini-app.onrender.com
  parameters:
    source: telegram
    league: khl
    user_id: "{{user_id}}"
```

#### CS2 Button
```yaml
text: "🎮 CS2"
web_app:
  url: https://aibet-mini-app.onrender.com
  parameters:
    source: telegram
    league: cs2
    user_id: "{{user_id}}"
```

## 📊 Educational Compliance

### Required Disclaimers
All bot responses must include:
```
⚠️ Образовательная цель:
Этот бот предоставляет информацию только в образовательных целях.
Никаких ставок или финансовых рекомендаций не дается.
```

### Mini App Content
- Educational sports analytics only
- Risk assessments and disclaimers
- No financial or betting advice
- Clear educational purpose indicators

## 🌐 Deployment Ready

### BotMother Configuration
- ✅ Complete YAML configuration
- ✅ All commands defined
- ✅ Web app integration
- ✅ Educational compliance
- ✅ Russian language support

### Mini App Integration
- ✅ URL parameter handling
- ✅ User session management
- ✅ League-specific content
- ✅ Educational analytics ready

## 🎯 Success Metrics

### Bot Engagement
- Users who start bot
- Button click rates
- Mini App opens
- User retention

### Mini App Usage
- Page views per user
- League preferences
- Session duration
- Educational content interaction

## 📞 Support

### Bot Issues
- Check BotFather configuration
- Verify web app URL
- Test command responses

### Mini App Issues
- Verify URL parameter parsing
- Check user session handling
- Test league-specific content

---

## 🎉 Result

**Complete no-code Telegram bot package ready for BotMother deployment**

### What you get:
- 🤖 **Fully configured Telegram bot**
- 🌐 **Mini App integration**
- 📊 **Educational analytics framework**
- 🔧 **Easy BotMother setup**
- 📋 **Complete documentation**

### Ready for:
- BotFather bot creation
- BotMother configuration
- Mini App integration
- Educational sports analytics

**Just copy, paste, and deploy!** 🚀
