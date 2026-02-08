# AIBET Telegram Bot - BotMother Setup Guide
# Complete no-code configuration for Telegram bot

## 🤖 BotMother Configuration

### Bot Basic Info
- **Name**: AIBET Sports Analytics
- **Username**: @aibet_sports_bot (example)
- **Description**: Educational sports analytics assistant for NHL, KHL, and CS2

### Main Menu Structure
```
🏒 Выерите вид спорта:
[🏒 NHL] [🏒 KHL] [🎮 CS2]
[🌐 Открыть Mini App] [ℹ️ О проекте]
```

### Command Implementation

#### /start Command
- Shows main menu with 5 inline buttons
- Each button opens Mini App with specific parameters
- User ID and source automatically passed

#### League Commands
- **/nhl** - Shows NHL info and opens Mini App
- **/khl** - Shows KHL info and opens Mini App  
- **/cs2** - Shows CS2 info and opens Mini App
- **/about** - Shows project information

### Web App Integration

#### Mini App URL
```
https://aibet-mini-app.onrender.com
```

#### Parameters Passed
```
source=telegram
user_id={user_id}
league={nhl|khl|cs2}
```

### Button Configuration

#### NHL Button
- **Text**: 🏒 NHL
- **Action**: Opens Mini App
- **Parameters**: league=nhl, source=telegram, user_id={user_id}

#### KHL Button  
- **Text**: 🏒 KHL
- **Action**: Opens Mini App
- **Parameters**: league=khl, source=telegram, user_id={user_id}

#### CS2 Button
- **Text**: 🎮 CS2
- **Action**: Opens Mini App
- **Parameters**: league=cs2, source=telegram, user_id={user_id}

#### Mini App Button
- **Text**: 🌐 Открыть Mini App
- **Action**: Opens Mini App
- **Parameters**: source=telegram, user_id={user_id}

#### About Button
- **Text**: ℹ️ О проекте
- **Action**: Shows text information
- **Content**: Project description and links

### User Flow

1. **User starts bot** → Shows main menu
2. **User selects league** → Opens Mini App with league parameter
3. **Mini App loads** → Receives user_id, source, league
4. **AI processes** → Educational analytics displayed
5. **User interacts** → Seamless experience

### Technical Implementation

#### BotMother Setup Steps

1. **Create Bot in BotFather**
   ```
   /newbot
   Name: AIBET Sports Analytics
   Username: aibet_sports_bot
   Description: Educational sports analytics
   Commands: /start, /nhl, /khl, /cs2, /about
   ```

2. **Configure in BotMother**
   - Upload BotMother_Config.yaml
   - Set web app URL
   - Configure buttons
   - Set language to Russian

3. **Test Commands**
   - `/start` → Should show main menu
   - `/nhl` → Should show NHL info
   - `/khl` → Should show KHL info
   - `/cs2` → Should show CS2 info
   - `/about` → Should show project info

4. **Verify Web App Integration**
   - Click buttons → Should open Mini App
   - Check URL parameters → Should include user_id, source, league

### Mini App Integration

#### Expected URL Parameters
```
https://aibet-mini-app.onrender.com?source=telegram&user_id=123456789&league=nhl
```

#### Mini App Responsibilities
- Parse URL parameters
- Store user session
- Show league-specific content
- Provide educational analytics
- Maintain user context

### Educational Compliance

#### Bot Messages
- All responses include educational disclaimer
- No betting advice or predictions
- Clear educational purpose statements
- Links to full Mini App for detailed analysis

#### Mini App Content
- Educational sports analytics only
- Risk assessments and disclaimers
- No financial or betting recommendations
- Clear educational purpose indicators

### Deployment Ready

#### Bot Configuration
- ✅ No server required
- ✅ No code deployment
- ✅ All logic in BotMother
- ✅ Web App integration ready

#### Mini App Integration
- ✅ URL parameter handling
- ✅ User session management
- ✅ Educational content ready
- ✅ League-specific routing

### Testing Checklist

#### Bot Tests
- [ ] `/start` shows main menu
- [ ] All buttons open Mini App
- [ ] URL parameters are correct
- [ ] League commands work
- [ ] `/about` shows project info

#### Mini App Tests
- [ ] Receives URL parameters
- [ ] Shows correct league content
- [ ] Maintains user session
- [ ] Educational disclaimers visible

### Launch Process

1. **Configure BotMother bot**
2. **Test all commands**
3. **Verify Mini App integration**
4. **Publish bot link**
5. **Monitor user interactions**

### Success Metrics

#### Bot Engagement
- Number of users starting bot
- Button click rates
- Mini App open rates
- User retention

#### Mini App Usage
- Page views per user
- League preferences
- Session duration
- Educational content engagement

---

**Result**: Complete no-code Telegram bot ready for BotMother deployment with Mini App integration
