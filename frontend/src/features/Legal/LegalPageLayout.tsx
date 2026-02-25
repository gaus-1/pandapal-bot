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
        <main className="max-w-3xl mx-auto px-fib-4 sm:px-fib-4 lg:px-fib-5 py-fib-5 sm:py-fib-6 lg:py-fib-6">
          <article className="bg-white dark:bg-slate-800 rounded-2xl sm:rounded-3xl border border-gray-100 dark:border-slate-700 dark:border-slate-600/50 shadow-md dark:shadow-lg p-fib-4 sm:p-fib-5 lg:p-fib-5">
            <header className="mb-fib-5 sm:mb-fib-5">
              <h1 className="font-display text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-50">
                {title}
              </h1>
              {subtitle && (
                <p className="mt-2 text-xs sm:text-sm text-gray-600 dark:text-slate-400">
                  {subtitle}
                </p>
              )}
              <p className="mt-1.5 text-xs sm:text-sm text-gray-500 dark:text-slate-500">
                {SITE_CONFIG.name} · актуально с 03.01.2026
              </p>
            </header>
            <div className="text-xs sm:text-sm text-gray-700 dark:text-slate-200 leading-relaxed space-y-fib-4 sm:space-y-fib-5 max-w-none [&_h2]:font-display [&_h2]:font-bold [&_h2]:text-sm sm:[&_h2]:text-base [&_h2]:text-gray-900 dark:[&_h2]:text-slate-50 [&_h2]:mt-6">
              {children}
            </div>
          </article>
        </main>
      </>
    );
  }
);
LegalPageLayout.displayName = 'LegalPageLayout';
