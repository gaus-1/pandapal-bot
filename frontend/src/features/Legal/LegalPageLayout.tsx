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
        <main className="max-w-3xl mx-auto px-4 sm:px-6 md:px-8 py-6 xs:py-8 sm:py-10 md:py-12">
          <article className="bg-white dark:bg-slate-800 rounded-2xl xs:rounded-2.5xl sm:rounded-3xl border border-gray-100 dark:border-slate-700 dark:border-slate-600/50 shadow-lg dark:shadow-xl p-4 xs:p-5 sm:p-6 md:p-8 lg:p-10">
            <header className="mb-4 xs:mb-5 sm:mb-6">
              <h1 className="font-display text-base xs:text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-50">
                {title}
              </h1>
              {subtitle && (
                <p className="mt-1.5 text-[10px] sm:text-[11px] text-gray-600 dark:text-slate-400">
                  {subtitle}
                </p>
              )}
              <p className="mt-1 text-[9px] sm:text-[10px] text-gray-500 dark:text-slate-500">
                {SITE_CONFIG.name} · актуально с 03.01.2026
              </p>
            </header>
            <div className="font-sans text-[10px] sm:text-[11px] text-gray-700 dark:text-slate-200 leading-relaxed space-y-2.5 max-w-none">
              {children}
            </div>
          </article>
        </main>
      </>
    );
  }
);
LegalPageLayout.displayName = 'LegalPageLayout';
