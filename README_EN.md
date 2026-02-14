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
- **Visualizations for all subjects** — function graphs, multiplication/addition/division tables, square roots values table (√1–√50), country and city maps with borders, climatograms of natural zones, algorithm flowcharts, melting and heating graphs, Mendeleev's periodic table
- **Homework checking** — photo of task + your solution → panda will check, find errors, correct and explain
- **Photo tasks** — text recognition from textbooks and notebooks via Vision API with solution explanation
- **Voice questions** — speech recognition via SpeechKit STT with confirmation ("Send" / "Edit") before sending to AI
- **Image generation** — create pictures from descriptions via YandexART
- **Adult topics explained** — money, banks, taxes, utilities, documents, health in simple words for life preparation
- **Adaptive learning** — tracking problematic topics, automatic difficulty adaptation to student level
- **Enhanced RAG system** — Professional RAG with semantics and vectors: hybrid search (pgvector vector + keyword), `knowledge_embeddings` table, VectorSearchService, context compression (75–90%), semantic cache
- Streaming responses via Server-Sent Events for instant generation
- Automatic translation and grammar explanations for 5 languages
- PandaPalGo Games: Tic-Tac-Toe, Checkers with smart opponent, 2048, Erudite (word building)
- Achievement and progress system with XP, levels, and rewards
- Premium: 299 RUB/month only, via YooKassa with card saving
- **Referral program** — personal links for teachers and partners; payouts for subscriptions via link, monthly report (1st–30th/31st)
- Multi-level content moderation for children's safety (150+ patterns)
- Dark theme for comfortable use

### Referral Program

Teachers and partners get a personal link: `https://t.me/PandaPalBot?startapp=ref_<telegram_id>`. Users who open the link and pay for a subscription are tracked; the referrer receives a payout (amount configurable via `REFERRAL_PAYOUT_RUB`). Monthly report for the calendar month: `python scripts/referral_report.py [--year YYYY] [--month MM]`. Payouts to referrers are done manually from the report data.

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

### Knowledge base indexing (RAG)

For semantic search, index materials into `knowledge_embeddings` once:

```bash
railway link   # select PandaPal project
railway run python scripts/update_knowledge_base.py
```

Script scrapes nsportal.ru, school203.spb.ru and indexes into pgvector.

### Environment variables (Railway / local)

Required variables are described in `config/env.template`. Copy to `.env` and fill in:

- `DATABASE_URL`, `TELEGRAM_BOT_TOKEN` — required
- `YANDEX_CLOUD_API_KEY`, `YANDEX_CLOUD_FOLDER_ID` — for YandexGPT, SpeechKit, Vision, Embeddings API
- `SECRET_KEY` — for sessions and encryption
- For Premium: `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`, etc. (see template)

## Technologies

### Backend

- Python 3.13, aiogram 3.24, aiohttp 3.13
- SQLAlchemy 2.0, PostgreSQL 17 + pgvector, Alembic
- Redis 7.1 for sessions (Upstash)
- Yandex Cloud: YandexGPT Pro, SpeechKit STT, Vision OCR, Translate API, Embeddings API (text-search-doc/query)
- YooKassa 3.9.0 for payments (production mode)
- Generation parameters: temperature=0.4, max_tokens=8192

### Frontend

- React 19, TypeScript 5, Vite 7
- TanStack Query 5, Zustand 5
- Tailwind CSS 3
- Telegram Mini App SDK 8.0
- **Responsive design**: 280px+ (foldable phones), 375px (mobile), 768px (tablet), 1920px (desktop); E2E `website.responsive.spec.ts`

### Infrastructure

- Railway.app for hosting (webhook mode, 24/7): web service + pgvector (PostgreSQL with extension)
- Cloudflare for DNS, SSL, CDN
- GitHub Actions for CI/CD
- Upstash Redis for sessions
- Keep-alive mechanism to prevent Railway FREE sleep

## Project Structure

