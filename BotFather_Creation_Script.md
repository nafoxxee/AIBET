# AIBET - BotFather Bot Creation Script
# Ready to copy-paste for BotFather

## 🤖 BotFather Commands

### Create New Bot

Send this to @BotFather:

```
/newbot
```

### Bot Configuration

When prompted, provide:

**Name:**
```
AIBET Sports Analytics
```

**Username:**
```
aibet_sports_bot
```

**About:**
```
Educational sports analytics assistant for NHL, KHL, and CS2 matches. Provides educational insights and analysis.
```

**Commands:**

#### /start Command
```
start - Главное меню с выбором лиги
```

#### /nhl Command
```
nhl - Информация о NHL и аналитика
```

#### /khl Command
```
khl - Информация о KHL и аналитика
```

#### /cs2 Command
```
cs2 - Информация о CS2 и аналитика
```

#### /about Command
```
about - О проекте AIBET и образовательная цель
```

### BotFather Complete Script

Copy this entire message and send to @BotFather:

```
/newbot
Name: AIBET Sports Analytics
Username: aibet_sports_bot
About: Educational sports analytics assistant for NHL, KHL, and CS2 matches. Provides educational insights and analysis.
Commands:
start - Главное меню с выбором лиги
nhl - Информация о NHL и аналитика
khl - Информация о KHL и аналитика
cs2 - Информация о CS2 и аналитика
about - О проекте AIBET и образовательная цель
```

### Alternative: Step-by-Step Creation

If you prefer step-by-step:

1. **Start with BotFather**
   ```
   /newbot
   ```

2. **Enter Bot Name**
   ```
   AIBET Sports Analytics
   ```

3. **Enter Bot Username**
   ```
   aibet_sports_bot
   ```

4. **Enter Bot About**
   ```
   Educational sports analytics assistant for NHL, KHL, and CS2 matches. Provides educational insights and analysis.
   ```

5. **Add Commands One by One**

   **Command 1:**
   ```
   /start - Главное меню с выбором лиги
   ```

   **Command 2:**
   ```
   /nhl - Информация о NHL и аналитика
   ```

   **Command 3:**
   ```
   /khl - Информация о KHL и аналитика
   ```

   **Command 4:**
   ```
   /cs2 - Информация о CS2 и аналитика
   ```

   **Command 5:**
   ```
   /about - О проекте AIBET и образовательная цель
   ```

### Post-Creation Steps

After BotFather responds:

1. **Copy Bot Token**
   - Keep it secure
   - Don't share it publicly

2. **Set Up BotMother**
   - Go to BotMother platform
   - Import BotMother_Config.yaml
   - Configure web app integration

3. **Test Bot**
   - Send `/start` to your bot
   - Verify all commands work
   - Test web app buttons

4. **Deploy Mini App**
   - Ensure Mini App URL is accessible
   - Test parameter handling
   - Verify educational content

### Bot Token Storage

Once you receive the token:

```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

Add to your Mini App environment variables.

### Mini App Integration

The bot will pass these parameters to Mini App:

```
https://your-mini-app-url.com?source=telegram&user_id=123456789&league=nhl
```

### Educational Compliance

All bot responses must include:

```
⚠️ Образовательная цель:
Этот бот предоставляет информацию только в образовательных целях.
Никаких ставок или финансовых рекомендаций не дается.
```

### Testing Checklist

- [ ] Bot responds to `/start`
- [ ] All buttons open Mini App
- [ ] League commands work
- [ ] `/about` shows project info
- [ ] Mini App receives parameters
- [ ] Educational disclaimers visible
- [ ] Web app integration functional

---

**Result**: Complete Telegram bot ready for BotMother + Mini App integration
