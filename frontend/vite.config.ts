import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@config': path.resolve(__dirname, './src/config'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
    },
  },
  build: {
    target: 'es2020',
    cssCodeSplit: true,
    // Оптимизированный лимит размера
    chunkSizeWarningLimit: 400,
    rollupOptions: {
      output: {
        // Оптимальное разделение бандла для стандартов 2025
        manualChunks: {
          // React core (должен загружаться первым)
          'react-core': ['react', 'react-dom'],
          // Роутинг (нужен почти сразу)
          'react-router': ['react-router-dom'],
          // Zustand (легкий, но отдельно)
          'state': ['zustand'],
          // Web vitals (загружается асинхронно)
          'monitoring': ['web-vitals'],
        },
        // Оптимизация имен файлов
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    sourcemap: false, // Отключаем sourcemap в проде
    minify: 'esbuild', // esbuild быстрее terser
    reportCompressedSize: true,
    // Оптимизация для детей (быстрая загрузка на медленных соединениях)
    assetsInlineLimit: 4096, // Инлайним маленькие файлы < 4KB
  },
  server: {
    host: 'localhost',
    port: 5173,
    strictPort: true,
    // Стабильный HMR без сетевых проблем
    hmr: {
      overlay: true,
      port: 5174,
    },
    // Отключаем предварительную оптимизацию для стабильности
    preTransformRequests: false,
    // Кэширование для стабильности
    fs: {
      strict: false,
    },
  },
  // Оптимизация для dev сборки - упрощенная для стабильности
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'zustand',
    ],
    force: true, // Принудительная переоптимизация
  },
})
