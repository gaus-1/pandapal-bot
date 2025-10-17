/**
 * Валидация входных данных
 * Защита от OWASP A03:2021 - Injection и A04:2021 - Insecure Design
 * @module security/validation
 */

/**
 * Максимальная длина различных полей (защита от DoS)
 */
export const MAX_LENGTHS = {
  USERNAME: 50,
  EMAIL: 254,
  MESSAGE: 2000,
  NAME: 100,
} as const;

/**
 * Регулярные выражения для валидации
 */
const PATTERNS = {
  // Только буквы, цифры, дефис, подчёркивание
  ALPHANUMERIC: /^[a-zA-Zа-яА-ЯёЁ0-9_-]+$/,

  // Email (RFC 5322 упрощённый)
  EMAIL: /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,

  // Telegram username (@username)
  TELEGRAM: /^@?[a-zA-Z0-9_]{5,32}$/,

  // Телефон (международный формат)
  PHONE: /^\+?[1-9]\d{1,14}$/,
} as const;

/**
 * Результат валидации
 */
export interface ValidationResult {
  valid: boolean;
  error?: string;
}

/**
 * Валидация username (для форм регистрации, если будут)
 *
 * @param username - Имя пользователя
 * @returns Результат валидации
 */
export const validateUsername = (username: string): ValidationResult => {
  // Проверка длины
  if (!username || username.length === 0) {
    return { valid: false, error: 'Имя пользователя обязательно' };
  }

  if (username.length < 3) {
    return { valid: false, error: 'Минимум 3 символа' };
  }

  if (username.length > MAX_LENGTHS.USERNAME) {
    return { valid: false, error: `Максимум ${MAX_LENGTHS.USERNAME} символов` };
  }

  // Проверка формата
  if (!PATTERNS.ALPHANUMERIC.test(username)) {
    return { valid: false, error: 'Только буквы, цифры, дефис и подчёркивание' };
  }

  return { valid: true };
};

/**
 * Валидация email
 *
 * @param email - Email адрес
 * @returns Результат валидации
 */
export const validateEmail = (email: string): ValidationResult => {
  if (!email || email.length === 0) {
    return { valid: false, error: 'Email обязателен' };
  }

  if (email.length > MAX_LENGTHS.EMAIL) {
    return { valid: false, error: 'Email слишком длинный' };
  }

  if (!PATTERNS.EMAIL.test(email)) {
    return { valid: false, error: 'Некорректный формат email' };
  }

  return { valid: true };
};

/**
 * Валидация текстового сообщения
 * Защита от XSS и DoS
 *
 * @param message - Текст сообщения
 * @param maxLength - Максимальная длина
 * @returns Результат валидации
 */
export const validateMessage = (
  message: string,
  maxLength: number = MAX_LENGTHS.MESSAGE
): ValidationResult => {
  if (!message || message.trim().length === 0) {
    return { valid: false, error: 'Сообщение не может быть пустым' };
  }

  if (message.length > maxLength) {
    return { valid: false, error: `Максимум ${maxLength} символов` };
  }

  // Проверка на подозрительные паттерны (script tags, etc)
  const dangerousPatterns = [
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
    /<iframe/gi,
    /javascript:/gi,
    /on\w+\s*=/gi, // onclick=, onerror=, etc
  ];

  const hasDangerousContent = dangerousPatterns.some((pattern) =>
    pattern.test(message)
  );

  if (hasDangerousContent) {
    return { valid: false, error: 'Обнаружен потенциально опасный контент' };
  }

  return { valid: true };
};

/**
 * Валидация возраста ребёнка
 *
 * @param age - Возраст
 * @returns Результат валидации
 */
export const validateAge = (age: number): ValidationResult => {
  if (!Number.isInteger(age)) {
    return { valid: false, error: 'Возраст должен быть целым числом' };
  }

  if (age < 6 || age > 18) {
    return { valid: false, error: 'Возраст должен быть от 6 до 18 лет' };
  }

  return { valid: true };
};

/**
 * Валидация класса (1-11)
 *
 * @param grade - Класс
 * @returns Результат валидации
 */
export const validateGrade = (grade: number): ValidationResult => {
  if (!Number.isInteger(grade)) {
    return { valid: false, error: 'Класс должен быть целым числом' };
  }

  if (grade < 1 || grade > 11) {
    return { valid: false, error: 'Класс должен быть от 1 до 11' };
  }

  return { valid: true };
};
