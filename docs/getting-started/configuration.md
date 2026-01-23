# Configuration Guide

## Environment Variables

### Required Variables

#### Database
```env
DATABASE_URL=postgresql://user:password@host:5432/database
```

#### Telegram Bot
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
WEBHOOK_DOMAIN=your-app.railway.app
```

#### Yandex Cloud
```env
YANDEX_FOLDER_ID=b1g***************
YANDEX_API_KEY=AQVN***************

# Optional: specific API keys for services
YANDEX_GPT_API_KEY=AQVN***************
YANDEX_VISION_API_KEY=AQVN***************
YANDEX_SPEECHKIT_API_KEY=AQVN***************
```

### Optional Variables

#### Redis (Sessions)
```env
REDIS_URL=redis://default:password@host:6379
```

#### YooKassa (Payments)
```env
YOOKASSA_SHOP_ID=123456
YOOKASSA_SECRET_KEY=live_***************
```

#### Application Settings
```env
# Environment
ENVIRONMENT=production  # or development

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Rate Limiting
API_RATE_LIMIT=60  # requests per minute
AI_RATE_LIMIT=30   # AI requests per minute

# Daily Limits
FREE_DAILY_LIMIT=30
MONTH_DAILY_LIMIT=500
```

## Configuration Files

### Python Configuration

`pyproject.toml` - Main Python configuration:
- Black formatter settings
- isort import sorting
- pytest configuration
- Project metadata

### Pre-commit Configuration

`.pre-commit-config.yaml` - Git hooks:
- Code formatting (black, isort)
- Linting (ruff, pylint)
- Security checks (bandit)
- TypeScript/ESLint checks

### Frontend Configuration

`frontend/vite.config.ts` - Vite build configuration
`frontend/tsconfig.json` - TypeScript configuration
`frontend/.eslintrc.cjs` - ESLint rules

## Database Configuration

### Connection Pool Settings

Default settings in `bot/database.py`:
```python
pool_size=5          # Number of connections
max_overflow=20      # Additional connections
pool_recycle=1800    # Recycle after 30 minutes
```

### Migration Configuration

`alembic.ini` - Alembic settings for database migrations

## Security Configuration

### Content Security Policy

Configured in `bot/security/middleware.py`:
- CSP headers
- CORS settings
- Rate limiting

### Moderation Patterns

`bot/config/forbidden_patterns.py` - Content moderation rules (150+ patterns)

## Monitoring Configuration

### Metrics

`bot/monitoring/prometheus_metrics.py` - Prometheus metrics configuration

### Logging

Configured via loguru in `web_server.py`:
- File rotation (10 MB)
- Retention (7 days)
- JSON format for production

## Next Steps

- [First Steps](first-steps.md)
- [Development Guide](../development/contributing.md)
- [Deployment Guide](../deployment/railway.md)
