/**
 * Input Sanitization утилиты
 * Защита от OWASP A03:2021 - Injection
 * @module security/sanitize
 */

/**
 * Очистка строки от потенциально опасных символов
 * Защита от XSS при отображении пользовательских данных
 *
 * @param input - Входная строка от пользователя
 * @returns Очищенная безопасная строка
 *
 * @example
 * const safe = sanitizeInput('<script>alert("XSS")</script>');
 * // Результат: '&lt;script&gt;alert("XSS")&lt;/script&gt;'
 */
export const sanitizeInput = (input: string): string => {
  if (!input) return '';

  // Экранируем опасные HTML-символы
  const htmlEntities: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
  };

  return input.replace(/[&<>"'/]/g, (char) => htmlEntities[char] || char);
};

/**
 * Валидация email адреса
 *
 * @param email - Email для проверки
 * @returns true если email валиден
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email) && email.length <= 254;
};

/**
 * Валидация URL
 * Защита от Open Redirect (OWASP A01:2021)
 *
 * @param url - URL для проверки
 * @param allowedDomains - Разрешённые домены
 * @returns true если URL безопасен
 */
export const isValidURL = (
  url: string,
  allowedDomains: string[] = ['pandapal.ru', 't.me']
): boolean => {
  try {
    const parsedUrl = new URL(url);

    // Проверяем протокол (только https)
    if (parsedUrl.protocol !== 'https:') return false;

    // Проверяем домен
    const hostname = parsedUrl.hostname;
    return allowedDomains.some((domain) =>
      hostname === domain || hostname.endsWith(`.${domain}`)
    );
  } catch {
    return false;
  }
};

/**
 * Защита от SQL Injection в query параметрах
 *
 * @param value - Значение параметра
 * @returns Очищенное значение
 */
export const sanitizeQueryParam = (value: string): string => {
  // Удаляем все символы кроме букв, цифр и подчёркивания (дефис тоже опасен для SQL)
  return value.replace(/[^a-zA-Zа-яА-ЯёЁ0-9_]/g, '');
};

/**
 * Проверка на SQL Injection паттерны
 *
 * @param input - Строка для проверки
 * @returns true если обнаружены опасные паттерны
 */
export const detectSQLInjection = (input: string): boolean => {
  const sqlPatterns = [
    /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|TABLE)\b)/i,
    /(--|;|\/\*|\*\/|'|"|`)/,
    /(\bOR\b|\bAND\b).*=.*=/i,
    /(\b(OR|AND)\b\s+['"]?\d+['"]?\s*=\s*['"]?\d+)/i,
  ];

  return sqlPatterns.some((pattern) => pattern.test(input));
};

/**
 * Rate limiting для клиентской стороны
 * Защита от OWASP A04:2021 - Insecure Design (brute force)
 */
export class RateLimiter {
  private attempts: Map<string, number[]> = new Map();

  /**
   * Проверяет, не превышен ли лимит запросов
   *
   * @param key - Ключ (например, IP или user ID)
   * @param maxAttempts - Максимум попыток
   * @param windowMs - Временное окно в миллисекундах
   * @returns true если лимит не превышен
   */
  public checkLimit(
    key: string,
    maxAttempts: number = 5,
    windowMs: number = 60000
  ): boolean {
    const now = Date.now();
    const userAttempts = this.attempts.get(key) || [];

    // Фильтруем только попытки в текущем временном окне
    const recentAttempts = userAttempts.filter(
      (timestamp) => now - timestamp < windowMs
    );

    if (recentAttempts.length >= maxAttempts) {
      return false; // Лимит превышен
    }

    // Добавляем новую попытку
    recentAttempts.push(now);
    this.attempts.set(key, recentAttempts);

    return true; // Лимит не превышен
  }

  /**
   * Очистка истории попыток
   */
  public clear(key: string): void {
    this.attempts.delete(key);
  }
}
