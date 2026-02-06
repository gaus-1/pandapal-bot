/**
 * API питомца-панды (тамагочи).
 */

import { telegram } from '../telegram';
import { API_BASE_URL } from './config';

function getAuthHeaders(): HeadersInit {
  const initData = telegram.getInitData();
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  if (initData) headers['X-Telegram-Init-Data'] = initData;
  return headers;
}

export interface PandaState {
  hunger: number;
  mood: number;
  energy: number;
  display_state: string;
  achievements: Array<{ id: string; title: string }>;
  can_feed: boolean;
  can_play: boolean;
  sleep_need_feed_first: boolean;
  total_fed_count: number;
  total_played_count: number;
  consecutive_visit_days: number;
}

export async function getPandaState(telegramId: number): Promise<PandaState> {
  const response = await fetch(`${API_BASE_URL}/miniapp/panda/${telegramId}/state`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: 'Ошибка загрузки панды' }));
    throw new Error(err.error || 'Ошибка загрузки панды');
  }
  const data = await response.json();
  return data.state;
}

export async function pandaFeed(telegramId: number): Promise<{
  success: boolean;
  message: string;
  state: PandaState;
}> {
  const response = await fetch(`${API_BASE_URL}/miniapp/panda/${telegramId}/feed`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: 'Ошибка' }));
    throw new Error(err.error || 'Ошибка кормления');
  }
  return response.json();
}

export async function pandaPlay(telegramId: number): Promise<{
  success: boolean;
  message: string;
  state: PandaState;
}> {
  const response = await fetch(`${API_BASE_URL}/miniapp/panda/${telegramId}/play`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: 'Ошибка' }));
    throw new Error(err.error || 'Ошибка игры');
  }
  return response.json();
}

export async function pandaSleep(telegramId: number): Promise<{
  success: boolean;
  message: string;
  need_feed_first?: boolean;
  state: PandaState;
}> {
  const response = await fetch(`${API_BASE_URL}/miniapp/panda/${telegramId}/sleep`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: 'Ошибка' }));
    throw new Error(err.error || 'Ошибка');
  }
  return response.json();
}
