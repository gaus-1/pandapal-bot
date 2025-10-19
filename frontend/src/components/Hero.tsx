/**
 * Компонент Hero (главная секция страницы)
 * Первое, что видит пользователь: заголовок, описание, CTA-кнопка
 * @module components/Hero
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';
import { ScrollIndicator } from './ScrollIndicator';

/**
 * Hero-секция с главным призывом к действию
 * Оптимизирована для конверсии: крупный заголовок + яркая кнопка + индикатор прокрутки
 */
export const Hero: React.FC = React.memo(() => {
  return (
    <section className="py-16 md:py-28 text-center">
      {/* Основной заголовок (H1 для SEO) */}
      <h1 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight mb-6">
        Безопасный ИИ-друг
        <br />
        для твоего ребенка
      </h1>

      {/* Описание продукта */}
      <p className="text-lg md:text-xl text-gray-700 max-w-2xl mx-auto mb-8">
        Адаптивное и безопасное обучение для 1-9 классов
      </p>

      {/* Главная CTA-кнопка (Call To Action) */}
      <div className="flex justify-center items-center">
        <a
          href={SITE_CONFIG.botUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="px-8 py-4 rounded-full bg-pink text-gray-900 font-semibold text-lg shadow-lg hover:shadow-xl transition-all duration-300"
          aria-label="Начать использовать PandaPal в Telegram"
        >
          Начать использовать
        </a>
      </div>

      {/* Индикатор прокрутки */}
      <div className="mt-16">
        <ScrollIndicator />
      </div>
    </section>
  );
});

// Для React DevTools
Hero.displayName = 'Hero';
