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
    <section className="pt-24 sm:pt-28 md:pt-32 pb-12 sm:pb-16 md:pb-20 text-center">
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
          "description": "Безопасный AI-ассистент для обучения школьников 1-9 классов",
          "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.9",
            "ratingCount": "150"
          }
        })}
      </script>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8">
        {/* Основной заголовок (H1 для SEO) */}
        <h1 className="font-display text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold leading-tight animate-fade-in text-gray-900 dark:text-slate-50 group cursor-default">
          <span className="inline-block">
            {'Безопасный AI-друг'.split('').map((char, index) => (
              <span
                key={index}
                className="inline-block hover-letter-bounce"
                style={{ animationDelay: `${index * 0.02}s` }}
              >
                {char === ' ' ? '\u00A0' : char}
              </span>
            ))}
          </span>
          <br />
          <span className="inline-block">
            {'для твоего ребенка'.split('').map((char, index) => (
              <span
                key={index + 20}
                className="inline-block hover-letter-bounce"
                style={{ animationDelay: `${(index + 20) * 0.02}s` }}
              >
                {char === ' ' ? '\u00A0' : char}
              </span>
            ))}
          </span>
        </h1>

        {/* Описание продукта */}
        <p className="mt-4 sm:mt-6 text-sm sm:text-base md:text-lg text-gray-700 dark:text-slate-200 max-w-2xl mx-auto animate-fade-in-delay">
          Адаптивное, игровое, безопасное обучение и общение детей 1–9 классов
        </p>

        {/* CTA кнопки */}
        <div className="mt-6 sm:mt-8 flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center items-stretch sm:items-center animate-fade-in-delay-2">
        {/* Основная CTA */}
        <a
          href={SITE_CONFIG.botUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => trackButtonClick('hero_start_bot')}
          className="inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 font-semibold text-base sm:text-lg shadow-md hover:shadow-lg dark:hover:shadow-xl transition-all duration-300 border-2 border-gray-200 dark:border-slate-600 hover:border-blue-500 dark:hover:border-blue-400 active:bg-gray-50 dark:active:bg-slate-600"
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
          className="inline-flex items-center justify-center px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 font-semibold text-base sm:text-lg shadow-md hover:shadow-lg dark:hover:shadow-xl transition-all duration-300 border-2 border-gray-200 dark:border-slate-600 hover:border-blue-500 dark:hover:border-blue-400 active:bg-gray-50 dark:active:bg-slate-600"
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
