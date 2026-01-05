/**
 * Компонент Features (блок преимуществ)
 * Отображает сетку из карточек преимуществ продукта
 * @module components/Features
 */

import React from 'react';
import { FeatureCard } from './FeatureCard';
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
      className="w-full flex justify-center py-12"
      aria-label="Преимущества"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto px-4 w-full">
        {/* Рендерим карточки из массива FEATURES */}
        {FEATURES.map((feature, index) => (
          <div
            key={feature.id}
            className="animate-fade-in"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <FeatureCard feature={feature} />
          </div>
        ))}
      </div>
    </section>
  );
});

// Для React DevTools
Features.displayName = 'Features';
