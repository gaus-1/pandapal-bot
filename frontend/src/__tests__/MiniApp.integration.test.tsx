/**
 * Integration тесты для MiniApp
 * Проверяет полный flow: аутентификация, навигация, загрузка данных
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MiniApp } from '../MiniApp';
import * as api from '../services/api';
import { createTelegramServiceMock, createMockInitData } from '../test/mocks/telegram.mock';
import { mockUserProfile, mockChatHistory, mockApiResponses } from '../test/mocks/api.mock';

// Mock API с реалистичными ответами
vi.mock('../services/api', () => ({
  authenticateUser: vi.fn(),
  getChatHistory: vi.fn(),
  sendAIMessage: vi.fn(),
}));

// Mock Telegram service - создаём мок внутри factory
vi.mock('../services/telegram', () => {
  const { createTelegramServiceMock } = require('../test/mocks/telegram.mock');
  return {
    telegram: createTelegramServiceMock(),
  };
});

describe('MiniApp Integration', () => {
  let telegram: ReturnType<typeof createTelegramServiceMock>;

  beforeEach(async () => {
    // Очищаем все моки
    vi.clearAllMocks();

    // Получаем telegram mock
    const telegramModule = await import('../services/telegram');
    telegram = telegramModule.telegram as any;

    // Настраиваем API моки с реалистичными ответами
    vi.mocked(api.authenticateUser).mockImplementation(mockApiResponses.authenticateUser);
    vi.mocked(api.getChatHistory).mockImplementation(mockApiResponses.getChatHistory);
    vi.mocked(api.sendAIMessage).mockImplementation(mockApiResponses.sendAIMessage);

    // Убеждаемся что Telegram mock возвращает правильный initData
    vi.mocked(telegram.getInitData).mockReturnValue(createMockInitData());
    vi.mocked(telegram.getUser).mockReturnValue({
      id: 123456789,
      first_name: 'Test',
      last_name: 'User',
      username: 'testuser',
      language_code: 'ru',
      is_premium: false,
    });
    vi.mocked(telegram.isTelegramWebApp).mockReturnValue(true);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('должен инициализировать Telegram SDK при монтировании', async () => {
    render(<MiniApp />);

    expect(telegram.init).toHaveBeenCalled();
    expect(telegram.getInitData).toHaveBeenCalled();
  });

  it('должен показать загрузку во время аутентификации', async () => {
    // Замедляем аутентификацию для теста
    vi.mocked(api.authenticateUser).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockUserProfile), 150))
    );

    render(<MiniApp />);

    // Проверяем что показывается загрузка
    expect(screen.getByText(/Загрузка/i)).toBeInTheDocument();

    // Ждём завершения аутентификации
    await waitFor(() => {
      expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('должен показать экран AI чата после успешной аутентификации', async () => {
    render(<MiniApp />);

    // Ждём загрузки приложения
    await waitFor(() => {
      expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
    }, { timeout: 5000 });

    // Проверяем что отображается интерфейс чата
    expect(screen.getByText(/PandaPal AI/i)).toBeInTheDocument();

    // Проверяем навигационные кнопки
    expect(screen.getByRole('button', { name: /Panda чат/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /SOS/i })).toBeInTheDocument();

    // Проверяем что есть поле ввода
    expect(screen.getByPlaceholderText(/Задай вопрос/i)).toBeInTheDocument();
  });

  it('должен показать ошибку если initData пустой', async () => {
    // Mock возвращает пустой initData
    vi.mocked(telegram.getInitData).mockReturnValue('');

    render(<MiniApp />);

    // Ждём появления ошибки
    await waitFor(() => {
      expect(screen.getByText(/Ошибка загрузки/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Проверяем текст ошибки
    expect(screen.getByText(/Telegram Mini App/i)).toBeInTheDocument();
  });

  it('должен показать ошибку при неудачной аутентификации', async () => {
    vi.mocked(api.authenticateUser).mockRejectedValue(
      new Error('Invalid Telegram signature')
    );

    render(<MiniApp />);

    // Ждём появления ошибки
    await waitFor(() => {
      expect(screen.getByText(/Ошибка загрузки/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Проверяем что есть кнопка retry
    expect(screen.getByRole('button', { name: /Попробовать снова/i })).toBeInTheDocument();
  });

  it('должен переключаться между экранами', async () => {
    const user = userEvent.setup();

    render(<MiniApp />);

    // Ждем загрузки приложения
    await waitFor(() => {
      expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
    }, { timeout: 5000 });

    // Проверяем что по умолчанию открыт AI чат
    expect(screen.getByPlaceholderText(/Задай вопрос/i)).toBeInTheDocument();

    // Находим и кликаем на кнопку SOS
    const sosButton = screen.getByRole('button', { name: /SOS/i });
    await user.click(sosButton);

    // Проверяем что открылся экран Emergency
    await waitFor(() => {
      expect(screen.getByText(/Экстренные номера/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Проверяем что есть экстренные номера
    expect(screen.getByText(/112/)).toBeInTheDocument();
  });

  it('должен вызывать haptic feedback при навигации', async () => {
    const user = userEvent.setup();

    render(<MiniApp />);

    // Ждем загрузки
    await waitFor(() => {
      expect(screen.queryByText(/Загрузка/i)).not.toBeInTheDocument();
    }, { timeout: 5000 });

    // Кликаем на кнопку SOS
    const sosButton = screen.getByRole('button', { name: /SOS/i });
    await user.click(sosButton);

    // Проверяем что был вызван haptic feedback
    expect(telegram.hapticFeedback).toHaveBeenCalledWith('medium');
  });

  it('должен показать кнопку "Попробовать снова" при ошибке', async () => {
    const user = userEvent.setup();

    vi.mocked(api.authenticateUser).mockRejectedValue(new Error('Network error'));

    render(<MiniApp />);

    // Ждём появления ошибки
    await waitFor(() => {
      expect(screen.getByText(/Ошибка загрузки/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Находим кнопку retry
    const retryButton = screen.getByRole('button', { name: /Попробовать снова/i });
    expect(retryButton).toBeInTheDocument();

    // Mock window.location.reload
    const reloadMock = vi.fn();
    Object.defineProperty(window.location, 'reload', {
      configurable: true,
      value: reloadMock,
    });

    // Кликаем на кнопку
    await user.click(retryButton);

    // Проверяем что была вызвана перезагрузка
    expect(reloadMock).toHaveBeenCalled();
  });
});
