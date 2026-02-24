/**
 * Общий layout для страниц юридических документов.
 * Единый стиль: карточка, типографика, светлая/тёмная тема.
 */

import React from 'react';
import { Header } from '../../components';
import { SITE_CONFIG } from '../../config/constants';

interface LegalPageLayoutProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

export const LegalPageLayout: React.FC<LegalPageLayoutProps> = React.memo(
  ({ title, subtitle, children }) => {
    return (
      <>
        <Header />
        <main className="max-w-3xl mx-auto px-4 sm:px-6 md:px-8 pt-6 xs:pt-7 sm:pt-8 pb-4 sm:pb-6 md:pb-8">
          <article className="bg-white dark:bg-slate-800 rounded-xl xs:rounded-2xl sm:rounded-3xl border border-gray-100 dark:border-slate-700 dark:border-slate-600/50 shadow-md dark:shadow-lg p-4 xs:p-5 sm:p-6 md:p-7 lg:p-8">
            <header className="mb-5 sm:mb-6">
              <h1 className="font-display text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-50">
                {title}
              </h1>
              {subtitle && (
                <p className="mt-2 text-[11px] sm:text-xs text-gray-600 dark:text-slate-400">
                  {subtitle}
                </p>
              )}
              <p className="mt-1.5 text-[11px] sm:text-xs text-gray-500 dark:text-slate-500">
                {SITE_CONFIG.name} · актуально с 03.01.2026
              </p>
            </header>
            <div className="font-sans text-[11px] sm:text-xs md:text-sm text-gray-700 dark:text-slate-200 leading-[1.75] space-y-4 sm:space-y-5 max-w-none [&_h2]:font-display [&_h2]:font-bold [&_h2]:text-xs sm:[&_h2]:text-sm md:[&_h2]:text-base [&_h2]:text-gray-900 dark:[&_h2]:text-slate-50 [&_h2]:mt-6">
              {children}
            </div>
          </article>
        </main>
      </>
    );
  }
);
LegalPageLayout.displayName = 'LegalPageLayout';
