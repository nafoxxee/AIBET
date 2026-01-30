# AI BET Analytics Platform

A comprehensive, production-ready analytics system for sports betting market analysis, specializing in Counter-Strike 2 (CS2) and Kontinental Hockey League (KHL) markets.

## 🎯 Overview

AI BET Analytics Platform is an AI-powered system that analyzes betting markets (not predictions), detects repeatable market scenarios, learns from historical outcomes, and provides probabilities through automated Telegram publishing. The system operates 24/7 using only free tools and libraries.

## 🏗️ Architecture

### Core Components

- **App Layer**: Main application controller, configuration management, and task scheduling
- **CS2 Module**: Dedicated CS2 parsing, analysis, and machine learning components
- **KHL Module**: Dedicated KHL parsing, analysis, and machine learning components
- **Storage Layer**: SQLite database for data persistence and historical analysis

### Key Features

- **Multi-Sport Support**: Independent CS2 and KHL modules with no data mixing
- **Real-Time Analysis**: Live match monitoring and scenario detection
- **Machine Learning**: Trained models for outcome prediction and pattern recognition
- **Telegram Integration**: Automated publishing to dedicated channels
- **24/7 Operation**: Fully automated scheduling and monitoring

## 📁 Project Structure

```
aibet-analytics-platform/
├── app/
│   ├── main.py                 # Telegram controller and bot logic
│   ├── config.py               # Configuration management
│   └── scheduler.py            # Task scheduling and heartbeat
│
├── cs2/                        # CS2 Module
│   ├── sources/
│   │   ├── hltv_parser.py      # HLTV.org match parsing
│   │   ├── odds_parser.py      # Public odds analysis
│   │   └── live_parser.py      # Live match data
│   ├── analysis/
│   │   ├── scenarios.py        # Scenario detection
│   │   ├── public_bias.py      # Public betting bias analysis
│   │   ├── lineup_changes.py   # Roster stability analysis
│   │   └── filters.py          # Match filtering and prioritization
│   └── ml/
│       ├── dataset.csv         # Training dataset
│       ├── trainer.py          # Model training
│       └── predictor.py        # Match prediction
│
├── khl/                        # KHL Module
│   ├── sources/
│   │   ├── matches_parser.py   # Match data parsing
│   │   ├── live_parser.py      # Live match analysis
│   │   └── odds_parser.py      # Odds and betting data
│   ├── analysis/
│   │   ├── period_logic.py     # Period-specific analysis
│   │   ├── pressure_model.py   # Pressure pattern detection
│   │   └── scenarios.py        # KHL scenario detection
│   └── ml/
│       ├── dataset.csv         # Training dataset
│       ├── trainer.py          # Model training
│       └── predictor.py        # Match prediction
│
├── storage/
│   └── database.db             # SQLite database
│
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Telegram Bot Token
- Telegram Channel IDs

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd aibet-analytics-platform
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export CS2_CHANNEL_ID="your_cs2_channel_id"
   export KHL_CHANNEL_ID="your_khl_channel_id"
   ```

4. **Run the application**
   ```bash
   python app/main.py
   ```

### Configuration

The system uses environment variables for configuration:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `CS2_CHANNEL_ID`: CS2 analytics channel ID
- `KHL_CHANNEL_ID`: KHL analytics channel ID

## 📊 Data Sources

### CS2 Data Sources (Free Only)

- **HLTV.org**: Matches, rosters, stand-ins, tournaments
- **Public Bookmaker Pages**: Odds and betting lines
- **Public Betting Percentages**: Market sentiment data

### KHL Data Sources (Free Only)

- **Flashscore / SofaScore**: Match data and statistics
- **Public Bookmaker Live Lines**: Real-time odds

## 🎯 Analysis Features

### CS2 Analytics

- **Favorite Odds Analysis**: 1.10–1.40 range monitoring
- **Public Money Detection**: >70% threshold analysis
- **Lineup Stability**: Stand-in and missing player tracking
- **Tournament Tier Classification**: S, A, B, C tier analysis
- **Map Progression**: Live match dynamics
- **Comeback Frequency**: Historical pattern analysis
- **Overtime Probability**: Late-game scenario detection

#### CS2 Detected Scenarios

- Overvalued Favorite
- Public Trap
- Delayed Market Reaction
- Map Comeback
- BO3 Volatility Pattern

### KHL Analytics

- **Home vs Away Factor**: Venue advantage analysis
- **Odds Movement Tracking**: Real-time market changes
- **Period Score Analysis**: Period-by-period breakdown
- **Penalty and Power Play Impact**: Special teams efficiency
- **Shot Pressure Metrics**: Offensive pressure analysis
- **Time Without Goals**: Scoring drought detection

#### KHL Detected Scenarios

- Favorite Lost 1st Period
- 0:0 After First Period
- Pressure Without Conversion
- Comeback Probability
- Late Goal Scenario

