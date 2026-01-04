-- Активация Premium подписки для пользователя 963126718 (Вячеслав)
-- Платёж: 30ecc421-000f-5001-8000-1fbb0ea447b2 (99₽, СБП)

-- Проверяем существующие активные подписки
SELECT id, user_telegram_id, plan_id, expires_at, is_active
FROM subscriptions
WHERE user_telegram_id = 963126718 AND is_active = true;

-- Деактивируем старые подписки (если есть)
UPDATE subscriptions
SET is_active = false
WHERE user_telegram_id = 963126718 AND is_active = true;

-- Создаём новую подписку на неделю
INSERT INTO subscriptions (
    user_telegram_id,
    plan_id,
    starts_at,
    expires_at,
    is_active,
    transaction_id,
    payment_method,
    payment_id
) VALUES (
    963126718,                                    -- Твой Telegram ID
    'week',                                       -- План: неделя
    NOW(),                                        -- Начало: сейчас
    NOW() + INTERVAL '7 days',                    -- Окончание: через 7 дней
    true,                                         -- Активна
    '30ecc421-000f-5001-8000-1fbb0ea447b2',      -- ID платежа
    'yookassa_sbp',                              -- Способ: СБП
    '30ecc421-000f-5001-8000-1fbb0ea447b2'       -- ID платежа YooKassa
);

-- Проверяем результат
SELECT id, user_telegram_id, plan_id, starts_at, expires_at, is_active, payment_id
FROM subscriptions
WHERE user_telegram_id = 963126718
ORDER BY created_at DESC
LIMIT 1;
