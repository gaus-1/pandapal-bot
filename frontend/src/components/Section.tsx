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
          <div className="text-xs xs:text-sm sm:text-base md:text-lg text-gray-700 dark:text-slate-200 max-w-3xl leading-relaxed mx-auto">
            {Array.isArray(section.description) ? (
              <ul className="text-left space-y-2.5 xs:space-y-3 sm:space-y-3.5 md:space-y-4 list-none pl-0 m-0">
                {section.description.map((item, index) => (
                  <li
                    key={index}
                    className="flex items-baseline gap-2.5 xs:gap-3 sm:gap-3.5 md:gap-4 list-none"
                  >
                    <span
                      className="text-blue-500 dark:text-blue-400 font-bold flex-shrink-0 leading-none"
                      style={{
                        fontSize: '0.75em',
                        lineHeight: '1.6',
                        verticalAlign: 'baseline'
                      }}
                    >
                      •
                    </span>
                    <span className="flex-1 leading-relaxed font-sans text-left break-words">
                      {item}
                    </span>
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
