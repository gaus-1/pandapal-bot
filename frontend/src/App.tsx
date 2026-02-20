/**
 * Главный компонент приложения
 * Отвечает за композицию всех секций страницы
 * @module App
 */

import React, { useEffect, useState } from 'react';
import { Header, Hero, Features, Section, Footer, CallToAction, SeoHead } from './components';
import { SECTIONS } from './config/constants';
import { telegram } from './services/telegram';
import { MiniApp } from './MiniApp';
import { PremiumScreen } from './features/Premium/PremiumScreen';
import { DonationScreen } from './features/Donation/DonationScreen';
import { PrivacyPage, PersonalDataPage, OfferPage } from './features/Legal';
import { IntentPage } from './features/Discoverability';
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
        } else if (pathname === '/bezopasnyy-ai-dlya-detey') {
          setCurrentRoute('safe-ai-ru');
        } else if (pathname === '/safe-ai-for-kids') {
          setCurrentRoute('safe-ai-en');
        } else if (pathname === '/pomoshch-s-domashkoy-v-telegram') {
          setCurrentRoute('homework-ru');
        } else if (pathname === '/homework-help-telegram-bot') {
          setCurrentRoute('homework-en');
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
        <SeoHead
          title="PandaPal Premium - расширенные возможности"
          description="Premium-подписка PandaPal: больше возможностей для безопасной помощи в учебе."
          canonicalPath="/premium"
        />
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
        <SeoHead
          title="Поддержать PandaPal"
          description="Поддержите развитие PandaPal - безопасного AI-помощника для школьников."
          canonicalPath="/donation"
        />
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
        <SeoHead
          title="Политика конфиденциальности PandaPal"
          description="Политика конфиденциальности сервиса PandaPal."
          canonicalPath="/privacy"
        />
        <PrivacyPage />
        <Footer />
        <CookieBanner />
      </div>
    );
  }
  if (currentRoute === 'personal-data') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
        <SeoHead
          title="Обработка персональных данных PandaPal"
          description="Правила обработки персональных данных в PandaPal."
          canonicalPath="/personal-data"
        />
        <PersonalDataPage />
        <Footer />
        <CookieBanner />
      </div>
    );
  }
  if (currentRoute === 'offer') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
        <SeoHead
          title="Договор оферты PandaPal"
          description="Публичная оферта сервиса PandaPal."
          canonicalPath="/offer"
        />
        <OfferPage />
        <Footer />
        <CookieBanner />
      </div>
    );
  }

  if (currentRoute === 'safe-ai-ru') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
        <SeoHead
          title="Безопасный ИИ для детей - PandaPal"
          description="PandaPal - безопасный AI-помощник для школьников: помощь с учебой, модерация и родительский контроль."
          canonicalPath="/bezopasnyy-ai-dlya-detey"
        />
        <IntentPage
          title="Безопасный ИИ для детей: PandaPal"
          subtitle="Помощь с учебой для школьников 1-9 классов в безопасной среде"
          description="PandaPal помогает детям с уроками по основным школьным предметам, поддерживает текст, фото и голосовые вопросы и использует модерацию контента для безопасного общения."
          botCta="Открыть @PandaPalBot"
          canonicalPath="/bezopasnyy-ai-dlya-detey"
          locale="ru"
          faq={[
            { question: 'Подходит ли PandaPal для младших школьников?', answer: 'Да, ответы адаптируются под возраст и уровень обучения.' },
            { question: 'Чем PandaPal полезен родителям?', answer: 'Сервис делает помощь с учебой более понятной и безопасной за счет встроенной модерации.' },
            { question: 'Где начать?', answer: 'Откройте официальный Telegram-бот @PandaPalBot или зайдите на pandapal.ru.' },
          ]}
        />
        <Footer />
        <CookieBanner />
      </div>
    );
  }

  if (currentRoute === 'safe-ai-en') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
        <SeoHead
          title="Safe AI tutor for kids - PandaPal"
          description="PandaPal is a safe AI tutor for school students with moderation, homework help, and Telegram access."
          canonicalPath="/safe-ai-for-kids"
          locale="en_US"
        />
        <IntentPage
          title="Safe AI Tutor for Kids: PandaPal"
          subtitle="Homework help and learning support for grades 1-9"
          description="PandaPal is a child-safe AI assistant that helps with school subjects, supports text/photo/voice input, and keeps educational interactions moderated."
          botCta="Open @PandaPalBot"
          canonicalPath="/safe-ai-for-kids"
          locale="en"
          faq={[
            { question: 'Is PandaPal safe for children?', answer: 'Yes. The service uses moderation and educational-first responses.' },
            { question: 'What can students ask?', answer: 'Students can ask homework and school-topic questions by text, photo, or voice.' },
            { question: 'How do I start?', answer: 'Use the official bot @PandaPalBot or visit pandapal.ru.' },
          ]}
        />
        <Footer />
        <CookieBanner />
      </div>
    );
  }

  if (currentRoute === 'homework-ru') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
        <SeoHead
          title="Помощь с домашкой в Telegram - PandaPal"
          description="PandaPal помогает с домашним заданием в Telegram: текст, фото и голосовые вопросы."
          canonicalPath="/pomoshch-s-domashkoy-v-telegram"
        />
        <IntentPage
          title="Помощь с домашним заданием в Telegram"
          subtitle="Быстрые объяснения по школьным предметам в формате Telegram-бота"
          description="PandaPal объясняет решения понятным языком, помогает разобрать ошибки и поддерживает вопросы в формате текста, фото задания и голосовых сообщений."
          botCta="Перейти в @PandaPalBot"
          canonicalPath="/pomoshch-s-domashkoy-v-telegram"
          locale="ru"
          faq={[
            { question: 'Можно ли отправить фото задания?', answer: 'Да, можно отправить фото и получить пошаговое объяснение.' },
            { question: 'По каким предметам работает бот?', answer: 'По основным школьным предметам для 1-9 классов.' },
            { question: 'Нужно ли что-то устанавливать?', answer: 'Нет, достаточно открыть @PandaPalBot в Telegram.' },
          ]}
        />
        <Footer />
        <CookieBanner />
      </div>
    );
  }

  if (currentRoute === 'homework-en') {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
        <SeoHead
          title="Telegram homework help bot - PandaPal"
          description="PandaPal is a Telegram homework help bot with text, photo, and voice support."
          canonicalPath="/homework-help-telegram-bot"
          locale="en_US"
        />
        <IntentPage
          title="Telegram Homework Help Bot"
          subtitle="School help for students with text, photo, and voice input"
          description="PandaPal helps students understand homework step by step and supports multiple input formats directly in Telegram."
          botCta="Open PandaPal bot"
          canonicalPath="/homework-help-telegram-bot"
          locale="en"
          faq={[
            { question: 'Can I send homework photos?', answer: 'Yes. PandaPal can process a photo and explain the solution.' },
            { question: 'Is it suitable for school students?', answer: 'Yes, it is designed for grades 1-9 educational support.' },
            { question: 'Where can I access it?', answer: 'Use the official Telegram bot @PandaPalBot.' },
          ]}
        />
        <Footer />
        <CookieBanner />
      </div>
    );
  }

  // Лендинг (главная страница)
  return (
    <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
      <SeoHead
        title="PandaPal - безопасный и полезный AI-друг для детей"
        description="PandaPal - безопасный AI-помощник и робот-репетитор для школьников 1-9 класса в формате Telegram Mini App."
        canonicalPath="/"
      />
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
