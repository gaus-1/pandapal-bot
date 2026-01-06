/**
 * Компонент Section (универсальная секция контента)
 * Переиспользуемый компонент для блоков "Для родителей", "Для учителей" и т.д.
 * @module components/Section
 */

import React from 'react';
import type { Section as SectionType } from '../types';

/**
 * Props для компонента Section
 */
interface SectionProps {
  /** Данные секции (заголовок, описание, ID) */
  section: SectionType;
}

/**
 * Универсальная секция контента с полупрозрачным фоном
 * ID используется как якорь для навигации (#parents, #teachers)
 * Легко добавлять новые секции через SECTIONS в constants.ts
 */
export const Section: React.FC<SectionProps> = React.memo(({ section }) => {
  return (
    <section id={section.id} className="py-12 md:py-16">
      {/* Контейнер с профессиональным дизайном */}
      <div className="rounded-3xl bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 dark:border-slate-600/50 p-8 md:p-12 shadow-lg dark:shadow-xl hover:shadow-xl dark:hover:shadow-2xl transition-shadow duration-300 text-center">
        {/* Заголовок секции */}
        <h2 className="font-display text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold mb-6 text-gray-900 dark:text-slate-50">
          {section.title}
        </h2>

        {/* Текст описания */}
        <p className="text-sm sm:text-base md:text-lg text-gray-700 dark:text-slate-200 max-w-3xl leading-relaxed mx-auto">
          {section.description}
        </p>
      </div>
    </section>
  );
});

// Для React DevTools
Section.displayName = 'Section';
