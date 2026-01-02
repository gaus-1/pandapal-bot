/**
 * Service Worker для PWA - оффлайн работа PandaPal Mini App
 */

const CACHE_NAME = 'pandapal-v1';
const OFFLINE_URL = '/offline.html';

// Файлы для кэширования
const urlsToCache = [
  '/',
  '/index.html',
  '/assets/index.css',
  '/assets/index.js',
  '/logo.png',
  '/manifest.json',
  OFFLINE_URL,
];

// Установка Service Worker
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('📦 Кэширование файлов');
      return cache.addAll(urlsToCache);
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
  // Игнорируем запросы к API - всегда через сеть
  if (event.request.url.includes('/api/')) {
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

  // Для остальных запросов: Cache First, затем Network
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) {
        return response;
      }

      return fetch(event.request)
        .then((response) => {
          // Кэшируем новые запросы
          if (
            !response ||
            response.status !== 200 ||
            response.type !== 'basic'
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
          // Если нет сети - показываем оффлайн страницу
          return caches.match(OFFLINE_URL);
        });
    })
  );
});

// Background Sync для отложенных запросов (опционально)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  }
});

async function syncMessages() {
  try {
    // Синхронизация отложенных сообщений
    console.log('🔄 Синхронизация сообщений');
  } catch (error) {
    console.error('❌ Ошибка синхронизации:', error);
  }
}
