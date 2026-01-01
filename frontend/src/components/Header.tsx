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
    <header className="max-w-6xl mx-auto px-4 py-6 flex items-center justify-between backdrop-blur-sm">
      {/* Логотип и название */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <img
            src={SITE_CONFIG.logo.src}
            alt={SITE_CONFIG.logo.alt}
            className="w-12 h-12 rounded-full shadow-lg ring-2 ring-white/50 dark:ring-slate-700 animate-logo-bounce"
            loading="eager"
            width="48"
            height="48"
          />
        </div>
        <span className="font-display text-2xl font-bold text-gray-900 dark:text-slate-50 animate-text-reveal">
          {SITE_CONFIG.name}
        </span>
      </div>

      {/* Навигация (скрыта на мобильных) */}
      <nav
        className="hidden md:flex items-center gap-6"
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
          className="px-6 py-2.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold hover:shadow-lg hover:scale-105 transition-all duration-200"
        >
          Начать
        </a>
      </nav>
    </header>
  );
});

// Для удобства отладки в React DevTools
Header.displayName = 'Header';
