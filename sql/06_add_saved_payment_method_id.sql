-- Добавление поля saved_payment_method_id в таблицу subscriptions
-- Эта миграция должна применяться после миграций add_payment_method и add_auto_renew

-- Проверяем, существует ли уже столбец
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'subscriptions'
        AND column_name = 'saved_payment_method_id'
    ) THEN
        -- Добавляем столбец
        ALTER TABLE subscriptions
        ADD COLUMN saved_payment_method_id VARCHAR(255) NULL;

        RAISE NOTICE 'Столбец saved_payment_method_id успешно добавлен';
    ELSE
        RAISE NOTICE 'Столбец saved_payment_method_id уже существует';
    END IF;
END $$;
