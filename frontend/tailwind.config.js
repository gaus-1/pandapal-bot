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
        pink: '#FFC0CB',
        sky: '#87CEEB',
      },
      fontFamily: {
        // Современные шрифты 2025: Inter для текста, Poppins для заголовков
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      // Адаптивная типографика под все устройства
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
      },
      // Брейкпоинты для 2025: включая складные телефоны
      screens: {
        'xs': '375px',   // Мини-телефоны
        'sm': '640px',   // Мобильные
        'md': '768px',   // Планшеты
        'lg': '1024px',  // Ноутбуки
        'xl': '1280px',  // Десктопы
        '2xl': '1536px', // Большие экраны
        'fold': '280px', // Складные телефоны (Galaxy Fold)
      },
    },
  },
  plugins: [],
}
