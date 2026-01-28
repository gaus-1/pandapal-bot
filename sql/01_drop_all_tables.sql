-- ============================================================================
-- СКРИПТ УДАЛЕНИЯ ВСЕХ ТАБЛИЦ PANDAPAL
-- ============================================================================
-- Этот скрипт удаляет все существующие таблицы в базе данных.
-- ВНИМАНИЕ: Все данные будут потеряны!
--
-- Использование в pgAdmin:
-- 1. Откройте Query Tool (Tools → Query Tool)
-- 2. Скопируйте и вставьте этот скрипт
-- 3. Нажмите F5 или кнопку Execute
-- ============================================================================

-- Удаляем таблицы в правильном порядке (сначала зависимые, потом основные)

-- Аналитика
DROP TABLE IF EXISTS analytics_config CASCADE;
DROP TABLE IF EXISTS analytics_alerts CASCADE;
DROP TABLE IF EXISTS analytics_trends CASCADE;
DROP TABLE IF EXISTS analytics_reports CASCADE;
DROP TABLE IF EXISTS user_events CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS analytics_metrics CASCADE;

-- Основные таблицы
DROP TABLE IF EXISTS chat_history CASCADE;
DROP TABLE IF EXISTS user_progress CASCADE;
DROP TABLE IF EXISTS learning_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Удаляем Alembic версии (если есть)
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Выводим результат
SELECT 'Все таблицы успешно удалены!' AS status;
