/**
 * Компонент Header (шапка сайта)
 * Содержит логотип, навигацию и CTA-кнопку
 * @module components/Header
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';

/**
 * Шапка сайта с адаптивной навигацией
 * На мобильных устройствах навигация скрыта (можно добавить гамбургер-меню)
 */
export const Header: React.FC = React.memo(() => {
  return (
    <header className="sticky top-0 z-40 backdrop-blur-md bg-white/90 dark:bg-slate-900/90 border-b border-gray-200 dark:border-slate-700 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 md:py-6 flex items-center justify-between">
        {/* Логотип и название */}
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="relative flex-shrink-0 p-1.5 bg-gradient-to-br from-blue-100/50 to-cyan-100/50 dark:from-slate-700/50 dark:to-slate-600/50 rounded-full backdrop-blur-sm">
            <img
              src={SITE_CONFIG.logo.src}
              alt={SITE_CONFIG.logo.alt}
              className="w-10 h-10 sm:w-12 sm:h-12 rounded-full shadow-lg ring-1 ring-blue-200/50 dark:ring-slate-500/50 animate-logo-bounce object-cover"
              loading="eager"
              width="48"
              height="48"
              onError={(e) => {
                // Fallback если логотип не загрузится
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                const emoji = document.createElement('div');
                emoji.textContent = '🐼';
                emoji.className = 'text-3xl sm:text-4xl';
                target.parentElement?.appendChild(emoji);
              }}
            />
          </div>
          <span className="font-display text-xl sm:text-2xl font-bold text-gray-900 dark:text-slate-50 animate-text-reveal">
            {SITE_CONFIG.name}
          </span>
        </div>

        {/* CTA-кнопка к Telegram-боту (десктоп) */}
        <a
          href={SITE_CONFIG.botUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="hidden md:inline-flex px-5 lg:px-6 py-2.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold text-sm hover:shadow-lg hover:scale-105 transition-all duration-200"
        >
          Начать
        </a>

        {/* Мобильная CTA кнопка */}
        <a
          href={SITE_CONFIG.botUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="md:hidden px-4 py-2 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold text-sm hover:shadow-lg active:scale-95 transition-all duration-200"
        >
          Начать
        </a>
      </div>
    </header>
  );
});

// Для удобства отладки в React DevTools
Header.displayName = 'Header';
