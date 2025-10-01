# 🐼 PandaPal — ИИ-бот для безопасного обучения школьников

Образовательный ИИ-ассистент для детей 1–9 классов с адаптивным обучением, геймификацией и родительским контролем.

## 🎯 О проекте

**PandaPal** — это дружелюбный ИИ-помощник, который:
- 📚 Помогает школьникам учиться в игровой форме
- 🎮 Адаптируется под возраст и интересы ребёнка
- 🔒 Обеспечивает безопасность и фильтрацию контента
- 📊 Предоставляет родителям аналитику прогресса
- 👨‍🏫 Даёт учителям инструменты для генерации заданий

## 🏗️ Архитектура проекта

```
PandaPal/
├── frontend/           # Веб-интерфейс (React + TypeScript + Tailwind)
│   ├── src/
│   │   ├── components/   # UI-компоненты
│   │   ├── config/       # Конфигурация и константы
│   │   ├── types/        # TypeScript типы
│   │   ├── utils/        # Вспомогательные функции
│   │   └── hooks/        # Кастомные React хуки
│   └── public/           # Статические файлы (logo.png)
│
├── backend/            # API-сервер (планируется: FastAPI/Flask)
│   └── [пока не создан]
│
├── bot/                # Telegram-бот (планируется: aiogram)
│   └── [пока не создан]
│
└── alembic/            # Миграции базы данных
    └── versions/       # История миграций
```

## 🚀 Быстрый старт

### Фронтенд

```bash
cd frontend
npm install
npm run dev
```

Откройте http://localhost:5173

### База данных

```bash
# Активируйте виртуальное окружение
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate # Linux/Mac

# Примените миграции
alembic upgrade head
```

## 🌐 Деплой

### Production окружение

- **Фронтенд:** https://pandapal.ru
- **Telegram Bot:** https://t.me/PandaPalBot
- **База данных:** PostgreSQL 17 на Render (Frankfurt)

### Автодеплой

При push в `main` → автоматический деплой на Render:
- Frontend → Static Site
- Bot → Web Service (Python)
- Database → PostgreSQL (уже развёрнута)

## 💾 База данных

### Схема (PostgreSQL 17)

#### Таблица `users`
Пользователи системы (дети, родители, учителя)
- `telegram_id` — уникальный ID из Telegram
- `user_type` — роль: child/parent/teacher
- `parent_telegram_id` — связь ребёнка с родителем
- `age`, `grade` — возраст и класс

#### Таблица `learning_sessions`
Сессии обучения (один урок/тест)
- `subject`, `topic` — предмет и тема
- `difficulty_level` — уровень сложности
- `questions_answered`, `correct_answers` — статистика

#### Таблица `user_progress`
Прогресс пользователя
- `subject`, `level` — предмет и уровень владения
- `points` — очки (для геймификации)
- `achievements` — достижения (JSON)

#### Таблица `chat_history`
История чата с ИИ (для контекста)
- `message_text` — текст сообщения
- `message_type` — тип (user/bot/system)

### Подключение

```bash
# External URL (для локальной разработки)
postgresql://pandapal_user:7rCuhY8R8C1fHvblUPdFjLzgMoLKn95D@dpg-d3bvnm37mgec73a3gjbg-a.frankfurt-postgres.render.com/pandapal_db
```

## 🛠️ Технологии

### Frontend
- React 19 (UI библиотека)
- TypeScript 5 (строгая типизация)
- Vite 7 (сборщик)
- Tailwind CSS 3 (стили)
- ESLint (линтинг)

### Backend (планируется)
- Python 3.13
- FastAPI/Flask (API)
- aiogram 3 (Telegram bot)
- SQLAlchemy 2 (ORM)
- Alembic (миграции)

### Infrastructure
- **Hosting:** Render.com
- **Database:** PostgreSQL 17
- **CDN:** Render Global CDN
- **SSL:** Let's Encrypt (автоматически)
- **Регион:** Frankfurt (EU Central)

## 📚 Документация

- [Frontend README](frontend/README.md) — документация фронтенда
- [CONTRIBUTING.md](CONTRIBUTING.md) — руководство по разработке
- [Database Schema](docs/database.md) — схема БД (создать)

## 🤝 Разработка

### Установка

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot

# 2. Установите зависимости фронтенда
cd frontend
npm install

# 3. Создайте Python venv (для бэкенда)
cd ..
python -m venv .venv
.\.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Workflow

1. Создайте feature branch: `git checkout -b feature/new-feature`
2. Внесите изменения
3. Проверьте код: `npm run lint` (фронтенд)
4. Закоммитьте: `git commit -m "feat: описание"`
5. Запушьте: `git push origin feature/new-feature`
6. Создайте Pull Request

## 📊 Статус проекта

### ✅ Готово
- [x] Frontend (веб-интерфейс)
- [x] PostgreSQL база данных
- [x] Схема БД (4 таблицы)
- [x] Домен pandapal.ru
- [x] Автодеплой на Render

### 🚧 В разработке
- [ ] Telegram-бот (aiogram)
- [ ] Backend API (FastAPI)
- [ ] Интеграция с ИИ (OpenAI/GigaChat)
- [ ] Система авторизации через Telegram
- [ ] Панель аналитики для родителей

### 📅 Roadmap
- [ ] Мобильное приложение (React Native)
- [ ] Интеграция с Google Classroom
- [ ] Голосовой ассистент
- [ ] Multilanguage support (en, ru)

## 🔐 Безопасность

- Все данные в БД зашифрованы
- HTTPS обязателен
- Фильтрация контента для детей
- Родительский контроль
- GDPR/ФЗ-152 compliance

## 📞 Контакты

- **Website:** https://pandapal.ru
- **Telegram Bot:** https://t.me/PandaPalBot
- **Email:** v81158847@gmail.com
- **GitHub:** https://github.com/gaus-1/pandapal-bot

## 📄 Лицензия

© 2025 PandaPal. Все права защищены.

---

**Сделано с ❤️ для детей и их родителей**
