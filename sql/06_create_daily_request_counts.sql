-- ============================================================================
-- МИГРАЦИЯ: Создание таблицы daily_request_counts
-- ============================================================================
-- Дата: 2026-01-XX
-- Описание: Таблица для подсчета дневных AI запросов пользователей
--           Независима от ChatHistory, не сбрасывается при очистке истории
-- ============================================================================

CREATE TABLE IF NOT EXISTS daily_request_counts (
    id BIGSERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,

    -- Дата запроса (только дата, без времени для группировки)
    date TIMESTAMPTZ NOT NULL,

    -- Количество запросов за день
    request_count INTEGER NOT NULL DEFAULT 0,

    -- Время последнего запроса
    last_request_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Уникальный индекс: один счетчик на пользователя в день
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_request_user_date
    ON daily_request_counts(user_telegram_id, date);

-- Индекс для быстрого поиска по дате
CREATE INDEX IF NOT EXISTS idx_daily_request_date
    ON daily_request_counts(date DESC);

-- Комментарии
COMMENT ON TABLE daily_request_counts IS 'Счетчик дневных AI запросов пользователей (независим от истории)';
COMMENT ON COLUMN daily_request_counts.date IS 'Дата запроса (начало дня в UTC)';
COMMENT ON COLUMN daily_request_counts.request_count IS 'Количество запросов за день';
COMMENT ON COLUMN daily_request_counts.last_request_at IS 'Время последнего запроса';
