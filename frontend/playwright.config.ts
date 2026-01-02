import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Configuration for PandaPal Mini App
 * Критические тесты для проверки реальной работы с Yandex API
 */
export default defineConfig({
  testDir: './e2e',

  // Timeout для тестов с реальными API
  timeout: 60000, // 60 секунд (Yandex API может быть медленным)

  fullyParallel: false, // Последовательно, чтобы не перегружать API

  // Retry только в CI (локально не надо)
  retries: process.env.CI ? 2 : 0,

  // Репортеры
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
  ],

  use: {
    // Base URL - production
    baseURL: 'https://pandapal.ru',

    // Скриншоты при ошибках
    screenshot: 'only-on-failure',

    // Видео при ошибках
    video: 'retain-on-failure',

    // Trace для отладки
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
    },
    {
      name: 'mobile',
      use: {
        ...devices['iPhone 13 Pro'],
        // Эмулируем реальное мобильное устройство
        isMobile: true,
        hasTouch: true,
      },
    },
  ],

  // Веб-сервер для локального тестирования (опционально)
  webServer: process.env.TEST_LOCAL ? {
    command: 'npm run preview',
    port: 4173,
    reuseExistingServer: !process.env.CI,
  } : undefined,
});
