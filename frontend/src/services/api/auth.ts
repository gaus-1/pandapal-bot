/**
 * API для аутентификации и профиля пользователя.
 */

import { telegram } from '../telegram';
import { API_BASE_URL } from './config';
import type { UserProfile, ProgressItem, Achievement, DashboardStats } from './types';

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
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      init_data: initData,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Authentication failed' }));
    throw new Error(errorData.error || 'Authentication failed');
  }

  return response.json();
}

/**
 * Получить профиль пользователя
 */
export async function getUserProfile(telegramId: number): Promise<UserProfile> {
  const response = await fetch(`${API_BASE_URL}/miniapp/profile/${telegramId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch user profile');
  }

  return response.json();
}

/**
 * Получить прогресс пользователя
 */
export async function getUserProgress(telegramId: number): Promise<ProgressItem[]> {
  const response = await fetch(`${API_BASE_URL}/miniapp/progress/${telegramId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch user progress');
  }

  return response.json();
}

/**
 * Получить достижения пользователя
 */
export async function getUserAchievements(telegramId: number): Promise<Achievement[]> {
  const response = await fetch(`${API_BASE_URL}/miniapp/achievements/${telegramId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch achievements');
  }

  return response.json();
}

/**
 * Получить статистику дашборда
 */
export async function getDashboardStats(telegramId: number): Promise<DashboardStats> {
  const response = await fetch(`${API_BASE_URL}/miniapp/dashboard/${telegramId}`);

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
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update profile');
  }

  return response.json();
}
