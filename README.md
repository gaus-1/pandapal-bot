<div align="center">

<img src="frontend/public/logo.png" alt="PandaPal Logo" width="120" height="120">

# PandaPal

**Образовательная платформа для школьников 1-9 классов**

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react&logoColor=white)](https://reactjs.org/)
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

- **Мультимодальное взаимодействие**: текст, голос, изображения
- **Безопасность**: 150+ фильтров контента, модерация 24/7, адаптация под возраст
- **Telegram Mini App**: полнофункциональное веб-приложение внутри Telegram
- **Поддержка всех школьных предметов**: математика, физика, химия, биология и другие
- **Упрощенные объяснения**: формулы и уравнения через простые слова и таблицы

---

## Технологии

### Backend
- **Python 3.13** — основной язык разработки
- **aiogram 3.x** — Telegram Bot API фреймворк
- **SQLAlchemy 2.0** — асинхронная ORM
- **Pydantic V2** — валидация данных
- **PostgreSQL 17** — база данных
- **Alembic** — миграции БД
- **FFmpeg** — обработка аудио

### Frontend
- **React 18** — UI фреймворк
- **TypeScript** — типизированный JavaScript
- **Vite** — сборщик модулей
- **TanStack Query** — управление серверным состоянием
- **Zustand** — клиентское состояние
- **Tailwind CSS** — стилизация

### Infrastructure
- **Railway.app** — хостинг и деплой (24/7, webhook mode)
- **Cloudflare** — DNS и SSL
- **Docker** — контейнеризация

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
├── bot/                   # Telegram Bot (aiogram)
│   ├── handlers/          # Обработчики команд
│   ├── services/          # Бизнес-логика
│   ├── config/            # Конфигурация
│   ├── models.py          # SQLAlchemy модели
│   └── database.py        # Управление БД
├── frontend/              # React приложение
│   ├── src/
│   │   ├── components/    # UI компоненты
│   │   ├── features/      # Фичи (AIChat, Emergency)
│   │   ├── services/      # API клиенты
│   │   └── store/         # Zustand store
│   └── public/            # Статика
├── tests/                 # Тесты (330+ passed, 74% critical coverage)
│   ├── unit/              # Unit тесты (реальные сервисы)
│   ├── integration/       # Интеграционные тесты
│   └── e2e/               # E2E тесты (реальные БД и сервисы)
├── docs/                  # Документация
├── scripts/               # Утилиты разработки
├── alembic/               # Миграции БД
└── sql/                   # SQL скрипты
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

- **330+ passed** тестов
- **74%** реальное покрытие критических модулей (без моков)
- **91.7%** покрытие моделей БД
- **11 E2E тестов** с реальными сервисами
- **0 failures** — все тесты проходят

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
npm run test
npm run test:coverage
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

# AI Cloud Services
AI_CLOUD_API_KEY=AQVN...
AI_CLOUD_FOLDER_ID=b1g...

# Security
SECRET_KEY=your-secret-key-min-32-chars

# Domain
WEBHOOK_DOMAIN=web-production-725aa.up.railway.app
FRONTEND_URL=https://pandapal.ru
```

Полный список: [config/env.template](config/env.template)

---

## Безопасность

### Реализованные меры

- Валидация входных данных (Pydantic схемы)
- Защита от SQL Injection (параметризованные запросы)
- Защита от XSS (CSP заголовки, санитизация)
- Модерация контента (150+ паттернов)
- Rate Limiting (защита от abuse)
- Секреты в переменных окружения
- HTTPS (Cloudflare Full Strict)
- Аудит безопасности (Bandit, Safety)

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
- [Структура Проекта](docs/PROJECT_STRUCTURE_AUDIT.md) — детальное описание архитектуры
- [Руководство по Метрикам](docs/ANALYTICS_METRICS_GUIDE.md) — работа с бизнес-метриками
- [Критический Анализ Проекта](PROJECT_CRITICAL_ANALYSIS.md) — подробный анализ

---

<div align="center">

**Сделано с ❤️ для детей и их родителей**

⭐ **Если проект полезен, поставьте звезду!** ⭐

</div>