```
PandaPal/
├── bot/                     # Backend logic
│   ├── handlers/            # Telegram command handlers
│   │   ├── ai_chat/         # Modular chat structure
│   │   │   ├── text.py      # Text messages (orchestrator pipeline)
│   │   │   ├── voice.py     # Voice and audio (FSM confirmation before sending to AI)
│   │   │   ├── image.py     # Image analysis
│   │   │   ├── document.py  # Document handling
│   │   │   └── helpers.py   # Helpers (Premium, viz, translation, sending, feedback)
│   │   └── ...              # Other handlers
│   ├── services/            # Business logic (AI, payments, games, Mini App, RAG)
│   │   ├── rag/             # Enhanced RAG system
│   │   │   ├── vector_search.py  # Semantic search (pgvector, knowledge_embeddings)
│   │   │   ├── query_expander.py # Multi-query expansion
│   │   │   ├── reranker.py       # Result reranking
│   │   │   ├── semantic_cache.py # Semantic cache
│   │   │   └── compressor.py     # Context compression (75-90%)
│   │   ├── embeddings_service.py  # Vector embeddings (Yandex Embeddings API)
│   │   ├── cache/           # Caching package (Redis + Memory LRU, SOLID SRP)
│   │   ├── miniapp/         # Mini App services (package)
│   │   │   ├── chat_context_service.py  # Chat context
│   │   │   ├── intent_service.py        # Intent detection
│   │   │   ├── audio_service.py         # Audio processing
│   │   │   ├── photo_service.py         # Photo/homework processing
│   │   │   └── visualization_service.py # Visualization detection
│   │   ├── games_service/   # PandaPalGo games (package, mixin architecture)
│   │   │   ├── session.py   # Session CRUD, stats, achievements
│   │   │   ├── tic_tac_toe.py, checkers.py, game_2048.py, erudite.py
│   │   │   └── __init__.py  # Facade combining mixins
│   │   ├── game_engines/    # Game engines (TicTacToe, Checkers, 2048, Erudite)
│   │   ├── visualization/   # Subject-specific visualizations
│   │   │   ├── detector.py       # Detection orchestrator
│   │   │   ├── detectors/        # request_words, schemes, diagrams, maps, physics, math_graphs, tables_and_diagrams (√1–√50)
│   │   │   ├── math/, sciences/, social/, languages/, other/
│   │   │   └── base.py, schemes.py
│   │   ├── referral_service.py   # Referral links (ref_<id>, whitelist)
│   │   └── ...              # Other services (moderation, payment, user, etc.)
│   ├── api/                 # HTTP endpoints
│   │   ├── miniapp/         # Telegram Mini App API
│   │   │   ├── chat_stream.py    # Streaming AI chat (SSE) — entry point
│   │   │   ├── stream_handlers/  # Streaming modules (package)
│   │   │   │   ├── ai_chat_stream.py  # Main SSE orchestrator
│   │   │   │   ├── _pre_checks.py, _media.py, _routing.py
│   │   │   │   ├── _visualization.py, _fallback.py, _history.py
│   │   │   │   └── _utils.py
│   │   │   ├── homework.py, chat.py, progress.py, other.py
│   │   │   └── helpers.py
│   │   ├── games_endpoints.py, premium_endpoints.py
│   │   ├── panda_endpoints.py, auth_endpoints.py
│   │   └── validators.py
│   ├── config/              # Settings, prompts, moderation patterns
│   ├── security/            # Middleware, validation, rate limiting, crypto
│   ├── monitoring/          # Metrics (Prometheus), Sentry
│   ├── keyboards/           # Bot keyboards (incl. news_bot)
│   ├── localization/       # Localization (locales)
│   ├── middleware/          # aiogram middleware
│   ├── news_bot/            # Standalone news bot (handlers, services)
│   ├── models/              # SQLAlchemy DB models (package: user, chat, games, payments, referral, etc.)
│   └── database/            # PostgreSQL connection (package)
│       ├── engine.py, alembic_utils.py, sql_migrations.py, service.py
├── frontend/                # React web application
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── features/        # AIChat, Premium, Games, Achievements, Donation, Emergency
│   │   ├── services/        # API clients
│   │   ├── hooks/           # useChatStream, etc.
│   │   ├── store/           # Zustand
│   │   ├── config/          # App config
│   │   └── types/           # TypeScript types
│   └── public/              # Static: logo, favicon, panda-chat-reactions, panda-tamagotchi
├── tests/                   # Tests (1000+)
│   ├── unit/                # Unit tests (~60 files)
│   ├── integration/         # Integration tests (~38 files)
│   ├── e2e/                 # End-to-end tests
│   ├── security/            # Security tests (OWASP, SQL injection, DDoS)
│   ├── resilience/          # Service resilience tests
│   ├── performance/         # Performance and load tests
│   └── fixtures/            # Shared fixtures
├── alembic/                 # DB migrations (Alembic)
├── scripts/                 # Utilities (update_knowledge_base.py, referral_report, check_*, etc.)
├── server_routes/           # Route registration (health, api, static, middleware)
└── web_server.py            # Entry point (aiohttp + aiogram webhook + frontend)
```

