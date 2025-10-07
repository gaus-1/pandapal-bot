# 🐼 PandaPal — Безопасный ИИ-ассистент для школьников

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![React](https://img.shields.io/badge/React-19+-61DAFB.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4.svg)
![AI](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-4285F4.svg)
![Coverage](https://img.shields.io/badge/Coverage-35.23%25-yellow.svg)
![Tests](https://img.shields.io/badge/Tests-152%20passing-success.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

> **Telegram-бот на базе Google Gemini AI для безопасного и адаптивного обучения школьников 1–11 классов**

🔗 **Попробовать:** [@PandaPalBot](https://t.me/PandaPalBot)  
🌐 **Сайт:** [pandapal.ru](https://pandapal.ru) *(в разработке)*

---

## ✨ Что умеет PandaPal (реально работает)

### 🎯 **Основной функционал**

✅ **AI-ассистент для обучения**
- Отвечает на вопросы по всем школьным предметам
- Объясняет сложные темы простым языком
- Решает задачи с подробным объяснением
- Дает подсказки вместо готовых ответов

✅ **Безопасность контента**
- 5-уровневая система модерации
- Фильтрация запрещенных тем (политика, насилие, 18+, наркотики)
- Контекстный анализ сообщений
- Возрастная адаптация контента

✅ **Умная память**
- Помнит последние 200 сообщений для контекста
- Автоудаление истории при достижении 400 сообщений
- Персонализация ответов на основе истории

✅ **Помощь с уроками**
- 9 предметов (математика, русский, физика, химия и др.)
- 4 типа помощи (решение, объяснение, проверка, подсказка)
- Специализированные промпты для каждого предмета

✅ **Профиль пользователя**
- Учет возраста (6-18 лет)
- Учет класса (1-11)
- Адаптация ответов под уровень ученика

✅ **Мониторинг и аналитика**
- Статистика сообщений и активности
- Отслеживание прогресса обучения
- Родительский контроль (базовая версия)

---

## 🚧 В разработке (roadmap)

### 🎮 **Геймификация** (запланировано)
- [ ] Система достижений и наград
- [ ] Опыт (XP) и уровни
- [ ] Рейтинг учеников
- [ ] Образовательные викторины

### 👨‍👩‍👧 **Для родителей** (частично реализовано)
- [x] Базовый мониторинг активности
- [ ] Детальные отчеты по прогрессу
- [ ] Контроль времени обучения
- [ ] Настройка уровня безопасности
- [ ] Еженедельные отчеты на email

### 👩‍🏫 **Для учителей** (в планах)
- [ ] Генерация индивидуальных заданий
- [ ] Автоматическая проверка работ
- [ ] Аналитика вовлеченности класса
- [ ] Управление группами учеников

---

## 🏗️ Архитектура

```
PandaPal/
├── 🐍 Backend (Telegram Bot)
│   ├── bot/
│   │   ├── handlers/          # Обработчики команд
│   │   │   ├── start.py       # /start - регистрация ✅
│   │   │   ├── ai_chat.py     # Общение с AI ✅
│   │   │   ├── menu.py        # Кнопки меню ✅
│   │   │   ├── achievements.py # Достижения (заглушка) 🚧
│   │   │   └── settings.py    # Настройки ✅
│   │   ├── services/          # Бизнес-логика
│   │   │   ├── ai_service.py           # Gemini AI ✅
│   │   │   ├── ai_response_generator.py # Генерация ответов ✅
│   │   │   ├── ai_context_manager.py    # Контекст и адаптация ✅
│   │   │   ├── moderation_service.py    # Модерация ✅
│   │   │   ├── advanced_moderation.py   # Продвинутая модерация ✅
│   │   │   ├── history_service.py       # История чата ✅
│   │   │   ├── user_service.py          # CRUD пользователей ✅
│   │   │   ├── parental_control.py      # Родительский контроль 🟡
│   │   │   ├── analytics_service.py     # Аналитика 🟡
│   │   │   └── vision_service.py        # Анализ изображений ✅
│   │   ├── keyboards/         # UI компоненты
│   │   │   ├── main_kb.py     # Главное меню ✅
│   │   │   └── achievements_kb.py # Достижения (новое) ✅
│   │   ├── models.py          # SQLAlchemy модели ✅
│   │   ├── database.py        # PostgreSQL ✅
│   │   └── config.py          # Настройки (Pydantic) ✅
│   ├── main.py                # Polling режим (для разработки) ✅
│   └── webhook_bot.py         # Webhook режим (для продакшена) ✅
│
├── ⚛️ Frontend (Landing Page)
│   ├── src/
│   │   ├── components/        # React компоненты ✅
│   │   ├── security/          # XSS защита, CSP ✅
│   │   └── test/              # Vitest тесты ✅
│   └── Dockerfile             # Контейнеризация ✅
│
├── 🧪 Tests
│   ├── unit/                  # 152 реальных теста ✅
│   └── integration/           # Интеграционные тесты 🟡
│
├── 📚 Documentation
│   ├── docs/
│   │   ├── BOT_FUNCTIONALITY_MAP.md  # Карта функционала ✅
│   │   ├── WEBHOOK_SETUP.md          # Настройка webhook ✅
│   │   └── TESTING.md                # Гайд по тестированию ✅
│   └── CONTRIBUTING.md               # Для разработчиков ✅
│
└── 🚀 DevOps
    ├── Dockerfile             # Docker для бота ✅
    ├── docker-compose.yml     # Локальная разработка ✅
    ├── .github/workflows/     # CI/CD (GitHub Actions) ✅
    └── scripts/               # Утилиты ✅
```

---

## 🚀 Быстрый старт

### 📋 **Требования**
- Python 3.11+
- PostgreSQL 14+
- Node.js 18+ (для frontend)
- Telegram Bot Token ([получить здесь](https://t.me/BotFather))
- Google Gemini API Key ([получить здесь](https://ai.google.dev/))

### 1️⃣ **Клонирование**
```bash
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot
```

### 2️⃣ **Настройка окружения**
```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/Mac)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 3️⃣ **Переменные окружения**

Создайте `.env` в корне проекта:
```env
# База данных
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/pandapal

# Telegram
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather

# Google Gemini AI
GEMINI_API_KEY=ваш_ключ_от_google
GEMINI_MODEL=gemini-1.5-flash

# Настройки AI
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2048

# Безопасность
SECRET_KEY=случайная_строка_минимум_32_символа
CONTENT_FILTER_LEVEL=5
FORBIDDEN_TOPICS=политика,насилие,оружие,наркотики,экстремизм,терроризм
```

### 4️⃣ **Инициализация БД**
```bash
# Создание таблиц
alembic upgrade head

# Или прямая инициализация
python -c "from bot.database import init_db; init_db()"
```

### 5️⃣ **Запуск**

**Локально (Polling режим):**
```bash
python main.py
```

**Продакшен (Webhook режим):**
```bash
export WEBHOOK_DOMAIN=your-domain.com
export PORT=8000
python webhook_bot.py
```

**Через Docker Compose:**
```bash
docker-compose up --build
```

---

## 🧪 Тестирование

### **Backend тесты**
```bash
# Запуск всех тестов
pytest tests/

# С покрытием
pytest tests/ --cov=bot --cov-report=html

# Только unit тесты
pytest tests/unit/ -v
```

**Текущее покрытие:** 35.23% (152 теста, все реальные)

### **Frontend тесты**
```bash
cd frontend

# Все тесты
npm test

# Адаптивность
npm test -- src/test/responsive.test.tsx

# Coverage
npm run test:coverage
```

**Frontend покрытие:** 13/13 тестов адаптивности ✅

---

## 📊 Статистика проекта

### **Кодовая база**
- **Python:** ~3,917 строк
- **TypeScript/React:** ~1,500 строк
- **Tests:** 152 реальных теста (без моков)
- **Handlers:** 8 роутеров
- **Services:** 18 сервисов
- **Models:** 10 таблиц БД

### **Функциональность**
- ✅ **Работает:** 60%
- 🚧 **В разработке:** 30%
- 📋 **Запланировано:** 10%

---

## 🔒 Безопасность

### **Модерация контента (5 уровней)**

**Уровень 1:** Простые запрещенные слова (50+ паттернов)  
**Уровень 2:** Regex для SQL Injection, XSS  
**Уровень 3:** Контекстный анализ (продвинутая модерация)  
**Уровень 4:** Gemini Safety Settings (BLOCK_MEDIUM_AND_ABOVE)  
**Уровень 5:** Post-модерация ответов AI

### **Защита данных**
- ✅ Пароли не хранятся (Telegram авторизация)
- ✅ Все секреты в `.env` (не в коде)
- ✅ PostgreSQL с шифрованием
- ✅ HTTPS для всех запросов
- ✅ CSP заголовки на frontend

### **Родительский контроль**
- Мониторинг активности детей
- Логирование всех взаимодействий
- Предупреждения о подозрительной активности (в разработке)

---

## 🛠️ Технологический стек

### **Backend**
| Технология | Версия | Назначение |
|-----------|--------|------------|
| Python | 3.11+ | Основной язык |
| aiogram | 3.15.0 | Telegram Bot API |
| Google Gemini AI | 0.8.3 | Language Model (generativeai) |
| SQLAlchemy | 2.0.36 | ORM для PostgreSQL |
| Alembic | 1.13.2 | Миграции БД |
| Pydantic | 2.9.2 | Валидация и настройки |
| Loguru | 0.7.3 | Логирование |
| aiohttp | 3.10.11 | Async HTTP сервер |
| Sentry | 2.18.0 | Мониторинг ошибок |

### **Frontend**
| Технология | Версия | Назначение |
|-----------|--------|------------|
| React | 19.1.1 | UI библиотека |
| TypeScript | 5.6+ | Типизация |
| Vite | 6.0+ | Сборщик |
| Tailwind CSS | 3.4+ | Стилизация |
| Vitest | 2.1.9 | Тестирование |

### **DevOps & Infrastructure**
- **Render.com** — Хостинг (Web Service + PostgreSQL)
- **GitHub Actions** — CI/CD Pipeline
- **Docker** — Контейнеризация
- **PostgreSQL 14+** — База данных
- **Nginx** — Веб-сервер для frontend

---

## 📱 Функциональность бота

### **Главное меню**

```
┌─────────────────────────────────────┐
│ 💬 Общение с AI  │ 📚 Помощь с уроками │
├─────────────────────────────────────┤
│ 📊 Мой прогресс  │ 🏆 Достижения       │
├─────────────────────────────────────┤
│        ⚙️ Настройки                  │
└─────────────────────────────────────┘
```

### **Команды**
- `/start` — Регистрация и приветствие ✅
- `💬 Общение с AI` — Свободный чат с Gemini ✅
- `📚 Помощь с уроками` — Выбор предмета и типа помощи ✅
- `📊 Мой прогресс` — Статистика и аналитика ✅
- `🏆 Достижения` — Система наград (заглушка) 🚧
- `⚙️ Настройки` — Профиль, возраст, класс ✅

### **Предметы** (9 предметов)
- 🔢 Математика
- 📖 Русский язык
- 🌍 Окружающий мир
- 🇬🇧 Английский язык
- ⚗️ Химия
- 🔬 Физика
- 📜 История
- 🌎 География
- 🎨 Другие предметы

### **Типы помощи**
- 📝 Решить задачу
- 📚 Объяснить тему
- ✅ Проверить ответ
- 💡 Дать подсказку

---

## 💾 База данных (PostgreSQL)

### **Схема**

**`users`** — Пользователи (дети, родители, учителя)
- telegram_id, username, first_name, age, grade, user_type

**`chat_history`** — История сообщений (до 400 на пользователя)
- user_telegram_id, message_text, message_type, timestamp

**`learning_sessions`** — Сессии обучения
- user_telegram_id, subject, topic, difficulty, results

**`user_progress`** — Прогресс по предметам
- user_telegram_id, subject, level, points, achievements

**`analytics_metrics`** — Метрики аналитики
- user_telegram_id, event_type, metadata, timestamp

---

## 🚀 Деплой

### **Render.com (Production - Webhook)**

**1. Создайте PostgreSQL Database:**
- Скопируйте External Database URL

**2. Создайте Web Service:**
- Repository: `https://github.com/gaus-1/pandapal-bot`
- Branch: `main`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python web_server.py`

**3. Environment Variables:**
```
DATABASE_URL=postgresql://... (из шага 1)
TELEGRAM_BOT_TOKEN=ваш_токен
GEMINI_API_KEY=ваш_ключ
GEMINI_MODEL=gemini-1.5-flash
WEBHOOK_DOMAIN=your-service.onrender.com
PORT=10000 (автоматически)
```

**4. Деплой:**
- Render автоматически задеплоит при push в main
- Webhook будет установлен автоматически
- Бот заработает через 2-3 минуты

### **Локальная разработка (Polling)**

```bash
# Активировать окружение
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Запустить бота
python main.py
```

---

## 🧪 Качество кода

### **Code Quality Tools**
- ✅ **Black** — форматирование кода
- ✅ **isort** — сортировка импортов
- ✅ **Flake8** — линтинг PEP 8
- ✅ **MyPy** — проверка типов
- ✅ **Pylint** — статический анализ
- ✅ **Pre-commit hooks** — автоматическая проверка

### **Архитектурные принципы**
- ✅ **SOLID** — Single Responsibility, Dependency Injection
- ✅ **Clean Architecture** — разделение на слои (handlers, services, models)
- ✅ **DRY** — переиспользование кода
- ✅ **Type Hints** — полная типизация

### **Метрики**
```
Покрытие тестами:     35.23%
Реальные тесты:       152 шт (без моков)
PEP 8 соответствие:   95%+
Документация кода:    90%+
```

---

## 🗺️ Roadmap 2025

### **Q1 2025 (Октябрь-Декабрь)**
- [x] ✅ Базовый AI чат с Gemini
- [x] ✅ Модерация контента (5 уровней)
- [x] ✅ Профили пользователей
- [x] ✅ История сообщений (200 контекст)
- [x] ✅ Помощь с уроками (9 предметов)
- [x] ✅ Webhook для продакшена
- [x] ✅ Профессиональная структура проекта
- [ ] 🚧 Система достижений
- [ ] 🚧 Родительский контроль UI
- [ ] 📋 Функционал для учителей

### **Q2 2025 (Январь-Март) - Планируется**
- [ ] Полная система геймификации
- [ ] Генерация и проверка заданий (AI)
- [ ] Образовательные викторины
- [ ] Контроль времени обучения
- [ ] Email отчеты для родителей
- [ ] Мобильное приложение (PWA)

### **Q3 2025 (Апрель-Июнь) - Планируется**
- [ ] Интеграция с электронными дневниками
- [ ] API для сторонних сервисов
- [ ] Расширенная аналитика (ML)
- [ ] Голосовой помощник (Speech-to-Text)
- [ ] Поддержка групповых занятий

---

## 🤝 Вклад в проект

Мы приветствуем вклад сообщества! Прочитайте [CONTRIBUTING.md](CONTRIBUTING.md) для деталей.

### **Как помочь:**
1. 🐛 Сообщить о баге ([Issues](https://github.com/gaus-1/pandapal-bot/issues))
2. 💡 Предложить новую функцию
3. 🔧 Исправить баг (Pull Request)
4. 📝 Улучшить документацию
5. ⭐ Поставить звезду проекту

### **Процесс разработки:**
1. Fork репозитория
2. Создайте feature ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'feat: Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

---

## 📄 Лицензия

MIT License © 2025 PandaPal Team

Вы можете свободно использовать, изменять и распространять этот проект.

---

## 🌟 Поддержка проекта

Если PandaPal помог вашему ребенку — поставьте ⭐ проекту!

### **Связь**
- 📧 Email: v81158847@gmail.com
- 🐛 Issues: [github.com/gaus-1/pandapal-bot/issues](https://github.com/gaus-1/pandapal-bot/issues)
- 💬 Telegram: [@PandaPalBot](https://t.me/PandaPalBot)

---

## 📸 Скриншоты

### Главное меню
![Главное меню](https://via.placeholder.com/300x500.png?text=Main+Menu)

### Общение с AI
![AI Chat](https://via.placeholder.com/300x500.png?text=AI+Chat)

### Помощь с уроками
![Homework Help](https://via.placeholder.com/300x500.png?text=Homework+Help)

---

## 🙏 Благодарности

- [Google Gemini AI](https://ai.google.dev/) — за мощный AI движок
- [aiogram](https://aiogram.dev/) — за отличный Telegram Bot Framework
- [Render.com](https://render.com/) — за бесплатный хостинг
- Всем тестировщикам и early adopters! 🎉

---

<p align="center">
  <b>Сделано с ❤️ и 🐼 для безопасного обучения детей</b><br>
  <i>PandaPal — учеба может быть интересной и безопасной!</i>
</p>

---

## 📈 Activity

![GitHub last commit](https://img.shields.io/github/last-commit/gaus-1/pandapal-bot)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/gaus-1/pandapal-bot)
![GitHub repo size](https://img.shields.io/github/repo-size/gaus-1/pandapal-bot)

**Статус:** 🟢 Active Development  
**Версия:** 1.0.0-beta  
**Последнее обновление:** Октябрь 2025
