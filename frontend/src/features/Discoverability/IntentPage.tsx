import React from 'react';
import { Header } from '../../components';

interface FaqItem {
  question: string;
  answer: string;
}

interface IntentPageProps {
  title: string;
  subtitle: string;
  description: string;
  botCta: string;
  canonicalPath: string;
  locale: 'ru' | 'en';
  faq: FaqItem[];
  /** Прямая ссылка на экран в Mini App (например тамагочи) — отображается второй кнопкой */
  directLinkUrl?: string;
  directLinkLabel?: string;
}

export const IntentPage: React.FC<IntentPageProps> = React.memo(
  ({ title, subtitle, description, botCta, canonicalPath, locale, faq, directLinkUrl, directLinkLabel }) => {
    const faqSchema = {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      url: `https://pandapal.ru${canonicalPath}`,
      inLanguage: locale,
      mainEntity: faq.map((item) => ({
        '@type': 'Question',
        name: item.question,
        acceptedAnswer: {
          '@type': 'Answer',
          text: item.answer,
        },
      })),
    };

    return (
      <>
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-12 lg:py-14">
          <article className="rounded-2xl sm:rounded-3xl bg-white/95 dark:bg-slate-800/95 border border-gray-100 dark:border-slate-600/60 p-6 sm:p-8 lg:p-10 shadow-lg dark:shadow-xl">
            <header className="mb-5 sm:mb-6">
              <h1 className="font-display text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-50">
                {title}
              </h1>
              <p className="mt-2 text-sm sm:text-base text-gray-600 dark:text-slate-300 leading-relaxed">{subtitle}</p>
            </header>

            <section className="space-y-4">
              <p className="text-sm sm:text-base text-gray-700 dark:text-slate-200 leading-relaxed">
                {description}
              </p>

              <p className="text-sm sm:text-base text-gray-700 dark:text-slate-200 leading-relaxed">
                Официальный сайт: <a className="text-blue-600 dark:text-blue-400 hover:underline" href="https://pandapal.ru">pandapal.ru</a>.{' '}
                Официальный бот: <a className="text-blue-600 dark:text-blue-400 hover:underline" href="https://t.me/PandaPalBot" target="_blank" rel="noopener noreferrer">@PandaPalBot</a>.
              </p>
            </section>

            <section className="mt-7 sm:mt-8">
              <h2 className="font-display text-base sm:text-lg md:text-xl font-bold text-gray-900 dark:text-slate-50 mb-4">
                Частые вопросы
              </h2>
              <div className="space-y-4">
                {faq.map((item) => (
                  <div key={item.question} className="rounded-xl border border-gray-200 dark:border-slate-600 p-4 sm:p-5">
                    <h3 className="font-display font-bold text-sm sm:text-base text-gray-900 dark:text-slate-100 mb-1.5">{item.question}</h3>
                    <p className="text-xs sm:text-sm text-gray-700 dark:text-slate-200 leading-relaxed">{item.answer}</p>
                  </div>
                ))}
              </div>
            </section>

            <div className="mt-7 sm:mt-8 flex flex-wrap gap-3 justify-center">
              <a
                href="https://t.me/PandaPalBot"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center px-6 py-3 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold text-xs sm:text-sm hover:opacity-90 transition-opacity"
              >
                {botCta}
              </a>
              {directLinkUrl && directLinkLabel && (
                <a
                  href={directLinkUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center px-6 py-3 rounded-full border-2 border-blue-500 dark:border-cyan-500 text-blue-600 dark:text-cyan-400 font-semibold text-xs sm:text-sm hover:bg-blue-50 dark:hover:bg-slate-700/50 transition-colors"
                >
                  {directLinkLabel}
                </a>
              )}
            </div>
          </article>
        </main>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
        />
      </>
    );
  }
);

IntentPage.displayName = 'IntentPage';
