/**
 * Компонент Footer (подвал сайта)
 * Содержит логотип и копирайт
 * @module components/Footer
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';

/**
 * Подвал сайта с автообновляемым годом
 * Отображается внизу каждой страницы
 */
export const Footer: React.FC = React.memo(() => {
  // Получаем текущий год автоматически (не нужно обновлять вручную)
  const currentYear = new Date().getFullYear();

  return (
    <footer
      className="max-w-6xl mx-auto px-4 py-12 text-center border-t border-gray-200/50 mt-16"
      role="contentinfo" // ARIA роль для accessibility
    >
      {/* Логотип и название */}
      <div className="flex items-center justify-center gap-3 mb-4">
        <img
          src={SITE_CONFIG.logo.src}
          alt={SITE_CONFIG.logo.alt}
          className="w-8 h-8 rounded-full"
          loading="lazy" // Ленивая загрузка (футер внизу страницы)
          width="32"
          height="32"
        />
        <span className="font-display text-lg font-semibold">
          {SITE_CONFIG.name}
        </span>
      </div>

      {/* Копирайт с автообновляемым годом */}
      <p className="text-sm text-gray-600">
        © {currentYear} {SITE_CONFIG.name}. Все права защищены.
      </p>
    </footer>
  );
});

// Для React DevTools
Footer.displayName = 'Footer';
