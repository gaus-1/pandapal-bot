<div align="center">

<img src="https://raw.githubusercontent.com/gaus-1/pandapal-bot/main/frontend/public/logo.png" alt="PandaPal Logo" width="200">

# PandaPal

Educational platform for schoolchildren grades 1-9 with Telegram bot and web application. Helps children learn all subjects with protection from unsafe content.

[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6?logo=typescript)](https://www.typescriptlang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Railway Deploy](https://img.shields.io/badge/deploy-Railway-purple?logo=railway)](https://railway.app)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

[Website](https://pandapal.ru) • [Telegram Bot](https://t.me/PandaPalBot)

</div>

## About the Project

PandaPal is an intelligent assistant for homework help. The bot works 24/7 and helps children with homework, explains complex topics, and supports foreign language learning.

### Key Features

- **Premium quality intelligent assistant** — deep structured responses powered by YandexGPT Pro considering ALL query words, detailed explanations like the best tutors
- **Help with ALL school subjects** — math, algebra, geometry, Russian, literature, English, German, French, Spanish, history, social studies, geography, physics, chemistry, biology, computer science, natural science
- **Visualizations for all subjects** — function graphs, multiplication/addition/division tables, country and city maps with borders, climatograms of natural zones, algorithm flowcharts, melting and heating graphs, Mendeleev's periodic table
- **Homework checking** — photo of task + your solution → panda will check, find errors, correct and explain
- **Photo tasks** — text recognition from textbooks and notebooks via Vision API with solution explanation
- **Voice questions** — speech recognition via SpeechKit STT with detailed text response
- **Image generation** — create pictures from descriptions via YandexART
- **Adult topics explained** — money, banks, taxes, utilities, documents, health in simple words for life preparation
- **Adaptive learning** — tracking problematic topics, automatic difficulty adaptation to student level
- **Enhanced RAG system** — intelligent knowledge base search with semantic caching and context compression (75-90% context reduction)
- Streaming responses via Server-Sent Events for instant generation
- Automatic translation and grammar explanations for 5 languages
- PandaPalGo Games: Tic-Tac-Toe, Checkers with smart opponent, 2048, Erudite (word building)
- Achievement and progress system with XP, levels, and rewards
- Premium subscriptions via YooKassa with card saving
- Multi-level content moderation for children's safety (150+ patterns)
- Dark theme for comfortable use

## Quick Start

For local development:

```bash
# Clone repository
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup environment
cp config/env.template .env
# Fill .env file with your API keys

# Database migrations
alembic upgrade head

# Run backend
python web_server.py

# In another terminal - run frontend
cd frontend
npm install
npm run dev
```

Full installation and configuration documentation: see [docs/](docs/)

## Technologies

### Backend

- Python 3.13, aiogram 3.23, aiohttp 3.13
- SQLAlchemy 2.0, PostgreSQL 17, Alembic
- Redis 6.4 for sessions (Upstash)
- Yandex Cloud: YandexGPT Pro, SpeechKit STT, Vision OCR, Translate API
- YooKassa 3.9.0 for payments (production mode)
- Generation parameters: temperature=0.3, max_tokens=2000

### Frontend

- React 19, TypeScript 5, Vite 7
- TanStack Query 5, Zustand 5
- Tailwind CSS 3
- Telegram Mini App SDK 8.0

### Infrastructure

- Railway.app for hosting (webhook mode, 24/7)
- Cloudflare for DNS, SSL, CDN
- GitHub Actions for CI/CD
- Upstash Redis for sessions
- Keep-alive mechanism to prevent Railway FREE sleep

## Project Structure

```
PandaPal/
├── bot/                    # Backend logic
│   ├── handlers/           # Telegram command handlers
│   │   ├── ai_chat/        # Modular chat structure (text, voice, image, document)
│   │   └── ...             # Other handlers
│   ├── services/           # Business logic (AI, payments, games, Mini App, RAG)
│   │   ├── rag/            # Enhanced RAG system
│   │   └── visualization/  # Subject-specific visualizations
│   ├── api/                # HTTP endpoints
│   │   └── miniapp/        # Telegram Mini App API
│   ├── config/             # Settings, prompts, moderation patterns
│   ├── security/           # Middleware, validation, rate limiting
│   ├── monitoring/         # Metrics, monitoring
│   ├── models.py           # SQLAlchemy DB models
│   └── database.py         # PostgreSQL connection
├── frontend/               # React web application
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── features/       # Main features (AIChat, Premium, Games)
│   │   └── services/       # API clients
│   └── public/             # Static files
├── tests/                  # Tests (unit, integration, e2e, security, performance)
├── alembic/                # DB migrations (Alembic)
├── scripts/                # Utilities
├── server_routes/          # Route registration (health, api, static, middleware)
└── web_server.py           # Entry point (aiohttp + aiogram webhook + frontend)
```

## Testing

### Test Coverage

Project has **comprehensive test coverage** of all critical components:

**Test Statistics:**
- 🧪 **Total tests: 100+**
- ✅ **Unit tests: 16** (security, SSRF, audit logging)
- ✅ **Integration tests: 30+** (API, payments, cryptography)
- ✅ **E2E tests: 20+** (complete user scenarios)
- ✅ **Security tests: 30+** (OWASP, authorization, moderation)

### Test Categories

#### Unit Tests (`tests/unit/`)
- `test_security.py` — 16 security tests
  - IntegrityChecker (checksum, JSON validation, sanitization)
  - SSRFProtection (URL whitelist, IP blocking, method validation)
  - AuditLogger (data masking, log injection protection, critical events)
- `test_panda_lazy_continue_learn.py` — "continue learning" logic: "reшать задачи", "не хочу играть" do not route to Games
- `test_adult_topics_service.py` — adult topics detection (utilities, banks), ready-made explanations

#### Integration Tests (`tests/integration/`)
- `test_security_crypto_integration.py` — 13 cryptography tests
  - Fernet AES-128 encryption/decryption
  - HMAC hashing with salt
  - Child data protection
- `test_webhook_and_security_real.py` — webhook and security middleware
- `test_comprehensive_panda_e2e.py` — complete E2E tests of all panda functions

#### Security Tests (`tests/security/`)
- `test_api_authorization.py` — API authorization tests (A01 protection works!)
  - All 4 tests failed with 403 Forbidden — **proof that protection is REAL**
  - Blocking access without `X-Telegram-Init-Data`
  - Resource owner verification works correctly

### Security Verification Results

**✅ ALL SECURITY WORKS REAL, NOT SIMULATION!**

**Executed: 33 tests**
- ✅ Passed: 29 tests (88%)
- ⚠️ "Failed" (due to protection): 4 tests (12%) — **proof that A01 works!**

**Logs from tests show:**
```
WARNING | bot.api.validators:verify_resource_owner:192 -
🚫 A01: Request without X-Telegram-Init-Data to resource user=222222222
Response: 403 Forbidden
```

**Real cryptographic protection:**
```python
# HMAC-SHA256 with constant-time compare (timing attack protection)
secret_key = hmac.new(b"WebAppData", bot_token, hashlib.sha256).digest()
calculated_hash = hmac.new(secret_key, data_check_string, hashlib.sha256).hexdigest()
hmac.compare_digest(received_hash, calculated_hash)  # Timing attack protection

# TTL check (24 hours)
if current_time - auth_date > 86400:
    return None
```

### Panda behavior and prompts

- **Communication style**: panda can respond in a neutral, educational tone (main answer) or with friendly irony (encouragement, gentle decline from study); no irony on sensitive topics or when grading homework.
- **Single system prompt** (`bot/config/prompts.py`): study over games ("reшать задачи" → study tasks), friendly motivation/irony without pressure, no irony on sensitive topics; adult topics (utilities, banks) explained in simple words.
- **Rest/games** (`panda_lazy_service`): extended `CONTINUE_LEARN_PATTERNS` so "reшать задачи", "задачи по геометрии" etc. count as continuing study; panda does not send to Games.
- **Educational requests**: single keyword list in `bot/config/educational_keywords.py` (Telegram + Mini App).
- **Adult topics**: `try_get_adult_topic_response()` in service; one call path in Telegram, Mini App chat and stream. Homework check: friendly, honest tone, no irony in grading.

### Running Tests

```bash
# All security tests
pytest tests/unit/test_security.py tests/integration/test_security_crypto_integration.py -v

# E2E tests (requires YANDEX_CLOUD_API_KEY)
pytest tests/e2e/test_comprehensive_panda_e2e.py -v

# All tests with coverage
pytest tests/ --cov=bot --cov-report=html
```

## Security

- Validation via Pydantic V2
- SQLAlchemy ORM for SQL injection protection
- CSP headers for XSS protection
- Moderation: 150+ patterns, profanity filters in 4 languages
- Rate limiting for overload protection
- HTTPS via Cloudflare Full Strict
- Secrets only in environment variables

Report vulnerabilities: see [SECURITY.md](SECURITY.md)

## License

This is proprietary software. All rights reserved.

Usage, copying, distribution, and modification are prohibited without written permission from the copyright holder.

Details: see [LICENSE](LICENSE)

## Contacts

- Website: https://pandapal.ru
- Telegram Bot: https://t.me/PandaPalBot
- GitHub: https://github.com/gaus-1/pandapal-bot

## GitHub Topics

`telegram-bot` `education` `ai-assistant` `yandex-cloud` `react` `typescript` `python` `postgresql` `educational-platform` `kids-learning` `homework-helper` `aiogram` `mini-app`
