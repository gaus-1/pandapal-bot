/**
 * Unit тесты для useChat hook
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useChat } from '../useChat';
import * as api from '../../services/api';
import type { ReactNode } from 'react';

// Mock responses
const mockChatHistory = [
  { role: 'user' as const, content: 'Привет', timestamp: new Date().toISOString() },
  { role: 'ai' as const, content: 'Привет! Чем помочь?', timestamp: new Date().toISOString() },
];

const mockApiResponses = {
  getChatHistory: async () => mockChatHistory,
  sendAIMessage: async (_telegramId: number, message?: string) => ({
    response: `AI response for: ${message}`,
  }),
};

// Mock API
vi.mock('../../services/api', () => ({
  getChatHistory: vi.fn(),
  sendAIMessage: vi.fn(),
}));

// Mock Telegram service
vi.mock('../../services/telegram', () => ({
  telegram: {
    hapticFeedback: vi.fn(),
    showAlert: vi.fn(),
    notifySuccess: vi.fn(),
    notifyError: vi.fn(),
  },
}));

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let mockTelegram: any;

describe('useChat', () => {
  let queryClient: QueryClient;

  beforeEach(async () => {
    // Создаем новый QueryClient для каждого теста
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();

    // Получаем telegram mock
    const telegramModule = await import('../../services/telegram');
    mockTelegram = telegramModule.telegram;

    // Настраиваем API моки
    vi.mocked(api.getChatHistory).mockImplementation(mockApiResponses.getChatHistory);
    vi.mocked(api.sendAIMessage).mockImplementation(mockApiResponses.sendAIMessage);
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('должен загружать историю чата', async () => {
    const { result } = renderHook(
      () => useChat({ telegramId: 123456789, limit: 20 }),
      { wrapper }
    );

    // Изначально загружается
    expect(result.current.isLoadingHistory).toBe(true);

    // Ждём загрузки
    await waitFor(() => {
      expect(result.current.isLoadingHistory).toBe(false);
    }, { timeout: 3000 });

    // Проверяем что история загрузилась
    expect(result.current.messages).toEqual(mockChatHistory);
    expect(api.getChatHistory).toHaveBeenCalledWith(123456789, 20);
  });

  it('должен отправлять текстовое сообщение', async () => {
    const { result } = renderHook(
      () => useChat({ telegramId: 123456789, limit: 20 }),
      { wrapper }
    );

    // Ждём загрузки истории
    await waitFor(() => {
      expect(result.current.isLoadingHistory).toBe(false);
    }, { timeout: 3000 });

    // Отправляем сообщение
    result.current.sendMessage({ message: 'Тест' });

    // Ждём завершения отправки
    await waitFor(() => {
      expect(result.current.isSending).toBe(false);
    }, { timeout: 3000 });

    // Проверяем что API был вызван правильно
    expect(api.sendAIMessage).toHaveBeenCalledWith(
      123456789,
      'Тест',
      undefined,
      undefined
    );

    // Проверяем что haptic feedback был вызван
    expect(mockTelegram.hapticFeedback).toHaveBeenCalled();
  });

  it('должен отправлять фото', async () => {
    const photoBase64 = 'data:image/png;base64,test';

    const { result } = renderHook(
      () => useChat({ telegramId: 123456789, limit: 20 }),
      { wrapper }
    );

    // Ждём загрузки истории
    await waitFor(() => {
      expect(result.current.isLoadingHistory).toBe(false);
    }, { timeout: 3000 });

    // Отправляем фото
    result.current.sendMessage({ photoBase64 });

    // Ждём завершения отправки
    await waitFor(() => {
      expect(result.current.isSending).toBe(false);
    }, { timeout: 3000 });

    // Проверяем что API был вызван с фото
    expect(api.sendAIMessage).toHaveBeenCalledWith(
      123456789,
      undefined,
      photoBase64,
      undefined
    );

    // Проверяем что был успех
    expect(mockTelegram.notifySuccess).toHaveBeenCalled();
  });

  it('должен отправлять аудио', async () => {
    const audioBase64 = 'data:audio/webm;base64,test';

    const { result } = renderHook(
      () => useChat({ telegramId: 123456789, limit: 20 }),
      { wrapper }
    );

    // Ждём загрузки истории
    await waitFor(() => {
      expect(result.current.isLoadingHistory).toBe(false);
    }, { timeout: 3000 });

    // Отправляем аудио
    result.current.sendMessage({ audioBase64 });

    // Ждём завершения отправки
    await waitFor(() => {
      expect(result.current.isSending).toBe(false);
    }, { timeout: 3000 });

    // Проверяем что API был вызван с аудио
    expect(api.sendAIMessage).toHaveBeenCalledWith(
      123456789,
      undefined,
      undefined,
      audioBase64
    );

    // Проверяем что был успех
    expect(mockTelegram.notifySuccess).toHaveBeenCalled();
  });

  it('должен обрабатывать ошибки отправки', async () => {
    const mockError = new Error('Network error');

    // Mock ошибки отправки
    vi.mocked(api.sendAIMessage).mockRejectedValue(mockError);

    const { result } = renderHook(
      () => useChat({ telegramId: 123456789, limit: 20 }),
      { wrapper }
    );

    // Ждём загрузки истории
    await waitFor(() => {
      expect(result.current.isLoadingHistory).toBe(false);
    }, { timeout: 3000 });

    // Отправляем сообщение (которое упадёт)
    result.current.sendMessage({ message: 'Тест' });

    // Ждём завершения (с ошибкой)
    await waitFor(() => {
      expect(result.current.isSending).toBe(false);
    }, { timeout: 3000 });

    // Проверяем что ошибка была обработана
    expect(result.current.sendError).toBeTruthy();
    expect(mockTelegram.notifyError).toHaveBeenCalled();
  });
});
