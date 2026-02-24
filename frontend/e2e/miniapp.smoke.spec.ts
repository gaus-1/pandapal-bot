/**
 * Smoke E2E для CI: лендинг + Mini App с моками API (без реального бэкенда и Yandex).
 */

import { test, expect } from '@playwright/test';

const mockUser = {
  telegram_id: 123456789,
  first_name: 'Test',
  last_name: 'User',
  user_type: 'child',
  is_premium: false,
};

const mockPandaPetState = {
  hunger: 50,
  mood: 50,
  energy: 50,
  last_fed_at: null,
  last_played_at: null,
  last_slept_at: null,
  can_feed: true,
  can_play: true,
  can_sleep: true,
  consecutive_visit_days: 0,
  achievements: {},
};

function setupApiMocks(context: { route: (pattern: string | RegExp, handler: (r: unknown) => Promise<void>) => Promise<void> }) {
  return context.route(/\/api\/miniapp\//, async (route: { request: () => { url: () => string; method: () => string }; fulfill: (opts: { status: number; body: string }) => Promise<void> }) => {
    const url = route.request().url();
    const method = route.request().method();

    if (url.includes('/miniapp/auth') && method === 'POST') {
      return route.fulfill({ status: 200, body: JSON.stringify({ success: true, user: mockUser }) });
    }
    if (url.includes('/miniapp/chat/history/') && method === 'GET') {
      return route.fulfill({ status: 200, body: JSON.stringify({ history: [] }) });
    }
    if (url.includes('/miniapp/chat/greeting/') && method === 'POST') {
      return route.fulfill({ status: 200, body: JSON.stringify({ success: true, message: 'Привет!', role: 'ai' }) });
    }
    if (url.includes('/miniapp/achievements/') && method === 'GET') {
      return route.fulfill({ status: 200, body: JSON.stringify([]) });
    }
    if (url.includes('/miniapp/games/') && method === 'GET' && url.includes('/stats')) {
      return route.fulfill({ status: 200, body: JSON.stringify({}) });
    }
    if (url.includes('/miniapp/games/') && method === 'POST' && url.includes('/create')) {
      return route.fulfill({
        status: 200,
        body: JSON.stringify({ session_id: 1, game_type: 'my_panda', game_state: {} }),
      });
    }
    if (url.includes('/miniapp/panda-pet/') && method === 'GET' && !url.includes('/feed') && !url.includes('/play') && !url.includes('/sleep')) {
      return route.fulfill({ status: 200, body: JSON.stringify(mockPandaPetState) });
    }
    if (url.includes('/miniapp/premium/status/') && method === 'GET') {
      return route.fulfill({ status: 200, body: JSON.stringify({ is_premium: false }) });
    }
    await route.fulfill({ status: 200, body: JSON.stringify({}) });
  });
}

test.describe('Smoke — лендинг и Mini App (моки API)', () => {
  test('лендинг загружается', async ({ page }) => {
    await page.goto('/');
    const h1 = page.locator('h1').first();
    await expect(h1).toBeVisible({ timeout: 10000 });
  });

  test.describe('Mini App', () => {
    test.beforeEach(async ({ page, context }) => {
      await context.addInitScript(() => {
        const mockInitData =
          'query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%2C%22language_code%22%3A%22ru%22%7D&auth_date=1234567890&hash=test_hash';
        (window as Window & { Telegram?: unknown }).Telegram = {
          WebApp: {
            initData: mockInitData,
            initDataUnsafe: {
              user: { id: 123456789, first_name: 'Test', last_name: 'User', username: 'testuser', language_code: 'ru', is_premium: false },
              auth_date: 1234567890,
              hash: 'test_hash',
              start_param: null,
            },
            version: '7.0',
            platform: 'web',
            colorScheme: 'light',
            themeParams: { bg_color: '#ffffff', text_color: '#000000', hint_color: '#999999', link_color: '#0088cc', button_color: '#0088cc', button_text_color: '#ffffff', secondary_bg_color: '#f4f4f4' },
            isExpanded: true,
            viewportHeight: 600,
            viewportStableHeight: 600,
            safeAreaInset: { top: 0, bottom: 0, left: 0, right: 0 },
            headerColor: '#ffffff',
            backgroundColor: '#ffffff',
            isClosingConfirmationEnabled: false,
            isVerticalSwipesEnabled: false,
            onEvent: () => {},
            offEvent: () => {},
            setHeaderColor: () => {},
            setBackgroundColor: () => {},
            ready: () => {},
            expand: () => {},
            close: () => {},
            MainButton: { text: '', color: '#0088cc', textColor: '#ffffff', isVisible: false, isActive: true, isProgressVisible: false, setText: () => {}, show: () => {}, hide: () => {}, enable: () => {}, disable: () => {}, showProgress: () => {}, hideProgress: () => {}, setParams: () => {}, onClick: () => {}, offClick: () => {} },
            BackButton: { isVisible: false, show: () => {}, hide: () => {}, onClick: () => {}, offClick: () => {} },
            HapticFeedback: { impactOccurred: () => {}, notificationOccurred: () => {}, selectionChanged: () => {} },
            showPopup: (_p: unknown, cb?: (id?: string) => void) => { if (cb) cb('ok'); },
            showAlert: (_m: string, cb?: () => void) => { if (cb) cb(); },
            showConfirm: (_m: string, cb?: (ok: boolean) => void) => { if (cb) cb(true); },
            openLink: () => {},
            openTelegramLink: () => {},
            sendData: () => {},
            isVersionAtLeast: () => true,
          },
        };
      });
      await context.setExtraHTTPHeaders({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 Telegram/10.0.0',
      });
      setupApiMocks(context);
      // Локальный режим: /miniapp даёт Mini App без auth (mock user), подходит для CI
      await page.goto(process.env.TEST_LOCAL ? '/miniapp' : '/?tgaddr=test');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
    });

    test('Mini App открывается', async ({ page }) => {
      await expect(page.locator('textarea[placeholder*="Задай вопрос"]')).toBeVisible({ timeout: 15000 });
    });

    test('навигация по экранам', async ({ page }) => {
      await expect(page.locator('textarea[placeholder*="Задай вопрос"]')).toBeVisible({ timeout: 15000 });

      await page.getByRole('button', { name: 'Достижения' }).click();
      await expect(page.getByRole('heading', { name: 'Достижения' })).toBeVisible({ timeout: 5000 });

      await page.getByRole('button', { name: 'Чат' }).click();
      await expect(page.locator('textarea[placeholder*="Задай вопрос"]')).toBeVisible({ timeout: 5000 });

      await page.getByRole('button', { name: 'PandaPalGo' }).click();
      await expect(page.getByRole('button', { name: /Моя панда/ }).first()).toBeVisible({ timeout: 5000 });

      await page.getByRole('button', { name: /Моя панда/ }).first().click();
      await expect(page.getByRole('heading', { name: 'Моя панда' }).or(page.getByRole('button', { name: /Покормить панду/ })).first()).toBeVisible({ timeout: 5000 });

      await page.getByRole('button', { name: 'Чат' }).click();
      await expect(page.locator('textarea[placeholder*="Задай вопрос"]')).toBeVisible({ timeout: 5000 });

      await page.getByRole('button', { name: 'Premium' }).click();
      await expect(page.getByRole('heading', { name: 'PandaPal Premium' }).or(page.locator('text=299')).first()).toBeVisible({ timeout: 5000 });

      await page.getByRole('button', { name: 'Чат' }).click();
      await expect(page.locator('textarea[placeholder*="Задай вопрос"]')).toBeVisible({ timeout: 5000 });
    });
  });
});
