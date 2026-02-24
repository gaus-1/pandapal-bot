import React from 'react';
import { Header } from '../../components';
import { HELP_CATEGORIES, getHelpArticlesByCategory } from '../../config/help-articles';

const navigateTo = (path: string) => {
  window.history.pushState(null, '', path);
  window.dispatchEvent(new Event('popstate'));
};

const linkClass =
  'rounded-lg border border-gray-200/80 dark:border-slate-600 bg-white/80 dark:bg-slate-900/40 px-3 py-1.5 min-h-[36px] flex items-center justify-center text-left text-xs sm:text-sm leading-snug text-gray-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-500 transition-colors';

export const HelpCenterPage: React.FC = React.memo(() => {
  const categories = [...HELP_CATEGORIES].sort((a, b) => a.order - b.order);

  return (
    <>
      <Header />
      <main className="w-full min-h-[calc(100vh-4rem)] box-border flex flex-col items-center justify-center px-3 xs:px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10 lg:py-12 overflow-x-hidden">
        <article className="w-full max-w-2xl min-w-0 mx-auto rounded-2xl sm:rounded-3xl bg-white/95 dark:bg-slate-800/95 border border-gray-100 dark:border-slate-600/60 shadow-lg dark:shadow-xl px-4 xs:px-5 sm:px-6 md:px-8 py-5 sm:py-6 md:py-8 lg:py-9">
          <header className="mb-6 sm:mb-7 text-center">
            <h1 className="font-display text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-50">
              Вопросы и ответы
            </h1>
            <p className="mt-2 text-xs sm:text-sm text-gray-600 dark:text-slate-300 max-w-xl mx-auto px-0">
              Ответы на частые вопросы о PandaPal: начало работы, учёба, игры, Premium и безопасность.
            </p>
          </header>

          <nav className="space-y-5 sm:space-y-6" aria-label="Разделы помощи">
            {categories.map((cat) => {
              const articles = getHelpArticlesByCategory(cat.id);
              if (articles.length === 0) return null;
              return (
                <section key={cat.id} className="w-full">
                  <h2 className="font-display text-base sm:text-lg font-bold text-gray-900 dark:text-slate-50 mb-3">
                    {cat.titleRu}
                  </h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 w-full">
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
