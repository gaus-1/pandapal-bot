/**
 * Регистрация Service Worker для PWA
 */

export function registerServiceWorker(): void {
  // Подавляем ошибки Service Worker в Telegram WebView
  if (typeof window !== 'undefined') {
    // Проверяем, что приложение не запущено в Telegram Web App
    // Используем type assertion для Telegram Web App API
    const telegramWebApp = (window as any).Telegram?.WebApp;
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

      console.error = (...args: any[]) => {
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

      console.warn = (...args: any[]) => {
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

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          console.log('✅ Service Worker зарегистрирован:', registration.scope);

          // Обновление Service Worker
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (
                  newWorker.state === 'installed' &&
                  navigator.serviceWorker.controller
                ) {
                  console.log('🔄 Доступно обновление приложения');
                  // Здесь можно показать уведомление пользователю
                }
              });
            }
          });
        })
        .catch((error) => {
          // Подавляем ошибки SW в Telegram WebView (это нормально)
          const errorMessage = error?.message || String(error);
          if (
            !errorMessage.includes('no controller') &&
            !errorMessage.includes('peer changed') &&
            !errorMessage.includes('no windows left') &&
            !errorMessage.includes('it is not a window')
          ) {
            console.warn('⚠️ Service Worker:', errorMessage);
          }
        });
    });
  }
}

/**
 * Проверка онлайн/оффлайн статуса
 */
export function setupOfflineDetection(): void {
  window.addEventListener('online', () => {
    console.log('🌐 Подключение восстановлено');
    // Можно показать уведомление
  });

  window.addEventListener('offline', () => {
    console.log('📡 Подключение потеряно');
    // Можно показать уведомление
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
