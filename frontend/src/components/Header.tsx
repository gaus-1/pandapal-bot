/**
 * Компонент Header (шапка сайта)
 * Содержит логотип, навигацию и CTA-кнопку
 * Адаптивное мобильное меню для всех устройств
 * @module components/Header
 */

import React, { useState } from 'react';
import { SITE_CONFIG, NAVIGATION_LINKS } from '../config/constants';
import './Header.css';

/**
 * Шапка сайта с адаптивной навигацией
 * На мобильных устройствах - гамбургер-меню
 * На десктопах - горизонтальная навигация
 */
export const Header: React.FC = React.memo(() => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="max-w-6xl mx-auto px-4 py-6 relative">
      <div className="flex items-center justify-between">
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

        {/* Мобильное гамбургер-меню (< 768px) */}
        <button
          className="md:hidden w-12 h-12 flex items-center justify-center rounded-lg bg-sky/10 hover:bg-sky/20 transition-colors"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label={mobileMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? (
            // Иконка закрытия (X)
            <svg
              className="w-6 h-6 text-gray-700"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          ) : (
            // Иконка гамбургера (☰)
            <svg
              className="w-6 h-6 text-gray-700"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          )}
        </button>

        {/* Десктопная навигация (≥ 768px) */}
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
      </div>

      {/* Мобильное выпадающее меню */}
      {mobileMenuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 mt-2 mx-4 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden z-50 animate-fadeIn">
          <nav
            className="flex flex-col"
            aria-label="Мобильная навигация"
          >
            {/* Ссылки навигации */}
            {NAVIGATION_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="px-6 py-4 text-base hover:bg-sky/10 transition-colors border-b border-gray-100 last:border-b-0"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </a>
            ))}

            {/* CTA-кнопка */}
            <a
              href={SITE_CONFIG.botUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mx-4 my-4 px-6 py-3 text-center rounded-full bg-sky text-white font-semibold shadow-md hover:shadow-lg transition-all"
              onClick={() => setMobileMenuOpen(false)}
            >
              Начать использовать 🚀
            </a>
          </nav>
        </div>
      )}
    </header>
  );
});

// Для удобства отладки в React DevTools
Header.displayName = 'Header';
