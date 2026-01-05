/**
 * Zustand Store - Централизованное управление состоянием приложения
 *
 * Поддерживает:
 * - Mini App пользователей (через Telegram initData)
 * - Web пользователей (через Telegram Login Widget)
 *
 * Следует принципам SOLID и обеспечивает типобезопасность
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { UserProfile } from '../services/api';

// Типы экранов приложения
export type Screen = 'ai-chat' | 'emergency' | 'achievements' | 'premium' | 'donation' | 'games';

// Интерфейс пользователя для веб-сайта (Telegram Login Widget)
export interface WebUser {
  telegram_id: number;
  full_name: string;
  username?: string;
  is_premium: boolean;
}

// Интерфейс состояния приложения
interface AppState {
  // Данные пользователя (Mini App - из initData)
  user: UserProfile | null;
  setUser: (user: UserProfile | null) => void;

  // Данные пользователя (Web - из Login Widget)
  webUser: WebUser | null;
  setWebUser: (user: WebUser | null) => void;

  // Session token для Web авторизации
  sessionToken: string | null;
  setSessionToken: (token: string | null) => void;

  // Состояние авторизации (для веб-сайта)
  isAuthenticated: boolean;
  isLoading: boolean;

  // Текущий экран
  currentScreen: Screen;
  setCurrentScreen: (screen: Screen) => void;

  // Состояние загрузки
  setIsLoading: (loading: boolean) => void;

  // Ошибки
  error: string | null;
  setError: (error: string | null) => void;
  clearError: () => void;

  // Проверка сессии (для веб-сайта)
  verifySession: () => Promise<boolean>;

  // Выход (для веб-сайта)
  logout: () => Promise<void>;

  // Сброс состояния (для тестов)
  reset: () => void;
}

// Начальное состояние
const initialState = {
  user: null,
  webUser: null,
  sessionToken: null,
  isAuthenticated: false,
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
    persist(
      (set, get) => ({
        ...initialState,

        // Установка пользователя Mini App
        setUser: (user) =>
          set({ user }, false, 'setUser'),

        // Установка пользователя Web
        setWebUser: (webUser) =>
          set({
            webUser,
            isAuthenticated: !!webUser,
          }, false, 'setWebUser'),

        // Установка session token
        setSessionToken: (token) =>
          set({ sessionToken: token }, false, 'setSessionToken'),

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

        // Проверка сессии
        verifySession: async () => {
          const { sessionToken } = get();

          if (!sessionToken) {
            return false;
          }

          set({ isLoading: true });

          try {
            const response = await fetch('/api/auth/telegram/verify', {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${sessionToken}`,
              },
            });

            if (response.ok) {
              const data = await response.json();

              if (data.success) {
                set({
                  webUser: data.user,
                  isAuthenticated: true,
                  isLoading: false,
                });
                return true;
              }
            }

            // Сессия невалидна - очищаем
            set({
              webUser: null,
              sessionToken: null,
              isAuthenticated: false,
              isLoading: false,
            });
            localStorage.removeItem('telegram_session');
            return false;
          } catch (error) {
            console.error('Ошибка проверки сессии:', error);
            set({ isLoading: false });
            return false;
          }
        },

        // Выход (для веб-сайта)
        logout: async () => {
          const { sessionToken } = get();

          // Отправляем запрос на backend для удаления сессии
          if (sessionToken) {
            try {
              await fetch('/api/auth/telegram/logout', {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${sessionToken}`,
                },
              });
            } catch (error) {
              console.error('Ошибка при выходе:', error);
            }
          }

          // Очищаем локальное состояние
          set({
            webUser: null,
            sessionToken: null,
            isAuthenticated: false,
          });

          // Очищаем localStorage
          localStorage.removeItem('telegram_session');
        },

        // Сброс состояния
        reset: () =>
          set(initialState, false, 'reset'),
      }),
      {
        name: 'pandapal-auth',
        partialize: (state) => ({
          sessionToken: state.sessionToken,
        }),
      }
    ),
    {
      name: 'PandaPal-Store',
      enabled: import.meta.env.DEV, // Devtools только в dev режиме
    }
  )
);

// Селекторы для оптимизации re-renders
export const selectUser = (state: AppState) => state.user;
export const selectWebUser = (state: AppState) => state.webUser;
export const selectCurrentScreen = (state: AppState) => state.currentScreen;
export const selectIsLoading = (state: AppState) => state.isLoading;
export const selectError = (state: AppState) => state.error;
export const selectIsAuthenticated = (state: AppState) => state.isAuthenticated;
