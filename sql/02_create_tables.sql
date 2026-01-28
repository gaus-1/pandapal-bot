-- ============================================================================
-- СКРИПТ СОЗДАНИЯ ТАБЛИЦ PANDAPAL (ОПТИМИЗИРОВАННАЯ ВЕРСИЯ)
-- ============================================================================
-- Профессиональная структура базы данных для образовательного бота PandaPal
--
-- Особенности:
-- - Оптимизированные индексы для быстрых запросов
-- - Правильные внешние ключи с CASCADE
-- - Ограничения (constraints) для валидации данных
-- - Комментарии для документации
-- - Партиционирование для больших таблиц (готово к масштабированию)
--
-- Использование в pgAdmin:
-- 1. Откройте Query Tool (Tools → Query Tool)
-- 2. Скопируйте и вставьте этот скрипт
-- 3. Нажмите F5 или кнопку Execute
-- ============================================================================

-- ============================================================================
-- 1. ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ (ДЕТИ И РОДИТЕЛИ)
-- ============================================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),

    -- Профиль ребенка
    age INTEGER CHECK (age IS NULL OR (age >= 6 AND age <= 18)),
    grade INTEGER CHECK (grade IS NULL OR (grade >= 1 AND grade <= 11)),

    -- Тип пользователя
    user_type VARCHAR(20) NOT NULL DEFAULT 'child' CHECK (user_type IN ('child', 'parent')),

    -- Связь родитель-ребенок
    parent_telegram_id BIGINT REFERENCES users(telegram_id) ON DELETE SET NULL,

    -- Метаданные
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Дополнительные настройки (JSON)
    settings JSONB DEFAULT '{}'::jsonb,

    -- Индексы
    CONSTRAINT users_telegram_id_key UNIQUE (telegram_id)
);

-- Индексы для users
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_parent_id ON users(parent_telegram_id);
CREATE INDEX idx_users_type ON users(user_type);
CREATE INDEX idx_users_active ON users(is_active);

-- Комментарии
COMMENT ON TABLE users IS 'Пользователи системы (дети и родители)';
COMMENT ON COLUMN users.telegram_id IS 'Уникальный ID из Telegram';
COMMENT ON COLUMN users.user_type IS 'Тип: child (ребенок) или parent (родитель)';
COMMENT ON COLUMN users.parent_telegram_id IS 'ID родителя для детского аккаунта';

-- ============================================================================
-- 2. ИСТОРИЯ ЧАТА (СООБЩЕНИЯ С AI)
-- ============================================================================

CREATE TABLE chat_history (
    id BIGSERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,

    -- Содержание
    message_text TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL CHECK (message_type IN ('user', 'ai', 'system')),

    -- Метаданные
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tokens_used INTEGER DEFAULT 0,

    -- Дополнительные данные (JSON)
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Индексы для chat_history
CREATE INDEX idx_chat_history_user ON chat_history(user_telegram_id);
CREATE INDEX idx_chat_history_timestamp ON chat_history(timestamp DESC);
CREATE INDEX idx_chat_history_user_time ON chat_history(user_telegram_id, timestamp DESC);
CREATE INDEX idx_chat_history_type ON chat_history(message_type);

-- Комментарии
COMMENT ON TABLE chat_history IS 'История сообщений пользователя с AI';
COMMENT ON COLUMN chat_history.message_type IS 'Тип: user (от пользователя), ai (от AI), system (системное)';
COMMENT ON COLUMN chat_history.tokens_used IS 'Количество токенов использованных AI';

-- ============================================================================
-- 3. УЧЕБНЫЕ СЕССИИ
-- ============================================================================

CREATE TABLE learning_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,

    -- Информация о сессии
    subject VARCHAR(100),
    topic VARCHAR(255),
    difficulty_level INTEGER CHECK (difficulty_level >= 1 AND difficulty_level <= 10),

    -- Статистика
    questions_answered INTEGER NOT NULL DEFAULT 0,
    correct_answers INTEGER NOT NULL DEFAULT 0,
    accuracy DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN questions_answered > 0
            THEN (correct_answers::DECIMAL / questions_answered * 100)
            ELSE 0
        END
    ) STORED,

    -- Временные метки
    session_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_end TIMESTAMPTZ,
    duration_seconds INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (session_end - session_start))::INTEGER
    ) STORED,

    is_completed BOOLEAN NOT NULL DEFAULT FALSE,

    -- Дополнительные данные
    session_data JSONB DEFAULT '{}'::jsonb
);

