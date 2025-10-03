/**
 * Компонент Header (шапка сайта)
 * Содержит логотип, навигацию и CTA-кнопку
 * @module components/Header
 */

import React from 'react';
import { SITE_CONFIG, NAVIGATION_LINKS } from '../config/constants';
import './Header.css';

/**
 * Шапка сайта с адаптивной навигацией
 * На мобильных устройствах навигация скрыта (можно добавить гамбургер-меню)
 */
export const Header: React.FC = React.memo(() => {
  return (
    <header className="max-w-6xl mx-auto px-4 py-6 flex items-center justify-between">
      {/* Логотип и название */}
      <div className="flex items-center gap-3">
        <img
          src={SITE_CONFIG.logo.src}
          alt={SITE_CONFIG.logo.alt}
          className="w-12 h-12 rounded-full shadow-md panda-logo-animated cursor-pointer transition-all duration-300 hover:scale-110 hover:rotate-12 hover:shadow-lg"
          loading="eager"
          width="48"
          height="48"
          onClick={() => window.location.href = '/'}
          title="Кликни на меня! 🐼"
        />
        <span className="font-display text-2xl font-bold">
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
            className="text-sm hover:text-pink transition-colors duration-200"
          >
            {link.label}
          </a>
        ))}

        {/* CTA-кнопка к Telegram-боту */}
        <a
          href={SITE_CONFIG.botUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="px-5 py-2 rounded-full bg-sky text-white hover:shadow-lg transition-shadow duration-200"
        >
          Начать
        </a>
      </nav>
    </header>
  );
});

// Для удобства отладки в React DevTools
Header.displayName = 'Header';

