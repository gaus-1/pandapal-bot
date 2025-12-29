/** @type {import('tailwindcss').Config} */
export default {
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
        sans: ['Open Sans', 'ui-sans-serif', 'system-ui'],
        display: ['Montserrat', 'ui-sans-serif', 'system-ui'],
      },
      // Safe areas для мобильных устройств с notch
      spacing: {
        'safe': 'env(safe-area-inset-bottom)',
        'safe-top': 'env(safe-area-inset-top)',
        'safe-left': 'env(safe-area-inset-left)',
        'safe-right': 'env(safe-area-inset-right)',
      },
      padding: {
        'safe': 'env(safe-area-inset-bottom)',
      },
      // Дополнительные брейкпоинты для мобильных
      screens: {
        'xs': '360px',   // Минимальные смартфоны
        'sm': '480px',   // Маленькие смартфоны
        'md': '768px',   // Планшеты
        'lg': '1024px',  // Десктопы
        'xl': '1280px',  // Большие десктопы
        '2xl': '1536px', // Ultra wide
        // Touch устройства
        'touch': { 'raw': '(hover: none) and (pointer: coarse)' },
        // Ориентация
        'landscape': { 'raw': '(orientation: landscape)' },
        'portrait': { 'raw': '(orientation: portrait)' },
      },
    },
  },
  plugins: [],
}
