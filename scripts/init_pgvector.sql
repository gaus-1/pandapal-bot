-- Инициализация pgvector при первом запуске контейнера
-- Используется в docker-compose для локальной разработки
CREATE EXTENSION IF NOT EXISTS vector;
