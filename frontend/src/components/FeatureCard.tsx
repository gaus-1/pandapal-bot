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
      <article className="rounded-2xl bg-white/80 backdrop-blur p-6 shadow-sm hover:shadow-md transition-shadow duration-200">
        {/* Заголовок преимущества */}
        <h3 className="font-display text-xl font-semibold mb-2">
          {feature.title}
        </h3>

        {/* Описание преимущества */}
        <p className="text-gray-700">{feature.description}</p>
      </article>
    );
  }
);

// Для React DevTools
FeatureCard.displayName = 'FeatureCard';
