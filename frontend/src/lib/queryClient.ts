/**
 * TanStack Query Configuration
 * Настройка кэширования и управления серверным состоянием
 */

import { QueryClient } from '@tanstack/react-query';

/**
 * Глобальный QueryClient с оптимизированными настройками
 * для production-ready Mini App
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Кэш данных на 5 минут
      staleTime: 5 * 60 * 1000,

      // Хранить кэш 10 минут после потери активности
      gcTime: 10 * 60 * 1000,

      // Автоматический retry с экспоненциальной задержкой
      retry: (failureCount, error: unknown) => {
        // Не делаем retry для 4xx ошибок (ошибки клиента)
        const httpError = error as { response?: { status?: number } };
        if (httpError?.response?.status && httpError.response.status >= 400 && httpError.response.status < 500) {
          return false;
        }
        // Максимум 3 попытки для 5xx ошибок
        return failureCount < 3;
      },

      // Задержка между retry (экспоненциальная)
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // Обновление при фокусе окна (полезно для Mini App)
      refetchOnWindowFocus: true,

      // Обновление при восстановлении соединения
      refetchOnReconnect: true,

      // Не обновлять при монтировании если данные свежие
      refetchOnMount: false,
    },
    mutations: {
      // Retry для мутаций только один раз
      retry: 1,
    },
  },
});

/**
 * Query Keys - централизованное управление ключами кэша
 * Следует best practice от TanStack Query
 */
export const queryKeys = {
  // Пользователь
  user: (telegramId: number) => ['user', telegramId] as const,

  // История чата
  chatHistory: (telegramId: number, limit?: number) =>
    ['chatHistory', telegramId, limit] as const,

  // Прогресс обучения
  progress: (telegramId: number) => ['progress', telegramId] as const,

  // Достижения
  achievements: (telegramId: number) => ['achievements', telegramId] as const,

  // Статистика дашборда
  dashboard: (telegramId: number) => ['dashboard', telegramId] as const,

  // Предметы
  subjects: () => ['subjects'] as const,
} as const;
