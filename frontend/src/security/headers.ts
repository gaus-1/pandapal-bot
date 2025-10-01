/**
 * Security Headers конфигурация
 * Защита от OWASP Top 10 уязвимостей
 * @module security/headers
 */

/**
 * Рекомендуемые HTTP-заголовки безопасности для Render
 * Настройки в Render Dashboard → Settings → Headers
 */

/**
 * OWASP A05:2021 - Security Misconfiguration
 * Защита от clickjacking, MIME-sniffing, XSS
 */
export const SECURITY_HEADERS = [
  {
    path: '/*',
    name: 'X-Frame-Options',
    value: 'DENY', // Запрет встраивания сайта в iframe (защита от clickjacking)
  },
  {
    path: '/*',
    name: 'X-Content-Type-Options',
    value: 'nosniff', // Запрет MIME-type sniffing
  },
  {
    path: '/*',
    name: 'X-XSS-Protection',
    value: '1; mode=block', // Включение XSS-фильтра браузера (legacy browsers)
  },
  {
    path: '/*',
    name: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin', // Защита от утечки referrer
  },
  {
    path: '/*',
    name: 'Permissions-Policy',
    value: 'geolocation=(), microphone=(), camera=()', // Запрет доступа к устройствам
  },
  {
    path: '/*',
    name: 'Strict-Transport-Security',
    value: 'max-age=31536000; includeSubDomains; preload', // HSTS (только HTTPS)
  },
  {
    path: '/*',
    name: 'Content-Security-Policy',
    value: `
      default-src 'self';
      script-src 'self' https://www.googletagmanager.com;
      style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
      font-src 'self' https://fonts.gstatic.com;
      img-src 'self' data: https:;
      connect-src 'self' https://api.pandapal.ru;
      frame-ancestors 'none';
      base-uri 'self';
      form-action 'self';
      upgrade-insecure-requests;
    `.replace(/\s+/g, ' ').trim(),
  },
] as const;

/**
 * CORS настройки для API (когда появится backend)
 * OWASP A05:2021 - Security Misconfiguration
 */
export const CORS_CONFIG = {
  // Разрешённые origins
  allowedOrigins: [
    'https://pandapal.ru',
    'https://www.pandapal.ru',
    'https://pandapal-frontend.onrender.com',
  ],
  
  // Разрешённые методы
  allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  
  // Разрешённые заголовки
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-Requested-With',
  ],
  
  // Credentials (cookies, auth headers)
  credentials: true,
  
  // Max age для preflight кэша
  maxAge: 86400, // 24 часа
} as const;

/**
 * Проверка origin для CORS
 * 
 * @param origin - Origin из request headers
 * @returns true если origin разрешён
 */
export const isAllowedOrigin = (origin: string): boolean => {
  return CORS_CONFIG.allowedOrigins.some(allowedOrigin => allowedOrigin === origin);
};
