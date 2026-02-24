import React from 'react';
import { Header } from '../../components';
import {
  getHelpArticleBySlug,
  HELP_CATEGORIES,
  type HelpArticle,
  type HelpBodyBlock,
} from '../../config/help-articles';

const navigateTo = (path: string) => {
  window.history.pushState(null, '', path);
  window.dispatchEvent(new Event('popstate'));
};

const linkClass =
  'rounded-lg border border-gray-200/80 dark:border-slate-600 bg-white/80 dark:bg-slate-900/40 px-3 py-1.5 min-h-[36px] flex items-center justify-center text-center text-xs sm:text-sm leading-snug text-gray-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-500 transition-colors';

function renderBody(blocks: HelpBodyBlock[]) {
  return (
    <div className="space-y-3">
      {blocks.map((block, i) =>
        block.type === 'p' ? (
          <p
            key={i}
            className="text-xs sm:text-sm md:text-base text-gray-700 dark:text-slate-200 leading-[1.72]"
          >
            {block.text}
          </p>
        ) : (
          <ul key={i} className="list-disc list-inside space-y-1 text-xs sm:text-sm text-gray-700 dark:text-slate-200">
            {block.items.map((item, j) => (
              <li key={j}>{item}</li>
            ))}
          </ul>
        )
      )}
    </div>
  );
}

export const HelpArticlePage: React.FC = React.memo(() => {
  const pathname = typeof window !== 'undefined' ? window.location.pathname : '';
  const slug = pathname.startsWith('/help/') ? pathname.replace(/^\/help\/?/, '').split('/')[0] : '';
  const article = slug ? getHelpArticleBySlug(slug) : undefined;

  if (!article) {
    return (
      <>
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-12 lg:py-14">
          <article className="rounded-2xl sm:rounded-3xl bg-white/95 dark:bg-slate-800/95 border border-gray-100 dark:border-slate-600/60 p-6 sm:p-8 lg:p-10 shadow-lg dark:shadow-xl">
            <p className="text-sm text-gray-600 dark:text-slate-300">Статья не найдена.</p>
            <a
              href="/help"
              onClick={(e) => {
                e.preventDefault();
                navigateTo('/help');
              }}
              className="mt-4 inline-block text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              Вернуться в раздел помощи
            </a>
          </article>
        </main>
      </>
    );
  }

  const category = HELP_CATEGORIES.find((c) => c.id === article.categoryId);
  const relatedArticles: HelpArticle[] = (article.relatedSlugs || [])
    .map((s) => getHelpArticleBySlug(s))
    .filter((a): a is HelpArticle => a !== undefined);

  return (
    <>
      <Header />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-12 lg:py-14">
        <article className="rounded-2xl sm:rounded-3xl bg-white/95 dark:bg-slate-800/95 border border-gray-100 dark:border-slate-600/60 p-6 sm:p-8 lg:p-10 shadow-lg dark:shadow-xl">
          <nav className="text-xs sm:text-sm text-gray-500 dark:text-slate-400 mb-4" aria-label="Хлебные крошки">
            <a
              href="/"
              onClick={(e) => {
                e.preventDefault();
                navigateTo('/');
              }}
              className="hover:text-blue-600 dark:hover:text-blue-400"
            >
              Главная
            </a>
            <span className="mx-1">→</span>
            <a
              href="/help"
              onClick={(e) => {
                e.preventDefault();
                navigateTo('/help');
              }}
              className="hover:text-blue-600 dark:hover:text-blue-400"
            >
              Помощь
            </a>
            {category && (
              <>
                <span className="mx-1">→</span>
                <span>{category.titleRu}</span>
              </>
            )}
            <span className="mx-1">→</span>
            <span className="text-gray-700 dark:text-slate-200">{article.titleRu}</span>
          </nav>

          <header className="mb-5 sm:mb-6">
            <h1 className="font-display text-xl sm:text-2xl md:text-3xl font-bold text-gray-900 dark:text-slate-50">
              {article.titleRu}
            </h1>
          </header>

          <section className="space-y-4">{renderBody(article.bodyRu)}</section>

          {(relatedArticles.length > 0 || (article.relatedIntentPaths && article.relatedIntentPaths.length > 0)) && (
            <section className="mt-7 sm:mt-8">
              <h2 className="font-display text-lg sm:text-xl font-bold text-gray-900 dark:text-slate-50 mb-3">
                См. также
              </h2>
              <div className="flex flex-wrap gap-2">
                {relatedArticles.map((a) => (
                  <a
                    key={a.id}
                    href={`/help/${a.slug}`}
                    onClick={(e) => {
                      e.preventDefault();
                      navigateTo(`/help/${a.slug}`);
                    }}
                    className={linkClass}
                  >
                    {a.titleRu}
                  </a>
                ))}
                {article.relatedIntentPaths?.map(({ path, labelRu }) => (
                  <a
                    key={path}
                    href={path}
                    onClick={(e) => {
                      e.preventDefault();
                      navigateTo(path);
                    }}
                    className={linkClass}
                  >
                    {labelRu}
                  </a>
                ))}
              </div>
            </section>
          )}
        </article>
      </main>
    </>
  );
});

HelpArticlePage.displayName = 'HelpArticlePage';
