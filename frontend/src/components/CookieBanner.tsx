/**
 * Баннер согласия на использование cookie (требование РКН).
 * Показывается при первом заходе, после «Принять» скрывается (localStorage).
 * По умолчанию показываем баннер, затем в useLayoutEffect скрываем только если уже принято —
 * так баннер гарантированно виден при первом заходе (localStorage может быть ещё недоступен при инициализации).
 */

import React, { useState, useLayoutEffect } from 'react';
import { LEGAL_ROUTES } from '../config/legal';

const STORAGE_KEY = 'cookie_consent_pandapal';

export const CookieBanner: React.FC = React.memo(() => {
  const [visible, setVisible] = useState(true);

  useLayoutEffect(() => {
    try {
      if (typeof window !== 'undefined' && localStorage.getItem(STORAGE_KEY) === 'accepted') {
        setVisible(false);
      }
    } catch {
      // оставляем visible true
    }
  }, []);

  const handleAccept = () => {
    try {
      localStorage.setItem(STORAGE_KEY, 'accepted');
      setVisible(false);
      // После принятия — открываем главную, если пользователь был на юридической странице (перешёл по ссылке из баннера)
      if (typeof window !== 'undefined' && window.location.pathname !== '/') {
        window.history.pushState(null, '', '/');
        window.dispatchEvent(new Event('popstate'));
      }
    } catch {
      // localStorage недоступен (приватный режим и т.п.) — баннер остаётся, пользователь может попробовать снова
    }
  };

  if (!visible) return null;

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50 px-4 sm:px-6 md:px-8 py-3 bg-white/95 dark:bg-slate-800/95 backdrop-blur border-t border-gray-200 dark:border-slate-700 shadow-[0_-4px_20px_rgba(0,0,0,0.08)] dark:shadow-[0_-4px_20px_rgba(0,0,0,0.3)]"
      role="dialog"
      aria-label="Уведомление об использовании cookie"
    >
      <div className="max-w-6xl mx-auto flex flex-col gap-3">
        <p className="font-sans text-xs sm:text-sm text-gray-700 dark:text-slate-200 leading-snug min-w-0">
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
          className="w-full inline-flex items-center justify-center px-6 py-3 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-600 dark:to-cyan-600 text-white font-semibold text-sm min-h-[44px] hover:scale-[1.02] active:scale-100 transition-transform focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 dark:focus:ring-offset-slate-800"
        >
          Принять
        </button>
      </div>
    </div>
  );
});
CookieBanner.displayName = 'CookieBanner';
