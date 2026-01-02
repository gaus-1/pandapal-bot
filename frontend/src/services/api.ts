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

  if (!initData) {
    throw new Error('Telegram initData недоступен');
  }

  const response = await fetch(`${API_BASE_URL}/miniapp/auth`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ initData }),
  });

  if (!response.ok) {
    throw new Error('Ошибка аутентификации');
  }

  const data = await response.json();
  return data.user;
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

/**
 * Отправить сообщение AI
 */
export async function sendAIMessage(
  telegramId: number,
  message: string
): Promise<{ response: string }> {
  const response = await fetch(`${API_BASE_URL}/miniapp/ai/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      telegram_id: telegramId,
      message,
    }),
  });

  if (!response.ok) {
    throw new Error('Ошибка отправки сообщения');
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
