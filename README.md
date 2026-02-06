# AIBET Analytics Platform v1.3 FULL

Production-ready analytics backend for NHL, KHL, and CS2 matches and odds with unified AI analytics.

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python -m app.main
```

### Production Deployment
```bash
# Deploy to Render
git clone https://github.com/nafoxxee/AIBET.git
# Connect to Render - auto-detects Dockerfile
# Service: https://aibet-analytics-v13.onrender.com
```

## 🎯 Features v1.3 FULL

### ✅ Production Ready
- **Python 3.11** + FastAPI 0.104.1
- **Single entry point**: `app.main:app`
- **In-memory TTL cache** with graceful fallbacks
- **JSON structured logging** with metrics
- **Rate limiting** + security protections
- **Health checks** + monitoring
- **CORS middleware** enabled
- **Global exception handling**

### ✅ AI Analytics v1.3
- **Educational disclaimers** on all responses
- **Risk assessment** with factor breakdown
- **Value analytics** with market inefficiency
- **Confidence levels** with detailed analysis
- **Not a prediction** warnings

### ✅ Unified API v1.3
- **All endpoints** under `/v1/` prefix
- **Structured JSON responses**
- **Failsafe behavior** - returns cached data on errors
- **Pydantic validation** for all responses

## 🌐 API Endpoints

### System
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /metrics` - Performance metrics
- `GET /docs` - Interactive documentation

### League Data
- `GET /v1/nhl/schedule` - NHL schedule
- `GET /v1/khl/schedule` - KHL schedule  
- `GET /v1/cs2/upcoming` - CS2 upcoming matches
- `GET /v1/odds/nhl` - NHL odds
- `GET /v1/odds/khl` - KHL odds
- `GET /v1/odds/cs2` - CS2 odds

### Unified Data
- `GET /v1/unified/matches` - All matches
- `GET /v1/unified/leagues` - League status
- `GET /v1/unified/summary` - Data summary

### AI Analytics
- `GET /v1/ai/context/{match_id}` - Match context
- `GET /v1/ai/score/{match_id}` - AI scoring
- `GET /v1/ai/explain/{match_id}` - AI explanation
- `GET /v1/ai/value` - Value signals

## 🤖 AI Response Structure

All AI responses include educational disclaimers:

```json
{
  "ai_score": 0.743,
  "confidence": 0.856,
  "risk_level": "medium",
  "value_score": 0.612,
  "not_a_prediction": true,
  "educational_purpose": true,
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

## � Project Structure

```
app/
├── main.py                 # FastAPI entry point v1.3
├── config.py               # Pydantic settings
├── cache.py                # In-memory TTL cache
├── logging.py              # JSON structured logging
├── metrics.py              # Performance metrics
├── schemas.py              # Unified Pydantic models
├── quality.py              # Data quality assessment
├── normalizer.py           # Data normalization
├── api/v1/                 # API routes
│   ├── nhl.py             # NHL endpoints
│   ├── khl.py             # KHL endpoints
│   ├── cs2.py             # CS2 endpoints
│   ├── odds.py            # Odds endpoints
│   ├── unified.py         # Combined endpoints
│   └── ai.py              # AI analytics endpoints
├── services/               # Data source services
├── utils/                  # Utility modules
└── ai/                     # AI analytics layer
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

## 🐳 Docker Configuration

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
Structured JSON logging with:
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

## 🚀 Deployment

### Render Free Deployment

1. **Clone Repository**
   ```bash
   git clone https://github.com/nafoxxee/AIBET.git
   cd AIBET
   ```

2. **Deploy to Render**
   - Connect repository to Render
   - Render auto-detects `Dockerfile` and `requirements.txt`
   - Service available at `https://aibet-analytics-v13.onrender.com`

### Health Checks

Render automatically monitors:
- `/health` endpoint
- Container responsiveness
- Resource usage

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
- ✅ **Failsafe behavior** with graceful degradation
- ✅ **Error handling** with structured responses

---

**Built with ❤️ for sports analytics and AI transparency**
