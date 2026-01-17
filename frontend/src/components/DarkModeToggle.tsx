/**
 * Dark Mode Toggle Component
 * Переключатель темной темы с сохранением в localStorage
 */

import React, { useEffect, useState } from 'react';

interface DarkModeToggleProps {
  isInline?: boolean; // Если true - используется внутри Header, иначе fixed позиционирование
}

export const DarkModeToggle: React.FC<DarkModeToggleProps> = ({ isInline = false }) => {
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

      // Загрузить тему из localStorage при монтировании
      useEffect(() => {
        setMounted(true);

        // ВСЕГДА светлая тема по умолчанию
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');

        const savedTheme = localStorage.getItem('theme');

        // Если пользователь явно выбрал темную тему - используем её
        if (savedTheme === 'dark') {
          setIsDark(true);
          document.documentElement.classList.add('dark');
          document.documentElement.classList.remove('light');
        } else {
          // Явно устанавливаем светлую тему по умолчанию
          setIsDark(false);
          document.documentElement.classList.remove('dark');
          document.documentElement.classList.add('light');
          localStorage.setItem('theme', 'light');
        }
      }, []);

      // Переключение темы
      const toggleTheme = () => {
        if (isDark) {
          document.documentElement.classList.remove('dark');
          document.documentElement.classList.add('light');
          localStorage.setItem('theme', 'light');
          setIsDark(false);
        } else {
          document.documentElement.classList.add('dark');
          document.documentElement.classList.remove('light');
          localStorage.setItem('theme', 'dark');
          setIsDark(true);
        }
      };

  // Не показываем кнопку до монтирования (избегаем мигания)
  if (!mounted) return null;

  // Стили в зависимости от режима (inline или fixed)
  const buttonClassName = isInline
    ? "w-11 h-11 sm:w-12 sm:h-12 rounded-full bg-white dark:bg-slate-700 shadow-md hover:shadow-lg border-2 border-gray-200 dark:border-slate-600 transition-all duration-300 hover:scale-105 active:scale-95 flex items-center justify-center touch-manipulation"
    : "fixed top-4 right-4 md:right-28 z-50 w-11 h-11 sm:w-12 sm:h-12 md:w-auto md:h-auto md:px-5 md:py-2.5 rounded-full bg-white dark:bg-slate-700 shadow-md hover:shadow-lg border-2 border-gray-200 dark:border-slate-600 transition-all duration-300 hover:scale-105 active:scale-95 text-sm font-semibold flex items-center justify-center touch-manipulation min-h-[44px] sm:min-h-[48px]";

  return (
    <button
      onClick={toggleTheme}
      className={buttonClassName}
      aria-label={isDark ? 'Включить светлую тему' : 'Включить темную тему'}
      title={isDark ? 'Светлая тема' : 'Темная тема'}
    >
      {isDark ? (
        // Иконка солнца (светлая тема)
        <svg className="w-5 h-5 text-yellow-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
