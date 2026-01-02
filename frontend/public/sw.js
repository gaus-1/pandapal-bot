/**
 * Service Worker для PWA - оффлайн работа PandaPal Mini App
 */

const CACHE_NAME = 'pandapal-v1';
const OFFLINE_URL = '/offline.html';

// Установка Service Worker - НЕ кэшируем конкретные файлы сразу
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('📦 Service Worker установлен');
      // Кэшируем только оффлайн страницу
      return cache.add(OFFLINE_URL).catch(err => {
        console.warn('Не удалось закэшировать offline.html:', err);
      });
    })
  );
  self.skipWaiting();
});

// Активация Service Worker
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Удаление старого кэша:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Обработка запросов
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Игнорируем chrome-extension, telegram.org и другие внешние протоколы
  if (
    url.protocol === 'chrome-extension:' ||
    url.protocol === 'moz-extension:' ||
    url.hostname.includes('telegram.org') ||
    url.hostname.includes('t.me')
  ) {
    return;
  }

  // Игнорируем запросы к API - всегда через сеть
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(
          JSON.stringify({ error: 'Offline mode', offline: true }),
          {
            headers: { 'Content-Type': 'application/json' },
            status: 503,
          }
        );
      })
    );
    return;
  }

  // Игнорируем запросы к метрике и внешним ресурсам
  if (
    url.hostname.includes('yandex.ru') ||
    url.hostname.includes('googleapis.com') ||
    url.hostname.includes('gstatic.com')
  ) {
    return;
  }

  // Network First для HTML файлов (всегда свежие)
  if (event.request.destination === 'document') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Кэшируем успешный ответ
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
          return response;
        })
        .catch(() => {
          // Если нет сети - пробуем из кэша, иначе оффлайн страница
          return caches.match(event.request).then((cachedResponse) => {
            return cachedResponse || caches.match(OFFLINE_URL);
          });
        })
    );
    return;
  }

  // Cache First для остальных ресурсов (JS, CSS, изображения)
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) {
        return response;
      }

      return fetch(event.request)
        .then((response) => {
          // Кэшируем только успешные запросы
          if (
            !response ||
            response.status !== 200 ||
            response.type === 'error'
          ) {
            return response;
          }

          const responseToCache = response.clone();

          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });

          return response;
        })
        .catch(() => {
          // Для изображений можно вернуть fallback
          if (event.request.destination === 'image') {
            return caches.match('/logo.png');
          }
          return new Response('Offline', { status: 503 });
        });
    })
  );
});
