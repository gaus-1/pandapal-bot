<div align="center">

<img src="frontend/public/logo.png" alt="PandaPal Logo" width="120" height="120">

# PandaPal

**Образовательная платформа для школьников 1-9 классов**

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=white)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red?logo=law&logoColor=white)](LICENSE)

**🔗 Ссылки:**
- 🌐 [Сайт](https://pandapal.ru)
- 🤖 [Telegram Бот](https://t.me/PandaPalBot)
- 📚 [Документация](docs/)
- 🛡️ [Безопасность](SECURITY.md)
- 🤝 [Вклад в проект](CONTRIBUTING.md)

</div>

---

## О проекте

PandaPal — образовательная платформа с Telegram-ботом и веб-приложением для школьников 1-9 классов. Помогает детям учиться по всем предметам с защитой от небезопасного контента.

### Почему этот проект?

✅ **Безопасное обучение** — 150+ фильтров контента, 5-уровневая модерация защищают детей от опасного контента
✅ **Доступность 24/7** — AI-ассистент всегда готов помочь с домашним заданием по любому предмету
✅ **Мультимодальность** — поддержка текста, голоса и изображений делает обучение интерактивным
✅ **Иностранные языки** — автоматическое определение языка и перевод с объяснением грамматики
✅ **Геймификация** — достижения, уровни и игры мотивируют детей учиться

### Возможности

- **AI-ассистент**: YandexGPT для помощи по всем школьным предметам (1-9 класс)
- **Мультимодальность**: текст, голос (SpeechKit), изображения (Vision API)
- **Иностранные языки**: автоматическое определение и перевод (английский, немецкий, французский, испанский) с объяснением грамматики
- **Переводчик**: Yandex Translate с поддержкой 4 языков и детальными объяснениями
- **PandaPalGo**: игры (Крестики-нолики, Шашки, 2048) с AI противником, адаптивный UI
- **Безопасность**: 150+ фильтров контента, 5-уровневая модерация, фильтры мата на 4 языках
- **Telegram Mini App**: React веб-приложение внутри Telegram
- **Геймификация**: достижения, уровни, XP, статистика игр
- **Экстренные номера**: 112, 101, 102, 103
- **Premium**: YooKassa (карты, СБП) и Telegram Stars
- **Авторизация**: Telegram Login Widget для сайта, Redis сессии (Upstash)
- **Обратная связь**: Yandex Forms для сбора отзывов
- **Донаты**: Telegram Stars для поддержки проекта
- **Тестирование**: 37+ интеграционных тестов для всех предметов и иностранных языков

---

## Технологии

### Backend
- **Python 3.13**, **aiogram 3.23**, **aiohttp 3.13** — бот и webhook сервер
- **SQLAlchemy 2.0**, **PostgreSQL 17**, **Alembic** — БД (connection pool: 100/200)
- **Redis 6.4** — персистентные сессии (Upstash, fallback на in-memory)
- **Yandex Cloud** — YandexGPT (yandexgpt-lite), SpeechKit STT, Vision OCR, Translate API
- **Yandex Forms** — сбор обратной связи
- **YooKassa 3.0** — платежи (карты, СБП, чеки 54-ФЗ)

### Frontend
- **React 19**, **TypeScript 5**, **Vite 7**
- **TanStack Query 5** (API клиент), **Zustand 5** (state management)
- **Tailwind CSS 3** (dark/light themes)
- **Telegram Mini App SDK 8.0** (web.telegram.org поддержка)
- **Playwright** — E2E тесты

### Infrastructure
- **Railway.app** — хостинг (24/7, webhook, auto deploy, keep-alive ping)
- **Cloudflare** — DNS, SSL, CDN, Full Strict mode
- **GitHub Actions** — CI/CD, тесты, Docker build attestations
- **Upstash Redis** — персистентные сессии (fallback на in-memory)

---

## Быстрый старт

```bash
# Клонировать
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot

# Backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# .env
cp config/env.template .env
# Заполнить .env

# БД
alembic upgrade head

# Запуск
python web_server.py
```

Frontend (отдельный терминал):
```bash
cd frontend
npm install
npm run dev
```

---

## Структура

```
PandaPal/
├── bot/
│   ├── handlers/         # Команды (start, ai_chat, translate, feedback, payment, games)
│   ├── services/         # Логика (AI, модерация, перевод, Premium, сессии, игры)
│   ├── config/           # Настройки, промпты (поддержка иностранных языков) (поддержка иностранных языков)
│   ├── security/         # Middleware, модерация, аудит
│   ├── api/              # Endpoints (Mini App, Premium, Auth, Games)
│   ├── models.py         # SQLAlchemy модели (User, ChatHistory, GameSession, GameStats)
│   └── database.py       # БД (PostgreSQL, connection pool)
├── frontend/
│   ├── src/
│   │   ├── components/   # UI (Header, Hero)
│   │   ├── features/     # AIChat, Premium, Donation, Games (адаптивный UI) (адаптивный UI)
│   │   └── services/     # API клиенты
│   └── public/           # Статика
├── tests/                # Unit, integration, E2E, security, performance
│   ├── integration/      # 37+ тестов: все предметы, иностранные языки
│   ├── unit/             # Unit тесты сервисов
│   ├── e2e/              # End-to-end тесты
│   └── security/         # Тесты безопасности
├── alembic/              # Миграции БД
└── scripts/              # Утилиты (миграции, аналитика, проверки)
```

---

## Разработка

### Локально

```bash
# Backend
python web_server.py

# Frontend
cd frontend && npm run dev

# БД
docker-compose up -d postgres
```

### Code Quality

```bash
pre-commit install
pre-commit run --all-files

black bot/
isort bot/
flake8 bot/
```

### Тестирование

```bash
# Все тесты
pytest tests/ -v

# Интеграционные тесты (требуют реальные API ключи)
pytest tests/integration/test_subjects_real_api.py -v
pytest tests/integration/test_foreign_languages_real.py -v

# Покрытие
pytest tests/ --cov=bot --cov-report=html
```

---

## Архитектура

### Backend (PEP 20)

**Zen of Python** в коде:
- **Simple is better than complex** — services слой, прямые зависимости
- **Explicit is better than implicit** — type hints, Pydantic валидация
- **Readability counts** — docstrings для публичных API
- **Errors should never pass silently** — try/except с логированием
- **Flat is better than nested** — модульная структура

### Ключевые компоненты

**Entry Point:**
- `web_server.py` — aiohttp сервер, webhook для Telegram

**Services (бизнес-логика):**
- `ai_service_solid.py` — Yandex Cloud (GPT, Speech, Vision)
- `translate_service.py` — Yandex Translate (автоопределение языка, 4 языка: EN, DE, FR, ES)
- `moderation_service.py` — фильтрация контента (150+ паттернов, мат на 4 языках)
- `yandex_cloud_service.py` — интеграция Yandex Cloud (OCR с переводом иностранных текстов)
- `speech_service.py` — распознавание речи (SpeechKit STT)
- `vision_service.py` — анализ изображений (Vision OCR)
- `payment_service.py` — YooKassa интеграция (карты, СБП)
- `subscription_service.py` — Premium подписки
- `session_service.py` — Redis сессии (Upstash, fallback на in-memory)
- `telegram_auth_service.py` — Telegram Login Widget
- `games_service.py` — PandaPalGo игры (TicTacToe, Checkers, 2048)
- `gamification_service.py` — достижения, уровни, XP

**API Endpoints:**
- `miniapp_endpoints.py` — Mini App API (AI chat, голос, изображения)
- `premium_endpoints.py` — YooKassa webhook, создание платежей
- `auth_endpoints.py` — Telegram Login Widget, сессии
- `games_endpoints.py` — PandaPalGo API (создание игр, ходы, статистика)

**Security:**
- `middleware.py` — CSP, CORS, rate limiting
- `telegram_auth.py` — HMAC-SHA256 валидация
- `overload_protection.py` — защита от перегрузки

---

## Деплой

### Railway.app

1. Push в `main` → auto deploy
2. Environment Variables в Railway Dashboard
3. Custom Domain: [pandapal.ru](https://pandapal.ru)

### Переменные

```env
DATABASE_URL=postgresql://...
TELEGRAM_BOT_TOKEN=...
YANDEX_CLOUD_API_KEY=...
YANDEX_CLOUD_FOLDER_ID=...
SECRET_KEY=...
WEBHOOK_DOMAIN=...
FRONTEND_URL=...
YOOKASSA_SHOP_ID=...
YOOKASSA_SECRET_KEY=...
YOOKASSA_INN=...
REDIS_URL=rediss://...  # Upstash Redis
```

Полный список: [config/env.template](config/env.template)

---

## Безопасность

- **Валидация** — Pydantic V2 для всех входных данных
- **SQL Injection** — SQLAlchemy ORM, параметризованные запросы
- **XSS** — CSP headers, санитизация HTML
- **Модерация** — 150+ паттернов, 5-уровневая система фильтрации, мат-фильтры на 4 языках (RU, EN, DE, FR, ES)
- **Rate Limiting** — 60 req/min API, 30 req/min AI, sliding window
- **CSRF** — Origin/Referer проверка, HMAC-SHA256 для Telegram
- **DDoS Protection** — overload protection middleware, IP блокировка
- **HTTPS** — Cloudflare Full Strict, обязательный SSL
- **Секреты** — только в .env, валидация при старте
- **OWASP Top 10** — покрыто тестами (security/), аудит логов

**Сообщить об уязвимости:** см. [SECURITY.md](SECURITY.md)

---

## Лицензия

**Проприетарная лицензия** — см. [LICENSE](LICENSE).

© 2026 Савин Вячеслав Евгеньевич. Все права защищены.

Коммерческое использование, копирование, модификация запрещены без письменного разрешения.

Контакт: 79516625803@ya.ru

---

## Контакты

- 🌐 **Сайт:** [pandapal.ru](https://pandapal.ru)
- 🤖 **Бот:** [@PandaPalBot](https://t.me/PandaPalBot)
- 💻 **GitHub:** [github.com/gaus-1/pandapal-bot](https://github.com/gaus-1/pandapal-bot)

---

<div align="center">

**Сделано с ❤️ для детей и их родителей**

⭐ **Если проект полезен, поставьте звезду!** ⭐

</div>
