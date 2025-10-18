/**
 * Компонент Footer (подвал сайта)
 * Содержит 3 колонки: О нас, Полезное, Контакты
 * @module components/Footer
 */

import React from 'react';
import { SITE_CONFIG } from '../config/constants';
import './Footer.css';

/**
 * Улучшенный Footer в стиле Montfort
 * 3 колонки с навигацией, соцсетями и информацией
 */
export const Footer: React.FC = React.memo(() => {
  const currentYear = new Date().getFullYear();

  return (
    <footer
      className="bg-gradient-to-b from-gray-50 to-gray-100 border-t border-gray-200 mt-20"
      role="contentinfo"
    >
      <div className="max-w-6xl mx-auto px-4 py-12 md:py-16">
        {/* Основной контент - 3 колонки */}
        <div className="grid md:grid-cols-3 gap-8 md:gap-12 mb-10">
          {/* Колонка 1: О проекте */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <img
                src={SITE_CONFIG.logo.src}
                alt={SITE_CONFIG.logo.alt}
                className="w-10 h-10 rounded-full panda-footer-logo"
                loading="lazy"
                width="40"
                height="40"
              />
              <span className="font-display text-xl font-bold">
                {SITE_CONFIG.name}
              </span>
            </div>
            <p className="text-gray-600 text-sm leading-relaxed mb-4">
              Безопасный AI-помощник для образования детей 6-18 лет.
              Персонализация, геймификация, модерация 24/7.
            </p>
            <div className="flex gap-3">
              <a
                href="https://t.me/PandaPalBot"
                target="_blank"
                rel="noopener noreferrer"
                className="w-12 h-12 flex items-center justify-center bg-sky text-white rounded-full hover:bg-sky/80 transition-colors"
                aria-label="Telegram"
                title="Telegram"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z"/>
                </svg>
              </a>
              <a
                href="https://github.com/gaus-1/pandapal-bot"
                target="_blank"
                rel="noopener noreferrer"
                className="w-12 h-12 flex items-center justify-center bg-gray-800 text-white rounded-full hover:bg-gray-700 transition-colors"
                aria-label="GitHub"
                title="GitHub"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
              </a>
            </div>
          </div>

          {/* Колонка 2: Полезное */}
          <div>
            <h3 className="font-bold text-lg mb-4 text-gray-900">Полезное</h3>
            <ul className="space-y-3">
              <li>
                <a
                  href="/docs"
                  className="text-gray-600 hover:text-sky transition-colors text-sm"
                >
                  📚 Документация
                </a>
              </li>
              <li>
                <a
                  href="#parents"
                  className="text-gray-600 hover:text-sky transition-colors text-sm"
                >
                  👨‍👩‍👧 Для родителей
                </a>
              </li>
              <li>
                <a
                  href="#mission"
                  className="text-gray-600 hover:text-sky transition-colors text-sm"
                >
                  🎯 Наша миссия
                </a>
              </li>
              <li>
                <a
                  href={SITE_CONFIG.botUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-600 hover:text-sky transition-colors text-sm"
                >
                  🤖 Попробовать бота
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/gaus-1/pandapal-bot/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-600 hover:text-sky transition-colors text-sm"
                >
                  🐛 Сообщить о баге
                </a>
              </li>
            </ul>
          </div>

          {/* Колонка 3: Технологии */}
          <div>
            <h3 className="font-bold text-lg mb-4 text-gray-900">Технологии</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>Google Gemini AI</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>React + TypeScript</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>Python + aiogram</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>PostgreSQL</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                <span>OWASP Top 10</span>
              </li>
            </ul>
            <div className="mt-6">
              <a
                href="https://github.com/gaus-1/pandapal-bot"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                <span>⭐ Star на GitHub</span>
              </a>
            </div>
          </div>
        </div>

        {/* Нижняя часть - копирайт */}
        <div className="border-t border-gray-300 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <img
              src={SITE_CONFIG.logo.src}
              alt={SITE_CONFIG.logo.alt}
              className="w-6 h-6 rounded-full cursor-pointer hover:scale-110 transition-transform"
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
              title="Наверх! 🚀"
            />
            <span>
              © {currentYear} {SITE_CONFIG.name}. Все права защищены.
            </span>
          </div>
          <div className="flex gap-4">
            <a href="#" className="hover:text-gray-900 transition-colors">
              Политика конфиденциальности
            </a>
            <a href="#" className="hover:text-gray-900 transition-colors">
              Условия использования
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
});

Footer.displayName = 'Footer';
