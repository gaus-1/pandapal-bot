/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class', // Используем class-based dark mode (проверяет класс 'dark' на элементе)
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Единая палитра для сайта и мини-апп
        pink: '#FFC0CB',
        sky: '#87CEEB',
        // Основные цвета (унифицированы)
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6', // Основной синий
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // Серые оттенки (унифицированы для светлой темы)
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
        // Slate оттенки (унифицированы для темной темы)
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b', // Основной для темной темы
          900: '#0f172a', // Альтернативный для темной темы
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        chat: ['Literata', 'Georgia', 'serif'],
      },
      // Типографика: иерархия по золотому сечению (16→26→42→48→68 px), line-height = size × 1.618
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1.21rem' }],
        'sm': ['0.875rem', { lineHeight: '1.42rem' }],
        'base': ['1rem', { lineHeight: '1.618rem' }],      // 16px
        'lg': ['1.125rem', { lineHeight: '1.82rem' }],
        'xl': ['1.25rem', { lineHeight: '2.02rem' }],
        '2xl': ['1.625rem', { lineHeight: '2.63rem' }],    // 26px
        '3xl': ['2.625rem', { lineHeight: '4.25rem' }],    // 42px
        '4xl': ['3rem', { lineHeight: '4.85rem' }],        // 48px
        '5xl': ['4.25rem', { lineHeight: '6.88rem' }],     // 68px
      },
      // Шкала отступов по Фибоначчи (8, 13, 21, 34… px) для гармонии и симметрии
      spacing: {
        'fib-1': '5px',
        'fib-2': '8px',
        'fib-3': '13px',
        'fib-4': '21px',
        'fib-5': '34px',
        'fib-6': '55px',
        'fib-7': '89px',
      },
      // Брейкпоинты 2026: складные, смартфоны, планшеты, ноутбуки, мониторы до 4K/ультрашироких
      screens: {
        'fold': '280px',   // Складные внешний экран (Galaxy Z Fold, iPhone Fold)
        'narrow': '320px', // Узкие экраны (часть складных 320px)
        'xs': '375px',     // iPhone SE, mini, стандартные узкие
        'sm': '640px',    // Крупные смартфоны, планшеты портрет
        'md': '768px',    // Планшеты
        'lg': '1024px',   // Ноутбуки, планшеты альбом
        'xl': '1280px',   // Десктопы
        '2xl': '1536px',  // Большие мониторы
        '3xl': '1920px',  // Full HD+ / презентации
        '4xl': '2560px',  // QHD/4K и ультраширокие
      },
    },
  },
  plugins: [],
}
