/**
 * API для игр.
 */

import { API_BASE_URL } from './config';

export interface GameSession {
  id: number;
  game_type: 'tic_tac_toe' | 'checkers' | '2048' | 'erudite';
  game_state: Record<string, unknown>;
  result: 'win' | 'loss' | 'draw' | 'in_progress' | null;
  score: number | null;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
}

export interface GameStats {
  game_type: string;
  total_games: number;
  wins: number;
  losses: number;
  draws: number;
  win_rate: number;
  best_score: number | null;
  total_score: number;
  last_played_at: string | null;
}

/**
 * Создать новую игровую сессию
 */
export async function createGame(telegramId: number, gameType: string): Promise<{ session_id: number; game_type: string; game_state: Record<string, unknown> }> {
  const response = await fetch(`${API_BASE_URL}/miniapp/games/${telegramId}/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ game_type: gameType }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(errorData.error || 'Ошибка создания игры');
  }

  const data = await response.json();
  return data;
}

/**
 * Сделать ход в крестики-нолики
 */
export async function ticTacToeMove(sessionId: number, position: number): Promise<{
  board: (string | null)[];
  winner: 'user' | 'ai' | null;
  game_over: boolean;
  ai_move: number | null;
}> {
  const response = await fetch(`${API_BASE_URL}/miniapp/games/tic-tac-toe/${sessionId}/move`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ position }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(errorData.error || 'Ошибка хода');
  }

  const data = await response.json();
  return data;
}

/**
 * Получить валидные ходы в шашках
 */
export async function getCheckersValidMoves(sessionId: number): Promise<Array<{
  from: [number, number];
  to: [number, number];
  capture: [number, number] | null;
}>> {
  const response = await fetch(`${API_BASE_URL}/miniapp/games/checkers/${sessionId}/valid-moves`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(errorData.error || 'Ошибка получения валидных ходов');
  }

  const data = await response.json();
  return data.valid_moves;
}

/**
 * Сделать ход в шашках
 */
export async function checkersMove(
  sessionId: number,
  fromRow: number,
  fromCol: number,
  toRow: number,
  toCol: number
): Promise<{
  board: (string | null)[][];
  kings?: boolean[][];
  winner: 'user' | 'ai' | null;
  game_over: boolean;
  ai_move: [number, number, number, number] | null;
}> {
  const response = await fetch(`${API_BASE_URL}/miniapp/games/checkers/${sessionId}/move`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from_row: fromRow,
      from_col: fromCol,
      to_row: toRow,
      to_col: toCol,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(errorData.error || 'Ошибка хода');
  }

  const data = await response.json();
  return data;
}

/**
 * Сделать ход в 2048
 */
export async function game2048Move(sessionId: number, direction: 'up' | 'down' | 'left' | 'right'): Promise<{
  board: number[][];
  score: number;
  game_over: boolean;
  won: boolean;
}> {
  const response = await fetch(`${API_BASE_URL}/miniapp/games/2048/${sessionId}/move`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ direction }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(errorData.error || 'Ошибка хода');
  }

  const data = await response.json();
  return data;
}


/**
 * Получить статистику игр
 */
export async function getGameStats(telegramId: number, gameType?: string): Promise<GameStats | Record<string, GameStats>> {
  const url = gameType
    ? `${API_BASE_URL}/miniapp/games/${telegramId}/stats?game_type=${gameType}`
    : `${API_BASE_URL}/miniapp/games/${telegramId}/stats`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Ошибка получения статистики');
  }

  const data = await response.json();
  return data.stats;
}

/**
 * Получить игровую сессию
 */
export async function getGameSession(sessionId: number): Promise<GameSession> {
  const response = await fetch(`${API_BASE_URL}/miniapp/games/session/${sessionId}`);

  if (!response.ok) {
    throw new Error('Ошибка получения сессии');
  }

  const data = await response.json();
  return data.session;
}

/**
 * Premium API
 */

/**
 * Создать платеж через ЮKassa
 */
