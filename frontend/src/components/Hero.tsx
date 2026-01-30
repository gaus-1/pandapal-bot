/**
 * Компонент Hero (главная секция страницы)
 * Первое, что видит пользователь: заголовок, описание, CTA-кнопка
 * @module components/Hero
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';
import { trackButtonClick } from '../utils/analytics';

/**
 * Hero-секция с главным призывом к действию
 * Оптимизирована для конверсии: крупный заголовок + яркие CTA
 */
export const Hero: React.FC = React.memo(() => {
  return (
    <section className="pt-12 sm:pt-16 md:pt-20 pb-12 sm:pb-16 md:pb-20 text-center">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Основной заголовок (H1 для SEO) */}
        <h1 className="font-display text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold leading-tight text-gray-900 dark:text-slate-50">
          Безопасный и полезный AI - друг для детей
        </h1>

        {/* Описание продукта */}
        <p className="mt-3 sm:mt-4 md:mt-5 text-sm sm:text-base md:text-lg text-gray-700 dark:text-slate-200 max-w-2xl mx-auto">
          Адаптивное, игровое, безопасное обучение и общение для детей 1–9 классов
        </p>

        {/* CTA кнопки */}
        <div className="mt-5 sm:mt-6 md:mt-7 flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center items-stretch sm:items-center">
        {/* Основная CTA */}
        <a
          href={SITE_CONFIG.botUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => trackButtonClick('hero_start_bot')}
          className="inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 font-semibold text-base sm:text-lg shadow-md hover:shadow-lg dark:hover:shadow-xl transition-all duration-300 border-2 border-gray-200 dark:border-slate-600 hover:border-blue-500 dark:hover:border-blue-400 active:bg-gray-50 dark:active:bg-slate-600 min-h-[44px] sm:min-h-[48px] touch-manipulation"
          aria-label="Начать использовать PandaPal в Telegram"
          data-cta-variant="primary"
        >
          Начни
        </a>

        {/* Вторичная CTA */}
        <a
          href="#benefits"
          onClick={(e) => {
            e.preventDefault();
            const element = document.getElementById('benefits');
            if (element) {
              // Учитываем высоту фиксированного Header при прокрутке
              const headerOffset = 100;
              const elementPosition = element.getBoundingClientRect().top;
              const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

              window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth',
              });
            }
            trackButtonClick('hero_learn_more');
          }}
          className="inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 font-semibold text-base sm:text-lg shadow-md hover:shadow-lg dark:hover:shadow-xl transition-all duration-300 border-2 border-gray-200 dark:border-slate-600 hover:border-blue-500 dark:hover:border-blue-400 active:bg-gray-50 dark:active:bg-slate-600 min-h-[44px] sm:min-h-[48px] touch-manipulation"
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
