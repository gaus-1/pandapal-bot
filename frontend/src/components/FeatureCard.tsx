/**
 * Компонент FeatureCard (карточка преимущества)
 * Переиспользуемая карточка для отображения одного преимущества продукта
 * @module components/FeatureCard
 */

import React from 'react';
import type { Feature } from '../types';

/**
 * Props для компонента FeatureCard
 */
interface FeatureCardProps {
  /** Данные преимущества (заголовок, описание) */
  feature: Feature;
}

/**
 * Карточка преимущества с hover-эффектом
 * Используется в компоненте Features для отображения списка преимуществ
 * Мемоизирована для оптимизации производительности
 */
export const FeatureCard: React.FC<FeatureCardProps> = React.memo(
  ({ feature }) => {
    return (
      <article className="rounded-2xl bg-white dark:bg-slate-800 p-6 shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-100 dark:border-slate-700">
        {/* Заголовок преимущества */}
        <h3 className="font-display text-xl font-bold mb-3 text-gray-900 dark:text-slate-100">
          {feature.title}
        </h3>

        {/* Описание преимущества */}
        <p className="text-gray-700 dark:text-slate-300 leading-relaxed">
          {feature.description}
        </p>
      </article>
    );
  }
);

// Для React DevTools
FeatureCard.displayName = 'FeatureCard';
