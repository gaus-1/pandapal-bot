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
    <section className="pt-24 sm:pt-28 md:pt-32 pb-12 sm:pb-16 md:pb-20 text-center px-4">
      {/* Schema.org для SEO */}
      <script type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          "name": "PandaPal",
          "applicationCategory": "EducationalApplication",
          "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "RUB"
          },
          "operatingSystem": "Telegram",
          "description": "Безопасный ИИ-ассистент для обучения школьников 1-9 классов",
          "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.9",
            "ratingCount": "150"
          }
        })}
      </script>

      {/* Основной заголовок (H1 для SEO) */}
      <h1 className="font-display text-2xl sm:text-4xl md:text-5xl lg:text-6xl font-bold leading-tight animate-fade-in text-gray-900 dark:text-slate-50 px-4">
        Безопасный ИИ-друг
        <br />
        для твоего ребенка
      </h1>

      {/* Описание продукта */}
      <p className="mt-4 sm:mt-6 text-sm sm:text-lg md:text-xl text-gray-700 dark:text-slate-300 max-w-2xl mx-auto animate-fade-in-delay px-4">
        Адаптивное, игровое и безопасное обучение для 1–9 классов
      </p>

      {/* CTA кнопки */}
      <div className="mt-6 sm:mt-8 flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center items-stretch sm:items-center animate-fade-in-delay-2 px-4">
        {/* Основная CTA */}
        <a
          href={SITE_CONFIG.botUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => trackButtonClick('hero_start_bot')}
          className="inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 font-semibold text-base sm:text-lg shadow-md hover:shadow-lg transition-all duration-300 border-2 border-gray-200 dark:border-slate-600 hover:border-blue-500 dark:hover:border-blue-400"
          aria-label="Начать использовать PandaPal в Telegram"
          data-cta-variant="primary"
        >
          Начни
        </a>

        {/* Вторичная CTA */}
        <a
          href="#cta"
          className="inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 font-semibold text-base sm:text-lg shadow-md hover:shadow-lg transition-all duration-300 border-2 border-gray-200 dark:border-slate-600 hover:border-blue-500 dark:hover:border-blue-400"
          aria-label="Узнать больше о PandaPal"
          data-cta-variant="secondary"
        >
          Узнать больше
        </a>
      </div>
    </section>
  );
});

// Для React DevTools
Hero.displayName = 'Hero';
