import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  // Алиасы для импортов
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@config': path.resolve(__dirname, './src/config'),
      '@scenes': path.resolve(__dirname, './src/scenes'),
      '@entities': path.resolve(__dirname, './src/entities'),
      '@managers': path.resolve(__dirname, './src/managers'),
      '@utils': path.resolve(__dirname, './src/utils'),
    },
  },

  // Сервер разработки
  server: {
    port: 5175,
    host: 'localhost',
    open: true,
  },

  // Оптимизация сборки
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Удаляем console.log в продакшене
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          phaser: ['phaser'], // Выносим Phaser в отдельный chunk
        },
      },
    },
  },

  // Оптимизация зависимостей
  optimizeDeps: {
    include: ['phaser'],
  },
});
