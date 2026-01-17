-- Добавление поддержки Premium подписок
-- Миграция: add_premium_subs

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
        CHECK (plan_id IN ('month', 'year'))
);

-- Создаем индексы
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_active
    ON subscriptions(user_telegram_id, is_active);
CREATE INDEX IF NOT EXISTS idx_subscriptions_expires
    ON subscriptions(expires_at);

-- Комментарии для документации
COMMENT ON COLUMN users.premium_until IS 'Дата окончания Premium подписки';
COMMENT ON TABLE subscriptions IS 'Таблица Premium подписок пользователей';
COMMENT ON COLUMN subscriptions.plan_id IS 'Тип плана: month, year';
