/**
 * Content Security Policy (CSP) конфигурация
 * Защита от OWASP A03:2021 - Injection (XSS, Code Injection)
 * @module security/csp
 */

/**
 * CSP директивы для защиты от XSS и injection-атак
 * Применяется через meta-тег в index.html или HTTP-заголовки Render
 */
export const CSP_DIRECTIVES = {
  // Скрипты только с текущего домена и Google Fonts
  'script-src': ["'self'", 'https://www.googletagmanager.com'],

  // Стили с текущего домена, inline-стили (для Tailwind), Google Fonts
  'style-src': ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],

  // Изображения с текущего домена и data: URIs
  'img-src': ["'self'", 'data:', 'https:'],

  // Шрифты с текущего домена и Google Fonts
  'font-src': ["'self'", 'https://fonts.gstatic.com'],

  // Подключения только к API (когда появится backend)
  'connect-src': ["'self'", 'https://api.pandapal.ru'],

  // Фреймы запрещены (защита от clickjacking)
  'frame-ancestors': ["'none'"],

  // Базовый URI — только текущий домен
  'base-uri': ["'self'"],

  // Формы отправляются только на текущий домен
  'form-action': ["'self'"],

  // Upgrade insecure requests (HTTP → HTTPS)
  'upgrade-insecure-requests': [],
} as const;

/**
 * Генерирует CSP строку для meta-тега
 * @returns Строка Content-Security-Policy
 */
export const generateCSPString = (): string => {
  return Object.entries(CSP_DIRECTIVES)
    .map(([directive, values]) => {
      if (values.length === 0) return directive;
      return `${directive} ${values.join(' ')}`;
    })
    .join('; ');
};

/**
 * CSP для Render.com (через Headers настройки)
 * Копировать в Render Dashboard → Settings → Headers
 */
export const RENDER_CSP_HEADER = {
  path: '/*',
  name: 'Content-Security-Policy',
  value: generateCSPString(),
};
