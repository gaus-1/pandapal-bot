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
      className="max-w-6xl mx-auto px-4 py-12 text-center border-t border-gray-200 dark:border-slate-700 dark:border-slate-600/50 mt-16"
      role="contentinfo"
    >
      {/* Логотип и название */}
      <div className="flex items-center justify-center gap-3 mb-4">
        <img
          src={SITE_CONFIG.logo.src}
          alt={SITE_CONFIG.logo.alt}
          className="w-10 h-10 rounded-full animate-logo-bounce object-cover"
          loading="lazy"
          width="40"
          height="40"
          onError={(e) => {
            // Fallback если логотип не загрузится
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            const emoji = document.createElement('div');
            emoji.textContent = '🐼';
            emoji.className = 'text-3xl animate-logo-bounce';
            target.parentElement?.appendChild(emoji);
          }}
        />
        <span className="font-display text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-100">
          {SITE_CONFIG.name}
        </span>
      </div>

      {/* Копирайт */}
      <p className="text-xs sm:text-sm md:text-base text-gray-600 dark:text-slate-400">
        © {currentYear} {SITE_CONFIG.name}. Все права защищены.
      </p>
    </footer>
  );
});

// Для React DevTools
Footer.displayName = 'Footer';
