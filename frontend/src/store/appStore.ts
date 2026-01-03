/**
 * Zustand Store - Централизованное управление состоянием Mini App
 * Следует принципам SOLID и обеспечивает типобезопасность
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { UserProfile } from '../services/api';

// Типы экранов приложения
export type Screen = 'ai-chat' | 'emergency' | 'achievements';

// Интерфейс состояния приложения
interface AppState {
  // Данные пользователя
  user: UserProfile | null;
  setUser: (user: UserProfile | null) => void;

  // Текущий экран
  currentScreen: Screen;
  setCurrentScreen: (screen: Screen) => void;

  // Состояние загрузки
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  // Ошибки
  error: string | null;
  setError: (error: string | null) => void;
  clearError: () => void;

  // Сброс состояния (для тестов и logout)
  reset: () => void;
}

// Начальное состояние
const initialState = {
  user: null,
  currentScreen: 'ai-chat' as Screen,
  isLoading: true,
  error: null,
};

/**
 * Hook для доступа к глобальному состоянию приложения
 * Использует Zustand для легкого и производительного управления состоянием
 */
export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      ...initialState,

      // Установка пользователя
      setUser: (user) =>
        set({ user }, false, 'setUser'),

      // Навигация между экранами
      setCurrentScreen: (screen) =>
        set({ currentScreen: screen }, false, 'setCurrentScreen'),

      // Управление загрузкой
      setIsLoading: (loading) =>
        set({ isLoading: loading }, false, 'setIsLoading'),

      // Управление ошибками
      setError: (error) =>
        set({ error }, false, 'setError'),

      clearError: () =>
        set({ error: null }, false, 'clearError'),

      // Сброс состояния
      reset: () =>
        set(initialState, false, 'reset'),
    }),
    {
      name: 'PandaPal-Store',
      enabled: import.meta.env.DEV, // Devtools только в dev режиме
    }
  )
);

// Селекторы для оптимизации re-renders
export const selectUser = (state: AppState) => state.user;
export const selectCurrentScreen = (state: AppState) => state.currentScreen;
export const selectIsLoading = (state: AppState) => state.isLoading;
export const selectError = (state: AppState) => state.error;
