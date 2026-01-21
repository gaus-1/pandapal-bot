-- Удаление Two Dots и добавление Erudite в game_type constraints

-- Удаляем старые записи Two Dots
DELETE FROM game_sessions WHERE game_type = 'two_dots';
DELETE FROM game_stats WHERE game_type = 'two_dots';

-- Удаляем старые constraints
ALTER TABLE game_sessions DROP CONSTRAINT IF EXISTS ck_game_sessions_game_type;
ALTER TABLE game_stats DROP CONSTRAINT IF EXISTS ck_game_stats_game_type;

-- Создаем новые constraints с erudite
ALTER TABLE game_sessions
ADD CONSTRAINT ck_game_sessions_game_type
CHECK (game_type IN ('tic_tac_toe', 'checkers', '2048', 'erudite'));

ALTER TABLE game_stats
ADD CONSTRAINT ck_game_stats_game_type
CHECK (game_type IN ('tic_tac_toe', 'checkers', '2048', 'erudite'));
