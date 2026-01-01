/**
 * Главный компонент приложения
 * Отвечает за композицию всех секций страницы
 * @module App
 */

import React from 'react';
import { Header, Hero, Features, Section, Footer, CallToAction } from './components';
import { DarkModeToggle } from './components/DarkModeToggle';
import { SECTIONS } from './config/constants';
import './index.css';

/**
 * Корневой компонент приложения PandaPal
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
  return (
    <div className="min-h-screen bg-gradient-to-b from-sky/20 to-pink/20 dark:from-slate-900 dark:to-slate-800 text-gray-900 dark:text-slate-100 smooth-scroll transition-colors duration-300">
      {/* Dark Mode Toggle */}
      <DarkModeToggle />

      {/* Шапка сайта */}
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
    </div>
  );
};

export default App;
