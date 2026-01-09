/**
 * Mini App Theme Toggle Component
 * Переключатель темы для Telegram Mini App
 * Всегда светлая тема по умолчанию, независимо от настроек Telegram
 */

import React, { useEffect, useState } from 'react';

export const MiniAppThemeToggle: React.FC = () => {
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Инициализация темы при монтировании
  useEffect(() => {
    setMounted(true);

    // Функция для применения темы
    const applyTheme = (dark: boolean) => {
      if (dark) {
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
        localStorage.setItem('theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');
        localStorage.setItem('theme', 'light');
      }
      setIsDark(dark);
    };

    // Всегда светлая тема по умолчанию, игнорируем тему Telegram
    // Проверяем только сохраненный выбор пользователя
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      applyTheme(true);
    } else {
      // По умолчанию всегда светлая тема
      applyTheme(false);
      localStorage.setItem('theme', 'light');
    }
  }, []);

  // Переключение темы
  const toggleTheme = () => {
    const newTheme = !isDark;

    if (newTheme) {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
      localStorage.setItem('theme', 'dark');
      setIsDark(true);
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.classList.add('light');
      localStorage.setItem('theme', 'light');
      setIsDark(false);
    }
  };

  // Не показываем кнопку до монтирования
  if (!mounted) return null;

  return (
    <button
      onClick={toggleTheme}
      className="flex-shrink-0 w-9 h-9 rounded-lg bg-gray-400/60 dark:bg-slate-600/60 hover:bg-gray-500/70 dark:hover:bg-slate-500/70 active:bg-gray-600/80 dark:active:bg-slate-500/80 active:scale-95 transition-all flex items-center justify-center border border-gray-400/40 dark:border-slate-500/40 shadow-sm"
      aria-label={isDark ? 'Включить светлую тему' : 'Включить темную тему'}
      title={isDark ? 'Светлая тема' : 'Темная тема'}
    >
      {isDark ? (
        // Иконка солнца (светлая тема)
        <svg className="w-5 h-5 text-yellow-400 dark:text-yellow-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ) : (
        // Иконка луны (темная тема)
        <svg className="w-5 h-5 text-slate-700 dark:text-slate-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      )}
    </button>
  );
};
