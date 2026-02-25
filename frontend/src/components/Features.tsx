/**
 * Компонент Features (блок преимуществ)
 * Отображает сетку из карточек преимуществ продукта
 * @module components/Features
 */

import React from 'react';
import { FeatureCard } from './FeatureCard';
import { MiniAppScreenshotsCarousel } from './MiniAppScreenshotsCarousel';
import { FEATURES } from '../config/constants';

/**
 * Секция с преимуществами PandaPal
 * Адаптивная сетка: 1 колонка на мобильных, 3 на десктопе
 * Данные берутся из constants.ts для лёгкого редактирования
 */
export const Features: React.FC = React.memo(() => {
  return (
    <section
      id="features"
      className="w-full py-fib-5 sm:py-fib-6 lg:py-fib-7"
      aria-label="Преимущества"
    >
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-fib-4 sm:gap-fib-5 lg:gap-fib-5">
          {/* Рендерим карточки из массива FEATURES */}
          {FEATURES.map((feature, index) => (
            <div
              key={feature.id}
              className="animate-fade-in flex"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <FeatureCard feature={feature} />
            </div>
          ))}
        </div>

        <MiniAppScreenshotsCarousel />
      </div>
    </section>
  );
});

// Для React DevTools
Features.displayName = 'Features';
