/**
 * Компонент Footer (подвал сайта)
 * Содержит логотип, кнопку обратной связи и копирайт
 * @module components/Footer
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';
import { trackButtonClick } from '../utils/analytics';

const FEEDBACK_FORM_URL = 'https://forms.yandex.ru/cloud/695ba5a6068ff07700f0029a';

/**
 * Подвал сайта с автообновляемым годом
 * Отображается внизу каждой страницы
 */
export const Footer: React.FC = React.memo(() => {
  // Получаем текущий год автоматически (не нужно обновлять вручную)
  const currentYear = new Date().getFullYear();

  const handleFeedbackClick = () => {
    trackButtonClick('footer_feedback');
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
          onError={(e) => {
            // Fallback если логотип не загрузится
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
            const emoji = document.createElement('div');
            emoji.textContent = '🐼';
            emoji.className = 'text-3xl animate-logo-bounce';
            target.parentElement?.appendChild(emoji);
          }}
        />
        <span className="font-display text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-100">
          {SITE_CONFIG.name}
        </span>
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

      {/* Копирайт */}
      <p className="text-xs sm:text-sm md:text-base text-gray-600 dark:text-slate-400">
        © {currentYear} {SITE_CONFIG.name}. Все права защищены.
      </p>
    </footer>
  );
});

// Для React DevTools
Footer.displayName = 'Footer';
