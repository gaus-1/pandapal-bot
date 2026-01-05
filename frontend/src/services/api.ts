/**
 * API Service для взаимодействия с Backend
 */

import { telegram } from './telegram';

const API_BASE_URL = import.meta.env.PROD
  ? 'https://pandapal.ru/api'
  : 'http://localhost:10000/api';

export interface UserProfile {
  telegram_id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  age?: number;
  grade?: number;
  user_type: 'child' | 'parent';
  premium_until?: string;
  is_premium: boolean;
  premium_days_left?: number;
  active_subscription?: {
    id: number;
    plan_id: string;
    starts_at: string;
    expires_at: string;
    is_active: boolean;
    payment_method?: string;
  };
}

export interface ProgressItem {
  subject: string;
  level: number;
  points: number;
  last_activity: string;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlock_date?: string;
  xp_reward?: number;
  progress?: number;
  progress_max?: number;
}

export interface DashboardStats {
  total_messages: number;
  learning_sessions: number;
  total_points: number;
  subjects_studied: number;
  current_streak: number;
}

/**
 * Аутентификация пользователя через Telegram initData
 */
export async function authenticateUser(): Promise<UserProfile> {
  const initData = telegram.getInitData();

  console.log('📡 API: Начало аутентификации');
  console.log('📡 API: initData length:', initData?.length || 0);
  console.log('📡 API: API URL:', `${API_BASE_URL}/miniapp/auth`);

  if (!initData) {
    console.error('❌ API: Telegram initData недоступен');
    throw new Error('Telegram initData недоступен. Убедитесь, что приложение открыто через Telegram.');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/miniapp/auth`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ initData }),
    });

    console.log('📡 API: Response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
      console.error('❌ API: Response error:', errorData);
      throw new Error(`Ошибка аутентификации: ${errorData.error || response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ API: Успешная аутентификация');
    return data.user;
  } catch (error) {
    console.error('❌ API: Network or fetch error:', error);
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Не удалось подключиться к серверу. Проверьте подключение к интернету.');
    }
    throw error;
  }
}

/**
 * Получить профиль пользователя
 */
export async function getUserProfile(telegramId: number): Promise<UserProfile> {
  const response = await fetch(`${API_BASE_URL}/miniapp/user/${telegramId}`);

  if (!response.ok) {
    throw new Error('Ошибка получения профиля');
  }

  const data = await response.json();
  return data.user;
}

/**
 * Получить прогресс обучения
 */
export async function getUserProgress(telegramId: number): Promise<ProgressItem[]> {
  const response = await fetch(`${API_BASE_URL}/miniapp/progress/${telegramId}`);

  if (!response.ok) {
    throw new Error('Ошибка получения прогресса');
  }

  const data = await response.json();
  return data.progress;
}

/**
 * Получить достижения
 */
export async function getUserAchievements(telegramId: number): Promise<Achievement[]> {
  const response = await fetch(`${API_BASE_URL}/miniapp/achievements/${telegramId}`);

  if (!response.ok) {
    throw new Error('Ошибка получения достижений');
  }

  const data = await response.json();
  return data.achievements;
}

/**
 * Получить статистику для дашборда
 */
export async function getDashboardStats(telegramId: number): Promise<DashboardStats> {
  const response = await fetch(`${API_BASE_URL}/miniapp/dashboard/${telegramId}`);

  if (!response.ok) {
    throw new Error('Ошибка получения статистики');
  }

  const data = await response.json();
  return data.stats;
}

export interface AchievementUnlocked {
  id: string;
  title: string;
  description: string;
  icon: string;
  xp_reward: number;
}

/**
 * Отправить сообщение AI (текст / фото / аудио)
 */
export async function sendAIMessage(
  telegramId: number,
  message?: string,
  photoBase64?: string,
  audioBase64?: string
): Promise<{ response: string; achievements_unlocked?: AchievementUnlocked[] }> {
  const response = await fetch(`${API_BASE_URL}/miniapp/ai/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      telegram_id: telegramId,
      // Отправляем message только если он есть (не пустая строка)
      ...(message && message.trim() ? { message } : {}),
      ...(photoBase64 ? { photo_base64: photoBase64 } : {}),
      ...(audioBase64 ? { audio_base64: audioBase64 } : {}),
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(errorData.error || 'Ошибка отправки сообщения');
  }

  return await response.json();
}

/**
 * Получить историю чата
 */
export async function getChatHistory(
  telegramId: number,
  limit: number = 50
): Promise<Array<{ role: 'user' | 'ai'; content: string; timestamp: string }>> {
  const response = await fetch(
    `${API_BASE_URL}/miniapp/chat/history/${telegramId}?limit=${limit}`
  );

  if (!response.ok) {
    throw new Error('Ошибка получения истории');
  }

  const data = await response.json();
  return data.history;
}

/**
 * Очистить историю чата
 */
export async function clearChatHistory(telegramId: number): Promise<{ deleted_count: number }> {
  const response = await fetch(
    `${API_BASE_URL}/miniapp/chat/history/${telegramId}`,
    {
      method: 'DELETE',
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(errorData.error || 'Ошибка очистки истории');
  }

  const data = await response.json();
  return data;
}

/**
 * Получить список предметов для обучения
 */
export async function getSubjects(): Promise<
  Array<{
    id: string;
    name: string;
    icon: string;
    description: string;
    grade_range: [number, number];
  }>
> {
  const response = await fetch(`${API_BASE_URL}/miniapp/subjects`);

  if (!response.ok) {
    throw new Error('Ошибка получения предметов');
  }

  const data = await response.json();
  return data.subjects;
}

/**
 * Обновить профиль пользователя
 */
export async function updateUserProfile(
  telegramId: number,
  updates: Partial<Pick<UserProfile, 'age' | 'grade'>>
): Promise<UserProfile> {
  const response = await fetch(`${API_BASE_URL}/miniapp/user/${telegramId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error('Ошибка обновления профиля');
  }

  const data = await response.json();
  return data.user;
}

/**
 * Игровые API
 */

export interface GameSession {
  id: number;
  game_type: 'tic_tac_toe' | 'checkers' | '2048';
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
