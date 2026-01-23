/**
 * API для премиум подписки.
 */

import { telegram } from '../telegram';
import { API_BASE_URL } from './config';

/**
 * Получить заголовки с авторизацией для защищенных запросов.
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

export async function createPremiumPayment(
  telegramId: number,
  planId: 'month' | 'year',
  userEmail?: string,
  userPhone?: string
): Promise<{
  success: boolean;
  payment_id: string;
  confirmation_url: string;
  amount: { value: number; currency: string };
}> {
  const response = await fetch(`${API_BASE_URL}/miniapp/premium/create-payment`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      telegram_id: telegramId,
      plan_id: planId,
      ...(userEmail && { user_email: userEmail }),
      ...(userPhone && { user_phone: userPhone }),
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(errorData.error || 'Ошибка создания платежа');
  }

  return await response.json();
}

/**
 * Получить статус Premium подписки
 */
export async function getPremiumStatus(telegramId: number): Promise<{
  success: boolean;
  is_premium: boolean;
  active_subscription: {
    id: number;
    plan_id: string;
    starts_at: string;
    expires_at: string;
    is_active: boolean;
    payment_method?: string;
    auto_renew?: boolean;
    has_saved_payment_method?: boolean;
  } | null;
}> {
  const response = await fetch(`${API_BASE_URL}/miniapp/premium/status/${telegramId}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error('Ошибка получения статуса Premium');
  }

  return await response.json();
}

/**
 * Удалить сохраненный способ оплаты (отвязать карту)
 */
export async function removeSavedPaymentMethod(telegramId: number): Promise<{
  success: boolean;
  message: string;
}> {
  const response = await fetch(`${API_BASE_URL}/miniapp/premium/remove-payment-method`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      telegram_id: telegramId,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(errorData.error || 'Ошибка отвязки карты');
  }

  return await response.json();
}
