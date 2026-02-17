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
        <main className="max-w-3xl mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10 md:py-12">
          <article className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 dark:border-slate-600/50 shadow-lg dark:shadow-xl p-6 sm:p-8 md:p-10">
            <header className="mb-6 sm:mb-8">
              <h1 className="font-display text-xl sm:text-2xl md:text-3xl font-bold text-gray-900 dark:text-slate-50">
                {title}
              </h1>
              {subtitle && (
                <p className="mt-2 text-sm sm:text-base text-gray-600 dark:text-slate-400">
                  {subtitle}
                </p>
              )}
              <p className="mt-2 text-xs text-gray-500 dark:text-slate-500">
                {SITE_CONFIG.name} · актуально с 03.01.2026
              </p>
            </header>
            <div className="prose prose-sm sm:prose-base max-w-none text-gray-700 dark:text-slate-200 leading-relaxed space-y-4">
              {children}
            </div>
          </article>
        </main>
      </>
    );
  }
);
LegalPageLayout.displayName = 'LegalPageLayout';
