# 📊 Руководство по просмотру данных в PostgreSQL

## ❓ Ответы на вопросы

### 1. Заполняются ли таблицы в PostgreSQL?

**Да, таблицы заполняются автоматически** при работе бота:

- **`users`** — при первом использовании бота (`/start` или отправке сообщения)
- **`chat_history`** — при каждом сообщении пользователя и ответе AI
- **`analytics_metrics`** — при записи метрик (безопасность, образование)
- **`user_events`** — при событиях пользователей
- **`user_sessions`** — при активностях детей (для родительского контроля)

**Где происходит запись:**
- `bot/services/user_service.py` — создание пользователей
- `bot/services/history_service.py` — сохранение сообщений
- `bot/services/analytics_service.py` — запись метрик
- `bot/handlers/ai_chat.py` — основной обработчик сообщений

### 2. Как посмотреть данные в таблицах?

#### Вариант 1: Утилита `view_database.py` (рекомендуется)

```bash
# Активируйте виртуальное окружение
venv\Scripts\activate  # Windows
# или
source venv/bin/activate  # Linux/Mac

# Установите tabulate (если еще не установлен)
pip install tabulate

# Просмотр статистики по всем таблицам
python scripts/view_database.py

# Просмотр данных из таблицы users
python scripts/view_database.py --table users

# Просмотр последних 50 сообщений
python scripts/view_database.py --table chat_history --limit 50

# Проверка активности PostgreSQL
python scripts/view_database.py --activity

# Активность за последние 24 часа
python scripts/view_database.py --recent 24
```

#### Вариант 2: Проверка подключения и структуры

```bash
python check_database.py
```

Показывает:
- Статус подключения к БД
- Список таблиц и количество записей
- Структуру БД (индексы, Foreign Keys)

#### Вариант 3: Прямое подключение через psql

```bash
# Подключение к PostgreSQL
psql -h localhost -U postgres -d pandapal_db

# Или используя DATABASE_URL из .env
psql $DATABASE_URL

# Примеры запросов:
SELECT COUNT(*) FROM users;
SELECT * FROM users LIMIT 10;
SELECT * FROM chat_history ORDER BY timestamp DESC LIMIT 20;
```

#### Вариант 4: Через Python интерактивно

```python
from bot.database import get_db
from bot.models import User, ChatHistory

# Просмотр пользователей
with get_db() as db:
    users = db.query(User).limit(10).all()
    for user in users:
        print(f"{user.telegram_id}: {user.first_name} ({user.user_type})")

# Просмотр сообщений
with get_db() as db:
    messages = db.query(ChatHistory).order_by(ChatHistory.timestamp.desc()).limit(10).all()
    for msg in messages:
        print(f"{msg.timestamp}: {msg.message_type} - {msg.message_text[:50]}")
```

### 3. Как проверить активность PostgreSQL?

#### Через утилиту:

```bash
python scripts/view_database.py --activity
```

Показывает:
- Размер базы данных
- Количество активных подключений
- Размеры таблиц (топ-10)
- Статистику операций (INSERT, UPDATE, DELETE)

#### Через SQL запросы:

```sql
-- Размер БД
SELECT pg_size_pretty(pg_database_size(current_database()));

-- Активные подключения
SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();

-- Размеры таблиц
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Статистика операций
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows
FROM pg_stat_user_tables
ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC;
```

## 📋 Основные таблицы

| Таблица | Описание | Когда заполняется |
|---------|----------|-------------------|
| `users` | Пользователи (дети и родители) | При первом использовании бота |
| `chat_history` | История сообщений | При каждом сообщении |
| `learning_sessions` | Учебные сессии | При начале урока/теста |
| `user_progress` | Прогресс по предметам | При завершении заданий |
| `analytics_metrics` | Аналитические метрики | При записи метрик |
| `user_sessions` | Пользовательские сессии | При активности детей |
| `user_events` | События пользователей | При важных событиях |
| `analytics_reports` | Аналитические отчеты | При генерации отчетов |

## 🔍 Быстрая диагностика

```bash
# 1. Проверка подключения
python check_database.py

# 2. Статистика по таблицам
python scripts/view_database.py --stats

# 3. Последние сообщения
python scripts/view_database.py --table chat_history --limit 20

# 4. Активность за последние 24 часа
python scripts/view_database.py --recent 24
```

## ⚠️ Важно

- Убедитесь, что `.env` файл настроен с правильным `DATABASE_URL`
- Для локальной разработки используйте `postgresql://postgres:postgres@localhost:5432/pandapal_db`
- Для Railway.app используйте `DATABASE_URL` из переменных окружения Railway
- Все запросы через утилиту выполняются в режиме только чтения (безопасно)

## 📚 Дополнительно

- Подробная документация: `scripts/README_VIEW_DB.md`
- Структура БД: `bot/models.py`
- Настройки БД: `bot/database.py`
