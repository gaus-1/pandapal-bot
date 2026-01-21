-- Исправление constraint для game_type после замены Tetris на Two Dots
-- Выполнить вручную в продакшене, если миграция не применилась автоматически

-- 1. Удаляем все записи с game_type='tetris'
DELETE FROM game_sessions WHERE game_type = 'tetris';
DELETE FROM game_stats WHERE game_type = 'tetris';

-- 2. Удаляем старые constraints (если они существуют)
ALTER TABLE game_sessions DROP CONSTRAINT IF EXISTS ck_game_sessions_game_type;
ALTER TABLE game_stats DROP CONSTRAINT IF EXISTS ck_game_stats_game_type;

-- 3. Создаем новые constraints с поддержкой two_dots
ALTER TABLE game_sessions
ADD CONSTRAINT ck_game_sessions_game_type
CHECK (game_type IN ('tic_tac_toe', 'checkers', '2048', 'two_dots'));

ALTER TABLE game_stats
ADD CONSTRAINT ck_game_stats_game_type
CHECK (game_type IN ('tic_tac_toe', 'checkers', '2048', 'two_dots'));
