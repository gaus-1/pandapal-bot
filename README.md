<div align="center">

<img src="https://raw.githubusercontent.com/gaus-1/pandapal-bot/main/frontend/public/logo.png" alt="PandaPal Logo" width="200">

# PandaPal

Образовательная платформа для школьников 1-9 классов с Telegram-ботом и веб-приложением (Mini App). Помогает детям учиться по предметам с модерацией небезопасного контента.

[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6?logo=typescript)](https://www.typescriptlang.org/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-46a758.svg)](https://docs.astral.sh/ruff/)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Railway Deploy](https://img.shields.io/badge/deploy-Railway-purple?logo=railway)](https://railway.app)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

[Сайт](https://pandapal.ru) • [Telegram Бот](https://t.me/PandaPalBot)

[English README](README_EN.md)

</div>

## О проекте

PandaPal — AI-помощник для учебы в формате Telegram Mini App и сайта. Основные сценарии: объяснение тем, помощь с домашними заданиями, голос/фото-вопросы, учебные игры, прогресс и премиум-подписка.

## Быстрый старт

Для локальной разработки:

```bash
# Клонирование репозитория
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot

# Установка зависимостей Python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Настройка окружения
cp config/env.template .env
# Заполните .env файл с вашими API ключами

# Миграции БД
alembic upgrade head

# Запуск backend
python web_server.py

# В другом терминале - запуск frontend
cd frontend
npm install
npm run dev
```

Полная документация по установке и настройке: см. [docs/](docs/)

### Ключевые возможности

- AI-чат для учебных вопросов (обычный и streaming SSE)
- Проверка домашних заданий по фото + история и статистика
- Голосовые вопросы с подтверждением перед отправкой в AI
- Визуализации по предметам (графики, таблицы, диаграммы, схемы, карты)
- Генерация изображений по учебным темам (YandexART)
- RAG-поиск по базе знаний с `pgvector` (`knowledge_embeddings`)
- Игры PandaPalGo: Моя панда (тамагочи с предзагрузкой), Крестики-нолики, Шашки, 2048, Эрудит
- AEO & GEO Оптимизация (Generative Engine Optimization) — полная поддержка AI поисковиков (Алиса, ChatGPTBot) через `llms.txt` и семантический `index.html` (Answer-first подход)
- Встроенная система защиты от перегрузок (Overload Protection Middleware)
- Мониторинг Prometheus, кастомное форматирование Loguru и система подробных health-чеков
- Прогресс, достижения и геймификация
- Premium через YooKassa (299 ₽/месяц), сохранение карт
- Реферальная программа (`ref_<telegram_id>`)
- Модерация контента для детской аудитории
- Адаптация ответов AI по возрасту/классу пользователя

### Реферальная программа

Преподаватели и партнёры получают персональную ссылку вида `https://t.me/PandaPalBot?startapp=ref_<telegram_id>`.
Оплаты по ссылке учитываются в системе, размер выплаты настраивается через `REFERRAL_PAYOUT_RUB`.
Месячный отчёт: `python scripts/referral_report.py [--year YYYY] [--month MM]`.

## Технологии

### Backend

- Python 3.13, aiogram 3.24, aiohttp 3.13
- SQLAlchemy 2.0, PostgreSQL 17 + pgvector, Alembic
- Redis 7.1 (Upstash)
- Yandex Cloud: YandexGPT Pro, YandexART, SpeechKit STT, Vision OCR, Translate API, Embeddings API
- YooKassa 3.9.0
- Мониторинг и Логирование: `Prometheus` metrics, `Loguru` formatting
- Параметры генерации по умолчанию: `temperature=0.35`, `max_tokens=8192`

### Frontend

- React 19, TypeScript 5, Vite 7
- TanStack Query 5, Zustand 5, Playwright (E2E), Vitest
- Tailwind CSS 3
- Telegram Mini App SDK 8.0

### Инфраструктура

- Railway (webhook режим)
- Cloudflare (DNS, SSL, CDN)
- GitHub Actions (CI/CD)
- Upstash Redis

## Структура проекта

```text
PandaPal/
├── .github/                 # CI/CD workflows, security policy, templates
├── bot/                     # Backend домен: API, handlers, services, models, security
│   ├── api/                 # HTTP endpoints (miniapp, premium, games, auth, panda-pet)
│   ├── handlers/            # Telegram handlers (text/voice/image/document)
│   ├── services/            # Бизнес-логика (AI, RAG, games, payments, moderation)
│   ├── database/            # Работа с БД и SQLAlchemy слой
│   ├── models/              # ORM-модели
│   ├── config/              # Конфигурационные модули
│   ├── security/            # Защита, middleware, crypto, audit
│   ├── middleware/          # Middleware для обработки запросов
│   ├── localization/        # Локализация и переводы
│   ├── utils/               # Вспомогательные утилиты
│   └── monitoring/          # Метрики и наблюдаемость
├── frontend/                # React Mini App и веб-интерфейс
│   ├── src/                 # components, features, hooks, services, store, utils
│   ├── public/              # Статические файлы
│   ├── dist/                # Production build
│   └── e2e/                 # Playwright e2e
├── tests/                   # unit, integration, e2e, security, resilience, performance
├── alembic/                 # Миграции БД
├── server_routes/           # Раздача статики и серверные роуты
├── scripts/                 # Операционные/служебные скрипты
├── config/                  # env.template и конфиги окружения
├── docs/                    # Техническая документация
├── data/                    # Данные проекта
├── metrics/                 # Материалы по метрикам
├── sql/                     # SQL-утилиты и заметки
├── logs/                    # Логи приложения
├── Dockerfile               # Основной контейнер приложения
├── docker-compose.yml       # Композиция сервисов для локальной разработки
└── web_server.py            # Точка входа backend-сервера
```

## Архитектура

### Обзор системы

```mermaid
graph TB
    user["Пользователь"] --> web["Сайт в браузере"]
    user --> miniapp["Telegram Mini App"]
    user --> tgbot["Telegram бот"]

    web --> server["Сервер web_server.py"]
    miniapp --> server
    tgbot --> telegramApi["Telegram Bot API"]
    telegramApi --> server

    server --> api["API и маршруты"]
    api --> services["Сервисы приложения"]
    services --> db["PostgreSQL + pgvector"]
    services --> redis["Redis кэш"]
    services --> yandex["Yandex Cloud"]
    services --> payments["YooKassa"]
```

Коротко по потоку:

- Пользователь работает через сайт, Mini App или Telegram-бот.
- Все запросы сходятся в `web_server.py` и API-маршрутах.
- Основная логика выполняется в сервисах `bot/services`.
- Данные и состояние хранятся в PostgreSQL/pgvector и Redis.
- Внешние интеграции: Telegram Bot API, Yandex Cloud, YooKassa.

### API Endpoints

- `GET /metrics` — сбор метрик в формате Prometheus
- `GET /api/v1/health` — проверка здоровья БД, систем и AI-сервисов
- `GET /api/v1/analytics/metrics` — системная аналитика в JSON формате
- `POST /api/miniapp/ai/chat` — non-streaming чат
- `POST /api/miniapp/ai/chat-stream` — streaming чат (SSE)
- `POST /api/miniapp/auth` — аутентификация Mini App
- `GET /api/miniapp/user/{telegram_id}` — профиль пользователя
- `GET /api/miniapp/chat/history/{telegram_id}` — история чата
- `POST /api/miniapp/homework/check` — проверка ДЗ по фото
- `GET /api/miniapp/homework/history/{telegram_id}` — история ДЗ
- `GET /api/miniapp/progress/{telegram_id}` — прогресс
- `GET /api/miniapp/achievements/{telegram_id}` — достижения
- `GET /api/miniapp/dashboard/{telegram_id}` — дашборд
- `GET /api/miniapp/subjects` — список предметов
- `GET /api/miniapp/premium/status/{telegram_id}` — статус Premium
- `POST /api/miniapp/premium/create-payment` — создание оплаты
- `POST /api/miniapp/premium/yookassa-webhook` — webhook YooKassa
- `POST /api/miniapp/donation/create-invoice` — создание доната
- `POST /api/miniapp/games/{telegram_id}/create` — создание игровой сессии (tic_tac_toe, checkers, 2048, erudite)
- `GET /api/miniapp/panda-pet/{telegram_id}` — состояние тамагочи; POST feed/play/sleep/climb/fall-from-tree/toilet

## Безопасность

- Валидация владельца ресурса через `X-Telegram-Init-Data` для защищенных endpoints
- Pydantic v2 для валидации входных данных
- SQLAlchemy ORM и параметризация запросов
- Модерация контента (многоуровневая фильтрация)
- Rate limiting и базовая защита API
- Секреты только в env переменных

Сообщить об уязвимости: см. [SECURITY.md](.github/SECURITY.md)

## Тестирование

- Наборы тестов: `unit`, `integration`, `e2e`, `security`, `resilience`, `performance`

Запуск:

```bash
pytest tests/ -v
```

### Частые проблемы локального запуска

- **Не стартует backend**: проверьте `.env` и обязательные переменные из `config/env.template`.
- **Ошибки миграций**: выполните `alembic upgrade head` и убедитесь, что `DATABASE_URL` указывает на рабочую БД.
- **Frontend не открывается**: запустите `npm run dev` из `frontend/` и проверьте порт в выводе Vite.
- **Проблемы с Telegram Mini App**: для локальной проверки открывайте веб-режим отдельно от Telegram-контекста.

## Наполнение базы знаний (RAG)

Для семантического поиска нужно проиндексировать материалы в `knowledge_embeddings`:

```bash
railway link   # выбрать проект PandaPal
railway run python scripts/update_knowledge_base.py
```

Используются учебные источники, а также материалы энциклопедического формата (включая Wikipedia) в RAG-пайплайне.

## Переменные окружения (Railway / локально)

Обязательные переменные для запуска описаны в `config/env.template`:

- `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`
- `YANDEX_CLOUD_API_KEY`, `YANDEX_CLOUD_FOLDER_ID`
- `SECRET_KEY`
- Для Premium: `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY` и др.

## Лицензия

Это проприетарное программное обеспечение. Все права защищены.

Подробности: см. [LICENSE](LICENSE)

## Контакты

- Сайт: https://pandapal.ru
- Telegram Бот: https://t.me/PandaPalBot
- GitHub: https://github.com/gaus-1/pandapal-bot

## GitHub Topics

`telegram-bot` `education` `ai-assistant` `yandex-cloud` `react` `typescript` `python` `postgresql` `pgvector` `rag` `educational-platform` `kids-learning` `homework-helper` `aiogram` `mini-app`
