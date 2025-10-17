/**
 * Утилиты для аналитики и трекинга
 * Поддержка Google Analytics 4, Yandex Metrika и других систем
 * @module utils/analytics
 */

/**
 * Отправка события клика по кнопке в аналитику
 *
 * @param buttonName - Название кнопки для отслеживания
 * @example
 * trackButtonClick('start_bot') // Клик по кнопке "Начать использовать"
 */
export const trackButtonClick = (buttonName: string): void => {
  // Проверяем наличие Google Analytics
  if (typeof window !== 'undefined' && 'gtag' in window) {
    // Отправляем событие в GA4
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).gtag('event', 'click', {
      event_category: 'Button',
      event_label: buttonName,
    });
  }

  // Можно добавить Yandex Metrika
  if (typeof window !== 'undefined' && 'ym' in window) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).ym(12345678, 'reachGoal', `button_${buttonName}`);
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
  // Google Analytics 4
  if (typeof window !== 'undefined' && 'gtag' in window) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).gtag('event', 'page_view', {
      page_path: pagePath,
    });
  }
};
