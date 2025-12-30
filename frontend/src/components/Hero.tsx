/**
 * Компонент Hero (главная секция страницы)
 * Первое, что видит пользователь: заголовок, описание, CTA-кнопка
 * @module components/Hero
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';

/**
 * Hero-секция с главным призывом к действию
 * Оптимизирована для конверсии: крупный заголовок + яркая кнопка
 */
export const Hero: React.FC = React.memo(() => {
  return (
    <section className="py-12 md:py-20 text-center">
      {/* Основной заголовок (H1 для SEO) */}
      <h1 className="font-display text-4xl md:text-6xl font-bold leading-tight">
        Безопасный ИИ-друг
        <br />
        для твоего ребенка
      </h1>

      {/* Описание продукта */}
      <p className="mt-6 text-lg md:text-xl text-gray-700 max-w-2xl mx-auto">
        Адаптивное, игровое и безопасное обучение для 1–9 классов
      </p>

      {/* Главная CTA-кнопка (Call To Action) */}
      <div className="mt-8">
        <a
          href={SITE_CONFIG.botUrl}
          target="_blank" // Открывается в новой вкладке
          rel="noopener noreferrer" // Защита от tabnabbing
          className="inline-block px-8 py-4 rounded-full bg-pink text-gray-900 font-semibold shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 active:scale-100"
          aria-label="Начать использовать PandaPal в Telegram"
        >
          Начать использовать
        </a>
      </div>
    </section>
  );
});

// Для React DevTools
Hero.displayName = 'Hero';
