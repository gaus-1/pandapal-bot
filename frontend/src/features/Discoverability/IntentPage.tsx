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
  faq: FaqItem[];
}

export const IntentPage: React.FC<IntentPageProps> = React.memo(
  ({ title, subtitle, description, botCta, faq }) => {
    return (
      <>
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10">
          <article className="rounded-2xl sm:rounded-3xl bg-white/95 dark:bg-slate-800/95 border border-gray-100 dark:border-slate-600/60 p-5 sm:p-7 md:p-8 shadow-lg dark:shadow-xl">
            <header className="mb-5 sm:mb-6">
              <h1 className="font-display text-xl sm:text-2xl md:text-3xl font-bold text-gray-900 dark:text-slate-50">
                {title}
              </h1>
              <p className="mt-2 text-sm sm:text-base text-gray-600 dark:text-slate-300">{subtitle}</p>
            </header>

            <section className="space-y-4">
              <p className="text-sm sm:text-base md:text-[1.05rem] text-gray-700 dark:text-slate-200 leading-[1.72]">
                {description}
              </p>

              <p className="text-sm sm:text-base md:text-[1.05rem] text-gray-700 dark:text-slate-200 leading-[1.72]">
                Официальный сайт: <a className="text-blue-600 dark:text-blue-400 hover:underline" href="https://pandapal.ru">pandapal.ru</a>.{' '}
                Официальный бот: <a className="text-blue-600 dark:text-blue-400 hover:underline" href="https://t.me/PandaPalBot" target="_blank" rel="noopener noreferrer">@PandaPalBot</a>.
              </p>
            </section>

            <section className="mt-7 sm:mt-8">
              <h2 className="font-display text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-50 mb-4">
                Частые вопросы
              </h2>
              <div className="space-y-4">
                {faq.map((item) => (
                  <div key={item.question} className="rounded-xl border border-gray-200 dark:border-slate-600 p-4 sm:p-5">
                    <h3 className="font-semibold text-gray-900 dark:text-slate-100 mb-1.5">{item.question}</h3>
                    <p className="text-sm sm:text-base text-gray-700 dark:text-slate-200 leading-[1.7]">{item.answer}</p>
                  </div>
                ))}
              </div>
            </section>

            <div className="mt-7 sm:mt-8">
              <a
                href="https://t.me/PandaPalBot"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center px-6 py-3 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold hover:opacity-90 transition-opacity"
              >
                {botCta}
              </a>
            </div>
          </article>
        </main>
      </>
    );
  }
);

IntentPage.displayName = 'IntentPage';
