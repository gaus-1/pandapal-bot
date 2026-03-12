import React from 'react';
import { Header } from '../../components';
import { HELP_CATEGORIES, getHelpArticlesByCategory } from '../../config/help-articles';

const navigateTo = (path: string) => {
  window.history.pushState(null, '', path);
  window.dispatchEvent(new Event('popstate'));
};

const linkClass =
  'rounded-lg border border-gray-200/80 dark:border-slate-600 bg-white/80 dark:bg-slate-900/40 px-fib-2 py-fib-1 min-h-[36px] flex items-center justify-center text-center text-xs sm:text-sm leading-snug text-gray-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-500 hover:bg-gray-50 dark:hover:bg-slate-800/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-800 transition-colors';

export const HelpCenterPage: React.FC = React.memo(() => {
  const categories = [...HELP_CATEGORIES].sort((a, b) => a.order - b.order);

  return (
    <>
      <Header />
      <main className="w-full max-w-4xl mx-auto px-fib-4 sm:px-fib-4 lg:px-fib-5 py-fib-5 sm:py-fib-6 lg:py-fib-6 flex flex-col items-center">
        <article className="w-full max-w-3xl mx-auto rounded-2xl sm:rounded-3xl bg-white/95 dark:bg-slate-800/95 border border-gray-100 dark:border-slate-600/60 px-fib-4 sm:px-fib-4 lg:px-fib-5 py-fib-4 sm:py-fib-5 lg:py-fib-5 shadow-lg dark:shadow-xl">
          <header className="mb-fib-4 sm:mb-fib-5 text-center">
            <h1 className="font-display text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-50">
              Вопросы и ответы
            </h1>
            <p className="mt-fib-2 text-sm sm:text-base text-gray-600 dark:text-slate-300 max-w-xl mx-auto leading-relaxed">
              Ответы на частые вопросы о PandaPal: начало работы, учёба, игры, Premium и безопасность.
            </p>
          </header>

          <nav className="space-y-fib-5" aria-label="Разделы помощи">
            {categories.map((cat) => {
              const articles = getHelpArticlesByCategory(cat.id);
              if (articles.length === 0) return null;
              return (
                <section key={cat.id} className="text-center">
                  <h2 className="font-display text-base sm:text-lg font-bold text-gray-900 dark:text-slate-50 mb-fib-3">
                    {cat.titleRu}
                  </h2>
                  <div className="flex flex-wrap justify-center gap-fib-2">
                    {articles.map((art) => (
                      <a
                        key={art.id}
                        href={`/help/${art.slug}`}
                        onClick={(e) => {
                          e.preventDefault();
                          navigateTo(`/help/${art.slug}`);
                        }}
                        className={linkClass}
                      >
                        {art.titleRu}
                      </a>
                    ))}
                  </div>
                </section>
              );
            })}
          </nav>
        </article>
      </main>
    </>
  );
});

HelpCenterPage.displayName = 'HelpCenterPage';
