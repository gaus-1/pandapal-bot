/**
 * Конфигурация Vitest для тестирования
 * @module vitest.config
 */

import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    // Используем jsdom для эмуляции браузерного окружения
    environment: 'jsdom',
    
    // Глобальные переменные (describe, it, expect)
    globals: true,
    
    // Setup файл для конфигурации тестов
    setupFiles: './src/test/setup.ts',
    
    // Coverage (покрытие кода тестами)
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
      ],
      // Минимальное покрытие
      statements: 70,
      branches: 70,
      functions: 70,
      lines: 70,
    },
    
    // Таймаут для тестов
    testTimeout: 10000,
    
    // Папки с тестами
    include: ['**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@config': path.resolve(__dirname, './src/config'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@security': path.resolve(__dirname, './src/security'),
    },
  },
});

