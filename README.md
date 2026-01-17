<div align="center">

<img src="https://raw.githubusercontent.com/gaus-1/pandapal-bot/main/frontend/public/logo.png" alt="PandaPal Logo" width="200">

# PandaPal

Образовательная платформа для школьников 1-9 классов с Telegram-ботом и веб-приложением. Помогает детям учиться по всем предметам с защитой от небезопасного контента.

[Сайт](https://pandapal.ru) • [Telegram Бот](https://t.me/PandaPalBot)

</div>

## О проекте

PandaPal — AI-ассистент для помощи в учебе. Бот работает 24/7 и помогает детям с домашними заданиями, объясняет сложные темы и поддерживает изучение иностранных языков.

### Ключевые возможности

- AI-ассистент на базе YandexGPT Pro для помощи по всем школьным предметам
- Streaming ответы через Server-Sent Events для быстрой генерации
- Поддержка текста, голоса и изображений с анализом через Vision API
- Автоматический перевод и объяснение грамматики для английского, немецкого, французского, испанского (5 языков)
- Игры PandaPalGo: Крестики-нолики, Шашки, 2048, Тетрис с AI противником
- Система достижений и прогресса с XP, уровнями и наградами
- Premium подписки через YooKassa с сохранением карт
- Многоуровневая модерация контента для безопасности детей (150+ паттернов)
- Темная тема для комфортного использования

## Технологии

### Backend

- Python 3.13, aiogram 3.23, aiohttp 3.13
- SQLAlchemy 2.0, PostgreSQL 17, Alembic
- Redis 6.4 для сессий (Upstash)
- Yandex Cloud: YandexGPT Pro, SpeechKit STT, Vision OCR, Translate API
- YooKassa 3.9.0 для платежей (продакшн режим)
- AI параметры: temperature=0.3, max_tokens=2000

### Frontend

- React 19, TypeScript 5, Vite 7
- TanStack Query 5, Zustand 5
- Tailwind CSS 3
- Telegram Mini App SDK 8.0

### Инфраструктура

- Railway.app для хостинга (webhook режим, 24/7)
- Cloudflare для DNS, SSL, CDN
- GitHub Actions для CI/CD
- Upstash Redis для сессий
- Keep-alive механизм для предотвращения сна на Railway FREE

## Структура проекта

```
PandaPal/
├── bot/                    # Backend логика
│   ├── handlers/           # Обработчики команд Telegram
│   │   ├── ai_chat/         # Модульная структура AI чата
│   │   │   ├── text.py      # Текстовые сообщения
│   │   │   ├── voice.py     # Голосовые и аудио
│   │   │   ├── image.py     # Изображения
│   │   │   ├── document.py  # Документы
│   │   │   ├── helpers.py   # Вспомогательные функции
│   │   │   └── __init__.py  # Регистрация router
│   │   ├── start.py         # Команда /start
│   │   └── ...              # Остальные handlers
│   ├── services/           # Бизнес-логика (AI, платежи, игры, Mini App)
│   │   ├── ai_service_solid.py          # Фасад над Yandex Cloud AI
│   │   ├── yandex_cloud_service.py      # Низкоуровневый Yandex Cloud клиент
│   │   ├── yandex_ai_response_generator.py  # Генерация AI ответов
│   │   ├── miniapp_chat_context_service.py  # Контекст чата для Mini App
│   │   ├── miniapp_intent_service.py        # Детекция intent'ов (таблицы, графики и т.п.)
│   │   ├── miniapp_audio_service.py         # Обработка аудио из Mini App
│   │   ├── miniapp_photo_service.py         # Обработка фото/домашки из Mini App
│   │   ├── miniapp_visualization_service.py # Детектор визуализаций для Mini App
│   │   ├── visualization_service.py         # Единая точка входа для визуализаций
│   │   ├── visualization/                   # Генерация графиков/таблиц по предметам
│   │   ├── games_service.py                 # Игры PandaPalGo (TicTacToe, Checkers, 2048, Tetris)
│   │   ├── gamification_service.py          # Достижения, уровни, XP
│   │   ├── premium_features_service.py      # Premium лимиты и доступ
│   │   ├── payment_service.py               # YooKassa / Telegram Stars
│   │   ├── history_service.py               # История чата (включая image_url)
│   │   └── token_rotator.py                 # Ротация AI‑ключей
│   ├── api/                # HTTP endpoints
│   │   ├── miniapp/        # API для Telegram Mini App
│   │   │   ├── chat_stream.py  # Streaming AI чат (SSE) + визуализации
│   │   │   ├── other.py        # История чата, предметы, логирование
│   │   │   └── __init__.py     # Регистрация Mini App маршрутов
│   │   ├── games_endpoints.py  # API для игр
│   │   ├── premium_endpoints.py# Премиум и платежи
│   │   └── auth_endpoints.py   # Telegram Login / auth API
│   ├── config/             # Настройки, промпты, паттерны модерации
│   ├── security/           # Middleware, валидация, rate limiting
│   ├── monitoring/         # Метрики, мониторинг
│   ├── interfaces.py       # Интерфейсы сервисов (SOLID)
│   ├── decorators.py       # Декораторы для логирования
│   ├── models.py           # SQLAlchemy модели БД
│   └── database.py         # Подключение к PostgreSQL
├── frontend/               # React веб-приложение
│   ├── src/
│   │   ├── components/     # UI компоненты
│   │   ├── features/       # Основные фичи (AIChat, Premium, Games)
│   │   └── services/       # API клиенты
│   └── public/             # Статические файлы
├── tests/                  # Тесты (unit, integration, e2e, security)
├── alembic/                # Миграции БД (Alembic)
├── scripts/                # Утилиты
└── web_server.py           # Entry point (aiohttp + aiogram webhook + frontend)
```

### Архитектурные принципы

- **Модульная структура** — файлы разбиты на подмодули (< 500 строк)
- **SOLID принципы** — разделение ответственности, интерфейсы, Dependency Injection
- **Потоковая обработка** — для больших файлов используется chunked reading
- **Безопасность** — валидация, модерация, rate limiting на всех уровнях

## Архитектура

### Entry Point

- `web_server.py` — aiohttp сервер с webhook для Telegram, раздача frontend
  - `PandaPalBotServer` — класс сервера с разделением ответственности (SRP)
  - `_setup_app_base()` — базовая инициализация приложения
  - `_setup_middleware()` — настройка security middleware
  - `_setup_health_endpoints()` — health check endpoints
  - `_setup_api_routes()` — регистрация API маршрутов
  - `_setup_frontend_static()` — раздача статических файлов frontend
  - `_setup_webhook_handler()` — обработчик webhook от Telegram

### Services (SOLID Architecture)

- `interfaces.py` — интерфейсы сервисов (IUserService, IModerationService, IAIService)
- `ai_service_solid.py` — главный AI сервис через Yandex Cloud (Facade паттерн)
- `yandex_cloud_service.py` — низкоуровневая работа с Yandex Cloud API
- `yandex_ai_response_generator.py` — генерация ответов с Dependency Injection
- `speech_service.py` — распознавание голоса через Yandex SpeechKit STT
- `vision_service.py` — анализ изображений через Yandex Vision API
- `moderation_service.py` — фильтрация контента (150+ паттернов, 4 языка)
- `user_service.py` — управление пользователями
- `payment_service.py` — интеграция с YooKassa (продакшн, сохранение карт)
- `premium_features_service.py` — проверка Premium статуса и лимитов
- `games_service.py` — логика игр PandaPalGo (TicTacToe, Checkers, 2048, Tetris)
- `gamification_service.py` — достижения, уровни, XP

### Handlers (Модульная структура)

- `handlers/ai_chat/` — модульная структура AI чата:
  - `text.py` — обработка текстовых сообщений
  - `voice.py` — голосовые и аудио сообщения
  - `image.py` — анализ изображений
  - `document.py` — обработка документов
  - `helpers.py` — вспомогательные функции (потоковое чтение файлов)
  - `__init__.py` — регистрация router и handlers

### API Endpoints

- `bot/api/miniapp/chat_stream.py` — Mini App AI chat с streaming (SSE), голос, изображения, визуализации
- `bot/api/miniapp/other.py` — история чата, предметы, логирование Mini App
- `premium_endpoints.py` — обработка платежей YooKassa, webhooks, сохранение карт
- `games_endpoints.py` — API для игр (создание сессий, ходы, завершение)
- `auth_endpoints.py` — Telegram Login Widget для сайта

### Security

- Многоуровневая модерация контента (150+ паттернов, 4 языка)
- Rate limiting: 60 req/min API, 30 req/min AI
- Daily limits: 30 запросов (free), 500 (month), без ограничений (year)
- CSP headers, CORS, CSRF защита
- Валидация всех входных данных через Pydantic V2
- Аудит логирование через loguru

## Безопасность

- Валидация через Pydantic V2
- SQLAlchemy ORM для защиты от SQL injection
- CSP headers для защиты от XSS
- Модерация: 150+ паттернов, фильтры мата на 4 языках
- Rate limiting для защиты от перегрузки
- HTTPS через Cloudflare Full Strict
- Секреты только в переменных окружения

Сообщить об уязвимости: см. [SECURITY.md](SECURITY.md)

## Последние изменения (2025)

### Архитектура и Рефакторинг

- Разбит монолитный `ai_chat.py` (1406 строк) на модульную структуру:
  - `text.py` — текстовые сообщения
  - `voice.py` — голосовые и аудио
  - `image.py` — изображения
  - `document.py` — документы
  - `helpers.py` — вспомогательные функции
- Оптимизирована обработка файлов: потоковое чтение вместо `file.read()`
- Применены SOLID принципы: разделение ответственности, модульность
- Улучшена поддерживаемость кода: каждый модуль < 500 строк

### AI и Модель

- Переход на YandexGPT Pro для всех пользователей
- Оптимизация температуры до 0.3 для баланса точности и естественности
- Streaming ответы через Server-Sent Events для быстрой генерации
- Улучшение промптов: структурированные ответы, запрет повторов
- Очистка AI ответов от повторяющихся фрагментов

### Платежи

- Переход на YooKassa продакшн режим
- Сохранение карт для автоплатежей
- Отвязка сохраненных карт через UI
- Улучшенная обработка webhooks и подписей
- Premium планы: Месяц (399₽) и Год (2990₽)

### Достижения и Геймификация

- Исправлена логика разблокировки достижений
- Предотвращение дублирования разблокировок
- Оптимизация проверки достижений
- Добавлена игра Тетрис в PandaPalGo

### Frontend

- Темная тема для всех экранов
- Приветственный экран с логотипом
- Замочки на кнопках оплаты при открытии вне мини-апп
- Улучшенная обработка аудио (WebM → OGG конвертация)
- Пастельные цвета и мягкие тени для блоков Premium и Donation
- Оптимизация производительности: lazy loading, code splitting, preload
- Улучшенная адаптивность для всех устройств (280px+)
- Оптимизация производительности: lazy loading, code splitting, preload
- Улучшенная адаптивность для всех устройств (280px+)

### Инфраструктура

- Keep-alive механизм для предотвращения сна на Railway FREE
- Улучшенное логирование и диагностика Yandex Cloud API
- Миграции БД для поддержки daily request limits

## Контакты

- Сайт: https://pandapal.ru
- Бот: https://t.me/PandaPalBot
- GitHub: https://github.com/gaus-1/pandapal-bot
