# 🔧 Применение миграции Premium подписок

## ⚠️ КРИТИЧНО: Миграция не применена на production!

В production БД отсутствует колонка `users.premium_until` и таблица `subscriptions`.

## 🚀 Варианты применения миграции

### Вариант 1: SQL скрипт (быстро, для Railway)

1. Подключитесь к Railway PostgreSQL через Railway CLI или pgAdmin
2. Выполните SQL скрипт:

```sql
-- Файл: sql/03_add_premium_subscriptions.sql

-- Добавляем поле premium_until в таблицу users
ALTER TABLE users
ADD COLUMN IF NOT EXISTS premium_until TIMESTAMP WITH TIME ZONE;

-- Создаем таблицу subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL,
    plan_id VARCHAR(20) NOT NULL,
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    transaction_id VARCHAR(255),
    invoice_payload VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_subscriptions_user
        FOREIGN KEY (user_telegram_id)
        REFERENCES users(telegram_id)
        ON DELETE CASCADE,
    CONSTRAINT ck_subscriptions_plan_id
        CHECK (plan_id IN ('week', 'month', 'year'))
);

-- Создаем индексы
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_active
    ON subscriptions(user_telegram_id, is_active);
CREATE INDEX IF NOT EXISTS idx_subscriptions_expires
    ON subscriptions(expires_at);
```

### Вариант 2: Alembic миграция (рекомендуется)

1. Подключитесь к Railway через CLI или установите переменную `DATABASE_URL`
2. Запустите миграцию:

```bash
# Локально (с правильным DATABASE_URL)
alembic upgrade head

# Или через Railway CLI
railway run alembic upgrade head
```

### Вариант 3: Автоматическое применение при старте

Установите переменную окружения в Railway:

```
AUTO_MIGRATE=true
```

При следующем деплое миграции применятся автоматически.

## ✅ Проверка применения

После применения миграции проверьте:

```sql
-- Проверка колонки premium_until
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'users' AND column_name = 'premium_until';

-- Проверка таблицы subscriptions
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'subscriptions';

-- Проверка индексов
SELECT indexname
FROM pg_indexes
WHERE tablename = 'subscriptions';
```

## 🔍 Текущая проблема

**Ошибка в логах:**
```
column users.premium_until does not exist
```

**Решение:** Примените миграцию одним из способов выше.

## 📝 После применения

После успешного применения миграции:
1. Перезапустите приложение на Railway
2. Проверьте логи - ошибки должны исчезнуть
3. Система оплаты Premium начнет работать
