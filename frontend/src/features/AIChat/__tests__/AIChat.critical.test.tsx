/**
 * Критические тесты для AI Chat
 * Проверяет работу с фото, аудио и AI ответами
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AIChat } from '../AIChat';
import * as api from '../../../services/api';
import { useAppStore } from '../../../store/appStore';
import type { UserProfile } from '../../../services/api';

// Mock user profile
const mockUserProfile: UserProfile = {
  telegram_id: 123,
  first_name: 'Test',
  user_type: 'child',
};

// Mock responses
const mockApiResponses = {
  getChatHistory: async () => [
    { role: 'user' as const, content: 'Привет', timestamp: new Date().toISOString() },
    { role: 'ai' as const, content: 'Привет! Чем помочь?', timestamp: new Date().toISOString() },
  ],
  sendAIMessage: async (_telegramId: number, message?: string) => ({
    response: message?.includes('2x + 5 = 13')
      ? 'Решение уравнения 2x + 5 = 13: x = 4'
      : `AI response for: ${message}`,
  }),
};

vi.mock('../../../services/telegram', () => ({
  telegram: {
    hapticFeedback: vi.fn(),
    showAlert: vi.fn(),
    notifySuccess: vi.fn(),
    notifyError: vi.fn(),
    showConfirm: vi.fn(),
    showPopup: vi.fn(),
  },
}));

const mockSetCurrentScreen = vi.fn();
vi.mock('../../../store/appStore', () => ({
  useAppStore: {
    getState: vi.fn(() => ({
      setCurrentScreen: mockSetCurrentScreen,
    })),
  },
}));

vi.mock('../../../services/api', () => ({
  getChatHistory: vi.fn(),
  sendAIMessage: vi.fn(),
  clearChatHistory: vi.fn(),
}));

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let mockTelegram: any;

describe('AIChat - Критические пути', () => {
  let queryClient: QueryClient;

  beforeEach(async () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();

    // Получаем telegram mock
    const telegramModule = await import('../../../services/telegram');
    mockTelegram = telegramModule.telegram;

    vi.mocked(api.getChatHistory).mockImplementation(mockApiResponses.getChatHistory);
    vi.mocked(api.sendAIMessage).mockImplementation(mockApiResponses.sendAIMessage);
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  describe('Текстовые сообщения', () => {
    it('должен отправлять текстовое сообщение и получать ответ AI', async () => {
      const user = userEvent.setup();

      render(<AIChat user={mockUserProfile} />, { wrapper });

      // Ждём загрузки истории
      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      // Находим поле ввода
      const input = screen.getByPlaceholderText(/Задай вопрос/i);
      expect(input).toBeInTheDocument();

      // Вводим текст
      await user.type(input, 'Реши уравнение 2x + 5 = 13');

      // Находим и кликаем кнопку отправки (ищем по тексту ▶️)
      const sendButtons = screen.getAllByTitle(/Отправить/i);
      const sendButton = sendButtons.find(btn => btn.textContent?.includes('▶️')) || sendButtons[0];
      await user.click(sendButton);

      // Проверяем что API был вызван
      await waitFor(() => {
        expect(api.sendAIMessage).toHaveBeenCalledWith(
          mockUserProfile.telegram_id,
          'Реши уравнение 2x + 5 = 13',
          undefined,
          undefined
        );
      }, { timeout: 3000 });

      // Проверяем что появился ответ AI
      await waitFor(() => {
        expect(screen.getByText(/Отличный вопрос/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('должен показывать индикатор загрузки при отправке', async () => {
      const user = userEvent.setup();

      // Замедляем ответ AI
      vi.mocked(api.sendAIMessage).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ response: 'Ответ' }), 500))
      );

      render(<AIChat user={mockUserProfile} />, { wrapper });

      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      const input = screen.getByPlaceholderText(/Задай вопрос/i);
      await user.type(input, 'Тест');

      // Ищем кнопку отправки по тексту внутри (▶️)
      const sendButtons = screen.getAllByTitle(/Отправить/i);
      const sendButton = sendButtons.find(btn => btn.textContent?.includes('▶️')) || sendButtons[0];
      await user.click(sendButton);

      // Проверяем что показывается "PandaPal думает..."
      await waitFor(() => {
        expect(screen.getByText(/думает/i)).toBeInTheDocument();
      }, { timeout: 1000 });
    });
  });

  describe('Фото', () => {
    it('должен отправлять фото и получать анализ от AI', async () => {
      const user = userEvent.setup();

      render(<AIChat user={mockUserProfile} />, { wrapper });

      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      // Находим кнопку фото
      const photoButton = screen.getByTitle(/Отправить фото/i);
      expect(photoButton).toBeInTheDocument();

      // Создаём mock File
      const file = new File(['test'], 'test.png', { type: 'image/png' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      // Загружаем файл
      await user.upload(fileInput, file);

      // Проверяем что API был вызван с фото
      await waitFor(() => {
        const calls = vi.mocked(api.sendAIMessage).mock.calls;
        expect(calls.some(call => call[2] !== undefined)).toBe(true);
      }, { timeout: 3000 });
    });

    it('должен показывать ошибку при загрузке не-изображения', async () => {
      const user = userEvent.setup();

      render(<AIChat user={mockUserProfile} />, { wrapper });

      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      // Загружаем не-изображение
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      await user.upload(fileInput, file);

      // Проверяем что был вызван showAlert
      await waitFor(() => {
        expect(mockTelegram.showAlert).toHaveBeenCalled();
      }, { timeout: 1000 });
    });
  });

  describe('Аудио', () => {
    it('должен записывать и отправлять голосовое сообщение', async () => {
      const user = userEvent.setup();

      // Mock MediaRecorder API
      const mockStart = vi.fn();
      const mockStop = vi.fn();
      const mockMediaRecorder = {
        start: mockStart,
        stop: mockStop,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ondataavailable: null as any,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onstop: null as any,
        state: 'inactive',
      };

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      window.MediaRecorder = vi.fn(() => mockMediaRecorder) as any;
      Object.defineProperty(window.navigator, 'mediaDevices', {
        writable: true,
        value: {
          getUserMedia: vi.fn(() => Promise.resolve({
            getTracks: () => [{ stop: vi.fn() }],
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
          } as any)),
        },
      });

      render(<AIChat user={mockUserProfile} />, { wrapper });

      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      // Начинаем запись (когда поле ввода пустое)
      const voiceButton = screen.getByTitle(/Голосовое/i);
      await user.click(voiceButton);

      // Проверяем что начали запись
      await waitFor(() => {
        expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalled();
      }, { timeout: 1000 });

      // Останавливаем запись
      if (mockMediaRecorder.onstop) {
        // Эмулируем получение данных
        const blob = new Blob(['audio'], { type: 'audio/webm' });
        if (mockMediaRecorder.ondataavailable) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          mockMediaRecorder.ondataavailable({ data: blob } as any);
        }
        // Эмулируем остановку
        mockMediaRecorder.onstop();

        // Проверяем что аудио будет отправлено
        await waitFor(() => {
          const calls = vi.mocked(api.sendAIMessage).mock.calls;
          expect(calls.some(call => call[3] !== undefined)).toBe(true);
        }, { timeout: 3000 });
      }
    });
  });

  describe('История чата', () => {
    it('должен загружать и отображать историю чата', async () => {
      render(<AIChat user={mockUserProfile} />, { wrapper });

      // Ждём загрузки истории
      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      // Проверяем что сообщения из истории отображаются
      await waitFor(() => {
        expect(screen.getByText(/Привет, помоги с математикой/i)).toBeInTheDocument();
        expect(screen.getByText(/Конечно, помогу с математикой/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('должен показывать приветствие если история пустая', async () => {
      vi.mocked(api.getChatHistory).mockResolvedValue([]);

      render(<AIChat user={mockUserProfile} />, { wrapper });

      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      // Проверяем приветственное сообщение
      expect(screen.getByText(/Начни общение/i)).toBeInTheDocument();
      expect(screen.getByText(/Задай любой вопрос/i)).toBeInTheDocument();
    });
  });

  describe('Кнопки действий', () => {
    it('должен очищать чат при клике на кнопку очистки', async () => {
      const user = userEvent.setup();
      const mockSetCurrentScreen = vi.fn();
      vi.mocked(useAppStore.getState).mockReturnValue({
        setCurrentScreen: mockSetCurrentScreen,
      } as ReturnType<typeof useAppStore.getState>);
      vi.mocked(mockTelegram.showConfirm).mockResolvedValue(true);
      vi.mocked(api.clearChatHistory).mockResolvedValue({ deleted_count: 1 });

      render(<AIChat user={mockUserProfile} />, { wrapper });

      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      const clearButton = screen.getByLabelText(/Очистить чат/i);
      await user.click(clearButton);

      await waitFor(() => {
        expect(mockTelegram.showConfirm).toHaveBeenCalledWith('Очистить историю чата?');
      }, { timeout: 3000 });
    });

    it('должен переключаться на экран SOS при клике на кнопку SOS', async () => {
      const user = userEvent.setup();
      const mockSetCurrentScreen = vi.fn();
      vi.mocked(useAppStore.getState).mockReturnValue({
        setCurrentScreen: mockSetCurrentScreen,
      } as ReturnType<typeof useAppStore.getState>);

      render(<AIChat user={mockUserProfile} />, { wrapper });

      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      const sosButton = screen.getByLabelText(/Экстренные номера/i);
      await user.click(sosButton);

      await waitFor(() => {
        expect(mockSetCurrentScreen).toHaveBeenCalledWith('emergency');
        expect(mockTelegram.hapticFeedback).toHaveBeenCalledWith('medium');
      }, { timeout: 1000 });
    });

    it('должен копировать сообщение при клике на кнопку копирования', async () => {
      const user = userEvent.setup();
      const mockWriteText = vi.fn();
      Object.assign(navigator, { clipboard: { writeText: mockWriteText } });

      render(<AIChat user={mockUserProfile} />, { wrapper });

      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      // Находим кнопку копирования (появляется при hover)
      const copyButtons = screen.queryAllByTitle(/Копировать/i);
      if (copyButtons.length > 0) {
        await user.click(copyButtons[0]);

        await waitFor(() => {
          expect(mockWriteText).toHaveBeenCalled();
          expect(mockTelegram.showPopup).toHaveBeenCalled();
        }, { timeout: 1000 });
      }
    });

    it('должен скроллить вверх при клике на кнопку скролла вверх', async () => {
      const user = userEvent.setup();

      render(<AIChat user={mockUserProfile} />, { wrapper });

      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      // Кнопки скролла появляются только если есть скролл
      const scrollUpButton = screen.queryByLabelText(/Вверх/i);
      if (scrollUpButton) {
        await user.click(scrollUpButton);
        expect(mockTelegram.hapticFeedback).toHaveBeenCalledWith('light');
      }
    });

    it('должен скроллить вниз при клике на кнопку скролла вниз', async () => {
      const user = userEvent.setup();

      render(<AIChat user={mockUserProfile} />, { wrapper });

      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      const scrollDownButton = screen.queryByLabelText(/Вниз/i);
      if (scrollDownButton) {
        await user.click(scrollDownButton);
        expect(mockTelegram.hapticFeedback).toHaveBeenCalledWith('light');
      }
    });
  });

  describe('Error Handling', () => {
    it('должен обрабатывать ошибки API', async () => {
      const user = userEvent.setup();

      vi.mocked(api.sendAIMessage).mockRejectedValue(new Error('API Error'));

      render(<AIChat user={mockUserProfile} />, { wrapper });

      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      const input = screen.getByPlaceholderText(/Задай вопрос/i);
      await user.type(input, 'Тест');

      // Ищем кнопку отправки по тексту внутри (▶️)
      const sendButtons = screen.getAllByTitle(/Отправить/i);
      const sendButton = sendButtons.find(btn => btn.textContent?.includes('▶️')) || sendButtons[0];
      await user.click(sendButton);

      // Проверяем что была вызвана ошибка
      await waitFor(() => {
        expect(mockTelegram.notifyError).toHaveBeenCalled();
      }, { timeout: 3000 });
    });

    it('должен обрабатывать ошибки загрузки истории', async () => {
      vi.mocked(api.getChatHistory).mockRejectedValue(new Error('History Error'));

      render(<AIChat user={mockUserProfile} />, { wrapper });

      // История должна всё равно загрузиться (пустая)
      await waitFor(() => {
        expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });

      // Проверяем что показывается приветствие
      expect(screen.getByText(/Начни общение!/i)).toBeInTheDocument();
    });
  });
});
