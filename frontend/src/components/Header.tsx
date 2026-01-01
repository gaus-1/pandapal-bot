/**
 * Компонент Header (шапка сайта)
 * Содержит логотип, навигацию и CTA-кнопку
 * @module components/Header
 */

import React from 'react';
import { SITE_CONFIG, NAVIGATION_LINKS } from '../config/constants';

/**
 * Шапка сайта с адаптивной навигацией
 * На мобильных устройствах навигация скрыта (можно добавить гамбургер-меню)
 */
export const Header: React.FC = React.memo(() => {
  return (
    <header className="sticky top-0 z-40 backdrop-blur-md bg-white/80 dark:bg-slate-900/80 border-b border-gray-200 dark:border-slate-700">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 md:py-6 flex items-center justify-between">
        {/* Логотип и название */}
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="relative flex-shrink-0">
            <img
              src={SITE_CONFIG.logo.src}
              alt={SITE_CONFIG.logo.alt}
              className="w-10 h-10 sm:w-12 sm:h-12 rounded-full shadow-lg ring-4 ring-blue-100 dark:ring-slate-700 animate-logo-bounce"
              loading="eager"
              width="48"
              height="48"
            />
          </div>
          <span className="font-display text-xl sm:text-2xl font-bold text-gray-900 dark:text-slate-50 animate-text-reveal">
            {SITE_CONFIG.name}
          </span>
        </div>

        {/* Навигация (скрыта на мобильных) */}
        <nav
          className="hidden md:flex items-center gap-4 lg:gap-6"
          aria-label="Основная навигация"
        >
          {/* Ссылки на секции страницы */}
          {NAVIGATION_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-gray-700 dark:text-slate-300 hover:text-pink-500 dark:hover:text-pink-400 transition-colors duration-200"
            >
              {link.label}
            </a>
          ))}

          {/* CTA-кнопка к Telegram-боту */}
          <a
            href={SITE_CONFIG.botUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 lg:px-6 py-2.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold text-sm hover:shadow-lg hover:scale-105 transition-all duration-200"
          >
            Начать
          </a>
        </nav>

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
