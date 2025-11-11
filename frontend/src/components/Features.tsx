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
      className="grid md:grid-cols-3 gap-6 py-12"
      aria-label="Преимущества"
    >
      {/* Рендерим карточки из массива FEATURES */}
      {FEATURES.map((feature) => (
        <FeatureCard key={feature.id} feature={feature} />
      ))}
    </section>
  );
});

// Для React DevTools
Features.displayName = 'Features';
