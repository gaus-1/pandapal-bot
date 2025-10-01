/**
 * Setup файл для Vitest
 * Настройка окружения перед запуском тестов
 * @module test/setup
 */

import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

// Matchers автоматически добавляются через импорт выше

// Очистка после каждого теста (unmount компонентов)
afterEach(() => {
  cleanup();
});

// Mock для window.matchMedia (для responsive тестов)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {}, // deprecated
    removeListener: () => {}, // deprecated
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => true,
  }),
});

// Mock для IntersectionObserver (для lazy loading)
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
} as any;

