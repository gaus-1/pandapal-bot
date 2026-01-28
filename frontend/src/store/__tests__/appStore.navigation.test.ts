/**
 * Тесты навигации и состояния для Zustand Store
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useAppStore } from '../appStore';
import type { UserProfile } from '../../services/api';

describe('AppStore - Навигация и состояние', () => {
  beforeEach(() => {
    useAppStore.getState().reset();
  });

  describe('Переключение экранов', () => {
    it('должен начинаться с экрана ai-chat', () => {
      const state = useAppStore.getState();
      expect(state.currentScreen).toBe('ai-chat');
    });

    it('должен переключаться на emergency экран', () => {
      useAppStore.getState().setCurrentScreen('emergency');

      const state = useAppStore.getState();
      expect(state.currentScreen).toBe('emergency');
    });

    it('должен переключаться обратно на ai-chat', () => {
      useAppStore.getState().setCurrentScreen('emergency');
      useAppStore.getState().setCurrentScreen('ai-chat');

      const state = useAppStore.getState();
      expect(state.currentScreen).toBe('ai-chat');
    });
  });

  describe('Управление пользователем', () => {
    it('должен устанавливать пользователя при успешной аутентификации', () => {
      const mockUser: UserProfile = {
        telegram_id: 123456789,
        first_name: 'Test',
        last_name: 'User',
        username: 'testuser',
        age: 10,
        grade: 5,
        user_type: 'child',
      };

      useAppStore.getState().setUser(mockUser);
      useAppStore.getState().setIsLoading(false);

      const state = useAppStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isLoading).toBe(false);
    });

    it('должен очищать пользователя при logout', () => {
      const mockUser: UserProfile = {
        telegram_id: 123456789,
        user_type: 'child',
      } as UserProfile;

      useAppStore.getState().setUser(mockUser);
      useAppStore.getState().setUser(null);

      const state = useAppStore.getState();
      expect(state.user).toBeNull();
    });
  });

  describe('Управление загрузкой', () => {
    it('должен начинаться в состоянии загрузки', () => {
      const state = useAppStore.getState();
      expect(state.isLoading).toBe(true);
    });

    it('должен отключать загрузку после аутентификации', () => {
      useAppStore.getState().setIsLoading(false);

      const state = useAppStore.getState();
      expect(state.isLoading).toBe(false);
    });

    it('должен включать загрузку при обновлении данных', () => {
      useAppStore.getState().setIsLoading(false);
      useAppStore.getState().setIsLoading(true);

      const state = useAppStore.getState();
      expect(state.isLoading).toBe(true);
    });
  });

  describe('Управление ошибками', () => {
    it('должен устанавливать ошибку при неудачной аутентификации', () => {
      const errorMessage = 'Invalid Telegram signature';

      useAppStore.getState().setError(errorMessage);
      useAppStore.getState().setIsLoading(false);

      const state = useAppStore.getState();
      expect(state.error).toBe(errorMessage);
      expect(state.isLoading).toBe(false);
    });

    it('должен очищать ошибку при повторной попытке', () => {
      useAppStore.getState().setError('Test error');
      useAppStore.getState().clearError();

      const state = useAppStore.getState();
      expect(state.error).toBeNull();
    });

    it('должен заменять старую ошибку новой', () => {
      useAppStore.getState().setError('Old error');
      useAppStore.getState().setError('New error');

      const state = useAppStore.getState();
      expect(state.error).toBe('New error');
    });
  });

  describe('Полный flow аутентификации', () => {
    it('должен правильно обрабатывать успешную аутентификацию', () => {
      const mockUser: UserProfile = {
        telegram_id: 123456789,
        first_name: 'Test',
        user_type: 'child',
      } as UserProfile;

      // Начальное состояние
      expect(useAppStore.getState().isLoading).toBe(true);
      expect(useAppStore.getState().user).toBeNull();
      expect(useAppStore.getState().error).toBeNull();

      // Успешная аутентификация
      useAppStore.getState().setUser(mockUser);
      useAppStore.getState().setIsLoading(false);
      useAppStore.getState().clearError();

      const state = useAppStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.user).toEqual(mockUser);
      expect(state.error).toBeNull();
    });

    it('должен правильно обрабатывать неудачную аутентификацию', () => {
      // Начальное состояние
      expect(useAppStore.getState().isLoading).toBe(true);
      expect(useAppStore.getState().error).toBeNull();

      // Неудачная аутентификация
      useAppStore.getState().setError('Authentication failed');
      useAppStore.getState().setIsLoading(false);

      const state = useAppStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.user).toBeNull();
      expect(state.error).toBe('Authentication failed');
    });
  });

  describe('Сброс состояния', () => {
    it('должен сбрасывать всё состояние к начальному', () => {
      // Устанавливаем различные значения
      const mockUser: UserProfile = {
        telegram_id: 123,
        user_type: 'child',
      } as UserProfile;

      useAppStore.getState().setUser(mockUser);
      useAppStore.getState().setCurrentScreen('emergency');
      useAppStore.getState().setIsLoading(false);
      useAppStore.getState().setError('test error');

      // Сбрасываем
      useAppStore.getState().reset();

      // Проверяем что всё вернулось к начальному состоянию
      const state = useAppStore.getState();
      expect(state.user).toBeNull();
      expect(state.currentScreen).toBe('ai-chat');
      expect(state.isLoading).toBe(true);
      expect(state.error).toBeNull();
    });
  });

  describe('Конкурентные обновления', () => {
    it('должен обрабатывать множественные setError вызовы', () => {
      useAppStore.getState().setError('Error 1');
      useAppStore.getState().setError('Error 2');
      useAppStore.getState().setError('Error 3');

      const state = useAppStore.getState();
      expect(state.error).toBe('Error 3');
    });

    it('должен обрабатывать быстрое переключение экранов', () => {
      useAppStore.getState().setCurrentScreen('emergency');
      useAppStore.getState().setCurrentScreen('ai-chat');
      useAppStore.getState().setCurrentScreen('emergency');

      const state = useAppStore.getState();
      expect(state.currentScreen).toBe('emergency');
    });

    it('должен обрабатывать чередование loading состояния', () => {
      useAppStore.getState().setIsLoading(false);
      useAppStore.getState().setIsLoading(true);
      useAppStore.getState().setIsLoading(false);

      const state = useAppStore.getState();
      expect(state.isLoading).toBe(false);
    });
  });
});
