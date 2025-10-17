/**
 * Дополнительная защита от Clickjacking
 * КРИТИЧЕСКИ ВАЖНО для защиты детей от скрытых фреймов
 * @module security/clickjacking
 */

/**
 * Проверяет, не встроен ли сайт в iframe (clickjacking защита)
 * Дополнительная защита на клиентской стороне
 */
export const detectClickjacking = (): boolean => {
  try {
    // Проверяем, не находимся ли мы в iframe
    if (window.self !== window.top) {
      console.error('🚫 ОБНАРУЖЕН CLICKJACKING! Сайт встроен в iframe');

      // Заменяем содержимое страницы предупреждением
      document.body.innerHTML = `
        <div style="
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: #ff4444;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: Arial, sans-serif;
          font-size: 24px;
          text-align: center;
          z-index: 999999;
        ">
          <div>
            <h1>🚫 ОБНАРУЖЕНА ПОПЫТКА АТАКИ!</h1>
            <p>Этот сайт не может быть встроен в другие страницы</p>
            <p>Для безопасности детей доступ разрешён только напрямую</p>
            <p>Перейдите на: <strong>https://pandapal.ru</strong></p>
          </div>
        </div>
      `;

      return true; // Clickjacking обнаружен
    }

    return false; // Всё в порядке
  } catch {
    // Если window.top недоступен (same-origin policy), это тоже может быть clickjacking
    console.error('🚫 Подозрение на clickjacking - window.top недоступен');
    return true;
  }
};

/**
 * Инициализирует защиту от clickjacking при загрузке страницы
 * КРИТИЧЕСКИ ВАЖНО для безопасности детей
 */
export const initClickjackingProtection = (): void => {
  // Проверяем сразу при загрузке
  if (detectClickjacking()) {
    return; // Страница уже заблокирована
  }

  // Дополнительная проверка через небольшой интервал
  setTimeout(() => {
    detectClickjacking();
  }, 100);

  // Проверяем при изменении размера окна (может быть попытка скрыть iframe)
  window.addEventListener('resize', () => {
    setTimeout(detectClickjacking, 50);
  });

  // Проверяем при попытке изменения фокуса
  window.addEventListener('blur', () => {
    setTimeout(() => {
      if (document.hidden) {
        detectClickjacking();
      }
    }, 100);
  });
};

/**
 * Защита от попыток скрыть iframe через CSS
 * Проверяет стили родительского окна
 */
export const checkParentFrameStyles = (): void => {
  try {
    // Пытаемся получить стили родительского окна
    if (window.parent !== window.self) {
      const parentDocument = window.parent.document;
      const parentBody = parentDocument.body;

      if (parentBody) {
        const styles = window.parent.getComputedStyle(parentBody);

        // Проверяем, не скрыт ли iframe
        if (styles.opacity === '0' || styles.visibility === 'hidden' || styles.display === 'none') {
          console.error('🚫 Попытка скрыть iframe через CSS - clickjacking!');
          detectClickjacking();
        }
      }
    }
  } catch {
    // Если не можем получить доступ - это нормально (same-origin policy)
    // Но если это не same-origin, то может быть clickjacking
  }
};

/**
 * Экспорт для использования в main.tsx
 */
export const SECURITY_PROTECTION = {
  detectClickjacking,
  initClickjackingProtection,
  checkParentFrameStyles,
};
