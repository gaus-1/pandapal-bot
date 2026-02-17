/**
 * Модальное окно согласия на обработку ПД перед переходом к форме отзывов (РКН).
 * Пустой чекбокс по умолчанию; кнопка активна только при согласии.
 */

import React, { useState } from 'react';
import { LEGAL_ROUTES } from '../config/legal';

interface FeedbackConsentModalProps {
  onClose: () => void;
  onOpenForm: () => void;
}

export const FeedbackConsentModal: React.FC<FeedbackConsentModalProps> = React.memo(
  ({ onClose, onOpenForm }) => {
    const [agreed, setAgreed] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      if (!agreed) return;
      onOpenForm();
      onClose();
    };

    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 dark:bg-black/50"
        role="dialog"
        aria-modal="true"
        aria-labelledby="feedback-modal-title"
      >
        <div
          className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-xl max-w-md w-full p-6"
          onClick={(e) => e.stopPropagation()}
        >
          <h2
            id="feedback-modal-title"
            className="font-display font-bold text-lg text-gray-900 dark:text-slate-50 mb-3"
          >
            Оставить отзыв
          </h2>
          <p className="text-sm text-gray-700 dark:text-slate-200 mb-4">
            Твой отзыв будет отправлен через форму на Яндексе. Мы обработаем твои ответы в соответствии с политикой обработки персональных данных.
          </p>
          <form onSubmit={handleSubmit}>
            <label className="flex items-start gap-3 cursor-pointer mb-5">
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                className="mt-1 w-4 h-4 rounded border-gray-300 dark:border-slate-600 text-blue-500 focus:ring-blue-400"
                aria-describedby="consent-desc"
              />
              <span id="consent-desc" className="text-sm text-gray-700 dark:text-slate-200">
                Я согласен на обработку персональных данных и ознакомился с{' '}
                <a
                  href={LEGAL_ROUTES.personalData}
                  className="text-blue-600 dark:text-blue-400 underline hover:no-underline"
                  onClick={(e) => {
                    e.preventDefault();
                    window.history.pushState(null, '', LEGAL_ROUTES.personalData);
                    window.dispatchEvent(new Event('popstate'));
                  }}
                >
                  Политикой обработки персональных данных
                </a>
                .
              </span>
            </label>
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 rounded-full border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-slate-200 font-medium text-sm hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors min-h-[44px]"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={!agreed}
                className="inline-flex items-center justify-center px-5 py-2.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-blue-600 dark:to-cyan-600 text-white font-semibold text-sm min-h-[44px] hover:scale-105 active:scale-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 dark:focus:ring-offset-slate-800"
              >
                Перейти к форме
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }
);
FeedbackConsentModal.displayName = 'FeedbackConsentModal';
