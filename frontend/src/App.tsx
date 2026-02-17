/**
 * Главный компонент приложения
 * Отвечает за композицию всех секций страницы
 * @module App
 */

import React, { useEffect, useState } from 'react';
import { Header, Hero, Features, Section, Footer, CallToAction } from './components';
import { SECTIONS } from './config/constants';
import { telegram } from './services/telegram';
import { MiniApp } from './MiniApp';
import { PremiumScreen } from './features/Premium/PremiumScreen';
import { DonationScreen } from './features/Donation/DonationScreen';
import { PrivacyPage, PersonalDataPage, OfferPage } from './features/Legal';
import { CookieBanner } from './components/CookieBanner';
import { logger } from './utils/logger';
import './index.css';

/**
 * Корневой компонент приложения PandaPal
 *
 * Логика:
 * - Если открыто в Telegram Mini App → показываем MiniApp
 * - Если открыто в браузере → показываем лендинг
 *
 * Архитектура:
 * - Header: шапка с логотипом и навигацией
 * - Main: основной контент (Hero, Features, CallToAction, динамические секции)
 * - Footer: подвал с копирайтом
 * - DarkModeToggle: переключатель темы
 *
 * Принципы:
 * - Модульность: каждый блок — отдельный компонент
 * - Масштабируемость: новые секции добавляются через SECTIONS
 * - Производительность: все компоненты мемоизированы (React.memo)
 */
const App: React.FC = () => {
  const [isInTelegram, setIsInTelegram] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [currentRoute, setCurrentRoute] = useState<string>('');

  useEffect(() => {
    // Проверяем, открыто ли приложение в Telegram
    // СТРОГАЯ проверка: только если есть initData ИЛИ явные признаки Telegram
    const hasInitData = telegram.getInitData() !== '' && telegram.getInitData() !== undefined;

    // Проверяем наличие tgaddr в URL (явный признак Telegram Mini App)
    let hasTgaddr = false;
    if (typeof window !== 'undefined') {
      // Проверяем search параметры
      const urlParams = new URLSearchParams(window.location.search);
      hasTgaddr = urlParams.has('tgaddr');

      // Если нет в search, проверяем hash (для web.telegram.org/k/#?tgaddr=...)
      if (!hasTgaddr && window.location.hash) {
        const hashParams = new URLSearchParams(window.location.hash.slice(1));
        hasTgaddr = hashParams.has('tgaddr');
      }
    }

    // Проверяем наличие window.Telegram.WebApp (только если есть initData или tgaddr)
    const hasTelegramWebApp = typeof window !== 'undefined' &&
      typeof (window as Window & { Telegram?: { WebApp?: unknown } }).Telegram !== 'undefined' &&
      typeof (window as Window & { Telegram?: { WebApp?: unknown } }).Telegram?.WebApp !== 'undefined';

    // Для web.telegram.org разрешаем без initData (он может появиться позже)
    const isTelegramUserAgent = typeof window !== 'undefined' &&
      (window.navigator.userAgent.includes('Telegram') ||
       window.location.hostname.includes('telegram.org') ||
       window.location.hostname.includes('web.telegram.org'));

    // СТРОГАЯ проверка: Mini App только если:
    // 1. Есть initData (главный признак) ИЛИ
    // 2. Есть tgaddr в URL (явный признак) ИЛИ
    // 3. Есть window.Telegram.WebApp И (Telegram User Agent ИЛИ web.telegram.org)
    const inTelegram = hasInitData ||
      hasTgaddr ||
      (hasTelegramWebApp && isTelegramUserAgent);

    setIsInTelegram(inTelegram);
    setIsChecking(false);

    logger.debug('App started:', inTelegram ? 'Telegram' : 'Browser');
  }, []);

  // Роутинг через URL pathname (history-based routing)
  useEffect(() => {
    const updateRoute = () => {
      if (typeof window !== 'undefined') {
        const pathname = window.location.pathname;

        if (pathname === '/premium') {
          setCurrentRoute('premium');
        } else if (pathname === '/donation' || pathname === '/support') {
          setCurrentRoute('donation');
        } else if (pathname === '/privacy') {
          setCurrentRoute('privacy');
        } else if (pathname === '/personal-data') {
          setCurrentRoute('personal-data');
        } else if (pathname === '/offer') {
          setCurrentRoute('offer');
        } else {
          setCurrentRoute('');
        }
      }
    };

    updateRoute();
    window.addEventListener('popstate', updateRoute);

    return () => {
      window.removeEventListener('popstate', updateRoute);
    };
  }, []);

  // Показываем загрузку пока проверяем окружение
  if (isChecking) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-slate-800">
        <div className="text-center">
          <div className="text-6xl mb-4">🐼</div>
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  // Если в Telegram → Mini App
  if (isInTelegram) {
    return <MiniApp />;
  }

  // Если в браузере → Роутинг
  // Premium страница
  if (currentRoute === 'premium') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10">
          <PremiumScreen user={null} />
        </main>
        <Footer />
        <CookieBanner />
      </div>
    );
  }

  // Donation страница
  if (currentRoute === 'donation') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
        <Header />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10">
          <DonationScreen user={null} />
        </main>
        <Footer />
        <CookieBanner />
      </div>
    );
  }

  // Юридические страницы (РКН)
  if (currentRoute === 'privacy') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
        <PrivacyPage />
        <Footer />
        <CookieBanner />
      </div>
    );
  }
  if (currentRoute === 'personal-data') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
        <PersonalDataPage />
        <Footer />
        <CookieBanner />
      </div>
    );
  }
  if (currentRoute === 'offer') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
        <OfferPage />
        <Footer />
        <CookieBanner />
      </div>
    );
  }

  // Лендинг (главная страница)
  return (
    <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
      {/* Шапка сайта (включает DarkModeToggle внутри) */}
      <Header />

      {/* Основной контент */}
      <main className="max-w-6xl mx-auto px-4">
        {/* Hero-секция: заголовок + CTA */}
        <Hero />

        {/* Блок преимуществ (3 карточки) */}
        <Features />

        {/* CTA с QR-кодом и кнопкой */}
        <CallToAction />

        {/* Динамические секции (Для родителей) */}
        {SECTIONS.map((section) => (
          <Section key={section.id} section={section} />
        ))}
      </main>

      {/* Подвал */}
      <Footer />
      <CookieBanner />
    </div>
  );
};

export default App;
