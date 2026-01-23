/**
 * API для чата с AI.
 */

import { API_BASE_URL } from './config';
import type { AchievementUnlocked } from './types';

export async function sendAIMessage(
  telegramId: number,
  message?: string,
  photoBase64?: string,
  audioBase64?: string
): Promise<{ response: string; achievements_unlocked?: AchievementUnlocked[] }> {
  const requestBody = {
    telegram_id: telegramId,
    // Отправляем message только если он есть (не пустая строка)
    ...(message && message.trim() ? { message } : {}),
    ...(photoBase64 ? { photo_base64: photoBase64 } : {}),
    ...(audioBase64 ? { audio_base64: audioBase64 } : {}),
  };

  console.log('📤 sendAIMessage вызван:', {
    telegramId,
    hasMessage: !!message,
    hasPhoto: !!photoBase64,
    hasAudio: !!audioBase64,
    audioLength: audioBase64?.length || 0,
  });

  const response = await fetch(`${API_BASE_URL}/miniapp/ai/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    const error = new Error(errorData.error || 'Ошибка отправки сообщения') as Error & {
      data?: unknown;
      response?: { data?: unknown; status?: number };
    };
    error.data = errorData;
    error.response = { data: errorData, status: response.status };
    throw error;
  }

  return await response.json();
}

/**
 * Получить историю чата
 */
export async function getChatHistory(
  telegramId: number,
  limit: number = 50
): Promise<Array<{ role: 'user' | 'ai'; content: string; timestamp: string; imageUrl?: string }>> {
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
/**
 * Добавить приветственное сообщение от бота в историю чата
 */
export async function addGreetingMessage(telegramId: number, message?: string): Promise<{ success: boolean; message: string; role: string }> {
  const response = await fetch(`${API_BASE_URL}/miniapp/chat/greeting/${telegramId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(message ? { message } : {}),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(errorData.error || 'Ошибка добавления приветствия');
  }

  return await response.json();
}

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
