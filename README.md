# 🐼 PandaPal — Безопасный ИИ-друг для школьников

![Python](https://img.shields.io/badge/Python-3.11.9-blue.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4.svg)
![AI](https://img.shields.io/badge/AI-Gemini-4285F4.svg)
![Coverage](https://img.shields.io/badge/Coverage-41%25-yellow.svg)
![Tests](https://img.shields.io/badge/Tests-336%20passing-success.svg)

**PandaPal** — это Telegram-бот на базе Google Gemini AI для безопасного и адаптивного обучения школьников 1–9 классов.

## 🎯 Основные возможности

✅ **Адаптивное обучение** — подстраивается под возраст (6-18 лет) и класс (1-11)  
✅ **Безопасность** — фильтрация запрещённого контента (политика, насилие, наркотики, 18+)  
✅ **Память контекста** — помнит последние 50 сообщений для связного диалога  
✅ **Помощь с уроками** — решение задач, объяснение тем, проверка ответов  
✅ **Родительский контроль** — аналитика прогресса, настройки безопасности  
✅ **Геймификация** — система достижений и мотивации

---

## 🏗️ Архитектура проекта

```
PandaPal/
├── frontend/               # React + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── components/     # UI компоненты (Header, Hero, TelegramLogin...)
│   │   ├── config/         # Константы и настройки
│   │   ├── security/       # XSS защита, валидация, CSP
│   │   ├── types/          # TypeScript типы
│   │   └── utils/          # Утилиты (analytics, image fallback...)
│   ├── public/             # Статика (logo.png, security.txt)
│   └── index.html          # HTML точка входа
│
├── bot/                    # Telegram бот (Python + aiogram 3)
│   ├── config.py           # Настройки из .env (Pydantic)
│   ├── models.py           # SQLAlchemy модели (User, ChatHistory...)
│   ├── database.py         # Подключение к PostgreSQL
│   ├── services/           # Бизнес-логика
│   │   ├── ai_service.py          # Gemini AI интеграция
│   │   ├── moderation_service.py  # Фильтрация контента
│   │   ├── history_service.py     # Память чата (50 сообщений)
│   │   └── user_service.py        # CRUD пользователей
│   ├── handlers/           # Обработчики команд и сообщений
│   │   ├── start.py        # /start команда
│   │   ├── ai_chat.py      # Общение с AI
│   │   └── settings.py     # Настройки профиля
│   └── keyboards/          # Telegram клавиатуры (Reply/Inline)
│
├── alembic/                # Миграции БД
├── logs/                   # Логи приложения
├── .env                    # Переменные окружения (НЕ коммитить!)
├── requirements.txt        # Python зависимости
├── main.py                 # Точка входа бота
└── README.md               # Этот файл
```

---

## 🚀 Быстрый старт

### 1️⃣ Клонирование репозитория

```bash
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot
```

### 2️⃣ Установка зависимостей

**Backend (Python):**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

**Frontend (Node.js):**
```bash
cd frontend
npm install
```

### 3️⃣ Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# База данных PostgreSQL
DATABASE_URL=postgresql+psycopg://user:password@host:5432/db_name

# Telegram бот
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Google Gemini AI
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.0-flash-exp

# Настройки AI
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2048

# Безопасность
SECRET_KEY=ваш_секретный_ключ_минимум_32_символа
FORBIDDEN_TOPICS=политика,насилие,оружие,наркотики,экстремизм
CONTENT_FILTER_LEVEL=5

# URL фронтенда
FRONTEND_URL=https://pandapal.ru
```

### 4️⃣ Инициализация базы данных

```bash
# Создание таблиц
python -c "from bot.database import init_db; init_db()"

# Или через Alembic миграции
alembic upgrade head
```

### 5️⃣ Запуск приложения

**Telegram бот:**
```bash
python main.py
```

**Frontend (для разработки):**
```bash
cd frontend
npm run dev
```

**Frontend (production build):**
```bash
npm run build
npm run preview
```

---

## 🗄️ База данных

### Таблицы

#### `users` — Пользователи
```sql
- id                    SERIAL PRIMARY KEY
- telegram_id           BIGINT UNIQUE NOT NULL
- username              VARCHAR(255)
- first_name            VARCHAR(255)
- age                   INTEGER (6-18)
- grade                 INTEGER (1-11)
- user_type             VARCHAR(20) ('child', 'parent', 'teacher')
- parent_telegram_id    BIGINT (FK to users)
- created_at            TIMESTAMP
- is_active             BOOLEAN
```

#### `chat_history` — История сообщений
```sql
- id                    SERIAL PRIMARY KEY
- user_telegram_id      BIGINT (FK to users)
- message_text          TEXT
- message_type          VARCHAR(50) ('user', 'ai')
- timestamp             TIMESTAMP
```

#### `learning_sessions` — Сессии обучения
```sql
- id                    SERIAL PRIMARY KEY
- user_telegram_id      BIGINT (FK to users)
- subject               VARCHAR(100)
- topic                 VARCHAR(255)
- difficulty_level      INTEGER
- questions_answered    INTEGER
- correct_answers       INTEGER
- session_start         TIMESTAMP
- session_end           TIMESTAMP
- is_completed          BOOLEAN
```

#### `user_progress` — Прогресс пользователя
```sql
- id                    SERIAL PRIMARY KEY
- user_telegram_id      BIGINT (FK to users)
- subject               VARCHAR(100)
- level                 INTEGER
- points                INTEGER
- achievements          JSONB
- last_activity         TIMESTAMP
```

---

## 🤖 Использование бота

### Команды

- `/start` — Начало работы, регистрация
- `💬 Общение с AI` — Режим диалога с AI
- `📚 Помощь с уроками` — Специализированная помощь (решение задач, объяснение тем)
- `⚙️ Настройки` — Изменение профиля (возраст, класс)

### Пример диалога

```
Пользователь: Объясни что такое дроби
AI: Привет! 🐼 Дроби — это числа, которые показывают часть от целого...

Пользователь: Реши задачу: 2/3 + 1/4
AI: Отлично! Давай решим пошагово:
1. Найдём общий знаменатель: 12
2. Приведём дроби: 2/3 = 8/12, 1/4 = 3/12
3. Сложим: 8/12 + 3/12 = 11/12
Ответ: 11/12 ✅
```

---

## 🔒 Безопасность

### Контент-фильтрация

**5-уровневая система фильтрации:**
1. **Уровень 1:** Простая проверка на запрещённые темы
2. **Уровень 2:** Regex-паттерны (SQL Injection, XSS)
3. **Уровень 3:** Контекстный анализ
4. **Уровень 4:** Gemini Safety Settings (BLOCK_MEDIUM_AND_ABOVE)
5. **Уровень 5:** Post-модерация ответов AI

**Запрещённые темы:**
- Политика, выборы, правительство
- Насилие, война, убийство
- Оружие (пистолеты, автоматы, бомбы)
- Наркотики, алкоголь
- Экстремизм, терроризм
- 18+ контент (porn, sex, adult)

### Защита на фронтенде

- **XSS Protection:** Sanitize всех пользовательских inputs
- **CORS:** Разрешены только доверенные домены
- **CSP (Content Security Policy):** Строгий CSP header
- **HTTPS Only:** HSTS с max-age=31536000
- **Input Validation:** Валидация email, возраста, username

---

## 📦 Деплой на Render.com

### Backend (Telegram бот)

1. **Создайте Web Service на Render:**
   - Repository: `https://github.com/gaus-1/pandapal-bot`
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
   - Environment Variables: Добавьте все из `.env`

2. **PostgreSQL:**
   - Создайте PostgreSQL Database на Render
   - Скопируйте `External Database URL` в `DATABASE_URL`

### Frontend (React)

1. **Создайте Static Site на Render:**
   - Repository: тот же
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`

2. **Custom Domain:**
   - Добавьте `pandapal.ru` в Render
   - Настройте A-record в DNS: `pandapal.ru → 216.24.57.1`

---

## 🛠️ Технологии

### Backend
- **Python 3.10+** — Основной язык
- **aiogram 3.15** — Telegram Bot Framework
- **Google Gemini AI** — Language Model (gemini-2.0-flash-exp)
- **SQLAlchemy 2.0** — ORM для PostgreSQL
- **Alembic** — Миграции БД
- **Pydantic** — Валидация данных
- **Loguru** — Логирование

### Frontend
- **React 18** + **TypeScript** + **Vite**
- **Tailwind CSS** — UI стилизация
- **Vitest** — Тестирование
- **ESLint** — Линтинг кода

### DevOps
- **Render.com** — Хостинг (Static Site + Web Service + PostgreSQL)
- **GitHub** — Version Control
- **Docker** (опционально) — Контейнеризация

---

## 📊 Аналитика и мониторинг

- **Логирование:** Все события сохраняются в `logs/pandapal_YYYY-MM-DD.log`
- **Database Logs:** История чата, прогресс пользователей
- **Error Tracking:** Loguru с ротацией логов (30 дней)

---

## 🧪 Тестирование

### Frontend
```bash
cd frontend

# Запуск тестов
npm test

# Coverage
npm run test:coverage
```

**Покрытие тестами:**
- ✅ Unit Tests: компоненты (Header, Hero, FeatureCard...)
- ✅ Integration Tests: App (полная интеграция)
- ✅ Security Tests: sanitize, validation

### Backend
```bash
# TODO: Добавить pytest тесты
pytest tests/
```

---

## 📝 Лицензия

MIT License — свободное использование и модификация.

---

## 🤝 Контакты и поддержка

- **Email:** v81158847@gmail.com
- **GitHub Issues:** [github.com/gaus-1/pandapal-bot/issues](https://github.com/gaus-1/pandapal-bot/issues)
- **Telegram:** [@PandaPalBot](https://t.me/PandaPalBot)

---

## 🌟 Roadmap

- [x] Поддержка голосовых сообщений (Speech-to-Text) - ✅ РЕАЛИЗОВАНО
- [ ] Обработка изображений (Gemini Vision для задач с картинками)
- [ ] Парсинг PDF/Word документов
- [ ] Расширенная аналитика для родителей (дашборд)

---

<p align="center">
  <b>Сделано с ❤️ и 🐼 для безопасного обучения детей</b>
</p>
