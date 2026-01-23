<div align="center">

<img src="https://raw.githubusercontent.com/gaus-1/pandapal-bot/main/frontend/public/logo.png" alt="PandaPal Logo" width="200">

# PandaPal

Educational platform for schoolchildren grades 1-9 with Telegram bot and web application. Helps children learn all subjects with protection from unsafe content.

[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6?logo=typescript)](https://www.typescriptlang.org/)
[![CI/CD](https://img.shields.io/github/actions/workflow/status/gaus-1/pandapal-bot/main-ci-cd.yml?label=CI%2FCD)](https://github.com/gaus-1/pandapal-bot/actions)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

[Website](https://pandapal.ru) • [Telegram Bot](https://t.me/PandaPalBot)

</div>

## About the Project

PandaPal is an intelligent assistant for homework help. The bot works 24/7 and helps children with homework, explains complex topics, and supports foreign language learning.

### Key Features

- **Enhanced RAG system** — intelligent knowledge base search with semantic caching, result reranking, and context compression for token savings (75-90%)
- **Premium quality intelligent assistant** — deep structured responses powered by YandexGPT Pro considering ALL query words, detailed explanations and visualizations
- **Adult topics explained** — accessible explanation of life questions for children (money, banks, documents, utilities, work, health) in simple words with examples
- **Visualizations with explanations** — automatic generation of charts, tables, diagrams (including pie charts), schemes, and maps with detailed explanations
- **Image generation** — create pictures from descriptions via YandexART (requires ai.imageGeneration.user role)
- **Homework checking** — automatic homework verification from photos with error detection, corrections, and explanations
- **Adaptive learning** — tracking problematic topics, automatic difficulty adaptation to student level
- Streaming responses via Server-Sent Events for fast generation
- Support for text, voice, and images with analysis via Vision API
- Automatic translation and grammar explanations for 5 languages (English, German, French, Spanish, Russian)
- PandaPalGo Games: Tic-Tac-Toe, Checkers, 2048, Erudite with opponent
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
- Parameters: temperature=0.3, max_tokens=2000

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
└── web_server.py           # Entry point (aiohttp + aiogram webhook + frontend)
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