## Testing

### Test Coverage

Project has **comprehensive test coverage** of all critical components:

**Test Statistics:**
- 🧪 **Total tests: 1000+**
- ✅ **Unit tests: 60+ files** (security, SSRF, audit logging, DB, cache, moderation, games, services)
- ✅ **Integration tests: 38+ files** (API, payments, cryptography, real Yandex Cloud API)
- ✅ **E2E tests: 5 files** (complete user scenarios)
- ✅ **Security tests: 6 files** (OWASP, SQL injection, DDoS, authorization)
- ✅ **Resilience tests: 5 files** (service resilience, degradation)
- ✅ **Performance tests: 7 files** (endpoint load, DB, payments)

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

**Example (security tests):**
- ✅ Authorization tests correctly return 403 — **proof that A01 protection works**

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
- **Rest/games** (`panda_lazy_service`): extended `CONTINUE_LEARN_PATTERNS` so "решать задачи", "задачи по геометрии" etc. count as continuing study; panda does not send to Games.
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

## Recent changes (2025–2026)

### Fixes and improvements (February 2026)

- **RAG semantic_cache**: `embedding_cache` queries use `CAST(:vec AS vector)` instead of `:vec::vector` to avoid PostgreSQL syntax errors with bound parameters.
- **Digit column artifact**: post-processing `_merge_digit_only_lines` merges lines that are only digits (model artifact: year 1837 as 1\\n8\\n3\\n7) into one line.
- **Streaming**: final response sent as `event: final`; frontend substitutes it into the last AI message to prevent UI flash.
- **Frontend**: Literata font (font-chat) for all Panda response text, size text-sm/sm:text-base.

### RAG, pgvector, Railway, visualizations (February 2026)

- **RAG with pgvector**: `knowledge_embeddings` table, VectorSearchService, hybrid search (vector + keyword), `update_knowledge_base.py` script for indexing (nsportal.ru, school203.spb.ru, Wikipedia)
- **Railway deployment**: pgvector on Railway, DATABASE_URL via `pgvector.railway.internal` (private network), SSL disable for internal network
- **Visualization**: square roots values table √1–√50 (algebra.py), pattern for "list/table of square roots" in detectors
- **RAG**: extended `_extract_topic_from_question` patterns for "list", "table of values", "all values"; `format_knowledge_for_ai` limit 300→1000 chars; list protection in ContextCompressor
- **Prompts**: rules for "list"/"table of values" requests — 10–15 concrete examples
- **Feedback form**: `offer_feedback_form` uses `total_requests` instead of `message_count`
- **Voice (FSM)**: confirmation of recognized text — inline buttons "Send" / "Edit" before sending to AI
- **Embeddings API**: `get_embedding` in YandexCloudService, EmbeddingService, `embedding_cache` table (pgvector)
- **SemanticCache**: full rewrite — pgvector + Yandex Embeddings API (cosine similarity), Jaccard removed
- **QueryExpander**: synonyms for "list", "square roots"
- **Tests**: `test_embeddings_real.py`, `test_semantic_cache_real.py`, `test_panda_responses_real.py` (E2E)
- **Chain-of-Thought (CoT)**: rules and few-shot examples in prompts.py; Zero-shot trigger for calculation tasks
- **Russian language**: strict grammar rules, no anglicisms (apdeyt→obnovleniye, fidbek→obratnaya svyaz)
- **E2E response validation**: ResponseQualityValidator, negative tests, empty/irrelevant checks, CoT word problems

