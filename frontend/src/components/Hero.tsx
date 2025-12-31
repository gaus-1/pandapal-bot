/**
 * Компонент Hero (главная секция страницы)
 * Первое, что видит пользователь: заголовок, описание, CTA-кнопка
 * @module components/Hero
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';

/**
 * Hero-секция с главным призывом к действию
 * Оптимизирована для конверсии: крупный заголовок + яркие CTA
 */
export const Hero: React.FC = React.memo(() => {
  return (
    <section className="py-12 md:py-20 text-center">
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
      <h1 className="font-display text-4xl md:text-6xl font-bold leading-tight animate-fade-in">
        Безопасный ИИ-друг
        <br />
        для твоего ребенка
      </h1>

      {/* Описание продукта */}
      <p className="mt-6 text-lg md:text-xl text-gray-700 max-w-2xl mx-auto animate-fade-in-delay">
        Адаптивное, игровое и безопасное обучение для 1–9 классов
      </p>

      {/* CTA кнопки (A/B тест: 2 варианта) */}
      <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center items-center animate-fade-in-delay-2">
        {/* Основная CTA - вариант A (розовая) */}
        <a
          href={SITE_CONFIG.botUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block px-8 py-4 rounded-full bg-pink text-gray-900 font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 active:scale-100 hover:-translate-y-1"
          aria-label="Начать использовать PandaPal в Telegram"
          data-cta-variant="primary"
        >
          🐼 Начать бесплатно
        </a>

        {/* Вторичная CTA - узнать больше */}
        <a
          href="#features"
          className="inline-block px-8 py-4 rounded-full bg-white text-gray-900 font-semibold shadow-md hover:shadow-lg transition-all duration-300 border-2 border-gray-200 hover:border-pink"
          aria-label="Узнать больше о PandaPal"
          data-cta-variant="secondary"
        >
          Узнать больше
        </a>
      </div>

      {/* Social proof */}
      <p className="mt-6 text-sm text-gray-500 animate-fade-in-delay-3">
        ✨ Уже помогли <strong>150+ семьям</strong> в обучении детей
      </p>
    </section>
  );
});

// Для React DevTools
Hero.displayName = 'Hero';
