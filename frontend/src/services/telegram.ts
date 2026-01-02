/**
 * Telegram Mini App Service
 * Обертка для работы с Telegram Web App API
 */

import WebApp from '@twa-dev/sdk';

export interface TelegramUser {
  id: number;
  firstName?: string;
  lastName?: string;
  username?: string;
  languageCode?: string;
  isPremium?: boolean;
}

export class TelegramService {
  private webApp = WebApp;

  /**
   * Инициализация Mini App
   */
  init(): void {
    try {
      // Сообщаем Telegram что приложение готово
      this.webApp.ready();

      // Разворачиваем на весь экран
      this.webApp.expand();

      // Адаптируем тему под Telegram
      this.applyTelegramTheme();

      console.log('✅ Telegram Mini App инициализирован');
      console.log('Платформа:', this.webApp.platform);
      console.log('Версия:', this.webApp.version);
    } catch (error) {
      console.error('❌ Ошибка инициализации Telegram Mini App:', error);
    }
  }

  /**
   * Применить тему Telegram к приложению
   */
  private applyTelegramTheme(): void {
    const { themeParams } = this.webApp;

    if (themeParams.bg_color) {
      document.documentElement.style.setProperty('--tg-theme-bg-color', themeParams.bg_color);
    }
    if (themeParams.text_color) {
      document.documentElement.style.setProperty('--tg-theme-text-color', themeParams.text_color);
    }
    if (themeParams.hint_color) {
      document.documentElement.style.setProperty('--tg-theme-hint-color', themeParams.hint_color);
    }
    if (themeParams.link_color) {
      document.documentElement.style.setProperty('--tg-theme-link-color', themeParams.link_color);
    }
    if (themeParams.button_color) {
      document.documentElement.style.setProperty('--tg-theme-button-color', themeParams.button_color);
    }
    if (themeParams.button_text_color) {
      document.documentElement.style.setProperty('--tg-theme-button-text-color', themeParams.button_text_color);
    }
  }

  /**
   * Получить данные пользователя из Telegram
   */
  getUser(): TelegramUser | null {
    const user = this.webApp.initDataUnsafe.user;

    if (!user) {
      return null;
    }

    return {
      id: user.id,
      firstName: user.first_name,
      lastName: user.last_name,
      username: user.username,
      languageCode: user.language_code,
      isPremium: user.is_premium,
    };
  }

  /**
   * Получить initData для аутентификации на backend
   */
  getInitData(): string {
    return this.webApp.initData;
  }

  /**
   * Показать главную кнопку (MainButton)
   */
  showMainButton(text: string, onClick: () => void): void {
    this.webApp.MainButton.setText(text);
    this.webApp.MainButton.onClick(onClick);
    this.webApp.MainButton.show();
  }

  /**
   * Скрыть главную кнопку
   */
  hideMainButton(): void {
    this.webApp.MainButton.hide();
  }

  /**
   * Показать кнопку "Назад"
   */
  showBackButton(onClick: () => void): void {
    this.webApp.BackButton.onClick(onClick);
    this.webApp.BackButton.show();
  }

  /**
   * Скрыть кнопку "Назад"
   */
  hideBackButton(): void {
    this.webApp.BackButton.hide();
  }

  /**
   * Вибрация (haptic feedback)
   */
  hapticFeedback(
    style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' = 'medium'
  ): void {
    this.webApp.HapticFeedback.impactOccurred(style);
  }

  /**
   * Уведомление об успехе (вибрация + звук)
   */
  notifySuccess(): void {
    this.webApp.HapticFeedback.notificationOccurred('success');
  }

  /**
   * Уведомление об ошибке (вибрация + звук)
   */
  notifyError(): void {
    this.webApp.HapticFeedback.notificationOccurred('error');
  }

  /**
   * Предупреждение (вибрация + звук)
   */
  notifyWarning(): void {
    this.webApp.HapticFeedback.notificationOccurred('warning');
  }

  /**
   * Закрыть Mini App
   */
  close(): void {
    this.webApp.close();
  }

  /**
   * Открыть ссылку
   */
  openLink(url: string, options?: { try_instant_view: boolean }): void {
    this.webApp.openLink(url, options);
  }

  /**
   * Открыть Telegram ссылку
   */
  openTelegramLink(url: string): void {
    this.webApp.openTelegramLink(url);
  }

  /**
   * Показать всплывающее сообщение
   */
  showAlert(message: string): Promise<void> {
    return new Promise((resolve) => {
      this.webApp.showAlert(message, () => resolve());
    });
  }

  /**
   * Показать подтверждение
   */
  showConfirm(message: string): Promise<boolean> {
    return new Promise((resolve) => {
      this.webApp.showConfirm(message, (confirmed) => resolve(confirmed));
    });
  }

  /**
   * Показать всплывающее меню
   */
  showPopup(params: {
    title?: string;
    message: string;
    buttons?: Array<{
      id?: string;
      type: 'default' | 'ok' | 'close' | 'cancel' | 'destructive';
      text: string;
    }>;
  }): Promise<string> {
    return new Promise((resolve) => {
      this.webApp.showPopup(params as any, (buttonId) => resolve(buttonId || ''));
    });
  }

  /**
   * Проверка, запущено ли приложение в Telegram
   */
  isInTelegram(): boolean {
    return this.webApp.initData !== '';
  }

  /**
   * Получить платформу
   */
  getPlatform(): string {
    return this.webApp.platform;
  }

  /**
   * Получить цветовую схему
   */
  getColorScheme(): 'light' | 'dark' {
    return this.webApp.colorScheme;
  }

  /**
   * Включить режим full screen
   */
  requestFullscreen(): void {
    if (this.webApp.isFullscreen === false) {
      this.webApp.requestFullscreen();
    }
  }

  /**
   * Выключить режим full screen
   */
  exitFullscreen(): void {
    if (this.webApp.isFullscreen === true) {
      this.webApp.exitFullscreen();
    }
  }

  /**
   * Открыть форму оплаты Telegram (invoice)
   */
  openInvoice(url: string, callback?: (status: string) => void): void {
    this.webApp.openInvoice(url, (status) => {
      if (callback) {
        callback(status);
      }
    });
  }
}

// Singleton экземпляр
export const telegram = new TelegramService();
