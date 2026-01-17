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
    <section id={section.id} className="py-8 xs:py-10 sm:py-12 md:py-14 lg:py-16">
      {/* Контейнер с профессиональным дизайном */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="rounded-2xl xs:rounded-2.5xl sm:rounded-3xl bg-white dark:bg-slate-800 border border-gray-100 dark:border-slate-700 dark:border-slate-600/50 p-4 xs:p-5 sm:p-6 md:p-8 lg:p-12 shadow-lg dark:shadow-xl hover:shadow-xl dark:hover:shadow-2xl transition-shadow duration-300 text-center">
          {/* Заголовок секции */}
          <h2 className="font-display text-lg xs:text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold mb-4 xs:mb-5 sm:mb-6 md:mb-7 lg:mb-8 text-gray-900 dark:text-slate-50">
            {section.title}
          </h2>

          {/* Текст описания */}
          <div className="text-xs xs:text-sm sm:text-base md:text-lg text-gray-700 dark:text-slate-200 max-w-3xl leading-relaxed mx-auto space-y-2.5 xs:space-y-2.5 sm:space-y-3 md:space-y-4">
            {Array.isArray(section.description) ? (
              <ul className="text-left space-y-2 xs:space-y-2 sm:space-y-2.5 md:space-y-3 list-none pl-0 m-0" style={{ listStyle: 'none', listStyleType: 'none', WebkitPaddingStart: 0, MozPaddingStart: 0, paddingLeft: 0, marginLeft: 0 }}>
                {section.description.map((item, index) => (
                  <li key={index} className="flex items-start gap-2 xs:gap-2 sm:gap-2.5 md:gap-3 list-none" style={{ listStyle: 'none', listStyleType: 'none', marginLeft: 0, paddingLeft: 0, WebkitPaddingStart: 0, MozPaddingStart: 0 }}>
                    <span className="text-blue-500 dark:text-blue-400 font-bold mt-0.5 xs:mt-0.5 sm:mt-0.5 md:mt-1 flex-shrink-0 text-base xs:text-base sm:text-lg md:text-xl">•</span>
                    <span className="flex-1 leading-snug xs:leading-normal sm:leading-relaxed font-sans">{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="font-sans">{section.description}</p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
});

// Для React DevTools
Section.displayName = 'Section';
