/**
 * Integration тесты для MiniApp
 * Проверяет полный flow: аутентификация, навигация, загрузка данных
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MiniApp } from '../MiniApp';
import * as api from '../services/api';
import * as telegramService from '../services/telegram';

// Mock API
vi.mock('../services/api', () => ({
  authenticateUser: vi.fn(),
  getChatHistory: vi.fn(),
  sendAIMessage: vi.fn(),
}));

// Mock Telegram service
vi.mock('../services/telegram', () => ({
  telegram: {
    init: vi.fn(),
    expand: vi.fn(),
    ready: vi.fn(),
    getInitData: vi.fn(() => 'mock_init_data'),
    getUser: vi.fn(() => ({ id: 123, first_name: 'Test' })),
    getPlatform: vi.fn(() => 'web'),
    isTelegramWebApp: vi.fn(() => true),
    isInTelegram: vi.fn(() => true),
    showBackButton: vi.fn(),
    hideBackButton: vi.fn(),
    hapticFeedback: vi.fn(),
    notifySuccess: vi.fn(),
    notifyError: vi.fn(),
    showAlert: vi.fn(),
  },
}));

describe('MiniApp Integration', () => {
  const mockUser = {
    telegram_id: 123456789,
    first_name: 'Test',
    last_name: 'User',
    username: 'testuser',
    age: 10,
    grade: 5,
    user_type: 'child' as const,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.authenticateUser).mockResolvedValue(mockUser);
    vi.mocked(api.getChatHistory).mockResolvedValue([]);
  });

  it('должен инициализировать Telegram SDK при монтировании', async () => {
    render(<MiniApp />);

    expect(telegramService.telegram.init).toHaveBeenCalled();
  });

  it('должен показать загрузку во время аутентификации', async () => {
    vi.mocked(api.authenticateUser).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockUser), 100))
    );

    render(<MiniApp />);

    expect(screen.getByText(/Загрузка.../i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText(/Загрузка.../i)).not.toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('должен показать экран AI чата после успешной аутентификации', async () => {
    render(<MiniApp />);

    await waitFor(() => {
      expect(screen.getByText(/PandaPal AI/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Panda чат/i)).toBeInTheDocument();
    expect(screen.getByText(/SOS/i)).toBeInTheDocument();
  });

  it('должен показать ошибку если initData пустой', async () => {
    vi.mocked(telegramService.telegram.getInitData).mockReturnValue('');

    render(<MiniApp />);

    await waitFor(() => {
      expect(screen.getByText(/Ошибка загрузки/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/через Telegram Mini App/i)).toBeInTheDocument();
  });

  it('должен показать ошибку при неудачной аутентификации', async () => {
    vi.mocked(api.authenticateUser).mockRejectedValue(
      new Error('Invalid Telegram signature')
    );

    render(<MiniApp />);

    await waitFor(() => {
      expect(screen.getByText(/Ошибка загрузки/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Попробовать снова/i)).toBeInTheDocument();
  });

  it('должен переключаться между экранами', async () => {
    const user = userEvent.setup();

    render(<MiniApp />);

    // Ждем загрузки
    await waitFor(() => {
      expect(screen.getByText(/PandaPal AI/i)).toBeInTheDocument();
    });

    // Проверяем что по умолчанию открыт AI чат
    expect(screen.getByText(/Задай вопрос.../i)).toBeInTheDocument();

    // Кликаем на SOS
    const sosButton = screen.getByRole('button', { name: /SOS/i });
    await user.click(sosButton);

    // Проверяем что открылся экран Emergency
    await waitFor(() => {
      expect(screen.getByText(/Экстренные номера/i)).toBeInTheDocument();
    });
  });

  it('должен вызывать haptic feedback при навигации', async () => {
    const user = userEvent.setup();

    render(<MiniApp />);

    await waitFor(() => {
      expect(screen.getByText(/PandaPal AI/i)).toBeInTheDocument();
    });

    const sosButton = screen.getByRole('button', { name: /SOS/i });
    await user.click(sosButton);

    expect(telegramService.telegram.hapticFeedback).toHaveBeenCalledWith('medium');
  });

  it('должен показать кнопку "Попробовать снова" при ошибке', async () => {
    const user = userEvent.setup();

    vi.mocked(api.authenticateUser).mockRejectedValue(new Error('Network error'));

    render(<MiniApp />);

    await waitFor(() => {
      expect(screen.getByText(/Ошибка загрузки/i)).toBeInTheDocument();
    });

    const retryButton = screen.getByRole('button', { name: /Попробовать снова/i });
    expect(retryButton).toBeInTheDocument();

    // Перезагружаем страницу при клике
    const reloadSpy = vi.spyOn(window.location, 'reload');
    reloadSpy.mockImplementation(() => {});

    await user.click(retryButton);

    expect(reloadSpy).toHaveBeenCalled();

    reloadSpy.mockRestore();
  });
});
