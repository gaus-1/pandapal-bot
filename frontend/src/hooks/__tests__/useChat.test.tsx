/**
 * Unit тесты для useChat hook
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useChat } from '../useChat';
import * as api from '../../services/api';
import type { ReactNode } from 'react';

// Mock API
vi.mock('../../services/api', () => ({
  getChatHistory: vi.fn(),
  sendAIMessage: vi.fn(),
}));

// Mock Telegram service
vi.mock('../../services/telegram', () => ({
  telegram: {
    hapticFeedback: vi.fn(),
    notifySuccess: vi.fn(),
    notifyError: vi.fn(),
  },
}));

describe('useChat', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    // Создаем новый QueryClient для каждого теста
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('должен загружать историю чата', async () => {
    const mockHistory = [
      { role: 'user' as const, content: 'Привет', timestamp: new Date().toISOString() },
      { role: 'ai' as const, content: 'Привет! Чем помочь?', timestamp: new Date().toISOString() },
    ];

    vi.mocked(api.getChatHistory).mockResolvedValue(mockHistory);

    const { result } = renderHook(
      () => useChat({ telegramId: 123, limit: 20 }),
      { wrapper }
    );

    expect(result.current.isLoadingHistory).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoadingHistory).toBe(false);
    });

    expect(result.current.messages).toEqual(mockHistory);
    expect(api.getChatHistory).toHaveBeenCalledWith(123, 20);
  });

  it('должен отправлять текстовое сообщение', async () => {
    const mockResponse = { response: 'Ответ AI' };

    vi.mocked(api.getChatHistory).mockResolvedValue([]);
    vi.mocked(api.sendAIMessage).mockResolvedValue(mockResponse);

    const { result } = renderHook(
      () => useChat({ telegramId: 123, limit: 20 }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isLoadingHistory).toBe(false);
    });

    result.current.sendMessage({ message: 'Тест' });

    await waitFor(() => {
      expect(result.current.isSending).toBe(false);
    });

    expect(api.sendAIMessage).toHaveBeenCalledWith(
      123,
      'Тест',
      undefined,
      undefined
    );
  });

  it('должен отправлять фото', async () => {
    const mockResponse = { response: 'Анализ фото' };
    const photoBase64 = 'data:image/png;base64,test';

    vi.mocked(api.getChatHistory).mockResolvedValue([]);
    vi.mocked(api.sendAIMessage).mockResolvedValue(mockResponse);

    const { result } = renderHook(
      () => useChat({ telegramId: 123, limit: 20 }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isLoadingHistory).toBe(false);
    });

    result.current.sendMessage({ photoBase64 });

    await waitFor(() => {
      expect(result.current.isSending).toBe(false);
    });

    expect(api.sendAIMessage).toHaveBeenCalledWith(
      123,
      undefined,
      photoBase64,
      undefined
    );
  });

  it('должен отправлять аудио', async () => {
    const mockResponse = { response: 'Распознанный текст' };
    const audioBase64 = 'data:audio/webm;base64,test';

    vi.mocked(api.getChatHistory).mockResolvedValue([]);
    vi.mocked(api.sendAIMessage).mockResolvedValue(mockResponse);

    const { result } = renderHook(
      () => useChat({ telegramId: 123, limit: 20 }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isLoadingHistory).toBe(false);
    });

    result.current.sendMessage({ audioBase64 });

    await waitFor(() => {
      expect(result.current.isSending).toBe(false);
    });

    expect(api.sendAIMessage).toHaveBeenCalledWith(
      123,
      undefined,
      undefined,
      audioBase64
    );
  });

  it('должен обрабатывать ошибки отправки', async () => {
    const mockError = new Error('Network error');

    vi.mocked(api.getChatHistory).mockResolvedValue([]);
    vi.mocked(api.sendAIMessage).mockRejectedValue(mockError);

    const { result } = renderHook(
      () => useChat({ telegramId: 123, limit: 20 }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isLoadingHistory).toBe(false);
    });

    result.current.sendMessage({ message: 'Тест' });

    await waitFor(() => {
      expect(result.current.isSending).toBe(false);
    });

    expect(result.current.sendError).toBeTruthy();
  });
});
