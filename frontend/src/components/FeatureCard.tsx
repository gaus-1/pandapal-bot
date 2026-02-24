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
      <article className="w-full rounded-2xl bg-white dark:bg-slate-800 p-9 sm:p-10 md:p-12 shadow-md hover:shadow-xl dark:hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-100 dark:border-slate-700 hover:border-gray-200 dark:hover:border-slate-600 flex flex-col h-full">
        {/* Заголовок преимущества */}
        <h3 className="font-display text-xl sm:text-2xl md:text-2xl font-bold mb-3 sm:mb-4 text-gray-900 dark:text-slate-100">
          {feature.title}
        </h3>

        {/* Описание преимущества */}
        <p className="text-base sm:text-lg md:text-lg text-gray-700 dark:text-slate-200 leading-relaxed flex-grow">
          {feature.description}
        </p>
      </article>
    );
  }
);

// Для React DevTools
FeatureCard.displayName = 'FeatureCard';
