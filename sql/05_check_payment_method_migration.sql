-- Проверка применения миграции payment_method
-- Убедитесь, что все колонки, индексы и constraint созданы

-- 1. Проверка колонок
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'subscriptions'
    AND column_name IN ('payment_method', 'payment_id')
ORDER BY column_name;

-- 2. Проверка индекса
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'subscriptions'
    AND indexname = 'idx_subscriptions_payment_id';

-- 3. Проверка constraint
SELECT
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'subscriptions'::regclass
    AND conname = 'ck_subscriptions_payment_method';
