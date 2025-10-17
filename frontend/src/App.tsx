/**
 * Главный компонент приложения PandaPal
 * Отвечает за композицию всех секций страницы
 * @module App
 * @version 2.0.0 - Редизайн в стиле Montfort Trading
 */

import React from 'react';
import { Header, Hero, Features, InfoTabs, Mission, TelegramQR, Footer } from './components';
import './index.css';

/**
 * Корневой компонент приложения PandaPal
 *
 * Архитектура (обновлено):
 * - Header: шапка с логотипом и навигацией
 * - Main: основной контент (Hero с scroll indicator, Features, Tabs, Mission)
 * - Footer: улучшенный подвал с 3 колонками
 *
 * Принципы:
 * - Модульность: каждый блок — отдельный компонент
 * - Премиальность: больше whitespace, анимации
 * - Производительность: все компоненты мемоизированы (React.memo)
 * - Адаптивность: mobile-first подход Tailwind CSS
 */
const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 text-gray-900">
      {/* Шапка сайта */}
      <Header />

      {/* Основной контент */}
      <main className="max-w-6xl mx-auto px-4">
        {/* Hero-секция: заголовок + CTA + scroll indicator */}
        <Hero />

        {/* Блок преимуществ (3 карточки) - увеличенные отступы */}
        <section id="features" className="py-8 md:py-12">
          <Features />
        </section>

        {/* Табы с информацией (Родители/Безопасность/Возможности) */}
        <InfoTabs />

        {/* Секция "Наша миссия" */}
        <Mission />

        {/* QR-код и кнопка для перехода в Telegram */}
        <TelegramQR />
      </main>

      {/* Улучшенный Footer */}
      <Footer />
    </div>
  );
};

export default App;
