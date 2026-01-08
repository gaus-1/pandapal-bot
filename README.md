# PandaPal

Образовательная платформа для школьников 1-9 классов с Telegram-ботом и веб-приложением. Помогает детям учиться по всем предметам с защитой от небезопасного контента.

## О проекте

PandaPal — это AI-ассистент для помощи в учебе. Бот работает 24/7 и помогает детям с домашними заданиями, объясняет сложные темы и поддерживает изучение иностранных языков.

Ключевые возможности:
- AI-ассистент на базе YandexGPT для помощи по всем школьным предметам
- Поддержка текста, голоса и изображений
- Автоматический перевод и объяснение грамматики для английского, немецкого, французского, испанского
- Игры PandaPalGo: Крестики-нолики, Шашки, 2048 с AI противником
- Система достижений и прогресса
- Premium подписки через YooKassa и Telegram Stars
- Многоуровневая модерация контента для безопасности детей

## Технологии

### Backend
- Python 3.13, aiogram 3.23, aiohttp 3.13
- SQLAlchemy 2.0, PostgreSQL 17, Alembic
- Redis 6.4 для сессий (Upstash)
- Yandex Cloud: YandexGPT, SpeechKit STT, Vision OCR, Translate API
- YooKassa 3.0 для платежей

### Frontend
- React 19, TypeScript 5, Vite 7
- TanStack Query 5, Zustand 5
- Tailwind CSS 3
- Telegram Mini App SDK 8.0

### Инфраструктура
- Railway.app для хостинга
- Cloudflare для DNS, SSL, CDN
- GitHub Actions для CI/CD
- Upstash Redis для сессий

## Структура проекта

```
PandaPal/
├── bot/                    # Backend логика
│   ├── handlers/           # Обработчики команд Telegram
│   ├── services/           # Бизнес-логика (AI, платежи, игры)
│   ├── api/                # HTTP endpoints для Mini App
│   ├── config/             # Настройки, промпты, паттерны модерации
│   ├── security/           # Middleware, валидация, rate limiting
│   ├── models.py           # SQLAlchemy модели БД
│   └── database.py         # Подключение к PostgreSQL
├── frontend/               # React веб-приложение
│   ├── src/
│   │   ├── components/     # UI компоненты
│   │   ├── features/       # Основные фичи (AIChat, Premium, Games)
│   │   └── services/       # API клиенты
│   └── public/             # Статические файлы
├── tests/                  # Тесты (unit, integration, e2e, security)
├── alembic/                # Миграции БД
└── scripts/                # Утилиты
```

## Архитектура

### Entry Point
- `web_server.py` — aiohttp сервер с webhook для Telegram, раздача frontend

### Services
- `ai_service_solid.py` — главный AI сервис через Yandex Cloud
- `yandex_ai_response_generator.py` — генерация ответов с учетом контекста
- `moderation_service.py` — фильтрация контента (150+ паттернов)
- `payment_service.py` — интеграция с YooKassa
- `games_service.py` — логика игр PandaPalGo
- `gamification_service.py` — достижения, уровни, XP

### API Endpoints
- `miniapp_endpoints.py` — AI chat, голос, изображения
- `premium_endpoints.py` — обработка платежей YooKassa
- `games_endpoints.py` — API для игр
- `auth_endpoints.py` — Telegram Login Widget для сайта

### Security
- Многоуровневая модерация контента
- Rate limiting (60 req/min API, 30 req/min AI)
- CSP headers, CORS, CSRF защита
- Валидация всех входных данных через Pydantic
- Аудит логирование

## Безопасность

- Валидация через Pydantic V2
- SQLAlchemy ORM для защиты от SQL injection
- CSP headers для защиты от XSS
- Модерация: 150+ паттернов, фильтры мата на 4 языках
- Rate limiting для защиты от перегрузки
- HTTPS через Cloudflare Full Strict
- Секреты только в переменных окружения

Сообщить об уязвимости: см. [SECURITY.md](SECURITY.md)

## Контакты

- Сайт: https://pandapal.ru
- Бот: https://t.me/PandaPalBot
- GitHub: https://github.com/gaus-1/pandapal-bot
