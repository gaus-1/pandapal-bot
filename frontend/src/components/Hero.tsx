/**
 * Компонент Hero (главная секция страницы)
 * Первое, что видит пользователь: заголовок, описание, CTA-кнопка
 * @module components/Hero
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';
import { HERO_TAGLINE_RU } from '../config/seo-text';
import { trackButtonClick } from '../utils/analytics';

/**
 * Hero-секция с главным призывом к действию
 * Оптимизирована для конверсии: крупный заголовок + яркие CTA
 */
export const Hero: React.FC = React.memo(() => {
  return (
    <section className="pt-fib-6 sm:pt-fib-7 lg:pt-fib-7 pb-fib-5 sm:pb-fib-6 lg:pb-fib-6 text-center">
      <div className="max-w-4xl mx-auto">
        {/* Основной заголовок (H1 для SEO, entity PandaPal в первом заголовке) */}
        <h1 className="font-display text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold leading-tight text-gray-900 dark:text-slate-50">
          PandaPal: безопасный и полезный AI-друг для детей
        </h1>

        {/* Описание продукта (канонический слоган из seo-text) */}
        <p className="mt-fib-3 sm:mt-fib-4 md:mt-fib-4 text-sm sm:text-base md:text-lg text-gray-700 dark:text-slate-200 max-w-2xl mx-auto leading-relaxed">
          {HERO_TAGLINE_RU}
        </p>

        {/* CTA кнопки: правило третей — лёгкий сдвиг вправо на десктопе для динамики */}
        <div className="mt-fib-4 sm:mt-fib-5 md:mt-fib-5 flex flex-col sm:flex-row gap-fib-3 sm:gap-fib-4 justify-center md:justify-center md:ml-[8%] items-stretch sm:items-center">
        {/* Основная CTA */}
        <a
          href={SITE_CONFIG.botUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => trackButtonClick('hero_start_bot')}
          className="inline-flex items-center justify-center px-fib-4 sm:px-fib-5 py-fib-2 sm:py-fib-3 rounded-full bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 font-semibold text-base sm:text-lg shadow-md hover:shadow-lg dark:hover:shadow-xl transition-all duration-300 border-2 border-gray-200 dark:border-slate-600 hover:border-blue-500 dark:hover:border-blue-400 active:bg-gray-50 dark:active:bg-slate-600 min-h-[44px] sm:min-h-[48px] touch-manipulation"
          aria-label="Начать использовать PandaPal в Telegram"
          data-cta-variant="primary"
        >
          Начни
        </a>

        {/* Локальная разработка: ссылка на Mini App с пандой */}
        {import.meta.env.DEV && typeof window !== 'undefined' &&
          (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && (
          <a
            href="/miniapp"
            className="inline-flex items-center justify-center px-fib-4 sm:px-fib-5 py-fib-2 sm:py-fib-3 rounded-full bg-amber-500 dark:bg-amber-600 text-white font-semibold text-base sm:text-lg shadow-md hover:shadow-lg transition-all border-2 border-amber-600 dark:border-amber-500 min-h-[44px] sm:min-h-[48px] touch-manipulation"
            aria-label="Открыть Mini App локально (игра Моя панда)"
          >
            Открыть Mini App (локально)
          </a>
        )}

        <a
          href="#benefits"
          onClick={() => {
            trackButtonClick('hero_learn_more');
          }}
          className="inline-flex items-center justify-center px-fib-4 sm:px-fib-5 py-fib-2 sm:py-fib-3 rounded-full bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 font-semibold text-base sm:text-lg shadow-md hover:shadow-lg dark:hover:shadow-xl transition-all duration-300 border-2 border-gray-200 dark:border-slate-600 hover:border-blue-500 dark:hover:border-blue-400 active:bg-gray-50 dark:active:bg-slate-600 min-h-[44px] sm:min-h-[48px] touch-manipulation"
          aria-label="Узнать больше о PandaPal"
          data-cta-variant="secondary"
        >
          Узнать больше
        </a>
      </div>
      </div>
    </section>
  );
});

// Для React DevTools
Hero.displayName = 'Hero';
