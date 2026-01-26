/**
 * API для аутентификации и профиля пользователя.
 */

import { telegram } from '../telegram';
import { API_BASE_URL } from './config';
import type { UserProfile, ProgressItem, Achievement, DashboardStats } from './types';

/**
 * Получить заголовки с авторизацией для защищенных запросов.
 * Включает X-Telegram-Init-Data для проверки владельца ресурса (OWASP A01).
 */
function getAuthHeaders(): HeadersInit {
  const initData = telegram.getInitData();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (initData) {
    headers['X-Telegram-Init-Data'] = initData;
  }

  return headers;
}

/**
 * Аутентификация пользователя через Telegram initData
 */
export async function authenticateUser(): Promise<UserProfile> {
  const initData = telegram.getInitData();

  if (!initData) {
    throw new Error('Telegram initData not available');
  }

  const response = await fetch(`${API_BASE_URL}/miniapp/auth`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      init_data: initData,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Authentication failed' }));
    throw new Error(errorData.error || 'Authentication failed');
  }

  const data = await response.json();
  return data.user; // Backend возвращает { success: true, user: {...} }
}

/**
 * Получить профиль пользователя
 */
export async function getUserProfile(telegramId: number): Promise<UserProfile> {
  const response = await fetch(`${API_BASE_URL}/miniapp/profile/${telegramId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user profile');
  }

  return response.json();
}

/**
 * Получить прогресс пользователя
 */
export async function getUserProgress(telegramId: number): Promise<ProgressItem[]> {
  const response = await fetch(`${API_BASE_URL}/miniapp/progress/${telegramId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user progress');
  }

  return response.json();
}

/**
 * Получить достижения пользователя
 */
export async function getUserAchievements(telegramId: number): Promise<Achievement[]> {
  const response = await fetch(`${API_BASE_URL}/miniapp/achievements/${telegramId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch achievements');
  }

  const data = await response.json();
  return data.achievements || [];
}

/**
 * Получить статистику дашборда
 */
export async function getDashboardStats(telegramId: number): Promise<DashboardStats> {
  const response = await fetch(`${API_BASE_URL}/miniapp/dashboard/${telegramId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    return {
      total_messages: 0,
      learning_sessions: 0,
      total_points: 0,
      subjects_studied: 0,
      current_streak: 0,
    };
  }

  return response.json();
}

/**
 * Получить предметы
 */
export async function getSubjects(): Promise<
  Array<{ id: string; name: string; icon: string; description: string }>
> {
  const response = await fetch(`${API_BASE_URL}/miniapp/subjects`);

  if (!response.ok) {
    throw new Error('Failed to fetch subjects');
  }

  return response.json();
}

/**
 * Обновить профиль пользователя
 */
export async function updateUserProfile(
  telegramId: number,
  data: { first_name?: string; age?: number; grade?: number }
): Promise<UserProfile> {
  const response = await fetch(`${API_BASE_URL}/miniapp/profile/${telegramId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update profile');
  }

  return response.json();
}
