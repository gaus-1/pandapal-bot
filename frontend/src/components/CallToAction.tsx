/**
 * Call to Action компонент с QR-кодом и кнопками
 * Как на скринах - QR слева, кнопка справа
 */

import React, { useState } from 'react';
import { SITE_CONFIG } from '../config/constants';

/** Статический QR в public — не зависит от внешнего API, загружается стабильно на ПК и смартфоне */
const QR_IMAGE_SRC = '/qr-bot.png';

export const CallToAction: React.FC = React.memo(() => {
  const [qrError, setQrError] = useState(false);
  const [qrLoaded, setQrLoaded] = useState(false);

  return (
    <div className="max-w-6xl mx-auto px-3 xs:px-4 sm:px-6 md:px-8 w-full box-border">
      <section id="cta" className="py-16 bg-gradient-to-br from-blue-50 via-white to-pink-50 dark:from-slate-800/60 dark:via-slate-900 dark:to-slate-800/60 rounded-3xl border border-gray-100 dark:border-slate-700 dark:border-slate-600/50 scroll-mt-20">
        <div className="px-4 sm:px-6 md:px-8 text-center">
        {/* Заголовок */}
        <h2 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-display font-bold mb-4 text-gray-900 dark:text-slate-50">
          Начни общение прямо сейчас! 🚀
        </h2>
        <p className="text-sm sm:text-base md:text-lg text-gray-600 dark:text-slate-400 mb-12">
          Отсканируй QR-код камерой телефона или нажми кнопку ниже
        </p>

        {/* QR + Кнопка - профессиональная сетка */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-12 md:gap-16 mb-12">
          {/* QR-код */}
          <div className="flex flex-col items-center">
            <div className="bg-white dark:bg-slate-800 p-4 sm:p-6 rounded-2xl shadow-xl dark:shadow-2xl border-2 border-gray-100 dark:border-slate-700 dark:border-slate-600/50 relative w-[220px] h-[220px] sm:w-[240px] sm:h-[240px] md:w-[260px] md:h-[260px] flex items-center justify-center">
              {qrError ? (
                <div className="flex flex-col items-center justify-center p-4 text-center">
                  <div className="text-4xl mb-2">📱</div>
                  <p className="text-sm text-gray-600 dark:text-slate-400 mb-2">
                    QR-код не загрузился
                  </p>
                  <a
                    href={SITE_CONFIG.botUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 dark:text-blue-400 hover:underline text-xs"
                  >
                    Нажми здесь
                  </a>
                </div>
              ) : (
                <>
                  <img
                    src={QR_IMAGE_SRC}
                    alt="QR-код для перехода в Telegram бота"
                    className={`w-full h-full max-w-[200px] max-h-[200px] sm:max-w-[220px] sm:max-h-[220px] md:max-w-[240px] md:max-h-[240px] object-contain transition-opacity duration-300 ${
                      qrLoaded ? 'opacity-100' : 'opacity-0'
                    }`}
                    loading="eager"
                    fetchPriority="high"
                    width="220"
                    height="220"
                    onLoad={() => setQrLoaded(true)}
                    onError={() => {
                      setQrError(true);
                      setQrLoaded(false);
                    }}
                  />
                  {!qrLoaded && !qrError && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="animate-pulse text-gray-400 dark:text-slate-500">
                        <div className="w-12 h-12 border-4 border-gray-300 dark:border-slate-600 border-t-blue-500 rounded-full"></div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
            <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-400 mt-4 font-medium">
              Наведи камеру на QR-код
            </p>
          </div>

          {/* Разделитель "или" */}
          <div className="flex items-center justify-center">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-100 to-pink-100 dark:from-slate-700 dark:to-slate-600 flex items-center justify-center shadow-md">
              <span className="text-lg font-bold text-gray-700 dark:text-slate-300">
                или
              </span>
            </div>
          </div>

          {/* Кнопки */}
          <div className="flex flex-col items-center gap-4">
            <a
              href={SITE_CONFIG.botUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-3 px-10 py-5 bg-gradient-to-r from-blue-500 via-blue-600 to-cyan-500 dark:from-blue-600 dark:via-blue-700 dark:to-cyan-600 hover:from-blue-600 hover:via-blue-700 hover:to-cyan-600 dark:hover:from-blue-700 dark:hover:via-blue-800 dark:hover:to-cyan-700 text-white font-bold text-lg rounded-2xl shadow-xl dark:shadow-2xl hover:shadow-2xl dark:hover:shadow-[0_20px_50px_rgba(0,0,0,0.5)] transform hover:scale-105 active:scale-100 transition-all duration-300 min-h-[44px] sm:min-h-[48px] touch-manipulation"
            >
              <svg className="w-7 h-7" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.643-.204-.657-.643.136-.953l11.566-4.458c.538-.196 1.006.128.832.941z"/>
              </svg>
              Открыть в Telegram
            </a>
            <a
              href={`${SITE_CONFIG.botUrl}?startapp=games`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-3 px-8 py-4 bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 dark:from-purple-600 dark:via-pink-600 dark:to-orange-600 hover:opacity-90 text-white font-semibold text-base rounded-xl shadow-lg dark:shadow-xl hover:shadow-xl transform hover:scale-105 active:scale-100 transition-all duration-300 min-h-[44px] sm:min-h-[48px] touch-manipulation"
            >
              🎮 PandaPalGo
            </a>
            <div className="flex items-baseline gap-2.5 xs:gap-3 sm:gap-3.5 max-w-xs text-left">
              <span className="text-xl sm:text-2xl flex-shrink-0 leading-none">💡</span>
              <p className="text-sm sm:text-base text-gray-600 dark:text-slate-400 leading-relaxed break-words">
                <span className="font-semibold text-yellow-600 dark:text-yellow-400">Совет:</span>
                {' '}Если ты на телефоне — просто нажми кнопку выше!
              </p>
            </div>
          </div>
        </div>

        {/* Преимущества внизу - выровненная сетка */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 pt-8 border-t border-gray-200 dark:border-slate-700">
          <div className="flex flex-col items-center text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900/30 dark:to-blue-800/30 flex items-center justify-center text-3xl mb-3 shadow-md">
              ⚡
            </div>
            <h3 className="font-bold text-base sm:text-lg text-gray-900 dark:text-slate-100 mb-2">
              Быстрый старт
            </h3>
            <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-400 leading-relaxed">
              Открой бота и отправь /start — мы сразу начнем!
            </p>
          </div>
          <div className="flex flex-col items-center text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-green-100 to-emerald-200 dark:from-green-900/30 dark:to-emerald-800/30 flex items-center justify-center text-3xl mb-3 shadow-md">
              🔒
            </div>
            <h3 className="font-bold text-base sm:text-lg text-gray-900 dark:text-slate-100 mb-2">
              Безопасно
            </h3>
            <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-400 leading-relaxed">
              Все данные защищены, контент модерируется AI
            </p>
          </div>
          <div className="flex flex-col items-center text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-100 to-amber-200 dark:from-yellow-900/30 dark:to-amber-800/30 flex items-center justify-center text-3xl mb-3 shadow-md">
              ⭐
            </div>
            <h3 className="font-bold text-base sm:text-lg text-gray-900 dark:text-slate-100 mb-2">
              Premium
            </h3>
            <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-400 leading-relaxed">
              Расширенные возможности и приоритетная поддержка!
            </p>
          </div>
        </div>
        </div>
      </section>
    </div>
  );
});

CallToAction.displayName = 'CallToAction';
