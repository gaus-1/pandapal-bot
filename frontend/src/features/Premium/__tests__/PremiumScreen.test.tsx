/**
 * Тесты для PremiumScreen
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PremiumScreen } from '../PremiumScreen';
import { telegram } from '../../../services/telegram';
import type { UserProfile } from '../../../services/api';

vi.mock('../../../services/telegram');

const mockUser: UserProfile = {
  telegram_id: 123456789,
  first_name: 'Test',
  user_type: 'child',
  age: 10,
  grade: 5,
  is_premium: false,
};

// Mock fetch
global.fetch = vi.fn();

describe('PremiumScreen', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.mocked(telegram.isInTelegram).mockReturnValue(true);
    vi.mocked(telegram.hapticFeedback).mockImplementation(() => {});
    vi.mocked(telegram.showAlert).mockResolvedValue(undefined);
    vi.mocked(telegram.openLink).mockImplementation(() => {});
    vi.mocked(telegram.notifyError).mockImplementation(() => {});

    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        confirmation_url: 'https://yookassa.ru/payment',
      }),
    } as Response);
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('отображает тарифный план', async () => {
    render(<PremiumScreen user={mockUser} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PandaPal Premium')).toBeInTheDocument();
    });

    expect(screen.getByText('Месяц')).toBeInTheDocument();
  });

  it('отображает цену плана', async () => {
    render(<PremiumScreen user={mockUser} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('299 ₽')).toBeInTheDocument();
    });
  });

  it('создает платеж при клике на кнопку покупки', async () => {
    const user = userEvent.setup();

    render(<PremiumScreen user={mockUser} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Premium за 299 ₽/)).toBeInTheDocument();
    });

    const buyButton = screen.getByText(/Premium за 299 ₽/);
    await user.click(buyButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/miniapp/premium/create-payment',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: expect.stringContaining('"plan_id":"month"'),
        })
      );
    });
  });

  it('открывает страницу оплаты при успешном создании платежа', async () => {
    const user = userEvent.setup();

    render(<PremiumScreen user={mockUser} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Premium за 299 ₽/)).toBeInTheDocument();
    });

    const buyButton = screen.getByText(/Premium за 299 ₽/);
    await user.click(buyButton);

    await waitFor(() => {
      expect(telegram.openLink).toHaveBeenCalledWith('https://yookassa.ru/payment');
    });
  });

  it('обрабатывает ошибки при создании платежа', async () => {
    const user = userEvent.setup();
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      json: async () => ({
        success: false,
        error: 'Ошибка создания платежа',
      }),
    } as Response);

    render(<PremiumScreen user={mockUser} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Premium за 299 ₽/)).toBeInTheDocument();
    });

    const buyButton = screen.getByText(/Premium за 299 ₽/);
    await user.click(buyButton);

    await waitFor(() => {
      expect(telegram.showAlert).toHaveBeenCalledWith(
        expect.stringContaining('Ошибка создания платежа')
      );
    });
  });

  it('показывает статус Premium если пользователь имеет Premium', async () => {
    const premiumUser = { ...mockUser, is_premium: true };

    render(<PremiumScreen user={premiumUser} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('✅ Premium активен')).toBeInTheDocument();
    });
  });

  it('показывает информацию о способах оплаты', async () => {
    render(<PremiumScreen user={mockUser} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Оплата только через Telegram/)).toBeInTheDocument();
    });
  });

  it('блокирует кнопку покупки во время обработки', async () => {
    const user = userEvent.setup();
    vi.mocked(global.fetch).mockImplementation(
      () =>
        new Promise(resolve =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: async () => ({
                  success: true,
                  confirmation_url: 'https://yookassa.ru/payment',
                }),
              } as Response),
            100
          )
        )
    );

    render(<PremiumScreen user={mockUser} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Premium за 299 ₽/)).toBeInTheDocument();
    });

    const buyButton = screen.getByText(/Premium за 299 ₽/);
    await user.click(buyButton);

    // Кнопка должна показывать "Обработка..."
    await waitFor(() => {
      expect(screen.getByText('Обработка...')).toBeInTheDocument();
    });
  });
});
