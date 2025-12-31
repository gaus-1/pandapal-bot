# 🐼 **PandaPal** - Безопасный ИИ-помощник для детей

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![React](https://img.shields.io/badge/React-18-61dafb?logo=react)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql)
![Railway](https://img.shields.io/badge/Railway-Deployed-0B0D0E?logo=railway)
![License](https://img.shields.io/badge/License-MIT-green)

**Образовательная платформа для школьников 1-9 классов с Telegram-ботом и веб-интерфейсом**

[🌐 Сайт](https://pandapal.ru) • [🤖 Telegram Бот](https://t.me/PandaPal_bot) • [📚 Документация](docs/)

</div>

---

## 📋 **Содержание**

- [О проекте](#о-проекте)
- [Технологии](#технологии)
- [Архитектура](#архитектура)
- [Функциональность](#функциональность)
- [Установка](#установка)
- [Структура проекта](#структура-проекта)
- [Разработка](#разработка)
- [Тестирование](#тестирование)
- [Деплой](#деплой)
- [Безопасность](#безопасность)
- [Команда](#команда)

---

## 🎯 **О проекте**

**PandaPal** — это современная образовательная платформа, объединяющая Telegram-бота и веб-приложение для безопасного и эффективного обучения школьников.

### **Ключевые особенности:**

✅ **Безопасность превыше всего** — 150+ фильтров контента, модерация 24/7
✅ **Адаптивность** — контент подстраивается под возраст ребенка (1-9 класс)
✅ **Мультимодальность** — текст, голос, изображения
✅ **Родительский контроль** — полная прозрачность и статистика
✅ **Современный стек** — Python 3.13, React 18, PostgreSQL 17

---

## 🛠️ **Технологии**

### **Backend**
- **Python 3.13** — основной язык
- **FastAPI** — современный веб-фреймворк
- **aiogram 3.x** — Telegram Bot API
- **SQLAlchemy 2.0** — ORM с async поддержкой
- **PostgreSQL 17** — реляционная база данных
- **Alembic** — миграции БД
- **Pydantic V2** — валидация данных

### **Frontend**
- **React 18** — UI фреймворк
- **TypeScript** — типизированный JavaScript
- **Vite** — сборщик модулей
- **Tailwind CSS** — utility-first CSS

### **AI & External APIs**
- **Yandex Cloud** — YandexGPT, SpeechKit, Vision
- **In-Memory LRU Cache** — кеширование

### **DevOps & Infrastructure**
- **Railway.app** — деплой и хостинг
- **Docker** — контейнеризация
- **GitHub Actions** — CI/CD
- **Cloudflare** — SSL и DNS
- **Pre-commit hooks** — качество кода

---

## 🏗️ **Архитектура**

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│              https://pandapal.ru                         │
└───────────────────┬─────────────────────────────────────┘
                    │ REST API
┌───────────────────┴─────────────────────────────────────┐
│                 BACKEND (FastAPI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Bot Service  │  │ AI Service   │  │ User Service │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└───────────────────┬─────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌─────────┐  ┌──────────────┐  ┌────────────┐
│Telegram │  │ PostgreSQL   │  │ Yandex     │
│   API   │  │   Database   │  │  Cloud     │
└─────────┘  └──────────────┘  └────────────┘
```

### **Принципы проектирования:**

- **SOLID** — все сервисы следуют принципам
- **DDD** — доменная модель изолирована
- **Clean Architecture** — слои не зависят друг от друга
- **API-First** — единая точка входа для всех клиентов

---

## ✨ **Функциональность**

### **Реализовано (90%)**

#### **🤖 Telegram Бот**
- ✅ Текстовые запросы с AI ответами
- ✅ Голосовые сообщения (SpeechKit)
- ✅ Анализ изображений (Vision API)
- ✅ Решение задач с фото
- ✅ Экстренные номера России
- ✅ Модерация контента 24/7

#### **🔒 Безопасность**
- ✅ 150+ запрещенных паттернов
- ✅ Фильтрация по возрасту
- ✅ Блокировка нецензурной лексики
- ✅ Защита от SQL/XSS
- ✅ OWASP Top 10 compliance

#### **👨‍👩‍👧 Родительский контроль**
- ✅ Статистика использования
- ✅ История сообщений
- ✅ Отчеты по предметам
- ✅ Индекс безопасности

#### **🌐 Веб-приложение**
- ✅ Адаптивный дизайн (mobile-first)
- ✅ PWA (Progressive Web App)
- ✅ SEO оптимизация
- ✅ Dark/Light режимы
- ✅ Lazy loading
- ✅ A/B тестирование CTA

---

## 🚀 **Установка**

### **Требования**
- Python 3.13+
- Node.js 20+
- PostgreSQL 17+
- Docker (опционально)

### **Быстрый старт**

```bash
# 1. Клонировать репозиторий
git clone https://github.com/yourusername/pandapal-bot.git
cd pandapal-bot

# 2. Настроить backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Настроить переменные окружения
cp config/env.template .env
# Заполнить .env своими данными

# 4. Инициализировать БД
alembic upgrade head

# 5. Запустить backend
python web_server.py

# 6. Настроить frontend (в новом терминале)
cd frontend
npm install
npm run dev
```

### **Docker (альтернатива)**

```bash
docker-compose up -d postgres
python web_server.py
```

---

## 📁 **Структура проекта**

```
PandaPal/
├── 📁 backend/           # Backend API (FastAPI)
├── 📁 bot/               # Telegram Bot (aiogram)
│   ├── handlers/         # Обработчики команд
│   ├── services/         # Бизнес-логика
│   ├── models.py         # SQLAlchemy модели
│   └── config.py         # Конфигурация
├── 📁 frontend/          # React приложение
│   ├── src/
│   │   ├── components/   # UI компоненты
│   │   ├── features/     # Фичи
│   │   └── services/     # API клиенты
│   └── public/           # Статика
├── 📁 tests/             # Тесты (180 passed, 39% coverage)
│   ├── unit/             # Unit тесты
│   └── integration/      # Интеграционные тесты
├── 📁 config/            # Конфигурационные файлы
├── 📁 docs/              # Документация
├── 📁 scripts/           # Утилиты разработки
├── 📁 sql/               # SQL миграции
├── 📁 logs/              # Логи (gitignored)
├── 📁 data/              # Локальные данные (gitignored)
├── .env                  # Переменные окружения
├── requirements.txt      # Python зависимости
├── Dockerfile            # Docker конфигурация
├── web_server.py         # Entry point
└── README.md             # Этот файл
```

**Подробнее:** [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE_AUDIT.md)

---

## 💻 **Разработка**

### **Локальная разработка**

```bash
# Backend (с hot-reload)
uvicorn bot.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (с hot-reload)
cd frontend && npm run dev

# База данных
docker-compose up -d postgres
```

### **Утилиты**

```bash
# Проверка БД
python scripts/check_db.py

# Поиск мертвого кода
python scripts/check_dead_code.py

# Проверка циклических импортов
python scripts/check_circular_imports.py

# Исправление кодировки
python scripts/fix_encoding.py
```

### **Code Quality**

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
pylint bot/

# Security
bandit -r bot/
safety check
```

---

## 🧪 **Тестирование**

### **Статистика:**
- ✅ **180 passed** тестов
- 📊 **39.12%** покрытие кода
- 🎯 **90%+** покрытие критических компонентов

### **Запуск тестов:**

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=bot --cov-report=html

# Только unit
pytest tests/unit/ -v

# Только integration
pytest tests/integration/ -v

# Параллельно (быстрее)
pytest tests/ -n auto
```

### **Покрытие ключевых модулей:**
- `models.py` — **94.71%**
- `ai_service_solid.py` — **90.62%**
- `speech_service.py` — **80.77%**
- `moderation_service.py` — **76.39%**
- `vision_service.py` — **65.91%**

---

## 🚢 **Деплой**

### **Railway.app (Production)**

Автоматический деплой через GitHub Actions:

1. **Push в `main`** → Railway автоматически деплоит
2. **Environment Variables** настроены в Railway Dashboard
3. **Custom Domain:** [pandapal.ru](https://pandapal.ru)

**Подробнее:** [docs/RAILWAY_SETUP.md](docs/RAILWAY_SETUP.md)

### **Переменные окружения (обязательные):**

```env
# Database
DATABASE_URL=postgresql://...

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABC...

# Yandex Cloud
YANDEX_CLOUD_API_KEY=AQVN...
YANDEX_CLOUD_FOLDER_ID=b1g...
YANDEX_GPT_MODEL=yandexgpt-lite

# Security
SECRET_KEY=your-secret-key-min-32-chars

# Domain
WEBHOOK_DOMAIN=pandapal.ru
FRONTEND_URL=https://pandapal.ru
```

**Полный список:** [config/env.template](config/env.template)

---

## 🔐 **Безопасность**

### **Реализованные меры:**

1. **Валидация входных данных** — Pydantic схемы
2. **SQL Injection защита** — параметризованные запросы
3. **XSS защита** — CSP заголовки, санитизация
4. **Модерация контента** — 150+ паттернов
5. **Rate Limiting** — защита от abuse
6. **Секреты** — хранятся в переменных окружения
7. **HTTPS** — Cloudflare Full (Strict)
8. **Аудит безопасности** — Bandit, Safety

### **OWASP Top 10:**
✅ A01:2021 – Broken Access Control
✅ A02:2021 – Cryptographic Failures
✅ A03:2021 – Injection
✅ A07:2021 – Identification and Authentication Failures
✅ A09:2021 – Security Logging and Monitoring Failures

---

## 📊 **Мониторинг**

### **Метрики:**
- **Uptime:** 99.5%+ (Railway)
- **Response Time:** <500ms (median)
- **Error Rate:** <1%
- **Active Users:** 150+ семей

### **Инструменты:**
- **Railway Logs** — централизованное логирование
- **Yandex Metrica** (ID: 104525544) — веб-аналитика
- **Sentry** (опционально) — мониторинг ошибок

---

## 🤝 **Вклад в проект**

Мы открыты для вклада! Прочитайте [CONTRIBUTING.md](CONTRIBUTING.md) для деталей.

### **Процесс:**

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'feat: Add AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

### **Соглашения:**

- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/)
- **Code Style:** PEP 8, Black, isort
- **Tests:** обязательны для новых фич
- **Documentation:** обновляйте при изменениях API

---

## 📄 **Лицензия**

Этот проект лицензирован под **MIT License** — см. [LICENSE](LICENSE).

---

## 👥 **Команда**

**Lead Developer:** [@gaus-1](https://github.com/gaus-1)

### **Технологический стек:**
- **Backend:** Python 3.13, FastAPI, aiogram, SQLAlchemy
- **Frontend:** React 18, TypeScript, Vite, Tailwind
- **Database:** PostgreSQL 17
- **AI:** Yandex Cloud (YandexGPT, SpeechKit, Vision)
- **Infrastructure:** Railway, Cloudflare, GitHub Actions

---

## 📞 **Контакты**

- **Website:** [pandapal.ru](https://pandapal.ru)
- **Telegram Bot:** [@PandaPal_bot](https://t.me/PandaPal_bot)
- **Email:** support@pandapal.ru
- **GitHub:** [github.com/gaus-1/pandapal-bot](https://github.com/gaus-1/pandapal-bot)

---

<div align="center">

**Сделано с ❤️ для детей и их родителей**

[⬆ Наверх](#-pandapal---безопасный-ии-помощник-для-детей)

</div>
