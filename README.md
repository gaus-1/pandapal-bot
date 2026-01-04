<div align="center">

<img src="frontend/public/logo.png" alt="PandaPal Logo" width="120" height="120">

# PandaPal

**Образовательная платформа для школьников 1-9 классов**

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=white)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/Tests-330%2B%20passed-brightgreen?logo=pytest)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-74%25%20critical-yellow?logo=codecov)](htmlcov/)
[![License](https://img.shields.io/badge/License-Proprietary-red?logo=law&logoColor=white)](LICENSE)

[Сайт](https://pandapal.ru) • [Telegram Бот](https://t.me/PandaPalBot) • [Документация](docs/)

</div>

---

## О проекте

PandaPal — образовательная платформа, объединяющая Telegram-бота и веб-приложение для безопасного обучения школьников 1-9 классов. Платформа помогает детям получать ответы на вопросы, решать задачи по всем школьным предметам, при этом обеспечивая защиту от небезопасного контента.

### Основные возможности

- **Мультимодальное взаимодействие**: текст, голос (SpeechKit), изображения (Vision API)
- **Безопасность**: 150+ фильтров контента, 5-уровневая модерация, адаптация под возраст (6-18 лет)
- **Telegram Mini App**: полнофункциональное веб-приложение внутри Telegram (React 19)
- **Геймификация**: система достижений, уровней, XP и наград для мотивации
- **Экстренные номера**: быстрый доступ к службам спасения России (112, 101, 102, 103)
- **Premium подписки**: расширенные возможности через ЮKassa (карты, СБП, банковские переводы)
- **Donation система**: поддержка проекта через добровольные пожертвования
- **Поддержка всех школьных предметов**: математика, физика, химия, биология, языки и другие
- **Упрощенные объяснения**: формулы и уравнения через простые слова и таблицы (без LaTeX)
- **Аналитика для родителей**: отчеты о активности, безопасность, прогресс обучения

---

## Технологии

### Backend
- **Python 3.13** — основной язык разработки
- **aiogram 3.23.0** — асинхронный Telegram Bot API фреймворк
- **SQLAlchemy 2.0.45** — асинхронная ORM для PostgreSQL
- **Pydantic V2** — валидация данных и настроек
- **PostgreSQL 17** — база данных (psycopg 3.3.2)
- **Alembic 1.17.2** — миграции БД
- **aiohttp 3.13.2** — асинхронный веб-сервер (webhook mode)
- **Yandex Cloud API** — YandexGPT, SpeechKit, Vision (REST API)

### Frontend
- **React 19.1.1** — UI фреймворк с современными хуками
- **TypeScript 5.8.3** — типизированный JavaScript
- **Vite 7.1.7** — быстрый сборщик модулей
- **TanStack Query 5.90.16** — управление серверным состоянием
- **Zustand 5.0.9** — легковесное клиентское состояние
- **Tailwind CSS 3.4.17** — utility-first стилизация
- **Telegram Mini App SDK** — интеграция с Telegram WebView

### Infrastructure & AI
- **Railway.app** — хостинг и деплой (24/7, webhook mode, автоматический CI/CD)
- **Cloudflare** — DNS, SSL (Full Strict), CDN
- **Docker** — контейнеризация (build attestations в CI/CD)
- **GitHub Actions** — автоматическая сборка и тестирование
- **Yandex Cloud** — AI сервисы (YandexGPT, SpeechKit, Vision)
- **ЮKassa** — платежная система (карты, СБП, банковские переводы)

---

## Быстрый старт

### Требования

- Python 3.13+
- Node.js 20+
- PostgreSQL 17+
- Docker (опционально)

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot

# Настроить backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Настроить переменные окружения
cp config/env.template .env
# Заполнить .env своими данными

# Инициализировать БД
alembic upgrade head

# Запустить backend
python web_server.py
```

В отдельном терминале:

```bash
# Настроить frontend
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker-compose up -d postgres
python web_server.py
```

---

## Структура проекта

```
PandaPal/
├── bot/                   # Telegram Bot (aiogram 3.23.0)
│   ├── handlers/          # Обработчики команд (start, ai_chat, menu, payment)
│   ├── services/          # Бизнес-логика (AI, модерация, аналитика, Premium)
│   ├── config/            # Конфигурация (настройки, промпты, паттерны)
│   ├── security/          # Безопасность (middleware, валидация, overload protection)
│   ├── api/               # API endpoints (Mini App, Premium, Donation, метрики)
│   ├── models.py          # SQLAlchemy модели (User, ChatHistory, Subscription, Payment)
│   └── database.py        # Управление БД (connection pool, миграции)
├── frontend/              # React 19 приложение (Telegram Mini App)
│   ├── src/
│   │   ├── components/    # UI компоненты (Header, Hero, FeatureCard)
│   │   ├── features/      # Фичи (AIChat, Emergency, Premium, Donation, Achievements)
│   │   ├── services/      # API клиенты (Telegram, Backend)
│   │   └── store/         # Zustand store (глобальное состояние)
│   └── public/            # Статика (logo, favicon)
├── tests/                 # Тесты (330+ passed, 74% critical coverage)
│   ├── unit/              # Unit тесты (реальные сервисы, без моков)
│   ├── integration/       # Интеграционные тесты (БД, API, Premium)
│   ├── e2e/               # E2E тесты (Playwright, реальные сервисы)
│   ├── security/          # Тесты безопасности (OWASP Top 10, SQL injection)
│   ├── performance/       # Performance тесты (нагрузочное тестирование)
│   └── resilience/        # Resilience тесты (degradation, memory leaks)
├── docs/                  # Документация (архитектура, деплой, тестирование)
├── scripts/               # Утилиты разработки (аналитика, оптимизация)
├── alembic/               # Миграции БД (версионирование схемы)
└── sql/                   # SQL скрипты (ручные миграции)
```

---

## Разработка

### Локальная разработка

```bash
# Backend
python web_server.py

# Frontend (в отдельном терминале)
cd frontend && npm run dev

# База данных
docker-compose up -d postgres
```

### Code Quality

```bash
# Pre-commit hooks
pre-commit install
pre-commit run --all-files

# Форматирование
black bot/
isort bot/

# Линтеры
flake8 bot/
mypy bot/

# Security
bandit -r bot/
safety check
```

### Утилиты

```bash
# Проверка БД
python check_database.py

# Просмотр метрик
python scripts/view_analytics_metrics.py --days 7

# Экспорт метрик
python scripts/export_metrics.py --format csv --days 30
```

---

## Тестирование

### Статистика

**Backend (Python):**
- **330+ passed** тестов (pytest)
- **74%** реальное покрытие критических модулей (без моков)
- **91.7%** покрытие моделей БД
- **11 E2E тестов** с реальными сервисами (Yandex Cloud API)
- **Comprehensive security tests** — SQL injection, DDoS/Slowloris, API authorization, resilience
- **0 failures** — все тесты проходят

**Frontend (React/TypeScript):**
- **78 passed** тестов (Vitest)
- **85%+** покрытие кода (Statements, Branches, Functions, Lines)
- **6 E2E тестов** (Playwright) — полный user journey
- **44 security теста** — OWASP Top 10 проверки

### Реальное покрытие критических модулей

- `moderation_service.py`: **76.4%** (безопасность детей)
- `history_service.py`: **87.1%** (история чата)
- `user_service.py`: **73.3%** (пользователи)
- `subscription_service.py`: **70.6%** (подписки)
- `knowledge_service.py`: **63.8%** (база знаний)
- `analytics_service.py`: **74.4%** (аналитика)
- `models.py`: **91.7%** (модели БД)

### Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=bot --cov-report=html

# Только unit (реальные сервисы)
pytest tests/unit/ -v

# Только E2E (реальные БД и сервисы)
pytest tests/e2e/ -v

# Только integration
pytest tests/integration/ -v

# Параллельно
pytest tests/ -n auto
```

### Принципы тестирования

- **Реальное тестирование** — используем реальные БД, сервисы, модерацию
- **Моки только для внешних API** — Telegram API, Yandex Cloud API (при отсутствии ключей)
- **E2E тесты** — полный flow с реальными компонентами
- **Критические модули** — тестируются реально без заглушек
- **Проверка результата** — проверяем поведение, а не реализацию

### Frontend тесты

```bash
cd frontend

# Unit тесты (Vitest)
npm run test
npm run test:ui          # UI интерфейс для тестов
npm run test:coverage    # С покрытием кода

# E2E тесты (Playwright)
npm run test:e2e         # Headless режим
npm run test:e2e:headed  # С открытым браузером
npm run test:e2e:ui      # UI для E2E тестов
npm run test:e2e:debug   # Отладка конкретного теста
```

---

## Деплой

### Railway.app (Production)

Автоматический деплой через GitHub:

1. Push в `main` → Railway автоматически деплоит
2. Environment Variables настроены в Railway Dashboard
3. Custom Domain: [pandapal.ru](https://pandapal.ru)

**Подробнее:** [docs/RAILWAY_SETUP.md](docs/RAILWAY_SETUP.md)

### Переменные окружения

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/pandapal_db

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABC...

# Yandex Cloud AI Services
YANDEX_CLOUD_API_KEY=AQVN...
YANDEX_CLOUD_FOLDER_ID=b1g...
YANDEX_GPT_MODEL=yandexgpt-lite  # или yandexgpt

# Security
SECRET_KEY=your-secret-key-min-32-chars

# Domain & Webhook
WEBHOOK_DOMAIN=pandapal-bot-production.up.railway.app
FRONTEND_URL=https://pandapal.ru

# Payments (ЮKassa)
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key
YOOKASSA_RETURN_URL=https://pandapal.ru/premium/success
YOOKASSA_IS_TEST=false
```

Полный список: [config/env.template](config/env.template)

---

## Безопасность

### Реализованные меры

- **Валидация входных данных** — Pydantic V2 схемы для всех API endpoints
- **Защита от SQL Injection** — параметризованные запросы SQLAlchemy, ORM
- **Защита от XSS** — CSP заголовки, санитизация HTML, экранирование
- **Модерация контента** — 150+ паттернов, 5-уровневая система фильтрации
- **Rate Limiting** — защита от DDoS (60 req/min API, 30 req/min AI)
- **Overload Protection** — защита от перегрузки при 1000+ одновременных запросах
- **CSRF Protection** — проверка Origin/Referer для веб-запросов
- **Security Headers** — X-Content-Type-Options, X-Frame-Options, HSTS
- **Comprehensive Security Tests** — SQL injection, DDoS/Slowloris, API authorization тесты
- **Секреты** — только в переменных окружения, без хардкода
- **HTTPS** — Cloudflare Full Strict, автоматический SSL
- **Аудит безопасности** — Bandit, Safety, регулярные проверки
- **Родительский контроль** — мониторинг активности, аналитика безопасности

### OWASP Top 10

- ✅ A01:2021 – Broken Access Control
- ✅ A02:2021 – Cryptographic Failures
- ✅ A03:2021 – Injection
- ✅ A07:2021 – Identification and Authentication Failures
- ✅ A09:2021 – Security Logging and Monitoring Failures

---

## Мониторинг

### Системные метрики

- **Uptime:** 99.5%+ (Railway)
- **Response Time:** <500ms (median)
- **Error Rate:** <1%
- **Tests:** 330+ passed (0 failures)
- **Coverage:** 74% критических модулей (реальное тестирование)

### Бизнес-метрики

Автоматический сбор 24/7:
- **Безопасность** — заблокированные сообщения, категории блокировок
- **Образование** — AI взаимодействия, активность детей
- **Технические** — системные показатели

```bash
# Просмотр метрик
python scripts/view_analytics_metrics.py --days 7

# Экспорт
python scripts/export_metrics.py --format csv --days 30
```

**Документация:** [docs/ANALYTICS_METRICS_GUIDE.md](docs/ANALYTICS_METRICS_GUIDE.md)

---

## Вклад в проект

Мы открыты для вклада! Прочитайте [CONTRIBUTING.md](CONTRIBUTING.md) для деталей.

### Процесс

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'feat: Add AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

### Соглашения

- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/)
- **Code Style:** PEP 8, Black, isort
- **Tests:** обязательны для новых фич
- **Documentation:** обновляйте при изменениях API

### Checklist перед коммитом

- [ ] Pre-commit hooks пройдены
- [ ] Тесты пройдены локально (`pytest tests/`)
- [ ] Coverage не упало (`pytest --cov=bot`)
- [ ] Документация обновлена

---

## Лицензия

Этот проект использует **проприетарную лицензию** — см. [LICENSE](LICENSE).

© 2026 Савин Вячеслав Евгеньевич. Все права защищены.

Программа предоставляется для использования по прямому назначению в образовательных целях. Любое коммерческое использование, копирование, модификация или распространение исходного кода запрещено без письменного разрешения правообладателя.

По вопросам коммерческой лицензии обращайтесь: 79516625803@ya.ru

---

## Контакты

- **Website:** [pandapal.ru](https://pandapal.ru)
- **Telegram Bot:** [@PandaPalBot](https://t.me/PandaPalBot)
- **GitHub:** [github.com/gaus-1/pandapal-bot](https://github.com/gaus-1/pandapal-bot)

---

## Дополнительная документация

- [Настройка Базы Данных](docs/DATABASE_SETUP.md) — инструкции по PostgreSQL
- [Деплой на Railway](docs/RAILWAY_SETUP.md) — гайд по развертыванию
- [Структура Проекта](docs/ARCHITECTURE/BOT_FUNCTIONALITY_MAP.md) — карта функционала бота
- [Руководство по Метрикам](docs/ANALYTICS_METRICS_GUIDE.md) — работа с бизнес-метриками
- [Безопасность](docs/SECURITY/SECURITY_IMPLEMENTATION.md) — реализация системы безопасности
- [Тестирование](docs/TESTING/TESTING.md) — руководство по тестированию (frontend и backend)

---

<div align="center">

**Сделано с ❤️ для детей и их родителей**

⭐ **Если проект полезен, поставьте звезду!** ⭐

</div>
