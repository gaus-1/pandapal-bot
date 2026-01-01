/**
 * Утилиты для аналитики и трекинга
 * Поддержка Google Analytics 4, Yandex Metrika и других систем
 * @module utils/analytics
 */

interface WindowWithGtag extends Window {
  gtag?: (...args: unknown[]) => void;
  ym?: (id: number, method: string, goal: string) => void;
}

/**
 * Отправка события клика по кнопке в аналитику
 *
 * @param buttonName - Название кнопки для отслеживания
 * @example
 * trackButtonClick('start_bot') // Клик по кнопке "Начать использовать"
 */
export const trackButtonClick = (buttonName: string): void => {
  const win = window as WindowWithGtag;

  // Проверяем наличие Google Analytics
  if (typeof window !== 'undefined' && win.gtag) {
    // Отправляем событие в GA4
    win.gtag('event', 'click', {
      event_category: 'Button',
      event_label: buttonName,
    });
  }

  // Можно добавить Yandex Metrika
  if (typeof window !== 'undefined' && win.ym) {
    win.ym(12345678, 'reachGoal', `button_${buttonName}`);
  }
};

/**
 * Отправка события просмотра страницы
 *
 * @param pagePath - Путь к странице
 * @example
 * trackPageView('/parents') // Просмотр секции "Для родителей"
 */
export const trackPageView = (pagePath: string): void => {
  const win = window as WindowWithGtag;

  // Google Analytics 4
  if (typeof window !== 'undefined' && win.gtag) {
    win.gtag('event', 'page_view', {
      page_path: pagePath,
    });
  }
};
