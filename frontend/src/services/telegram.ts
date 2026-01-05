/**
 * Telegram Mini App Service
 * Обертка для работы с Telegram Web App API
 */

import WebApp from "@twa-dev/sdk";

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
   * Следует современным стандартам 2026 года для Telegram Mini Apps
   */
  init(): void {
    try {
      // Сообщаем Telegram что приложение готово
      this.webApp.ready();

      // Разворачиваем на весь экран для иммерсивного опыта
      this.webApp.expand();

      // Устанавливаем правильный viewport height для мобильных устройств
      this.setViewportHeight();

      // Адаптируем тему под Telegram (с динамическим обновлением)
      this.applyTelegramTheme();

      // Включаем плавные анимации (60 FPS)
      this.enableSmoothAnimations();

      console.log("✅ Telegram Mini App инициализирован");
      console.log("📱 Платформа:", this.webApp.platform);
      console.log("📦 Версия:", this.webApp.version);
      console.log("🌓 Тема:", this.webApp.colorScheme);
      console.log("🔐 InitData длина:", this.webApp.initData?.length || 0);
      console.log("👤 Пользователь:", this.webApp.initDataUnsafe.user);

      // Проверка доступности initData
      if (!this.webApp.initData) {
        console.warn(
          "⚠️ КРИТИЧНО: initData недоступен! Приложение запущено НЕ через Telegram.",
        );
        console.warn(
          "⚠️ Убедитесь что приложение открывается через кнопку Mini App в Telegram!",
        );
      }
    } catch (error) {
      console.error("❌ Ошибка инициализации Telegram Mini App:", error);
    }
  }

  /**
   * Установить правильный viewport height для мобильных устройств
   * Решает проблему с адресной строкой браузера на iOS/Android
   */
  private setViewportHeight(): void {
    const setVH = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty("--vh", `${vh}px`);
    };

    setVH();
    window.addEventListener("resize", setVH);
    window.addEventListener("orientationchange", setVH);
  }

  /**
   * Включить плавные анимации для 60 FPS
   */
  private enableSmoothAnimations(): void {
    // Используем CSS переменные для плавных переходов
    document.documentElement.style.setProperty(
      "--transition-fast",
      "150ms cubic-bezier(0.4, 0, 0.2, 1)",
    );
    document.documentElement.style.setProperty(
      "--transition-base",
      "200ms cubic-bezier(0.4, 0, 0.2, 1)",
    );
    document.documentElement.style.setProperty(
      "--transition-slow",
      "300ms cubic-bezier(0.4, 0, 0.2, 1)",
    );

    // Включаем hardware acceleration для анимаций
    const style = document.createElement("style");
    style.textContent = `
      * {
        -webkit-transform: translateZ(0);
        transform: translateZ(0);
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Применить тему Telegram к приложению
   * Поддерживает динамическое обновление при смене темы
   */
  private applyTelegramTheme(): void {
    const applyTheme = () => {
      const { themeParams } = this.webApp;

      if (themeParams.bg_color) {
        document.documentElement.style.setProperty(
          "--tg-theme-bg-color",
          themeParams.bg_color,
        );
      }
      if (themeParams.text_color) {
        document.documentElement.style.setProperty(
          "--tg-theme-text-color",
          themeParams.text_color,
        );
      }
      if (themeParams.hint_color) {
        document.documentElement.style.setProperty(
          "--tg-theme-hint-color",
          themeParams.hint_color,
        );
      }
      if (themeParams.link_color) {
        document.documentElement.style.setProperty(
          "--tg-theme-link-color",
          themeParams.link_color,
        );
      }
      if (themeParams.button_color) {
        document.documentElement.style.setProperty(
          "--tg-theme-button-color",
          themeParams.button_color,
        );
      }
      if (themeParams.button_text_color) {
        document.documentElement.style.setProperty(
          "--tg-theme-button-text-color",
          themeParams.button_text_color,
        );
      }

      // Устанавливаем цветовую схему для CSS
      const colorScheme = this.webApp.colorScheme || "light";
      document.documentElement.setAttribute("data-theme", colorScheme);
      if (colorScheme === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    };

    // Применяем тему сразу
    applyTheme();

    // Подписываемся на изменения темы (динамическое обновление)
    this.webApp.onEvent("themeChanged", applyTheme);
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
    style: "light" | "medium" | "heavy" | "rigid" | "soft" = "medium",
  ): void {
    this.webApp.HapticFeedback.impactOccurred(style);
  }

  /**
   * Уведомление об успехе (вибрация + звук)
   */
  notifySuccess(): void {
    this.webApp.HapticFeedback.notificationOccurred("success");
  }

  /**
   * Уведомление об ошибке (вибрация + звук)
   */
  notifyError(): void {
    this.webApp.HapticFeedback.notificationOccurred("error");
  }

  /**
   * Предупреждение (вибрация + звук)
   */
  notifyWarning(): void {
    this.webApp.HapticFeedback.notificationOccurred("warning");
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
      type: "default" | "ok" | "close" | "cancel" | "destructive";
      text: string;
    }>;
  }): Promise<string> {
    return new Promise((resolve) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      this.webApp.showPopup(params as any, (buttonId: string | undefined) =>
        resolve(buttonId || ""),
      );
    });
  }

  /**
   * Проверка, запущено ли приложение в Telegram
   * СТРОГАЯ проверка - только по initData (самый надежный признак)
   */
  isInTelegram(): boolean {
    // СТРОГАЯ проверка: только initData (объект WebApp может существовать и вне Telegram)
    const hasInitData =
      this.webApp.initData !== "" &&
      this.webApp.initData !== undefined &&
      this.webApp.initData !== null;

    // Дополнительная проверка: user agent (для надежности)
    const isTelegramUserAgent =
      typeof window !== "undefined" &&
      (window.navigator.userAgent.includes("Telegram") ||
        window.location.hostname.includes("telegram.org") ||
        window.location.hostname.includes("web.telegram.org"));

    // Только если есть initData ИЛИ точно в Telegram по user agent
    return hasInitData || isTelegramUserAgent;
  }

  /**
   * Получить платформу
   */
  getPlatform(): string {
    return this.webApp.platform || "unknown";
  }

  /**
   * Проверить, запущено ли приложение внутри Telegram
   * Более строгая проверка - только по initData
   */
  isTelegramWebApp(): boolean {
    return this.webApp.initData !== "" && this.webApp.initData !== undefined;
  }

  /**
   * Получить цветовую схему
   */
  getColorScheme(): "light" | "dark" {
    return this.webApp.colorScheme;
  }

  /**
   * Получить start parameter из deep link
   * Используется для deep linking: ?startapp=games
   */
  getStartParam(): string | null {
    return this.webApp.initDataUnsafe?.start_param || null;
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