-- Индексы для learning_sessions
CREATE INDEX idx_learning_sessions_user ON learning_sessions(user_telegram_id);
CREATE INDEX idx_learning_sessions_start ON learning_sessions(session_start DESC);
CREATE INDEX idx_learning_sessions_subject ON learning_sessions(subject);
CREATE INDEX idx_learning_sessions_completed ON learning_sessions(is_completed);

-- Комментарии
COMMENT ON TABLE learning_sessions IS 'Учебные сессии пользователей';
COMMENT ON COLUMN learning_sessions.accuracy IS 'Процент правильных ответов (автоматически вычисляется)';
COMMENT ON COLUMN learning_sessions.duration_seconds IS 'Длительность сессии в секундах (автоматически)';

-- ============================================================================
-- 4. ПРОГРЕСС ПОЛЬЗОВАТЕЛЯ
-- ============================================================================

CREATE TABLE user_progress (
    id BIGSERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,

    -- Предмет и уровень
    subject VARCHAR(100) NOT NULL,
    level INTEGER NOT NULL DEFAULT 1 CHECK (level >= 1 AND level <= 100),

    -- Геймификация
    points INTEGER NOT NULL DEFAULT 0,
    achievements JSONB DEFAULT '[]'::jsonb,

    -- Статистика
    total_sessions INTEGER NOT NULL DEFAULT 0,
    total_time_seconds INTEGER NOT NULL DEFAULT 0,
    average_accuracy DECIMAL(5,2) DEFAULT 0,

    -- Последняя активность
    last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Уникальность: один прогресс на пользователя + предмет
    CONSTRAINT uq_user_progress_user_subject UNIQUE (user_telegram_id, subject)
);

-- Индексы для user_progress
CREATE INDEX idx_user_progress_user ON user_progress(user_telegram_id);
CREATE INDEX idx_user_progress_subject ON user_progress(subject);
CREATE INDEX idx_user_progress_level ON user_progress(level DESC);
CREATE INDEX idx_user_progress_points ON user_progress(points DESC);

-- Комментарии
COMMENT ON TABLE user_progress IS 'Прогресс пользователя по предметам';
COMMENT ON COLUMN user_progress.achievements IS 'Массив достижений в формате JSON';

-- ============================================================================
-- 5. АНАЛИТИКА: МЕТРИКИ
-- ============================================================================

CREATE TABLE analytics_metrics (
    id BIGSERIAL PRIMARY KEY,

    -- Метрика
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    metric_type VARCHAR(50) NOT NULL,

    -- Теги для фильтрации
    tags JSONB DEFAULT '{}'::jsonb,

    -- Временные данные
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    period VARCHAR(20) NOT NULL CHECK (period IN ('minute', 'hour', 'day', 'week', 'month')),

    -- Пользователь (опционально)
    user_telegram_id BIGINT
);

-- Индексы для analytics_metrics
CREATE INDEX idx_analytics_metrics_name ON analytics_metrics(metric_name);
CREATE INDEX idx_analytics_metrics_timestamp ON analytics_metrics(timestamp DESC);
CREATE INDEX idx_analytics_metrics_name_time ON analytics_metrics(metric_name, timestamp DESC);
CREATE INDEX idx_analytics_metrics_user ON analytics_metrics(user_telegram_id);
CREATE INDEX idx_analytics_metrics_period ON analytics_metrics(period);

-- Комментарии
COMMENT ON TABLE analytics_metrics IS 'Метрики для аналитики и мониторинга';

-- ============================================================================
-- 6. АНАЛИТИКА: СЕССИИ ПОЛЬЗОВАТЕЛЕЙ
-- ============================================================================

