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
        <main className="max-w-2xl mx-auto px-4 sm:px-6 md:px-8 pt-6 xs:pt-7 sm:pt-8 pb-2 xs:pb-3 sm:pb-4 md:pb-5">
          <article className="bg-white dark:bg-slate-800 rounded-xl xs:rounded-2xl sm:rounded-2.5xl border border-gray-100 dark:border-slate-700 dark:border-slate-600/50 shadow-md dark:shadow-lg p-3.5 xs:p-4 sm:p-5 md:p-6 lg:p-7">
            <header className="mb-3 xs:mb-4 sm:mb-5">
              <h1 className="font-display text-sm xs:text-base sm:text-lg md:text-xl font-bold text-gray-900 dark:text-slate-50">
                {title}
              </h1>
              {subtitle && (
                <p className="mt-1 text-[9px] sm:text-[10px] text-gray-600 dark:text-slate-400">
                  {subtitle}
                </p>
              )}
              <p className="mt-1 text-[9px] sm:text-[10px] text-gray-500 dark:text-slate-500">
                {SITE_CONFIG.name} · актуально с 03.01.2026
              </p>
            </header>
            <div className="font-sans text-[9px] sm:text-[10px] text-gray-700 dark:text-slate-200 leading-relaxed space-y-2 max-w-none [&_h2]:font-display [&_h2]:font-bold [&_h2]:text-[10px] sm:[&_h2]:text-[11px] [&_h2]:text-gray-900 dark:[&_h2]:text-slate-50 [&_h2]:mt-3">
              {children}
            </div>
          </article>
        </main>
      </>
    );
  }
);
LegalPageLayout.displayName = 'LegalPageLayout';