## 🤖 Machine Learning

### Model Architecture

- **CS2 Models**: RandomForest classification + GradientBoosting regression
- **KHL Models**: RandomForest classification + GradientBoosting regression
- **Training Frequency**: Daily model retraining
- **Features**: Odds, public bias, team stats, historical performance

### Prediction Outputs

- **Win Probabilities**: Team1, Team2, Draw (KHL)
- **Confidence Scores**: Model certainty levels
- **Risk Assessment**: Risk factors and recommendations
- **Feature Importance**: Key predictive factors

## 📱 Telegram Integration

### Channels

- **CS2 Channel**: https://t.me/aibetcsgo
- **KHL Channel**: https://t.me/aibetkhl

### Bot Commands

- `/start`: Initialize bot
- `/status`: System status check
- `/cs2`: CS2 analytics information
- `/khl`: KHL analytics information
- `/help`: Available commands

### Message Format

Each analysis includes:
- Match information and odds
- Detected scenarios with confidence levels
- Risk assessment and recommendations
- Real-time updates for live matches

## ⚙️ System Operations

### Task Scheduling

- **CS2 Parsing**: Every 5 minutes
- **KHL Parsing**: Every 5 minutes
- **Odds Updates**: Every 10 minutes
- **Live Data**: Every 1 minute
- **Analysis**: Every 3 minutes
- **ML Training**: Every 24 hours
- **Heartbeat**: Every 1 hour

### Data Management

- **Database**: SQLite with automatic cleanup
- **Retention**: 30 days for live data, longer for historical
- **Backup**: Manual database backups recommended

## 🔧 Development

### Adding New Sports

1. Create new sport directory under root
2. Implement parsers in `sources/` subdirectory
3. Add analysis modules in `analysis/` subdirectory
4. Create ML components in `ml/` subdirectory
5. Update database schema for new sport tables
6. Add Telegram formatting for new sport

### Customizing Analysis

Modify scenario detection logic in respective `scenarios.py` files:

```python
# Example: Add new scenario
def _detect_custom_scenario(self, match_data):
    # Your custom logic here
    return Scenario(
        name="Custom Scenario",
        confidence=0.8,
        description="Custom scenario description",
        factors=["Factor 1", "Factor 2"],
        recommendation="Custom recommendation"
    )
```

### Model Training

Models are automatically trained daily, but can be manually triggered:

```python
from cs2.ml.trainer import train_cs2_models
from khl.ml.trainer import train_khl_models

await train_cs2_models()
await train_khl_models()
```

## 📈 Monitoring

### System Health

- **Heartbeat Messages**: Regular status updates to Telegram
- **Error Logging**: Comprehensive error tracking
- **Performance Metrics**: Task execution monitoring
- **Database Status**: Storage and cleanup monitoring

### Analytics Tracking

- **Prediction Accuracy**: Model performance tracking
- **Scenario Detection**: Success rate monitoring
- **User Engagement**: Telegram interaction metrics

## 🛡️ Security Considerations

- **Token Security**: Store Telegram tokens securely
- **Rate Limiting**: Respect website rate limits
- **Data Privacy**: No personal data collection
- **API Security**: No paid APIs or authentication

## 🔄 Maintenance

### Regular Tasks

- **Database Cleanup**: Automatic old data removal
- **Model Retraining**: Daily model updates
- **Log Rotation**: Prevent log file bloat
- **Dependency Updates**: Regular package updates

### Troubleshooting

Common issues and solutions:

1. **Parsing Failures**: Check website structure changes
2. **Database Errors**: Verify disk space and permissions
3. **Telegram Issues**: Validate bot tokens and channel access
4. **Model Performance**: Ensure sufficient training data

## 📝 License

This project is provided as-is for educational and analytical purposes. Users are responsible for complying with applicable laws and regulations regarding sports betting and data usage.

## 🤝 Support

For issues and questions:

1. Check the troubleshooting section
2. Review log files for error details
3. Verify configuration settings
4. Test individual components

## 🚀 Production Deployment

### Requirements

- **Server**: 24/7 availability recommended
- **Python**: 3.8+ runtime environment
- **Storage**: Sufficient disk space for database
- **Network**: Stable internet connection
- **Memory**: Minimum 2GB RAM recommended

### Deployment Steps

1. Set up production environment
2. Configure environment variables
3. Install dependencies
4. Initialize database
5. Start the application
6. Monitor system health

### Scaling Considerations

- **Database**: Consider PostgreSQL for large-scale deployment
- **Caching**: Redis for improved performance
- **Monitoring**: Add comprehensive logging and alerting
- **Load Balancing**: Multiple instances for high availability

---

**Disclaimer**: This system provides analytics and probabilities, not guarantees. Sports betting involves risk. Use responsibly and within legal limits.
