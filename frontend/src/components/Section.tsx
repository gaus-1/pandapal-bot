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

interface DescriptionGroup {
  title: string;
  items: string[];
}

const splitLeadAndBody = (text: string): { lead: string; body: string } => {
  const separator = ' — ';
  const idx = text.indexOf(separator);
  if (idx === -1) {
    return { lead: text, body: '' };
  }
  return {
    lead: text.slice(0, idx),
    body: text.slice(idx + separator.length),
  };
};

const buildBenefitsGroups = (items: string[]): DescriptionGroup[] => {
  const safeSlice = (start: number, end: number) => items.slice(start, Math.min(end, items.length));

  return [
    { title: 'Учеба каждый день', items: safeSlice(0, 4) },
    { title: 'Форматы и предметы', items: safeSlice(4, 7) },
    { title: 'Мотивация и безопасность', items: safeSlice(7, 10) },
    { title: 'Важное и доступ', items: safeSlice(10, 13) },
  ].filter((group) => group.items.length > 0);
};

/**
 * Универсальная секция контента с полупрозрачным фоном
 * ID используется как якорь для навигации (#parents, #teachers)
 * Легко добавлять новые секции через SECTIONS в constants.ts
 */
export const Section: React.FC<SectionProps> = React.memo(({ section }) => {
  const descriptionItems = Array.isArray(section.description) ? section.description : null;
  const isDescriptionList = descriptionItems !== null;
  const isBenefitsSection = section.id === 'benefits' && isDescriptionList;
  const benefitsGroups = isBenefitsSection ? buildBenefitsGroups(descriptionItems) : [];

  return (
    <section id={section.id} className="py-fib-5 sm:py-fib-6 lg:py-fib-7">
      {/* Контейнер с профессиональным дизайном */}
      <div className="max-w-6xl mx-auto">
        <div className="rounded-2xl sm:rounded-3xl bg-white/95 dark:bg-slate-800/95 border border-gray-100 dark:border-slate-600/60 p-fib-4 sm:p-fib-5 lg:p-fib-5 shadow-lg dark:shadow-xl hover:shadow-xl dark:hover:shadow-2xl transition-shadow duration-300 text-center">
          {/* Заголовок секции */}
          <h2 className="font-display text-lg sm:text-2xl md:text-3xl lg:text-4xl font-bold mb-fib-4 sm:mb-fib-5 lg:mb-fib-5 text-gray-900 dark:text-slate-50">
            {section.title}
          </h2>

          {/* Текст описания */}
          <div className="text-sm sm:text-base md:text-lg text-gray-700 dark:text-slate-200 max-w-5xl leading-relaxed mx-auto">
            {isDescriptionList ? (
              isBenefitsSection ? (
                <div className="text-left">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-fib-4 sm:gap-fib-5 lg:gap-fib-5">
                    {benefitsGroups.map((group) => (
                      <div
                        key={group.title}
                        className="rounded-xl sm:rounded-2xl border border-slate-200/80 dark:border-slate-600/70 bg-slate-50/80 dark:bg-slate-900/35 p-fib-4 sm:p-fib-4 lg:p-fib-5"
                      >
                        <h3 className="font-display text-sm sm:text-lg font-bold text-slate-900 dark:text-slate-100 mb-fib-2 sm:mb-fib-3">
                          {group.title}
                        </h3>

                        <ul className="m-0 p-0 space-y-fib-2 sm:space-y-fib-3">
                          {group.items.map((item, index) => {
                            const { lead, body } = splitLeadAndBody(item);
                            return (
                              <li
                                key={`${group.title}-${index}`}
                                className="flex items-start gap-fib-2 sm:gap-fib-3 list-none"
                              >
                                <span
                                  aria-hidden="true"
                                  className="mt-[0.58em] h-1.5 w-1.5 rounded-full bg-blue-500 dark:bg-blue-400 flex-shrink-0"
                                />
                                <span className="text-slate-700 dark:text-slate-200 break-words leading-relaxed">
                                  <span className="font-semibold text-slate-900 dark:text-slate-100">
                                    {lead}
                                  </span>
                                  {body ? ` — ${body}` : ''}
                                </span>
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <ul className="text-left m-0 p-0 space-y-fib-3 sm:space-y-fib-4 lg:space-y-fib-5">
                  {descriptionItems.map((item, index) => (
                    <li key={index} className="flex items-start gap-fib-2 sm:gap-fib-3 list-none">
                      <span
                        aria-hidden="true"
                        className="mt-[0.62em] h-1.5 w-1.5 rounded-full bg-blue-500 dark:bg-blue-400 flex-shrink-0"
                      />
                      <span className="leading-[1.68] break-words text-slate-700 dark:text-slate-200">
                        {item}
                      </span>
                    </li>
                  ))}
                </ul>
              )
            ) : (
              <p>{section.description}</p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
});

// Для React DevTools
Section.displayName = 'Section';
