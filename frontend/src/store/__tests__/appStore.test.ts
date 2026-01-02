/**
 * Unit тесты для Zustand Store
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useAppStore } from '../appStore';
import type { UserProfile } from '../../services/api';

describe('AppStore', () => {
  beforeEach(() => {
    // Сбрасываем состояние перед каждым тестом
    useAppStore.getState().reset();
  });

  it('должен иметь правильное начальное состояние', () => {
    const state = useAppStore.getState();

    expect(state.user).toBeNull();
    expect(state.currentScreen).toBe('ai-chat');
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('должен устанавливать пользователя', () => {
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

    const state = useAppStore.getState();
    expect(state.user).toEqual(mockUser);
  });

  it('должен менять текущий экран', () => {
    useAppStore.getState().setCurrentScreen('emergency');

    const state = useAppStore.getState();
    expect(state.currentScreen).toBe('emergency');
  });

  it('должен управлять состоянием загрузки', () => {
    useAppStore.getState().setIsLoading(false);

    const state = useAppStore.getState();
    expect(state.isLoading).toBe(false);
  });

  it('должен устанавливать и очищать ошибки', () => {
    const errorMessage = 'Test error';

    useAppStore.getState().setError(errorMessage);
    expect(useAppStore.getState().error).toBe(errorMessage);

    useAppStore.getState().clearError();
    expect(useAppStore.getState().error).toBeNull();
  });

  it('должен сбрасывать состояние', () => {
    // Устанавливаем какие-то значения
    useAppStore.getState().setUser({
      telegram_id: 123,
      user_type: 'child',
    } as UserProfile);
    useAppStore.getState().setCurrentScreen('emergency');
    useAppStore.getState().setIsLoading(false);
    useAppStore.getState().setError('test');

    // Сбрасываем
    useAppStore.getState().reset();

    // Проверяем что вернулись к начальному состоянию
    const state = useAppStore.getState();
    expect(state.user).toBeNull();
    expect(state.currentScreen).toBe('ai-chat');
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });

  describe('Селекторы', () => {
    it('selectUser должен возвращать пользователя', () => {
      const mockUser: UserProfile = {
        telegram_id: 123,
        user_type: 'child',
      } as UserProfile;

      useAppStore.getState().setUser(mockUser);

      const user = useAppStore.getState().user;
      expect(user).toEqual(mockUser);
    });

    it('selectCurrentScreen должен возвращать текущий экран', () => {
      useAppStore.getState().setCurrentScreen('emergency');

      const screen = useAppStore.getState().currentScreen;
      expect(screen).toBe('emergency');
    });
  });
});
