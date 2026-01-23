# Installation Guide

## Prerequisites

- Python 3.13+
- Node.js 18+
- PostgreSQL 17+
- Redis 6.4+ (optional, for sessions)

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb pandapal

# Run migrations
alembic upgrade head
```

### 4. Environment Configuration

```bash
# Copy template
cp config/env.template .env

# Edit .env with your values
```

Required environment variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/pandapal

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
WEBHOOK_DOMAIN=your_domain.com

# Yandex Cloud
YANDEX_FOLDER_ID=your_folder_id
YANDEX_API_KEY=your_api_key

# Optional: Redis
REDIS_URL=redis://localhost:6379

# Optional: YooKassa
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key
```

### 5. Frontend Setup

```bash
cd frontend
npm install
```

### 6. Run Application

Backend:
```bash
python web_server.py
```

Frontend (development):
```bash
cd frontend
npm run dev
```

Frontend (production build):
```bash
cd frontend
npm run build
```

## Production Deployment

See [deployment guide](../deployment/railway.md) for Railway.app deployment instructions.

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Test connection
python scripts/check_database.py
```

### Missing Dependencies

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Pre-commit Hooks Failing

```bash
# Update hooks
pre-commit autoupdate

# Run manually
pre-commit run --all-files
```

## Next Steps

- [Configuration Guide](configuration.md)
- [First Steps](first-steps.md)
- [Development Guide](../development/contributing.md)
