-- Добавление полей payment_method и payment_id в таблицу subscriptions
-- Миграция: add_payment_method

-- Добавляем поле payment_method
ALTER TABLE subscriptions
ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20);

-- Добавляем поле payment_id
ALTER TABLE subscriptions
ADD COLUMN IF NOT EXISTS payment_id VARCHAR(255);

-- Создаем индекс на payment_id для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_subscriptions_payment_id
ON subscriptions(payment_id);

-- Добавляем constraint для payment_method
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_subscriptions_payment_method'
    ) THEN
        ALTER TABLE subscriptions
        ADD CONSTRAINT ck_subscriptions_payment_method
        CHECK (payment_method IS NULL OR payment_method IN ('stars', 'yookassa_card', 'yookassa_sbp', 'yookassa_other'));
    END IF;
END $$;
