/**
 * Регистрация Service Worker для PWA
 */

export function registerServiceWorker(): void {
  // Подавляем ошибки Service Worker в Telegram WebView
  if (typeof window !== 'undefined') {
    // Проверяем, что приложение не запущено в Telegram Web App
    // Используем type assertion для Telegram Web App API
    const telegramWebApp = (window as Window & { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
    const isTelegramWebApp =
      telegramWebApp?.initData ||
      window.location.hostname.includes('telegram.org') ||
      window.location.hostname.includes('web.telegram.org') ||
      window.navigator.userAgent.includes('Telegram');

    if (isTelegramWebApp) {
      // Полностью отключаем SW в Telegram WebView
      // Подавляем все ошибки SW в консоли
      const originalError = console.error;
      const originalWarn = console.warn;

      console.error = (...args: unknown[]) => {
        const message = args.join(' ');
        // Подавляем ошибки SW и Telegram WebView
        if (
          message.includes('[SW]') ||
          message.includes('Service Worker') ||
          message.includes('no controller') ||
          message.includes('no windows left') ||
          message.includes('it is not a window') ||
          message.includes('SW registration failed') ||
          message.includes('device-orientation') ||
          message.includes('MP-MTPROTO')
        ) {
          return; // Подавляем эти ошибки
        }
        originalError.apply(console, args);
      };

      console.warn = (...args: unknown[]) => {
        const message = args.join(' ');
        // Подавляем предупреждения SW и Telegram WebView
        if (
          message.includes('[SW]') ||
          message.includes('Service Worker') ||
          message.includes('device-orientation') ||
          message.includes('Unrecognized feature')
        ) {
          return; // Подавляем эти предупреждения
        }
        originalWarn.apply(console, args);
      };

      // Отключаем SW полностью
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then((registrations) => {
          registrations.forEach((registration) => {
            registration.unregister().catch(() => {
              // Игнорируем ошибки при отмене регистрации
            });
          });
        });
      }

      return; // Не регистрируем SW в Telegram WebView
    }
  }

  // Отключаем Service Worker для обычного браузера (не в Telegram)
  // Это предотвращает показ кнопки "Установить" в браузере
  // PWA функциональность не нужна - сайт должен работать только в Telegram Mini App
  if ('serviceWorker' in navigator) {
    // Отменяем регистрацию всех существующих Service Workers
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      registrations.forEach((registration) => {
        registration.unregister().catch(() => {
          // Игнорируем ошибки при отмене регистрации
        });
      });
    });
    return; // Не регистрируем новый Service Worker
  }
}

/**
 * Проверка онлайн/оффлайн статуса
 */
export function setupOfflineDetection(): void {
  window.addEventListener('online', () => {
    // Подключение восстановлено
  });

  window.addEventListener('offline', () => {
    // Подключение потеряно
  });
}

/**
 * Запрос разрешения на уведомления (опционально)
 */
export async function requestNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) {
    return false;
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }

  return false;
}
