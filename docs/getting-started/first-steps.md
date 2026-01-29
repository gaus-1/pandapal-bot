# First Steps with PandaPal

## Quick Start

After installation, follow these steps to get started with development.

## 1. Create Telegram Bot

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot` command
3. Follow instructions to create bot
4. Copy bot token to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   ```

## 2. Set Up Yandex Cloud

1. Create account at [Yandex Cloud](https://cloud.yandex.ru)
2. Create folder and get folder ID
3. Create API key in IAM
4. Add to `.env`:
   ```env
   YANDEX_FOLDER_ID=your_folder_id
   YANDEX_API_KEY=your_api_key
   ```

## 3. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Verify database
python scripts/check_database.py
```

## 4. Run Development Server

Terminal 1 (Backend):
```bash
python web_server.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

## 5. Test Bot Locally

### Using ngrok for webhook

```bash
# Install ngrok
npm install -g ngrok

# Start tunnel
ngrok http 10000

# Update .env with ngrok URL
WEBHOOK_DOMAIN=your-id.ngrok.io
```

### Send test message

1. Open your bot in Telegram
2. Send `/start` command
3. Try asking a question

## 6. Explore Features

### AI Chat
Send any educational question to test AI responses

### Voice Messages
Send voice message to test speech recognition

### Images
Send image to test Vision API analysis

### Games
Use `/games` command or Mini App games section

## Common Development Tasks

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/unit/test_ai_service.py -v

# With coverage
pytest tests/ --cov=bot --cov-report=html
```

### Code Formatting

```bash
# Format code
black bot/ frontend/src/
isort bot/

# Check linting
ruff check bot/
pylint bot/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Frontend Development

```bash
cd frontend

# Run dev server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
```

## Debugging

### Enable Debug Logging

```env
LOG_LEVEL=DEBUG
```

### Check Logs

```bash
# View logs
tail -f logs/pandapal.log

# Search logs
grep "ERROR" logs/pandapal.log
```

### Database Inspection

```bash
# Connect to database
psql $DATABASE_URL

# Check tables
\dt

# Query users
SELECT * FROM users LIMIT 10;
```

## Next Steps

- [Architecture Overview](../architecture/overview.md)
- [API Documentation](../api/telegram-bot.md)
- [Testing Guide](../development/testing.md)
