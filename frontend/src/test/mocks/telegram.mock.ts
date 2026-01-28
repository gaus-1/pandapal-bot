/**
 * Professional Telegram SDK Mock
 * Полноценная эмуляция Telegram Web App API для тестирования
 */

import { vi } from 'vitest';

/**
 * Создаёт реалистичный initData для тестов
 */
export function createMockInitData(userId: number = 123456789): string {
  const user = {
    id: userId,
    first_name: 'Test',
    last_name: 'User',
    username: 'testuser',
    language_code: 'ru',
    is_premium: false,
  };

  // Реалистичный query string как от Telegram
  const params = new URLSearchParams({
    user: JSON.stringify(user),
    auth_date: Math.floor(Date.now() / 1000).toString(),
    hash: 'mock_hash_for_testing',
  });

  return params.toString();
}

/**
 * Mock Telegram WebApp API
 */
export const createTelegramMock = (options: {
  initData?: string;
  userId?: number;
  platform?: string;
  version?: string;
} = {}) => {
  const initData = options.initData || createMockInitData(options.userId);

  const user = {
    id: options.userId || 123456789,
    first_name: 'Test',
    last_name: 'User',
    username: 'testuser',
    language_code: 'ru',
    is_premium: false,
  };

  const mockWebApp = {
    // Данные
    initData,
    initDataUnsafe: {
      user,
      auth_date: Math.floor(Date.now() / 1000),
      hash: 'mock_hash_for_testing',
    },
    version: options.version || '7.0',
    platform: options.platform || 'web',
    colorScheme: 'light' as const,
    themeParams: {
      bg_color: '#ffffff',
      text_color: '#000000',
      hint_color: '#999999',
      link_color: '#0088cc',
      button_color: '#0088cc',
      button_text_color: '#ffffff',
      secondary_bg_color: '#f4f4f4',
    },
    isExpanded: true,
    viewportHeight: 600,
    viewportStableHeight: 600,
    headerColor: '#ffffff',
    backgroundColor: '#ffffff',
    isClosingConfirmationEnabled: false,
    isVerticalSwipesEnabled: false,

    // Методы жизненного цикла
    ready: vi.fn(),
    expand: vi.fn(),
    close: vi.fn(),

    // BackButton
    BackButton: {
      isVisible: false,
      show: vi.fn(function(this: { isVisible: boolean }) { this.isVisible = true; }),
      hide: vi.fn(function(this: { isVisible: boolean }) { this.isVisible = false; }),
      onClick: vi.fn(),
      offClick: vi.fn(),
    },

    // MainButton
    MainButton: {
      text: '',
      color: '#0088cc',
      textColor: '#ffffff',
      isVisible: false,
      isActive: true,
      isProgressVisible: false,
      setText: vi.fn(),
      show: vi.fn(),
      hide: vi.fn(),
      enable: vi.fn(),
      disable: vi.fn(),
      showProgress: vi.fn(),
      hideProgress: vi.fn(),
      setParams: vi.fn(),
      onClick: vi.fn(),
      offClick: vi.fn(),
    },

    // HapticFeedback
    HapticFeedback: {
      impactOccurred: vi.fn(),
      notificationOccurred: vi.fn(),
      selectionChanged: vi.fn(),
    },

    // CloudStorage
    CloudStorage: {
      setItem: vi.fn((_key, _value, callback) => callback?.(null, true)),
      getItem: vi.fn((_key, callback) => callback?.(null, '')),
      getItems: vi.fn((_keys, callback) => callback?.(null, {})),
      removeItem: vi.fn((_key, callback) => callback?.(null, true)),
      removeItems: vi.fn((_keys, callback) => callback?.(null, true)),
      getKeys: vi.fn((callback) => callback?.(null, [])),
    },

    // Popup
    showPopup: vi.fn((_params, callback) => {
      callback?.('ok');
      return Promise.resolve('ok');
    }),

    showAlert: vi.fn((_message, callback) => {
      callback?.();
      return Promise.resolve();
    }),

    showConfirm: vi.fn((_message, callback) => {
      callback?.(true);
      return Promise.resolve(true);
    }),

    showScanQrPopup: vi.fn(),
    closeScanQrPopup: vi.fn(),

    // Links
    openLink: vi.fn(),
    openTelegramLink: vi.fn(),

    // Invoice
    openInvoice: vi.fn((_url, callback) => {
      callback?.('paid');
      return Promise.resolve('paid');
    }),

    // Другие методы
    sendData: vi.fn(),
    switchInlineQuery: vi.fn(),
    requestWriteAccess: vi.fn((callback) => {
      callback?.(true);
      return Promise.resolve(true);
    }),
    requestContact: vi.fn((callback) => {
      callback?.(true);
      return Promise.resolve(true);
    }),

    // Events
    onEvent: vi.fn(),
    offEvent: vi.fn(),

    // Settings button
    SettingsButton: {
      isVisible: false,
      show: vi.fn(),
      hide: vi.fn(),
      onClick: vi.fn(),
      offClick: vi.fn(),
    },

    // Для проверки доступности
    isVersionAtLeast: vi.fn(() => true),
  };

  return mockWebApp;
};

/**
 * Mock для TelegramService
 */
export const createTelegramServiceMock = (webApp = createTelegramMock()) => ({
  init: vi.fn(),
  expand: vi.fn(),
  ready: vi.fn(),
  getInitData: vi.fn(() => webApp.initData),
  getUser: vi.fn(() => webApp.initDataUnsafe.user),
  getPlatform: vi.fn(() => webApp.platform),
  isTelegramWebApp: vi.fn(() => true),
  isInTelegram: vi.fn(() => true),
  showBackButton: vi.fn((callback?: () => void) => {
    webApp.BackButton.show();
    if (callback) {
      webApp.BackButton.onClick(callback);
    }
  }),
  hideBackButton: vi.fn(() => {
    webApp.BackButton.hide();
  }),
  hapticFeedback: vi.fn((style: string) => {
    if (style === 'light' || style === 'medium' || style === 'heavy') {
      webApp.HapticFeedback.impactOccurred(style);
    }
  }),
  notifySuccess: vi.fn(() => {
    webApp.HapticFeedback.notificationOccurred('success');
  }),
  notifyError: vi.fn(() => {
    webApp.HapticFeedback.notificationOccurred('error');
  }),
  showAlert: vi.fn((message: string) => webApp.showAlert(message, () => {})),
  showConfirm: vi.fn((message: string) => webApp.showConfirm(message, () => {})),
  close: vi.fn(() => webApp.close()),
  openLink: vi.fn((_url: string) => webApp.openLink(_url)),
  openInvoice: vi.fn((_url: string, callback?: (status: string) => void) =>
    webApp.openInvoice(_url, callback)
  ),
});
