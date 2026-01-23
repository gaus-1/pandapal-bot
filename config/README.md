# Configuration Directory

Project configuration files for different environments and tools.

## Files

### Environment Templates
- `env.template` - Environment variables template for local development

### Python Configuration
- `pyproject.toml` - Python project metadata and tool configuration
  - Black formatter settings
  - isort import sorting
  - pytest configuration

### Type Checking
- `pyrightconfig.json` - Pyright type checker configuration

### Testing
- `pytest.ini` - pytest configuration and test discovery

## Usage

### Local Development Setup

1. Copy environment template:
   ```bash
   cp config/env.template .env
   ```

2. Fill in required values:
   ```env
   DATABASE_URL=postgresql://...
   TELEGRAM_BOT_TOKEN=...
   YANDEX_API_KEY=...
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

Required variables:
- `DATABASE_URL` - PostgreSQL connection string
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `YANDEX_FOLDER_ID` - Yandex Cloud folder ID
- `YANDEX_API_KEY` - Yandex Cloud API key

Optional variables:
- `REDIS_URL` - Redis connection string
- `YOOKASSA_SHOP_ID` - YooKassa shop ID
- `YOOKASSA_SECRET_KEY` - YooKassa secret key
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

See `env.template` for complete list.

## Configuration Files Location

Additional configuration files:
- Root: `.pylintrc`, `.pre-commit-config.yaml`, `.gitignore`
- Bot: `bot/config/` - Application-specific configuration
- Frontend: `frontend/` - Frontend build configuration

## Notes

- Never commit `.env` files with secrets
- Use `env.template` as reference for required variables
- Production secrets managed via Railway environment variables
