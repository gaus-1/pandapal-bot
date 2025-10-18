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
    <section className="py-16 md:py-28 text-center min-h-[85vh] flex flex-col justify-center">
      {/* Основной заголовок (H1 для SEO) */}
      <h1 className="font-display text-5xl md:text-7xl font-bold leading-tight mb-6">
        Безопасный ИИ-друг
        <br />
        для твоего ребенка
      </h1>

      {/* Описание продукта */}
      <p className="mt-6 text-xl md:text-2xl text-gray-700 max-w-3xl mx-auto font-medium">
        Адаптивное обучение для детей 6-18 лет с AI-модерацией 24/7
      </p>

      {/* Подзаголовок с деталями */}
      <p className="mt-4 text-base md:text-lg text-gray-600 max-w-2xl mx-auto">
        Геймификация, персонализация и полная безопасность контента.
        Присоединяйся к тысячам семей, доверяющих PandaPal!
      </p>

      {/* Главные CTA-кнопки (Call To Action) */}
      <div className="mt-10 flex flex-col md:flex-row gap-4 justify-center">
        <a
          href={SITE_CONFIG.botUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="px-10 py-5 rounded-full bg-pink text-gray-900 font-semibold text-lg shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105 active:scale-100"
          aria-label="Начать использовать PandaPal в Telegram"
        >
          Начать бесплатно
        </a>
        <a
          href="/play"
          className="px-10 py-5 rounded-full bg-gradient-to-r from-green-400 to-blue-500 text-white font-semibold text-lg shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105 active:scale-100"
        >
          🎮 PandaPal Go
        </a>
        <a
          href="/docs"
          className="px-10 py-5 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold text-lg shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105 active:scale-100"
        >
          📚 Документация
        </a>
      </div>

      {/* Индикатор прокрутки (в стиле Montfort) */}
      <div className="mt-16 md:mt-20">
        <ScrollIndicator />
      </div>
    </section>
  );
});

// Для React DevTools
Hero.displayName = 'Hero';
