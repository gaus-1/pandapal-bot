-- Создание таблицы payments для хранения полной истории платежей
-- Миграция: add_payments_table

-- Создаем таблицу payments
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    payment_id VARCHAR(255) NOT NULL UNIQUE,  -- Уникальный ID от ЮKassa или Telegram
    user_telegram_id BIGINT NOT NULL,
    subscription_id INTEGER,  -- Связь с подпиской (если платеж успешен)
    payment_method VARCHAR(20) NOT NULL,  -- 'stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other'
    plan_id VARCHAR(20) NOT NULL,  -- 'month', 'year'
    amount FLOAT NOT NULL,  -- Сумма платежа
    currency VARCHAR(10) NOT NULL DEFAULT 'RUB',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'succeeded', 'cancelled', 'failed'
    payment_metadata JSONB,  -- Дополнительные данные платежа
    webhook_data JSONB,  -- Полные данные webhook для отладки
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP WITH TIME ZONE,  -- Дата успешной оплаты
    CONSTRAINT fk_payments_user
        FOREIGN KEY (user_telegram_id)
        REFERENCES users(telegram_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_payments_subscription
        FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(id)
        ON DELETE SET NULL,
    CONSTRAINT ck_payments_payment_method
        CHECK (payment_method IN ('stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other')),
    CONSTRAINT ck_payments_plan_id
        CHECK (plan_id IN ('month', 'year')),
    CONSTRAINT ck_payments_status
        CHECK (status IN ('pending', 'succeeded', 'cancelled', 'failed'))
);

-- Создаем индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_telegram_id ON payments(user_telegram_id);
CREATE INDEX IF NOT EXISTS idx_payments_subscription_id ON payments(subscription_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_user_status ON payments(user_telegram_id, status);
CREATE INDEX IF NOT EXISTS idx_payments_created ON payments(created_at);
CREATE INDEX IF NOT EXISTS idx_payments_paid ON payments(paid_at);

-- Комментарии для документации
COMMENT ON TABLE payments IS 'Таблица для хранения полной истории всех платежей (успешных и неуспешных)';
COMMENT ON COLUMN payments.payment_id IS 'Уникальный ID платежа в платежной системе (ЮKassa или Telegram)';
COMMENT ON COLUMN payments.subscription_id IS 'ID подписки, если платеж успешен и создана подписка';
COMMENT ON COLUMN payments.status IS 'Статус платежа: pending, succeeded, cancelled, failed';
COMMENT ON COLUMN payments.webhook_data IS 'Полные данные webhook для отладки и аудита';
