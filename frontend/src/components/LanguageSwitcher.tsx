"""
Компонент для переключения языка README.
Позволяет переключаться между русской и английской версиями документации.
"""

import React from 'react';

interface LanguageSwitcherProps {
  currentLang: 'ru' | 'en';
  onLangChange: (lang: 'ru' | 'en') => void;
}

export const LanguageSwitcher: React.FC<LanguageSwitcherProps> = React.memo(
  ({ currentLang, onLangChange }) => {
    return (
      <div className="flex items-center gap-2 p-4 bg-gray-50 rounded-lg">
        <span className="text-sm text-gray-600">Язык документации:</span>
        <div className="flex gap-1">
          <button
            onClick={() => onLangChange('ru')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              currentLang === 'ru'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
            }`}
          >
            🇷🇺 Русский
          </button>
          <button
            onClick={() => onLangChange('en')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              currentLang === 'en'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
            }`}
          >
            🇺🇸 English
          </button>
        </div>
      </div>
    );
  }
);

LanguageSwitcher.displayName = 'LanguageSwitcher';