### SOLID SRP refactoring (February 2026)

- **`bot/services/games_service.py`** (1025 lines) → package `bot/services/games_service/`: `session.py`, `tic_tac_toe.py`, `checkers.py`, `game_2048.py`, `erudite.py`; mixin architecture with `GamesServiceBase` + game-specific mixins; facade via `__init__.py`
- **`bot/api/miniapp/stream_handlers/ai_chat_stream.py`** (1743 lines) → orchestrator + 7 modules: `_pre_checks.py`, `_media.py`, `_routing.py`, `_visualization.py`, `_fallback.py`, `_history.py`, `_utils.py`
- **`bot/database.py`** (633 lines) → package `bot/database/`: `engine.py`, `alembic_utils.py`, `sql_migrations.py`, `service.py`; backward-compatible re-exports via `__init__.py`
- **`bot/services/cache_service.py`** (652 lines) → package `bot/services/cache/`: `memory.py`, `service.py`, `specialized.py`; compatibility shim preserved
- **`bot/services/visualization/detector.py`** (1809 lines) → 300-line orchestrator + 7 detector modules in `detectors/`: `request_words`, `schemes`, `diagrams`, `maps`, `physics`, `math_graphs`, `tables_and_diagrams`
- **`bot/handlers/ai_chat/text.py`** (775 lines) → 509 lines; 6 helpers extracted to `helpers.py` (Premium limits, translation, visualization, response sending, feedback)
- **`bot/services/adult_topics_service.py`** (919 lines) → 190 lines; 26 topics extracted to `bot/config/adult_topics_data.py`
- **`web_server.py`** — entry point, webhook, healthcheck
- Added SOLID/PEP 20 architecture rules to prevent regressions

### Architecture and code quality (2026)

- **Security**: admin command access restricted to `admin_telegram_ids`; payment amount validation (1–10000 Stars); Telegram initData `auth_date` future check; IP validation from headers (ipaddress)
- **Performance**: `FORBIDDEN_PATTERNS` and `EDUCATIONAL_KEYWORDS` converted to `frozenset` (O(1) lookup); removed unused queue code in overload_protection
- **Modernization**: `datetime.now(UTC)` everywhere instead of deprecated `utcnow()`; no hardcoded secrets in config defaults (values from env only)
- **Code**: shared Premium limit helper in `ai_chat/helpers.py`; unified voice/audio logic in `voice.py`; memoize delegates to cache_result in decorators; achievements leaderboard uses real XP/level from GamificationService
- **Frontend**: centralized `logger` (debug logs only in dev); removed debug `console.log` from production code
- **Tests**: fixed flaky reminder test; pytest config consolidated (root `pytest.ini` as main)

## Referral Program

- Personal links: `https://t.me/PandaPalBot?startapp=ref_<telegram_id>`
- Referrer whitelist in DB; payouts recorded on payment success
- Monthly report: `python scripts/referral_report.py [--year YYYY] [--month MM]`
- Payout amount: `REFERRAL_PAYOUT_RUB` (default 100)

## Security

- Validation via Pydantic V2
- SQLAlchemy ORM for SQL injection protection
- CSP headers for XSS protection
- Moderation: 150+ patterns, profanity filters in 4 languages
- Rate limiting: 300 req/min API, 100 req/min AI, 20 req/min auth
- HTTPS via Cloudflare Full Strict
- Secrets only in environment variables

Report vulnerabilities: see [SECURITY.md](.github/SECURITY.md)

## License

This is proprietary software. All rights reserved.

Usage, copying, distribution, and modification are prohibited without written permission from the copyright holder.

Details: see [LICENSE](LICENSE)

## Contacts

- Website: https://pandapal.ru
- Telegram Bot: https://t.me/PandaPalBot
- GitHub: https://github.com/gaus-1/pandapal-bot

## GitHub Topics

`telegram-bot` `education` `ai-assistant` `yandex-cloud` `react` `typescript` `python` `postgresql` `pgvector` `rag` `educational-platform` `kids-learning` `homework-helper` `aiogram` `mini-app`
