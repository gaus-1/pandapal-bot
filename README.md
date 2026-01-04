<div align="center">

<img src="frontend/public/logo.png" alt="PandaPal Logo" width="120" height="120">

# PandaPal

**Образовательная платформа для школьников 1-9 классов**

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=white)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red?logo=law&logoColor=white)](LICENSE)

[Сайт](https://pandapal.ru) • [Telegram Бот](https://t.me/PandaPalBot) • [Документация](docs/)

</div>

---

## О проекте

PandaPal — образовательная платформа с Telegram-ботом и веб-приложением для школьников 1-9 классов. Помогает детям учиться по всем предметам с защитой от небезопасного контента.

### Возможности

- **Мультимодальность**: текст, голос (SpeechKit), изображения (Vision API)
- **Безопасность**: 150+ фильтров контента, 5-уровневая модерация
- **Telegram Mini App**: React веб-приложение внутри Telegram
- **Геймификация**: достижения, уровни, XP
- **Экстренные номера**: 112, 101, 102, 103
- **Premium**: YooKassa (карты, СБП, переводы) и Telegram Stars
- **Авторизация**: Telegram Login Widget для сайта, Redis сессии
- **Донаты**: Telegram Stars для поддержки проекта

---

## Технологии

### Backend
- **Python 3.13**, **aiogram 3.23**, **aiohttp 3.13** — бот и webhook сервер
- **SQLAlchemy 2.0**, **PostgreSQL 17**, **Alembic** — БД
- **Redis 6.4** — персистентные сессии (Upstash)
- **Yandex Cloud** — YandexGPT, SpeechKit, Vision
- **YooKassa** — платежи (карты, СБП)

### Frontend
- **React 19**, **TypeScript 5**, **Vite 7**
- **TanStack Query 5**, **Zustand 5**
- **Tailwind CSS 3**
- **Telegram Mini App SDK**

### Infrastructure
- **Railway.app** — хостинг (24/7, webhook, auto deploy)
- **Cloudflare** — DNS, SSL, CDN
- **GitHub Actions** — CI/CD

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
│   ├── handlers/         # Команды (start, ai_chat, payment)
│   ├── services/         # Логика (AI, модерация, Premium, сессии)
│   ├── config/           # Настройки, промпты
│   ├── security/         # Middleware, модерация
│   ├── api/              # Endpoints (Mini App, Premium, Auth)
│   ├── models.py         # SQLAlchemy модели
│   └── database.py       # БД
├── frontend/
│   ├── src/
│   │   ├── components/   # UI (Header, Hero)
│   │   ├── features/     # AIChat, Premium, Donation
│   │   └── services/     # API клиенты
│   └── public/           # Статика
├── tests/                # Unit, integration, E2E
├── alembic/              # Миграции
└── scripts/              # Утилиты
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
- `ai_service.py` — Yandex Cloud (GPT, Speech, Vision)
- `moderation_service.py` — фильтрация контента
- `payment_service.py` — YooKassa интеграция
- `subscription_service.py` — Premium подписки
- `session_service.py` — Redis сессии (fallback на in-memory)
- `telegram_auth_service.py` — Telegram Login Widget

**API Endpoints:**
- `miniapp_endpoints.py` — Mini App API
- `premium_endpoints.py` — YooKassa webhook, создание платежей
- `auth_endpoints.py` — Telegram Login Widget, сессии

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

- **Валидация** — Pydantic V2
- **SQL Injection** — SQLAlchemy ORM
- **XSS** — CSP headers
- **Модерация** — 150+ паттернов, 5 уровней
- **Rate Limiting** — 60 req/min API, 30 req/min AI
- **CSRF** — Origin/Referer проверка
- **HTTPS** — Cloudflare Full Strict
- **Секреты** — только в .env
- **OWASP Top 10** — покрыто тестами

---

## Лицензия

**Проприетарная лицензия** — см. [LICENSE](LICENSE).

© 2026 Савин Вячеслав Евгеньевич. Все права защищены.

Коммерческое использование, копирование, модификация запрещены без письменного разрешения.

Контакт: 79516625803@ya.ru

---

## Контакты

- **Сайт:** [pandapal.ru](https://pandapal.ru)
- **Бот:** [@PandaPalBot](https://t.me/PandaPalBot)
- **GitHub:** [github.com/gaus-1/pandapal-bot](https://github.com/gaus-1/pandapal-bot)

---

<div align="center">

**Сделано с ❤️ для детей и их родителей**

⭐ **Если проект полезен, поставьте звезду!** ⭐

</div>
