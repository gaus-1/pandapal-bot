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
      <div className="max-w-6xl mx-auto px-fib-4 sm:px-fib-4 lg:px-fib-5 py-fib-4 sm:py-fib-4 lg:py-fib-5 flex items-center justify-between">
        {/* Логотип и название - кликабельные для возврата на главную */}
        <a
          href="/"
          onClick={(e) => {
            e.preventDefault();
            window.history.pushState(null, '', '/');
            window.dispatchEvent(new Event('popstate'));
            trackButtonClick('header_logo_home');
          }}
          className="flex items-center gap-fib-2 sm:gap-fib-3 hover:opacity-80 transition-opacity cursor-pointer"
          aria-label="На главную"
        >
          <img
            src="/logo-96.webp"
            srcSet="/logo-48.webp 48w, /logo-96.webp 96w, /logo-200.webp 200w"
            sizes="(max-width: 640px) 40px, 48px"
            alt={SITE_CONFIG.logo.alt}
            className="w-10 h-10 sm:w-12 sm:h-12 rounded-full animate-logo-bounce object-cover"
            loading="eager"
            fetchPriority="high"
            width="48"
            height="48"
            onError={(e) => {
              // Fallback: пробуем PNG, затем emoji
              const target = e.target as HTMLImageElement;
              if (target.src.includes('.webp')) {
                target.src = SITE_CONFIG.logo.src;
                return;
              }
              target.style.display = 'none';
              const emoji = document.createElement('div');
              emoji.textContent = '🐼';
              emoji.className = 'text-3xl sm:text-4xl animate-logo-bounce';
              target.parentElement?.appendChild(emoji);
            }}
          />
          <span className="hidden xs:inline font-display text-xl sm:text-2xl font-bold text-gray-900 dark:text-slate-50 animate-text-reveal">
            {SITE_CONFIG.name}
          </span>
        </a>

        {/* Кнопки в правом верхнем углу */}
        <div className="flex items-center gap-fib-2 xs:gap-fib-2 sm:gap-fib-3">
          {/* Навигация */}
          <nav className="hidden sm:flex items-center gap-fib-2">
            <a
              href="/help"
              onClick={(e) => {
                e.preventDefault();
                window.history.pushState(null, '', '/help');
                window.dispatchEvent(new Event('popstate'));
                trackButtonClick('header_help');
              }}
              className="nav-link-header"
            >
              Помощь
            </a>
            <a
              href="/premium"
              onClick={(e) => {
                e.preventDefault();
                window.history.pushState(null, '', '/premium');
                window.dispatchEvent(new Event('popstate'));
                trackButtonClick('header_premium');
              }}
              className="nav-link-header"
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
            className="inline-flex items-center justify-center px-fib-3 xs:px-fib-4 sm:px-fib-4 lg:px-fib-5 py-fib-2 sm:py-fib-2 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-600 dark:to-cyan-600 text-white font-semibold text-sm hover:shadow-lg dark:hover:shadow-xl hover:scale-105 active:scale-100 transition-all duration-200 min-h-[40px] xs:min-h-[44px] sm:min-h-[48px] touch-manipulation"
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
