/**
 * Компонент QR-кода для быстрого перехода в Telegram бот
 * @module components/TelegramQR
 */

import React, { useEffect, useState } from 'react';
import { SITE_CONFIG } from '../config/constants';

/**
 * QR-код для перехода в Telegram бот
 * Генерируется через API QR Server
 */
export const TelegramQR: React.FC = React.memo(() => {
  const [qrUrl, setQrUrl] = useState<string>('');
  
  useEffect(() => {
    // Генерируем QR-код через публичный API
    // Используем QR Server API (бесплатный, без лимитов)
    const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(SITE_CONFIG.botUrl)}`;
    
    setQrUrl(qrApiUrl);
  }, []);
  
  const handleTelegramClick = () => {
    // Открываем бота в новой вкладке
    window.open(SITE_CONFIG.botUrl, '_blank', 'noopener,noreferrer');
    
    // Трекинг клика (если есть аналитика)
    if (typeof window !== 'undefined' && 'gtag' in window) {
      (window as any).gtag('event', 'telegram_bot_open', {
        event_category: 'Engagement',
        event_label: 'QR Section',
      });
    }
  };
  
  return (
    <section className="py-12 md:py-16" id="telegram-qr">
      <div className="rounded-2xl bg-gradient-to-br from-sky/10 to-pink/10 p-8 md:p-12 text-center">
        <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">
          Начни общение прямо сейчас! 🚀
        </h2>
        
        <p className="text-lg text-gray-700 max-w-2xl mx-auto mb-8">
          Отсканируй QR-код камерой телефона или нажми кнопку ниже
        </p>
        
        {/* QR-код */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-8 mb-8">
          {/* QR код */}
          <div className="bg-white p-6 rounded-2xl shadow-lg">
            {qrUrl ? (
              <img
                src={qrUrl}
                alt="QR-код для Telegram бота PandaPal"
                className="w-48 h-48"
                loading="lazy"
                width="200"
                height="200"
              />
            ) : (
              <div className="w-48 h-48 bg-gray-100 rounded-lg animate-pulse" />
            )}
            <p className="text-sm text-gray-500 mt-3">
              Наведи камеру на QR-код
            </p>
          </div>
          
          {/* Или разделитель */}
          <div className="hidden md:flex items-center justify-center">
            <div className="w-px h-32 bg-gray-300" />
            <span className="absolute bg-white px-3 text-gray-500 font-semibold">
              или
            </span>
          </div>
          
          <div className="md:hidden text-gray-500 font-semibold">
            или
          </div>
          
          {/* Кнопка */}
          <div className="flex flex-col items-center gap-4">
            <button
              onClick={handleTelegramClick}
              className="inline-flex items-center gap-3 px-8 py-4 rounded-full bg-gradient-to-r from-sky to-pink text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 active:scale-100"
              aria-label="Открыть PandaPal бота в Telegram"
            >
              {/* Telegram иконка */}
              <svg 
                className="w-6 h-6" 
                viewBox="0 0 24 24" 
                fill="currentColor"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z"/>
              </svg>
              Открыть в Telegram
            </button>
            
            <p className="text-sm text-gray-600 max-w-xs">
              💡 <strong>Совет:</strong> Если ты на телефоне — просто нажми кнопку выше!
            </p>
          </div>
        </div>
        
        {/* Дополнительная информация */}
        <div className="grid md:grid-cols-3 gap-4 mt-8 text-left">
          <div className="bg-white/60 backdrop-blur p-4 rounded-xl">
            <div className="text-2xl mb-2">⚡</div>
            <h3 className="font-semibold mb-1">Быстрый старт</h3>
            <p className="text-sm text-gray-600">
              Открой бота и отправь /start — мы сразу начнём!
            </p>
          </div>
          
          <div className="bg-white/60 backdrop-blur p-4 rounded-xl">
            <div className="text-2xl mb-2">🔒</div>
            <h3 className="font-semibold mb-1">Безопасно</h3>
            <p className="text-sm text-gray-600">
              Все данные защищены, контент модерируется AI
            </p>
          </div>
          
          <div className="bg-white/60 backdrop-blur p-4 rounded-xl">
            <div className="text-2xl mb-2">🆓</div>
            <h3 className="font-semibold mb-1">Бесплатно</h3>
            <p className="text-sm text-gray-600">
              Полный доступ ко всем функциям без оплаты
            </p>
          </div>
        </div>
      </div>
    </section>
  );
});

TelegramQR.displayName = 'TelegramQR';

