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
      {/* Контейнер с закруглёнными углами и размытым фоном */}
      <div className="rounded-2xl bg-white/60 backdrop-blur p-8 md:p-12">
        {/* Заголовок секции (H2 для иерархии) */}
        <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">
          {section.title}
        </h2>

        {/* Текст описания */}
        <p className="text-lg text-gray-700 max-w-3xl">
          {section.description}
        </p>
      </div>
    </section>
  );
});

// Для React DevTools
Section.displayName = 'Section';

