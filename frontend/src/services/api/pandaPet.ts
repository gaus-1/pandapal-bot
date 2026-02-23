/**
 * API для «Моя панда» (тамагочи).
 */

import { telegram } from '../telegram';
import { API_BASE_URL } from './config';

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

export interface PandaPetState {
  hunger: number;
  mood: number;
  energy: number;
  last_fed_at: string | null;
  last_played_at: string | null;
  last_slept_at: string | null;
  /** Есть после деплоя бэкенда с toilet; для совместимости со старым API — опционально */
  last_toilet_at?: string | null;
  can_feed: boolean;
  can_play: boolean;
  can_sleep: boolean;
  /** Есть после деплоя бэкенда с toilet; для совместимости — опционально */
  can_toilet?: boolean;
  consecutive_visit_days: number;
  achievements: Record<string, unknown>;
}

export async function getPandaPetState(telegramId: number): Promise<PandaPetState> {
  const response = await fetch(`${API_BASE_URL}/miniapp/panda-pet/${telegramId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(data.error || 'Ошибка загрузки состояния панды');
  }
  return response.json();
}

export async function feedPandaPet(telegramId: number): Promise<PandaPetState> {
  const response = await fetch(`${API_BASE_URL}/miniapp/panda-pet/${telegramId}/feed`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(data.error || 'Не удалось покормить');
  }
  return response.json();
}

export async function playPandaPet(telegramId: number): Promise<PandaPetState> {
  const response = await fetch(`${API_BASE_URL}/miniapp/panda-pet/${telegramId}/play`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(data.error || 'Не удалось поиграть');
  }
  return response.json();
}

export async function sleepPandaPet(telegramId: number): Promise<PandaPetState> {
  const response = await fetch(`${API_BASE_URL}/miniapp/panda-pet/${telegramId}/sleep`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(data.error || 'Не удалось уложить спать');
  }
  return response.json();
}

export async function fallFromTreePandaPet(telegramId: number): Promise<PandaPetState> {
  const response = await fetch(
    `${API_BASE_URL}/miniapp/panda-pet/${telegramId}/fall-from-tree`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({}),
    }
  );
  if (!response.ok) {
    const data = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(data.error || 'Не удалось выполнить действие');
  }
  return response.json();
}

export async function toiletPandaPet(telegramId: number): Promise<PandaPetState> {
  const response = await fetch(`${API_BASE_URL}/miniapp/panda-pet/${telegramId}/toilet`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(data.error || 'Действие доступно раз в 20 минут');
  }
  return response.json();
}
