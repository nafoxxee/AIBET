# AIBET Analytics Platform

Production-ready analytics backend for NHL, KHL, and CS2 matches and odds.

## 🎯 Overview

AIBET Analytics Platform is a **production-ready** backend built with Python 3.11 + FastAPI, designed for deployment on Render Free tier. It aggregates, normalizes, and analyzes sports data from multiple sources without requiring databases, APIs, or external dependencies.

## � Supported Leagues

- **🏒 NHL** - National Hockey League (via public JSON API)
- **🏒 KHL** - Kontinental Hockey League (via HTML parsing)
- **🎮 CS2** - Counter-Strike 2 Esports (via multi-source parsing)

## 🚀 Features

### ✅ Production Ready
- **Python 3.11** + FastAPI
- **In-memory TTL cache** with configurable expiration
- **JSON structured logging** for monitoring
- **Rate limiting** + security protections
- **Health checks** for all services
- **Metrics collection** for performance monitoring

### ✅ AI-Ready
- **Global Match ID** (deterministic hash)
- **Unified data schemas** with Pydantic v2
- **Feature engineering** for ML models
- **AI scoring engine** with confidence levels
- **Explainable AI** with educational disclaimers

### ✅ Telegram Mini App Ready
- **RESTful API** with unified endpoints
- **Real-time data** updates
- **Mobile-optimized** responses

### ✅ Premium-Ready
- **Modular architecture** for easy scaling
- **Value betting analytics** with risk assessment
- **AI transparency** with factor explanations
- **Multi-tier access** patterns

## � Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── config.py               # Pydantic settings management
├── cache.py                # In-memory TTL cache implementation
├── logging.py              # JSON structured logging
├── metrics.py              # Performance metrics collection
├── schemas.py              # Unified Pydantic models
├── quality.py              # Data quality assessment
├── normalizer.py           # Data normalization utilities
├── api/                    # API routes
│   ├── v1/
│   │   ├── nhl.py      # NHL endpoints
│   │   ├── khl.py      # KHL endpoints
│   │   ├── cs2.py      # CS2 endpoints
│   │   ├── odds.py     # Odds endpoints
│   │   ├── unified.py  # Combined endpoints
│   │   └── ai.py       # AI analytics endpoints
├── services/               # Data source services
│   ├── nhl.py        # NHL API client
│   ├── khl.py        # KHL HTML parser
│   ├── cs2.py        # CS2 multi-source parser
│   └── odds.py       # Odds analysis service
├── utils/                  # Utility modules
│   ├── ids.py         # ID generation
│   ├── rate_limit.py  # Rate limiting
│   └── time.py        # Time utilities
├── ai/                     # AI analytics layer
│   ├── context.py     # Context builder
│   ├── features.py    # Feature engineering
│   ├── scoring.py     # AI scoring engine
│   ├── explanation.py # Explanation generator
│   └── prompts.py     # AI prompt templates
└── requirements.txt        # Python dependencies
```

## 🔧 Configuration

Environment variables (`.env`):

```bash
# Server
DEBUG=false
PORT=8000

# Service Toggles
ENABLE_NHL=true
ENABLE_KHL=true
ENABLE_CS2=true

# Cache TTL (seconds)
TTL_NHL=300
TTL_KHL=600
TTL_CS2=300
TTL_ODDS=180

# Cache Settings
CACHE_MAX_ITEMS=1000

# AI Settings
AI_EXPLAIN_MODE=true
```

## 🌐 API Endpoints

### Unified Data
- `GET /v1/unified/matches` - All matches from all leagues
- `GET /v1/unified/leagues` - Available leagues and status
- `GET /v1/unified/summary` - Data summary
- `GET /v1/unified/search` - Search by team names

### League-Specific
- `GET /v1/nhl/schedule` - NHL schedule
- `GET /v1/khl/schedule` - KHL schedule
- `GET /v1/cs2/upcoming` - CS2 upcoming matches
- `GET /v1/odds/nhl` - NHL odds
- `GET /v1/odds/khl` - KHL odds
- `GET /v1/odds/cs2` - CS2 odds

### AI Analytics
- `GET /v1/ai/context/{match_id}` - AI context for match
- `GET /v1/ai/score/{match_id}` - AI scoring
- `GET /v1/ai/explain/{match_id}` - AI explanation
- `GET /v1/ai/value` - Value betting signals
- `GET /v1/ai/features/{match_id}` - AI features

### System
- `GET /health` - Application health
- `GET /metrics` - Performance metrics
- `GET /docs` - API documentation

## 🚀 Deployment

### Render Free Deployment

1. **Fork & Push**
   ```bash
   git clone https://github.com/your-username/aibet-analytics.git
   cd aibet-analytics
   git push origin main
   ```

2. **Deploy to Render**
   - Connect repository to Render
   - Render will auto-detect `Dockerfile` and `requirements.txt`
   - Service will be available at `https://your-app.onrender.com`

### Docker Configuration

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT}"]
```

### Health Checks

Render automatically monitors:
- `/health` endpoint
- Container responsiveness
- Resource usage

## 📊 Monitoring

### Metrics Available
- Request count by endpoint
- Response time statistics
- Cache hit/miss ratios
- Source failure tracking
- Error tracking

### Logging

Structured JSON logging includes:
- Timestamp
- Log level
- Module and function
- Error details
- Custom fields

## 🤖 AI Analytics

### Global Match ID

Deterministic hash based on:
- League identifier
- Team names
- Start time

### Scoring System

- **Confidence Score**: 0.0-1.0 based on data quality
- **Value Score**: 0.0-1.0 based on market inefficiency
- **Risk Level**: Low/Medium/High
- **Educational Disclaimer**: All responses marked as educational

### Feature Engineering

- Recent form analysis (last 5 matches)
- Head-to-head historical data
- Odds movement and volatility
- League-specific factors
- Time-based performance patterns

## 🔒 Security

### Rate Limiting
- IP-based rate limiting (100 requests/minute)
- User-Agent validation
- Loop protection
- Burst protection

### Data Validation
- Team name validation
- Odds range validation
- Date format validation
- Data quality assessment

## 🎯 Premium Features

### Value Betting Analytics
- Market inefficiency detection
- Odds vs form analysis
- Volatility assessment
- Risk/reward calculations

### AI Transparency
- Factor explanations
- Confidence levels
- Educational disclaimers
- Not a prediction warnings

## 📱 Telegram Mini App Ready

### Mobile-Optimized
- Lightweight responses
- Progressive loading
- Offline support
- Push notifications ready

### Real-time Updates
- WebSocket ready
- Cache invalidation
- Live score updates

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## 📈 Scaling

### Free Tier Optimizations
- In-memory caching
- Efficient data structures
- Minimal dependencies
- Optimized parsing
- Graceful degradation

### Premium Scaling
- Redis cache layer
- PostgreSQL database
- ML model integration
- Real-time data pipelines

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. Follow coding standards

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- Documentation: `/docs` endpoint
- Health: `/health` endpoint
- Metrics: `/metrics` endpoint
- Issues: GitHub Issues

---

**Built with ❤️ for sports analytics and AI transparency**
