/**
 * Компонент Header (шапка сайта)
 * Содержит логотип, навигацию и CTA-кнопку
 * @module components/Header
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';
import { DarkModeToggle } from './DarkModeToggle';
import { trackButtonClick } from '../utils/analytics';

/**
 * Шапка сайта с адаптивной навигацией
 * На мобильных устройствах навигация скрыта (можно добавить гамбургер-меню)
 */
export const Header: React.FC = React.memo(() => {
  return (
    <header className="absolute top-0 left-0 right-0 z-40 relative">
      {/* Градиентная граница снизу - прозрачная вверху, видимая внизу, без размытия */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-b from-transparent to-gray-200/60 dark:to-slate-600/60"></div>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 md:py-6 flex items-center justify-between">
        {/* Логотип и название - кликабельные для возврата на главную */}
        <a
          href="/"
          onClick={(e) => {
            e.preventDefault();
            window.history.pushState(null, '', '/');
            window.dispatchEvent(new Event('popstate'));
            trackButtonClick('header_logo_home');
          }}
          className="flex items-center gap-2 sm:gap-3 hover:opacity-80 transition-opacity cursor-pointer"
          aria-label="На главную"
        >
          <img
            src={SITE_CONFIG.logo.src}
            alt={SITE_CONFIG.logo.alt}
            className="w-10 h-10 sm:w-12 sm:h-12 rounded-full animate-logo-bounce object-cover"
            loading="eager"
            width="48"
            height="48"
            style={{
              animation: 'logoBounce 2s ease-in-out infinite',
              willChange: 'transform',
              transform: 'translateZ(0)',
              backfaceVisibility: 'hidden',
            }}
            onError={(e) => {
              // Fallback если логотип не загрузится
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              const emoji = document.createElement('div');
              emoji.textContent = '🐼';
              emoji.className = 'text-3xl sm:text-4xl animate-logo-bounce';
              emoji.style.cssText = 'animation: logoBounce 2s ease-in-out infinite; will-change: transform; transform: translateZ(0); backface-visibility: hidden;';
              target.parentElement?.appendChild(emoji);
            }}
          />
          <span className="font-display text-xl sm:text-2xl font-bold text-gray-900 dark:text-slate-50 animate-text-reveal">
            {SITE_CONFIG.name}
          </span>
        </a>

        {/* Кнопки в правом верхнем углу */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Навигация */}
          <nav className="hidden sm:flex items-center gap-2">
            <a
              href="https://t.me/PandaPalBot?startapp=premium"
              onClick={() => {
                trackButtonClick('header_premium');
                // Ссылка напрямую откроет мини-апп если Telegram установлен
                // Иначе откроет страницу бота в браузере
              }}
              className="nav-link-header"
              target="_blank"
              rel="noopener noreferrer"
            >
              Premium
            </a>
            <a
              href="/donation"
              onClick={(e) => {
                e.preventDefault();
                window.history.pushState(null, '', '/donation');
                window.dispatchEvent(new Event('popstate'));
                trackButtonClick('header_donation');
              }}
              className="nav-link-header"
            >
              Поддержать
            </a>
          </nav>

          {/* CTA-кнопка к Telegram-боту */}
          <a
            href={SITE_CONFIG.botUrl}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => trackButtonClick('header_start_bot')}
            className="inline-flex items-center justify-center px-4 sm:px-5 lg:px-6 py-2 sm:py-2.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-600 dark:to-cyan-600 text-white font-semibold text-sm hover:shadow-lg dark:hover:shadow-xl hover:scale-105 active:scale-100 transition-all duration-200"
          >
            Войти
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
