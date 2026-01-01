# 📋 Инструкция по применению SQL файлов к базе данных PostgreSQL

## Шаг 1: Подключение к базе данных в pgAdmin

1. Откройте **pgAdmin 4**
2. Найдите ваше подключение к PostgreSQL 17
3. Выберите базу данных `pandapal_db` (или вашу)

## Шаг 2: Применение SQL скриптов

### Вариант A: Первая установка (чистая БД)

1. Откройте **Query Tool** (Инструменты → Редактор запросов)
2. Откройте файл `sql/02_create_tables.sql`
3. Нажмите **F5** или кнопку **Execute/Play**
4. Проверьте что все таблицы созданы:
   ```sql
   SELECT table_name
   FROM information_schema.tables
   WHERE table_schema = 'public'
   ORDER BY table_name;
   ```

### Вариант B: Пересоздание таблиц (если уже есть данные)

⚠️ **ВНИМАНИЕ: Все данные будут удалены!**

1. Сделайте бэкап данных:
   ```sql
   -- В pgAdmin: правой кнопкой на базу → Backup
   ```

2. Откройте **Query Tool**
3. Сначала выполните `sql/01_drop_all_tables.sql`
4. Затем выполните `sql/02_create_tables.sql`

### Вариант C: Использование Alembic (рекомендуется для продакшена)

1. Убедитесь что `.env` содержит правильный `DATABASE_URL`
2. Запустите миграции:
   ```bash
   # В терминале проекта
   cd C:\Users\Vyacheslav\PandaPal
   .\venv\Scripts\activate
   alembic upgrade head
   ```

## Шаг 3: Проверка применения

```sql
-- Проверяем что таблицы созданы
SELECT 'База данных PandaPal успешно создана!' AS status;

-- Считаем количество таблиц
SELECT COUNT(*) AS tables_count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- Должно быть минимум 8 таблиц:
-- 1. users
-- 2. chat_history
-- 3. learning_sessions
-- 4. user_progress
-- 5. analytics_metrics
-- 6. user_sessions
-- 7. user_events
-- 8. analytics_reports
```

## Шаг 4: Настройка .env для подключения

Создайте файл `.env` в корне проекта:

```env
# Замените на ваши реальные данные из pgAdmin
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/pandapal_db
TELEGRAM_BOT_TOKEN=your_bot_token
YANDEX_CLOUD_API_KEY=your_api_key
YANDEX_CLOUD_FOLDER_ID=your_folder_id
SECRET_KEY=your_secret_key_32_chars_minimum
```

## Шаг 5: Тестирование подключения

```python
# Запустите в Python:
from bot.database import DatabaseService

# Проверяем подключение
if DatabaseService.check_connection():
    print("✅ База данных подключена успешно!")
else:
    print("❌ Ошибка подключения к БД")
```

## Полезные SQL команды

```sql
-- Просмотр всех таблиц
\dt

-- Просмотр структуры таблицы
\d+ chat_history

-- Просмотр индексов
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Просмотр внешних ключей
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM
    information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE constraint_type = 'FOREIGN KEY';
```

## Troubleshooting

### Ошибка: "relation already exists"
- Значит таблицы уже созданы
- Используйте `01_drop_all_tables.sql` сначала

### Ошибка: "permission denied"
- Проверьте что у пользователя PostgreSQL есть права
- Подключитесь как суперпользователь (postgres)

### Ошибка подключения в Python
- Проверьте `DATABASE_URL` в `.env`
- Формат: `postgresql://user:password@host:port/database`
- Убедитесь что PostgreSQL запущен (проверьте в pgAdmin)

## Автоматизация (для CI/CD)

```bash
# Применить SQL скрипт из командной строки
psql -U postgres -d pandapal_db -f sql/02_create_tables.sql

# Или через Python
python -c "from bot.database import init_db; init_db()"
```