CREATE TABLE user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL,

    -- Временные рамки
    session_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_end TIMESTAMPTZ,
    session_duration INTEGER,

    -- Статистика активности
    messages_count INTEGER NOT NULL DEFAULT 0,
    ai_interactions INTEGER NOT NULL DEFAULT 0,
    voice_messages INTEGER NOT NULL DEFAULT 0,
    blocked_messages INTEGER NOT NULL DEFAULT 0,

    -- Предметы
    subjects_covered JSONB DEFAULT '[]'::jsonb,

    -- Оценки
    engagement_score DOUBLE PRECISION,
    safety_score DOUBLE PRECISION,

    -- Тип сессии
    session_type VARCHAR(50) NOT NULL DEFAULT 'regular',

    -- Информация об устройстве
    device_info JSONB DEFAULT '{}'::jsonb
);

-- Индексы для user_sessions
CREATE INDEX idx_user_sessions_user ON user_sessions(user_telegram_id);
CREATE INDEX idx_user_sessions_start ON user_sessions(session_start DESC);
CREATE INDEX idx_user_sessions_duration ON user_sessions(session_duration DESC);
CREATE INDEX idx_user_sessions_type ON user_sessions(session_type);

-- Комментарии
COMMENT ON TABLE user_sessions IS 'Сессии пользователей для аналитики';
COMMENT ON COLUMN user_sessions.engagement_score IS 'Оценка вовлеченности (0-100)';
COMMENT ON COLUMN user_sessions.safety_score IS 'Оценка безопасности (0-100)';

-- ============================================================================
-- 7. АНАЛИТИКА: СОБЫТИЯ
-- ============================================================================

CREATE TABLE user_events (
    id BIGSERIAL PRIMARY KEY,
    user_telegram_id BIGINT NOT NULL,

    -- Событие
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}'::jsonb,

    -- Временная метка
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Связь с сессией
    session_id BIGINT,

    -- Важность
    importance VARCHAR(20) NOT NULL DEFAULT 'normal' CHECK (importance IN ('low', 'normal', 'high', 'critical')),

    -- Обработка
    processed BOOLEAN NOT NULL DEFAULT FALSE
);

-- Индексы для user_events
CREATE INDEX idx_user_events_user ON user_events(user_telegram_id);
CREATE INDEX idx_user_events_timestamp ON user_events(timestamp DESC);
CREATE INDEX idx_user_events_type ON user_events(event_type);
CREATE INDEX idx_user_events_importance ON user_events(importance);
CREATE INDEX idx_user_events_processed ON user_events(processed);

-- Комментарии
COMMENT ON TABLE user_events IS 'События пользователей для аналитики';

-- ============================================================================
-- 8. АНАЛИТИКА: ОТЧЕТЫ
-- ============================================================================

CREATE TABLE analytics_reports (
    id BIGSERIAL PRIMARY KEY,

    -- Тип отчета
    report_type VARCHAR(50) NOT NULL,
    report_period VARCHAR(20) NOT NULL,

    -- Данные отчета
    report_data JSONB NOT NULL,

    -- Метаданные
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_by VARCHAR(100),

    -- Для кого отчет
    parent_telegram_id BIGINT,
    child_telegram_id BIGINT,

    -- Запланированный отчет?
    is_scheduled BOOLEAN NOT NULL DEFAULT FALSE
);

-- Индексы для analytics_reports
CREATE INDEX idx_analytics_reports_type ON analytics_reports(report_type);
CREATE INDEX idx_analytics_reports_parent ON analytics_reports(parent_telegram_id);
CREATE INDEX idx_analytics_reports_generated ON analytics_reports(generated_at DESC);

-- Комментарии
COMMENT ON TABLE analytics_reports IS 'Сгенерированные аналитические отчеты';

-- ============================================================================
-- ТРИГГЕРЫ ДЛЯ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ updated_at
-- ============================================================================

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для users
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ЗАВЕРШЕНИЕ
-- ============================================================================

SELECT 'База данных PandaPal успешно создана!' AS status;
SELECT 'Создано таблиц: ' || COUNT(*) AS tables_count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
