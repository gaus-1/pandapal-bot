/**
 * Telegram Mini App Service
 * Обертка для работы с Telegram Web App API
 */

import WebApp from "@twa-dev/sdk";
import { logger } from "../utils/logger";

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

      // Safe area для полноэкранного режима (Bot API 8.0+)
      this.applySafeAreaInsets();
      if (typeof this.webApp.onEvent === "function") {
        this.webApp.onEvent("safeAreaChanged", () => this.applySafeAreaInsets());
      }

      // Включаем плавные анимации (60 FPS)
      this.enableSmoothAnimations();

      logger.debug("Telegram Mini App init:", this.webApp.platform, this.webApp.version);

      // Проверка доступности initData (только если точно в Telegram)
      const isTelegramUA = typeof window !== 'undefined' &&
        (window.navigator.userAgent.includes('Telegram') ||
         window.location.hostname.includes('telegram.org') ||
         window.location.hostname.includes('web.telegram.org'));

      if (!this.webApp.initData && isTelegramUA) {
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
   * Решает проблему с адресной строкой браузера на iOS/Android.
   * Дополнительно выставляет --tg-viewport-* из API для привязки к низу экрана.
   */
  private setViewportHeight(): void {
    const setVH = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty("--vh", `${vh}px`);
    };

    const setTgViewport = () => {
      const vh = (this.webApp as { viewportHeight?: number }).viewportHeight;
      const stable = (this.webApp as { viewportStableHeight?: number }).viewportStableHeight;
      if (typeof vh === "number") {
        document.documentElement.style.setProperty("--tg-viewport-height", `${vh}px`);
      }
      if (typeof stable === "number") {
        document.documentElement.style.setProperty("--tg-viewport-stable-height", `${stable}px`);
      }
    };

    setVH();
    setTgViewport();
    window.addEventListener("resize", setVH);
    window.addEventListener("orientationchange", setVH);

    if (typeof this.webApp.onEvent === "function") {
      this.webApp.onEvent("viewportChanged", (e: { isStateStable?: boolean }) => {
        if (e?.isStateStable) setTgViewport();
      });
    }
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
   * Применить тему Telegram к приложению (только CSS-переменные и data-theme).
   * Подписка на themeChanged для обновления переменных при смене темы в Telegram.
   * Класс .dark по-прежнему управляется только MiniAppThemeToggle.
   */
  private applyTelegramTheme(): void {
    const applyTheme = () => {
      const themeParams = this.webApp.themeParams ?? {};
      if (themeParams.bg_color) {
        document.documentElement.style.setProperty("--tg-theme-bg-color", themeParams.bg_color);
      }
      if (themeParams.text_color) {
        document.documentElement.style.setProperty("--tg-theme-text-color", themeParams.text_color);
      }
      if (themeParams.hint_color) {
        document.documentElement.style.setProperty("--tg-theme-hint-color", themeParams.hint_color);
      }
      if (themeParams.link_color) {
        document.documentElement.style.setProperty("--tg-theme-link-color", themeParams.link_color);
      }
      if (themeParams.button_color) {
        document.documentElement.style.setProperty("--tg-theme-button-color", themeParams.button_color);
      }
      if (themeParams.button_text_color) {
        document.documentElement.style.setProperty("--tg-theme-button-text-color", themeParams.button_text_color);
      }
      const optional = themeParams as unknown as Record<string, string | undefined>;
      if (optional.secondary_bg_color) {
        document.documentElement.style.setProperty("--tg-theme-secondary-bg-color", optional.secondary_bg_color);
      }
      if (optional.header_bg_color) {
        document.documentElement.style.setProperty("--tg-theme-header-bg-color", optional.header_bg_color);
      }
      if (optional.bottom_bar_bg_color) {
        document.documentElement.style.setProperty("--tg-theme-bottom-bar-bg-color", optional.bottom_bar_bg_color);
      }
      if (optional.accent_text_color) {
        document.documentElement.style.setProperty("--tg-theme-accent-text-color", optional.accent_text_color);
      }
      if (optional.section_bg_color) {
        document.documentElement.style.setProperty("--tg-theme-section-bg-color", optional.section_bg_color);
      }
      if (optional.section_header_text_color) {
        document.documentElement.style.setProperty("--tg-theme-section-header-text-color", optional.section_header_text_color);
      }
      if (optional.section_separator_color) {
        document.documentElement.style.setProperty("--tg-theme-section-separator-color", optional.section_separator_color);
      }
      if (optional.subtitle_text_color) {
        document.documentElement.style.setProperty("--tg-theme-subtitle-text-color", optional.subtitle_text_color);
      }
      if (optional.destructive_text_color) {
        document.documentElement.style.setProperty("--tg-theme-destructive-text-color", optional.destructive_text_color);
      }

      const colorScheme = this.webApp.colorScheme ?? "light";
      document.documentElement.setAttribute("data-theme", colorScheme);
    };

    applyTheme();

    if (typeof this.webApp.onEvent === "function") {
      this.webApp.onEvent("themeChanged", applyTheme);
    }

    const themeParams = this.webApp.themeParams ?? {};
    if (typeof this.webApp.isVersionAtLeast === "function" && this.webApp.isVersionAtLeast("6.1")) {
      try {
        const opt = themeParams as unknown as Record<string, string | undefined>;
        const bg = themeParams.bg_color ?? "bg_color";
        const header = opt.header_bg_color ?? themeParams.bg_color ?? "bg_color";
        if (typeof this.webApp.setBackgroundColor === "function") {
          this.webApp.setBackgroundColor(bg as "bg_color" | "secondary_bg_color" | `#${string}`);
        }
        if (typeof this.webApp.setHeaderColor === "function") {
          this.webApp.setHeaderColor(header as "bg_color" | "secondary_bg_color" | `#${string}`);
        }
      } catch (e) {
        logger.debug("setHeaderColor/setBackgroundColor:", e);
      }
    }
  }

  /**
   * Применить safe area insets из API (Bot API 8.0+) в CSS-переменные.
   */
  private applySafeAreaInsets(): void {
    const inset = (this.webApp as { safeAreaInset?: { top?: number; bottom?: number; left?: number; right?: number } }).safeAreaInset;
    if (!inset) return;
    const root = document.documentElement.style;
    if (typeof inset.top === "number") root.setProperty("--tg-safe-area-inset-top", `${inset.top}px`);
    if (typeof inset.bottom === "number") root.setProperty("--tg-safe-area-inset-bottom", `${inset.bottom}px`);
    if (typeof inset.left === "number") root.setProperty("--tg-safe-area-inset-left", `${inset.left}px`);
    if (typeof inset.right === "number") root.setProperty("--tg-safe-area-inset-right", `${inset.right}px`);
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
   * С поддержкой fallback для старых версий Telegram Web App
   */
  showAlert(message: string): Promise<void> {
    return new Promise((resolve) => {
      try {
        // Проверяем версию Telegram Web App
        const version = parseFloat(this.webApp.version || '0');

        // showAlert доступен с версии 6.0, но может использовать showPopup внутри
        // Для версий < 6.1 используем fallback на нативный alert
        if (version < 6.1 && typeof this.webApp.showAlert === 'function') {
          // Пробуем использовать showAlert, но ловим ошибку если не поддерживается
          try {
            this.webApp.showAlert(message, () => resolve());
          } catch {
            // Fallback на нативный alert для старых версий
            console.warn('Telegram showAlert не поддерживается, используем fallback');
            alert(message);
            resolve();
          }
        } else {
          // Для новых версий используем стандартный метод
          this.webApp.showAlert(message, () => resolve());
        }
      } catch (error) {
        // Если произошла ошибка, используем fallback
        console.warn('Ошибка при показе alert через Telegram API:', error);
        alert(message);
        resolve();
      }
    });
  }

  /**
   * Показать подтверждение
   * С поддержкой fallback для старых версий Telegram Web App
   */
  showConfirm(message: string): Promise<boolean> {
    return new Promise((resolve) => {
      try {
        // Проверяем версию Telegram Web App
        const version = parseFloat(this.webApp.version || '0');

        // showConfirm доступен с версии 6.0, но может использовать showPopup внутри
        // Для версий < 6.1 используем fallback на нативный confirm
        if (version < 6.1 && typeof this.webApp.showConfirm === 'function') {
          // Пробуем использовать showConfirm, но ловим ошибку если не поддерживается
          try {
            this.webApp.showConfirm(message, (confirmed) => resolve(confirmed));
          } catch {
            // Fallback на нативный confirm для старых версий
            console.warn('Telegram showConfirm не поддерживается, используем fallback');
            const confirmed = confirm(message);
            resolve(confirmed);
          }
        } else {
          // Для новых версий используем стандартный метод
          this.webApp.showConfirm(message, (confirmed) => resolve(confirmed));
        }
      } catch (error) {
        // Если произошла ошибка, используем fallback
        console.warn('Ошибка при показе confirm через Telegram API:', error);
        const confirmed = confirm(message);
        resolve(confirmed);
      }
    });
  }

  /**
   * Показать всплывающее меню
   * С поддержкой fallback для старых версий Telegram Web App
   * ВАЖНО: showPopup доступен только с версии 6.1+
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
      try {
        // Проверяем версию Telegram Web App
        const version = parseFloat(this.webApp.version || '0');

        // showPopup доступен только с версии 6.1+
        if (version < 6.1) {
          console.warn('showPopup не поддерживается в версии', version, ', используем fallback');
          // Fallback: показываем сообщение через alert и возвращаем пустую строку
          alert(params.message);
          resolve("");
          return;
        }

        // Для версий 6.1+ используем стандартный метод
        if (typeof this.webApp.showPopup === 'function') {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          this.webApp.showPopup(params as any, (buttonId: string | undefined) =>
            resolve(buttonId || ""),
          );
        } else {
          // Если метод не существует, используем fallback
          console.warn('showPopup не доступен, используем fallback');
          alert(params.message);
          resolve("");
        }
      } catch (error) {
        // Если произошла ошибка, используем fallback
        console.warn('Ошибка при показе popup через Telegram API:', error);
        alert(params.message);
        resolve("");
      }
    });
  }

  /**
   * Проверка, запущено ли приложение в Telegram
   * Проверка по initData, user agent, tgaddr в URL и window.Telegram.WebApp
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

    // Проверяем наличие tgaddr в URL (явный признак Telegram Mini App)
    let hasTgaddr = false;
    if (typeof window !== "undefined") {
      // Проверяем search параметры
      const urlParams = new URLSearchParams(window.location.search);
      hasTgaddr = urlParams.has("tgaddr");

      // Если нет в search, проверяем hash (для web.telegram.org/k/#?tgaddr=...)
      if (!hasTgaddr && window.location.hash) {
        const hashParams = new URLSearchParams(window.location.hash.slice(1));
        hasTgaddr = hashParams.has("tgaddr");
      }
    }

    // Проверяем наличие window.Telegram.WebApp
    const hasTelegramWebApp =
      typeof window !== "undefined" &&
      typeof (window as Window & { Telegram?: { WebApp?: unknown } }).Telegram !== "undefined" &&
      typeof (window as Window & { Telegram?: { WebApp?: unknown } }).Telegram?.WebApp !== "undefined";

    // КРИТИЧНО: Строгая проверка - только если есть initData (основной критерий)
    // ИЛИ точно в Telegram по user agent ИЛИ есть tgaddr
    // НЕ используем hasTelegramWebApp как основной критерий, т.к. объект может существовать вне Telegram
    return hasInitData || (isTelegramUserAgent && hasTelegramWebApp) || hasTgaddr;
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
