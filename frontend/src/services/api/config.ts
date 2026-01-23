/**
 * Конфигурация API.
 */

export const API_BASE_URL = import.meta.env.PROD
  ? 'https://pandapal.ru/api'
  : 'http://localhost:10000/api';

/**
 * Отправить лог на сервер для отладки
 */
export async function sendLogToServer(
  level: 'log' | 'error' | 'warn' | 'info',
  message: string,
  data?: Record<string, unknown>,
  telegramId?: number
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/miniapp/log`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        level,
        message,
        data,
        telegram_id: telegramId,
        user_agent: navigator.userAgent,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
      console.debug('Лог не отправлен на сервер:', errorData);
    }
  } catch (error) {
    console.debug('Не удалось отправить лог на сервер:', error);
  }
}
