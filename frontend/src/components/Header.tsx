/**
 * Компонент Header (шапка сайта)
 * Содержит логотип, навигацию и CTA-кнопку
 * @module components/Header
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';
import { DarkModeToggle } from './DarkModeToggle';

/**
 * Шапка сайта с адаптивной навигацией
 * На мобильных устройствах навигация скрыта (можно добавить гамбургер-меню)
 */
export const Header: React.FC = React.memo(() => {
  return (
    <header className="absolute top-0 left-0 right-0 z-40">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 md:py-6 flex items-center justify-between">
        {/* Логотип и название */}
        <div className="flex items-center gap-2 sm:gap-3">
          <img
            src={SITE_CONFIG.logo.src}
            alt={SITE_CONFIG.logo.alt}
            className="w-10 h-10 sm:w-12 sm:h-12 rounded-full animate-logo-bounce object-cover"
            loading="eager"
            width="48"
            height="48"
            onError={(e) => {
              // Fallback если логотип не загрузится
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              const emoji = document.createElement('div');
              emoji.textContent = '🐼';
              emoji.className = 'text-3xl sm:text-4xl animate-logo-bounce';
              target.parentElement?.appendChild(emoji);
            }}
          />
          <span className="font-display text-xl sm:text-2xl font-bold text-gray-900 dark:text-slate-50 animate-text-reveal">
            {SITE_CONFIG.name}
          </span>
        </div>

        {/* Кнопки в правом верхнем углу */}
        <div className="flex items-center gap-3">
          {/* CTA-кнопка к Telegram-боту */}
          <a
            href={SITE_CONFIG.botUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center px-4 sm:px-5 lg:px-6 py-2 sm:py-2.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-600 dark:to-cyan-600 text-white font-semibold text-sm hover:shadow-lg hover:scale-105 transition-all duration-200"
          >
            Начни
          </a>

          {/* Переключатель темы - встроен в header */}
          <DarkModeToggle isInline />
        </div>
      </div>
    </header>
  );
});

// Для удобства отладки в React DevTools
Header.displayName = 'Header';
