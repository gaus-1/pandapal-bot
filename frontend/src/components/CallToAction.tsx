/**
 * Call to Action компонент с QR-кодом и кнопками
 * Как на скринах - QR слева, кнопка справа
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';

export const CallToAction: React.FC = React.memo(() => {
  return (
    <section className="py-16 px-4 bg-gradient-to-br from-blue-50 to-pink-50 dark:from-slate-800 dark:to-slate-900 rounded-3xl my-16">
      <div className="max-w-5xl mx-auto text-center">
        {/* Заголовок */}
        <h2 className="text-3xl md:text-4xl font-display font-bold mb-4 text-gray-900 dark:text-slate-50">
          Начни общение прямо сейчас! 🚀
        </h2>
        <p className="text-lg text-gray-700 dark:text-slate-300 mb-12">
          Отсканируй QR-код камерой телефона или нажми кнопку ниже
        </p>

        {/* QR + Кнопка */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-16">
          {/* QR-код */}
          <div className="bg-white dark:bg-slate-700 p-6 rounded-2xl shadow-xl">
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(SITE_CONFIG.botUrl)}`}
              alt="QR-код для перехода в Telegram бота"
              className="w-48 h-48 md:w-56 md:h-56"
              loading="lazy"
            />
            <p className="text-sm text-gray-600 dark:text-slate-400 mt-4">
              Наведи камеру на QR-код
            </p>
          </div>

          {/* Разделитель "или" */}
          <div className="flex items-center justify-center">
            <span className="text-xl font-semibold text-gray-500 dark:text-slate-400">
              или
            </span>
          </div>

          {/* Кнопка */}
          <div className="flex flex-col gap-4">
            <a
              href={SITE_CONFIG.botUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-3 px-8 py-4 bg-blue-500 hover:bg-blue-600 text-white font-semibold text-lg rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.643-.204-.657-.643.136-.953l11.566-4.458c.538-.196 1.006.128.832.941z"/>
              </svg>
              Открыть в Telegram
            </a>
            <p className="text-sm text-center">
              <span className="inline-flex items-center gap-1 text-yellow-600 dark:text-yellow-400">
                💡 Совет:
              </span>
              <span className="text-gray-600 dark:text-slate-400 ml-1">
                Если ты на телефоне — просто нажми кнопку выше!
              </span>
            </p>
          </div>
        </div>

        {/* Преимущества внизу */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-16 text-center">
          <div>
            <div className="text-3xl mb-2">⚡</div>
            <h3 className="font-bold text-gray-900 dark:text-slate-100 mb-1">
              Быстрый старт
            </h3>
            <p className="text-sm text-gray-600 dark:text-slate-400">
              Открой бота и отправь /start — мы сразу начнем!
            </p>
          </div>
          <div>
            <div className="text-3xl mb-2">🔒</div>
            <h3 className="font-bold text-gray-900 dark:text-slate-100 mb-1">
              Безопасно
            </h3>
            <p className="text-sm text-gray-600 dark:text-slate-400">
              Все данные защищены, контент модерируется AI
            </p>
          </div>
          <div>
            <div className="text-3xl mb-2">🎁</div>
            <h3 className="font-bold text-gray-900 dark:text-slate-100 mb-1">
              Бесплатно
            </h3>
            <p className="text-sm text-gray-600 dark:text-slate-400">
              Полный доступ ко всем функциям без оплаты!
            </p>
          </div>
        </div>
      </div>
    </section>
  );
});

CallToAction.displayName = 'CallToAction';
