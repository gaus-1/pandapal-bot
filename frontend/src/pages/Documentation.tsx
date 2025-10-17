/**
 * Страница документации с переключением языков.
 * Отображает README.md с возможностью переключения между русским и английским языками.
 */

import React from 'react';
import { ReadmeViewer } from '../components/ReadmeViewer';

export const Documentation: React.FC = React.memo(() => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <a href="/" className="flex items-center space-x-2">
                <span className="text-2xl">🐼</span>
                <span className="text-xl font-bold text-gray-900">PandaPal</span>
              </a>
              <span className="ml-4 text-sm text-gray-500">/ Документация</span>
            </div>
            <div className="flex items-center space-x-4">
              <a
                href="/"
                className="text-gray-600 hover:text-gray-900 text-sm font-medium"
              >
                ← На главную
              </a>
              <a
                href="https://github.com/gaus-1/pandapal-bot"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors"
              >
                GitHub
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6">
            <div className="mb-6">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                📚 Документация PandaPal
              </h1>
              <p className="text-gray-600">
                Полная документация по установке, настройке и использованию PandaPal бота.
                Переключайтесь между русским и английским языками для удобства.
              </p>
            </div>

            <ReadmeViewer />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-4 mb-4 md:mb-0">
              <span className="text-gray-600 text-sm">
                © 2025 PandaPal Team. Made with ❤️ and 🐼
              </span>
            </div>
            <div className="flex items-center space-x-6">
              <a
                href="https://t.me/PandaPalBot"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-900 text-sm"
              >
                Попробовать бота
              </a>
              <a
                href="https://github.com/gaus-1/pandapal-bot/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-900 text-sm"
              >
                Сообщить о баге
              </a>
              <a
                href="https://github.com/gaus-1/pandapal-bot"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-900 text-sm"
              >
                GitHub
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
});

Documentation.displayName = 'Documentation';
