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
      className="max-w-6xl mx-auto px-4 py-12 text-center border-t border-gray-200 dark:border-slate-700 mt-16"
      role="contentinfo"
    >
      {/* Логотип и название */}
      <div className="flex items-center justify-center gap-3 mb-4">
        <img
          src={SITE_CONFIG.logo.src}
          alt={SITE_CONFIG.logo.alt}
          className="w-10 h-10 rounded-full"
          loading="lazy"
          width="40"
          height="40"
        />
        <span className="font-display text-xl font-bold text-gray-900 dark:text-slate-100">
          {SITE_CONFIG.name}
        </span>
      </div>

      {/* Копирайт */}
      <p className="text-sm text-gray-600 dark:text-slate-400">
        © {currentYear} {SITE_CONFIG.name}. Все права защищены.
      </p>
    </footer>
  );
});

// Для React DevTools
Footer.displayName = 'Footer';
