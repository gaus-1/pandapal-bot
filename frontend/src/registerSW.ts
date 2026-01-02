/**
 * Регистрация Service Worker для PWA
 */

export function registerServiceWorker(): void {
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
          console.error('❌ Ошибка регистрации Service Worker:', error);
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
