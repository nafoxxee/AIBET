# AIBET Analytics Platform v1.3 FULL

Production-ready analytics backend for NHL, KHL, and CS2 matches and odds with unified AI analytics.

## 🎯 Overview

AIBET Analytics Platform v1.3 FULL is a **production-ready** backend built with Python 3.11 + FastAPI, designed for deployment on Render Free tier. It aggregates, normalizes, and analyzes sports data from multiple sources with comprehensive AI analytics and educational disclaimers.

## 🏒 Supported Leagues

- **🏒 NHL** - National Hockey League (via public JSON API)
- **🏒 KHL** - Kontinental Hockey League (via HTML parsing)
- **🎮 CS2** - Counter-Strike 2 Esports (via multi-source parsing)

## 🚀 Features v1.3 FULL

### ✅ Production Ready
- **Python 3.11** + FastAPI 0.104.1
- **In-memory TTL cache** with configurable expiration
- **JSON structured logging** with structlog
- **Rate limiting** + security protections
- **Health checks** for all services
- **Metrics collection** for performance monitoring
- **CORS middleware** enabled by default
- **Global exception handling** with structured responses

### ✅ AI-Ready v1.3
- **Global Match ID** (deterministic hash)
- **Unified data schemas** with Pydantic v2
- **Feature engineering** for ML models
- **AI scoring engine** with confidence levels
- **Explainable AI** with educational disclaimers
- **Risk assessment** with factor breakdown
- **Value betting analytics** with market inefficiency detection

### ✅ Unified API v1.3
- **Single entry point**: `app.main:app`
- **Unified endpoints** under `/v1/` prefix
- **Structured JSON responses** with success/error handling
- **Educational disclaimers** on all AI responses
- **Pydantic validation** for all API responses

## 📁 Project Structure v1.3

```
app/
├── main.py                 # FastAPI application entry point v1.3
├── config.py               # Pydantic settings management
├── cache.py                # In-memory TTL cache implementation
├── logging.py              # JSON structured logging
├── metrics.py              # Performance metrics collection
├── schemas.py              # Unified Pydantic models
├── quality.py              # Data quality assessment
├── normalizer.py           # Data normalization utilities
├── api/                    # API routes v1.3
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
├── ai/                     # AI analytics layer v1.3
│   ├── context.py     # Context builder
│   ├── features.py    # Feature engineering
│   ├── scoring.py     # AI scoring engine
│   ├── explanation.py # Explanation generator
│   └── prompts.py     # AI prompt templates
└── requirements.txt        # Python dependencies v1.3
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

## 🌐 API Endpoints v1.3

### Root & System
- `GET /` - Root endpoint with API information
- `GET /health` - Health check with service status
- `GET /metrics` - Performance metrics
- `GET /docs` - Interactive API documentation
- `GET /redoc` - ReDoc documentation

### League-Specific
- `GET /v1/nhl/schedule` - NHL schedule
- `GET /v1/khl/schedule` - KHL schedule
- `GET /v1/cs2/upcoming` - CS2 upcoming matches
- `GET /v1/odds/nhl` - NHL odds
- `GET /v1/odds/khl` - KHL odds
- `GET /v1/odds/cs2` - CS2 odds

### Unified Data
- `GET /v1/unified/matches` - All matches from all leagues
- `GET /v1/unified/leagues` - Available leagues and status
- `GET /v1/unified/summary` - Data summary
- `GET /v1/unified/search` - Search by team names

### AI Analytics v1.3
- `GET /v1/ai/context/{match_id}` - AI context for match
- `GET /v1/ai/score/{match_id}` - AI scoring with confidence
- `GET /v1/ai/explain/{match_id}` - AI explanation with disclaimers
- `GET /v1/ai/value` - Value betting signals with risk assessment
- `GET /v1/ai/features/{match_id}` - AI features for analysis

## 🤖 AI Analytics v1.3

### Response Structure
All AI responses include:
```json
{
  "ai_score": 0.743,
  "confidence": 0.856,
  "risk_level": "medium",
  "value_score": 0.612,
  "not_a_prediction": true,
  "educational_purpose_only": true,
  "disclaimer": "This analysis is provided for educational purposes only...",
  "analysis_timestamp": "2026-02-06T12:00:00Z",
  "factors": {
    "form_analysis": 0.75,
    "historical_data": 0.68,
    "market_factors": 0.72,
    "league_factors": 0.82
  },
  "confidence_breakdown": {
    "data_quality": 0.9,
    "sample_size": 0.8,
    "market_stability": 0.87
  },
  "risk_factors": ["Limited data quality", "High market volatility"]
}
```

## 🚀 Deployment v1.3

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python -m app.main
```

### Render Free Deployment

1. **Clone Repository**
   ```bash
   git clone https://github.com/nafoxxee/AIBET.git
   cd AIBET
   ```

2. **Deploy to Render**
   - Connect repository to Render
   - Render will auto-detect `Dockerfile` and `requirements.txt`
   - Service will be available at `https://aibet-analytics-v13.onrender.com`

### Docker Configuration

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
```

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
- Performance metrics

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

## 🎯 Educational Disclaimers

All AI responses include:
- **Educational purpose only** statements
- **Not a prediction** warnings
- **Responsible gambling** messages
- **Risk assessment** factors

## 🛠️ Development

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/
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

## 🎉 v1.3 Features

- ✅ **Unified API** with single entry point
- ✅ **Educational AI** with disclaimers
- ✅ **Risk assessment** with factor breakdown
- ✅ **Value analytics** with market inefficiency
- ✅ **Production-ready** Docker configuration
- ✅ **Comprehensive monitoring** and logging
- ✅ **CORS enabled** for frontend integration
- ✅ **Error handling** with structured responses

---

**Built with ❤️ for sports analytics and AI transparency**
