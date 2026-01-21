<div align="center">

<img src="https://raw.githubusercontent.com/gaus-1/pandapal-bot/main/frontend/public/logo.png" alt="PandaPal Logo" width="200">

# PandaPal

Образовательная платформа для школьников 1-9 классов с Telegram-ботом и веб-приложением. Помогает детям учиться по всем предметам с защитой от небезопасного контента.

[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6?logo=typescript)](https://www.typescriptlang.org/)
[![CI/CD](https://img.shields.io/github/actions/workflow/status/gaus-1/pandapal-bot/main-ci-cd.yml?label=CI%2FCD)](https://github.com/gaus-1/pandapal-bot/actions)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

[Сайт](https://pandapal.ru) • [Telegram Бот](https://t.me/PandaPalBot)

</div>

## О проекте

PandaPal — интеллектуальный помощник для помощи в учебе. Бот работает 24/7 и помогает детям с домашними заданиями, объясняет сложные темы и поддерживает изучение иностранных языков.

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

- **Enhanced RAG система** — умный поиск по базе знаний с семантическим кешированием, переранжированием результатов и контекстной компрессией для экономии токенов (75-90%)
- **Интеллектуальный помощник премиум качества** — глубокие структурированные ответы на базе YandexGPT Pro с учетом ВСЕХ слов запроса, развернутые объяснения и визуализации
- **Объяснение взрослых тем** — доступное объяснение жизненных вопросов для детей (деньги, банки, документы, ЖКУ, работа, здоровье) простыми словами с примерами
- **Визуализации с пояснениями** — автоматическая генерация графиков, таблиц, диаграмм (включая круговые), схем и карт с подробными объяснениями
- **Генерация изображений** — создание картинок по описанию через YandexART (требует роль ai.imageGeneration.user)
- **Проверка домашних заданий** — автоматическая проверка ДЗ по фото с поиском ошибок, исправлениями и объяснениями
- **Адаптивное обучение** — отслеживание проблемных тем, автоматическая адаптация сложности под уровень ученика
- Streaming ответы через Server-Sent Events для быстрой генерации
- Поддержка текста, голоса и изображений с анализом через Vision API
- Автоматический перевод и объяснение грамматики для 5 языков (английский, немецкий, французский, испанский, русский)
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
│   ├── services/           # Бизнес-логика (AI, платежи, игры, Mini App, RAG)
│   │   ├── ai_service_solid.py          # Фасад над Yandex Cloud AI
│   │   ├── yandex_cloud_service.py      # Низкоуровневый Yandex Cloud клиент
│   │   ├── yandex_ai_response_generator.py  # Генерация AI ответов с RAG
│   │   ├── rag/                         # Enhanced RAG система
│   │   │   ├── query_expander.py        # Расширение запросов (multi-query)
│   │   │   ├── reranker.py              # Переранжирование результатов
│   │   │   ├── semantic_cache.py        # Семантическое кеширование
│   │   │   ├── compressor.py            # Контекстная компрессия (75-90%)
│   │   │   └── __init__.py              # Экспорт RAG компонентов
│   │   ├── miniapp_chat_context_service.py  # Контекст чата для Mini App
│   │   ├── miniapp_intent_service.py        # Детекция intent'ов (таблицы, графики и т.п.)
│   │   ├── miniapp_audio_service.py         # Обработка аудио из Mini App
│   │   ├── miniapp_photo_service.py         # Обработка фото/домашки из Mini App
│   │   ├── miniapp_visualization_service.py # Детектор визуализаций для Mini App
│   │   ├── visualization_service.py         # Единая точка входа для визуализаций
│   │   ├── visualization/                   # Генерация графиков/таблиц по предметам
│   │   ├── homework_service.py              # Проверка домашних заданий по фото
│   │   ├── adaptive_learning_service.py     # Адаптивное обучение, проблемные темы
│   │   ├── games_service.py                 # Игры PandaPalGo (TicTacToe, Checkers, 2048, Tetris)
│   │   ├── gamification_service.py          # Достижения, уровни, XP
│   │   ├── premium_features_service.py      # Premium лимиты и доступ
│   │   ├── payment_service.py               # YooKassa / Telegram Stars
│   │   ├── history_service.py               # История чата (включая image_url)
│   │   ├── adult_topics_service.py          # Объяснение взрослых тем детям (деньги, ЖКУ, документы)
│   │   ├── yandex_art_service.py            # Генерация изображений через YandexART
│   │   └── token_rotator.py                 # Ротация AI‑ключей
│   ├── api/                # HTTP endpoints
│   │   ├── miniapp/        # API для Telegram Mini App
│   │   │   ├── chat_stream.py  # Streaming AI чат (SSE) + визуализации
│   │   │   ├── homework.py     # Проверка домашних заданий (check, history, statistics)
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
├── tests/                  # Тесты (unit, integration, e2e, security, performance)
│   ├── unit/              # Unit тесты отдельных компонентов
│   ├── integration/       # Интеграционные тесты с реальным API
│   ├── e2e/               # End-to-end тесты полных сценариев
│   │   └── test_comprehensive_panda_e2e.py  # Комплексные E2E тесты всех функций
│   ├── security/          # Тесты безопасности
│   └── performance/       # Тесты производительности
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
- `yandex_ai_response_generator.py` — генерация ответов с RAG и Dependency Injection
- **`rag/`** — Enhanced RAG система для умного поиска:
  - `query_expander.py` — multi-query RAG, расширение синонимами
  - `reranker.py` — переранжирование по relevance, age, recency, source quality
  - `semantic_cache.py` — кеширование похожих запросов (Jaccard similarity)
  - `compressor.py` — контекстная компрессия для экономии токенов (75-90%)
- `knowledge_service.py` — база знаний с enhanced_search и дедупликацией
- `speech_service.py` — распознавание голоса через Yandex SpeechKit STT
- `vision_service.py` — анализ изображений через Yandex Vision API, проверка домашних заданий
- `homework_service.py` — проверка домашних заданий по фото с анализом ошибок
- `adaptive_learning_service.py` — адаптивное обучение, отслеживание проблемных тем, расчет уровня сложности
- `moderation_service.py` — фильтрация контента (150+ паттернов, 4 языка)
- `user_service.py` — управление пользователями
- `payment_service.py` — интеграция с YooKassa (продакшн, сохранение карт)
- `premium_features_service.py` — проверка Premium статуса и лимитов
- `games_service.py` — логика игр PandaPalGo (TicTacToe, Checkers, 2048, Tetris)
- `gamification_service.py` — достижения, уровни, XP
- **`visualization/`** — Генерация визуализаций по предметам:
  - `detector.py` — детектор запросов на визуализацию (графики, таблицы, схемы, карты)
  - `math/` — математические визуализации (графики функций, таблицы умножения, геометрия)
  - `sciences/` — физика, химия (диаграммы, формулы)
  - `social/` — география, история (карты, схемы, таймлайны)
  - `languages/` — таблицы грамматики, схемы времен
  - `other/` — информатика, окружающий мир

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
- `bot/api/miniapp/homework.py` — проверка домашних заданий (check, history, statistics)
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

- **YandexGPT Pro** для всех пользователей с temperature=0.7 (ранее 0.3)
- **Enhanced RAG система** — интеллектуальный поиск по базе знаний с компрессией контекста (75-90%)
- **Streaming ответы** через Server-Sent Events для мгновенной генерации
- **Улучшенные промпты для AI**:
  - Структурированные ответы с параграфами и нумерацией
  - Учет ВСЕХ слов в запросе пользователя
  - Глубокие 4-параграфные объяснения для визуализаций
  - Динамическая адаптация инструкций под тип контента
  - Запрет дублирования значений таблиц умножения/сложения
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

### Инфраструктура

- Keep-alive механизм для предотвращения сна на Railway FREE
- Улучшенное логирование и диагностика Yandex Cloud API
- Миграции БД для поддержки daily request limits

### Тестирование и качество

- **Комплексные E2E тесты** — полное покрытие всех функций панды с реальным API
  - Тестирование визуализаций (графики, таблицы, диаграммы, карты) с проверкой качества генерации
  - Тестирование текстовых ответов по всем предметам с валидацией развернутости и структурированности
  - Тестирование обработки фото по всем предметам с полным анализом через Vision API
  - Тестирование проверки домашних заданий через homework endpoint с реальными данными
  - Тестирование модерации — проверка что школьные вопросы (история, география) не блокируются
  - Полный путь пользователя со всеми функциями: текст → визуализация → фото → проверка ДЗ
  - Все тесты используют реальный Yandex Cloud API для проверки работы в production-подобных условиях

### Новые возможности (2026)

- **Enhanced RAG система** — полноценная система Retrieval-Augmented Generation
  - **Multi-query RAG** — расширение запросов синонимами и связанными терминами
  - **Reranking** — переранжирование результатов по relevance, age_match, recency, source_quality
  - **Semantic Cache** — кеширование похожих запросов (Jaccard similarity) с TTL
  - **Context Compression** — сжатие контекста на 75-90% для экономии токенов
  - **Дедупликация** — удаление дубликатов из результатов поиска
  - Интеграция в `knowledge_service.enhanced_search()` и AI response generator
- **Улучшения качества AI ответов**
  - **Структурированные ответы** — четкая структура с параграфами и нумерацией
  - **Учет ВСЕХ слов запроса** — AI анализирует каждое слово в вопросе пользователя
  - **Глубокие объяснения визуализаций** — 4-параграфная структура с минимум 4-6 предложений
  - **Запрет перечисления таблиц** — AI объясняет КАК использовать таблицу, не дублирует значения
  - **Динамические промпты** — адаптация инструкций под тип контента (график/таблица/схема)
- **Проверка домашних заданий** — автоматическая проверка ДЗ по фото с поиском ошибок и подробными объяснениями
  - API endpoints для проверки, истории и статистики
  - Интеграция с Yandex Vision API для распознавания текста
  - Сохранение результатов проверок в БД для отслеживания прогресса
- **Адаптивное обучение** — умная система персонализации обучения
  - Отслеживание проблемных тем по каждому предмету
  - Автоматическая адаптация сложности под уровень ученика
  - Рекомендации по повторению сложных тем

## Лицензия

Это проприетарное программное обеспечение. Все права защищены.

Использование, копирование, распространение и модификация запрещены без письменного разрешения правообладателя.

Подробности: см. [LICENSE](LICENSE)

## Контакты

- Сайт: https://pandapal.ru
- Telegram Бот: https://t.me/PandaPalBot
- GitHub: https://github.com/gaus-1/pandapal-bot
