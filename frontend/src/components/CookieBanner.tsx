/**
 * Баннер согласия на использование cookie (требование РКН).
 * Показывается при первом заходе, после «Принять» скрывается (localStorage).
 */

import React, { useState, useEffect } from 'react';
import { LEGAL_ROUTES } from '../config/legal';

const STORAGE_KEY = 'cookie_consent_pandapal';

export const CookieBanner: React.FC = React.memo(() => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored !== 'accepted') {
        setVisible(true);
      }
    } catch {
      setVisible(true);
    }
  }, []);

  const handleAccept = () => {
    try {
      localStorage.setItem(STORAGE_KEY, 'accepted');
    } catch {
      // ignore
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50 px-4 py-4 sm:py-3 bg-white/95 dark:bg-slate-800/95 backdrop-blur border-t border-gray-200 dark:border-slate-700 shadow-[0_-4px_20px_rgba(0,0,0,0.08)] dark:shadow-[0_-4px_20px_rgba(0,0,0,0.3)]"
      role="dialog"
      aria-label="Уведомление об использовании cookie"
    >
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <p className="text-sm text-gray-700 dark:text-slate-200">
          Мы используем cookie и метрику, чтобы сайт работал удобнее и мы понимали, как им пользуются. Продолжая пользоваться сайтом, ты соглашаешься с нашей политикой. Подробнее:{' '}
          <a
            href={LEGAL_ROUTES.privacy}
            className="text-blue-600 dark:text-blue-400 underline hover:no-underline"
            onClick={(e) => {
              e.preventDefault();
              window.history.pushState(null, '', LEGAL_ROUTES.privacy);
              window.dispatchEvent(new Event('popstate'));
            }}
          >
            Политика конфиденциальности
          </a>
          {' и '}
          <a
            href={LEGAL_ROUTES.personalData}
            className="text-blue-600 dark:text-blue-400 underline hover:no-underline"
            onClick={(e) => {
              e.preventDefault();
              window.history.pushState(null, '', LEGAL_ROUTES.personalData);
              window.dispatchEvent(new Event('popstate'));
            }}
          >
            Обработка персональных данных
          </a>
          .
        </p>
        <button
          type="button"
          onClick={handleAccept}
          className="flex-shrink-0 inline-flex items-center justify-center px-5 py-2.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-600 dark:to-cyan-600 text-white font-semibold text-sm min-h-[44px] hover:scale-105 active:scale-100 transition-all focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 dark:focus:ring-offset-slate-800"
        >
          Принять
        </button>
      </div>
    </div>
  );
});
CookieBanner.displayName = 'CookieBanner';
