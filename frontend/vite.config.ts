import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // React core - отдельно (большой, редко меняется)
          if (id.includes('node_modules/react/') || id.includes('node_modules/react-dom/')) {
            return 'react-vendor';
          }
          // TanStack Query - отдельно (часто используется)
          if (id.includes('node_modules/@tanstack/')) {
            return 'tanstack-vendor';
          }
          // Telegram SDK - отдельно (редко меняется)
          if (id.includes('node_modules/@twa-dev/')) {
            return 'telegram-vendor';
          }
          // Zustand - отдельно (легковесный, но популярный)
          if (id.includes('node_modules/zustand/')) {
            return 'zustand-vendor';
          }
          // Остальные vendor библиотеки
          if (id.includes('node_modules/')) {
            return 'vendor';
          }
        },
      },
    },
    sourcemap: false,
    minify: 'esbuild',
    // Оптимизация размера бандла
    chunkSizeWarningLimit: 1000,
    // Включаем сжатие
    reportCompressedSize: true,
    // Оптимизация для production
    cssCodeSplit: true,
    cssMinify: true,
  },
  server: {
    host: true,
    port: 5173,
  },
})
