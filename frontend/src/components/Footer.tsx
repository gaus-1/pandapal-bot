/**
 * Компонент Footer (подвал сайта)
 * Содержит логотип, ссылки на документы (РКН), кнопку обратной связи и копирайт
 * @module components/Footer
 */

import React, { useState } from 'react';
import { SITE_CONFIG } from '../config/constants';
import { LEGAL_ROUTES, FEEDBACK_FORM_URL } from '../config/legal';
import { trackButtonClick } from '../utils/analytics';
import { FeedbackConsentModal } from './FeedbackConsentModal';

const navigateTo = (path: string) => {
  window.history.pushState(null, '', path);
  window.dispatchEvent(new Event('popstate'));
};

/**
 * Подвал сайта с автообновляемым годом
 * Отображается внизу каждой страницы
 */
export const Footer: React.FC = React.memo(() => {
  const currentYear = new Date().getFullYear();
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);

  const handleFeedbackClick = () => {
    trackButtonClick('footer_feedback');
    setFeedbackModalOpen(true);
  };

  const handleOpenForm = () => {
    window.open(FEEDBACK_FORM_URL, '_blank', 'noopener,noreferrer');
  };

  return (
    <footer
      className="max-w-6xl mx-auto px-4 py-12 text-center border-t border-gray-200 dark:border-slate-700 dark:border-slate-600/50 mt-16"
      role="contentinfo"
    >
      {/* Логотип и название */}
      <div className="flex items-center justify-center gap-3 mb-6">
        <img
          src={SITE_CONFIG.logo.src}
          alt={SITE_CONFIG.logo.alt}
          className="w-10 h-10 rounded-full animate-logo-bounce object-cover"
          loading="lazy"
          width="40"
          height="40"
          style={{
            animation: 'logoBounce 2s ease-in-out infinite',
            willChange: 'transform',
            transform: 'translateZ(0)',
            backfaceVisibility: 'hidden',
          }}
          onError={(e) => {
            // Fallback если логотип не загрузится
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            const emoji = document.createElement('div');
            emoji.textContent = '🐼';
            emoji.className = 'text-3xl animate-logo-bounce';
            emoji.style.cssText = 'animation: logoBounce 2s ease-in-out infinite; will-change: transform; transform: translateZ(0); backface-visibility: hidden;';
            target.parentElement?.appendChild(emoji);
          }}
        />
        <span className="font-display text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-100">
          {SITE_CONFIG.name}
        </span>
      </div>

      {/* Ссылки на документы (РКН) — в карточке для мобильных */}
      <div className="max-w-3xl mx-auto mb-5">
        <nav
          className="rounded-xl sm:rounded-2xl border border-gray-100 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 p-1.5 sm:p-2.5 grid grid-cols-1 sm:grid-cols-3 gap-1.5 sm:gap-2 text-xs sm:text-sm"
          aria-label="Документы"
        >
          <a
            href={LEGAL_ROUTES.privacy}
            onClick={(e) => {
              e.preventDefault();
              navigateTo(LEGAL_ROUTES.privacy);
            }}
            className="rounded-lg border border-gray-200/80 dark:border-slate-600 bg-white/80 dark:bg-slate-900/40 px-3 py-1.5 min-h-[36px] flex items-center justify-center text-center leading-snug text-gray-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-500 transition-colors"
          >
            Политика конфиденциальности
          </a>
          <a
            href={LEGAL_ROUTES.personalData}
            onClick={(e) => {
              e.preventDefault();
              navigateTo(LEGAL_ROUTES.personalData);
            }}
            className="rounded-lg border border-gray-200/80 dark:border-slate-600 bg-white/80 dark:bg-slate-900/40 px-3 py-1.5 min-h-[36px] flex items-center justify-center text-center leading-snug text-gray-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-500 transition-colors"
          >
            Обработка персональных данных
          </a>
          <a
            href={LEGAL_ROUTES.offer}
            onClick={(e) => {
              e.preventDefault();
              navigateTo(LEGAL_ROUTES.offer);
            }}
            className="rounded-lg border border-gray-200/80 dark:border-slate-600 bg-white/80 dark:bg-slate-900/40 px-3 py-1.5 min-h-[36px] flex items-center justify-center text-center leading-snug text-gray-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-500 transition-colors"
          >
            Договор оферты
          </a>
        </nav>
      </div>

      {/* Внутренние SEO-ссылки по ключевым интентам */}
      <div className="max-w-3xl mx-auto mb-6">
        <nav
          className="rounded-xl border border-gray-100 dark:border-slate-700 bg-white/70 dark:bg-slate-800/70 p-1.5 sm:p-2.5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-xs sm:text-sm"
          aria-label="Полезные страницы"
        >
          <a href="/bezopasnyy-ai-dlya-detey" className="rounded-lg border border-gray-200/80 dark:border-slate-600 bg-white/80 dark:bg-slate-900/40 px-3 py-1.5 min-h-[36px] flex items-center justify-center text-center leading-snug text-gray-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-500 transition-colors">
            Безопасный ИИ для детей
          </a>
          <a href="/pomoshch-s-domashkoy-v-telegram" className="rounded-lg border border-gray-200/80 dark:border-slate-600 bg-white/80 dark:bg-slate-900/40 px-3 py-1.5 min-h-[36px] flex items-center justify-center text-center leading-snug text-gray-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-500 transition-colors">
            Помощь с домашкой в Telegram
          </a>
          <a href="/safe-ai-for-kids" className="rounded-lg border border-gray-200/80 dark:border-slate-600 bg-white/80 dark:bg-slate-900/40 px-3 py-1.5 min-h-[36px] flex items-center justify-center text-center leading-snug text-gray-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-500 transition-colors">
            Safe AI tutor for kids
          </a>
          <a href="/homework-help-telegram-bot" className="rounded-lg border border-gray-200/80 dark:border-slate-600 bg-white/80 dark:bg-slate-900/40 px-3 py-1.5 min-h-[36px] flex items-center justify-center text-center leading-snug text-gray-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-500 transition-colors">
            Telegram homework help bot
          </a>
        </nav>
      </div>

      {/* Кнопка обратной связи */}
      <div className="mb-6">
        <button
          onClick={handleFeedbackClick}
          className="inline-flex items-center justify-center gap-2 px-4 sm:px-5 md:px-6 py-2 sm:py-2.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-600 dark:to-cyan-600 text-white font-medium text-sm sm:text-base hover:shadow-lg dark:hover:shadow-xl hover:scale-105 active:scale-100 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 dark:focus:ring-offset-slate-800"
          aria-label="Оставить отзыв о PandaPal"
        >
          <span className="text-base sm:text-lg">📝</span>
          <span>Оставь отзыв</span>
        </button>
      </div>

      {feedbackModalOpen && (
        <FeedbackConsentModal
          onClose={() => setFeedbackModalOpen(false)}
          onOpenForm={handleOpenForm}
        />
      )}

      {/* Копирайт */}
      <p className="text-xs sm:text-sm md:text-base text-gray-600 dark:text-slate-400">
        © {currentYear} {SITE_CONFIG.name}. Все права защищены.
      </p>
    </footer>
  );
});

// Для React DevTools
Footer.displayName = 'Footer';
