/**
 * Тесты для навигации в MiniApp
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MiniApp } from '../../MiniApp';
import { useAppStore } from '../../store/appStore';
import { telegram } from '../../services/telegram';

vi.mock('../../services/telegram');
vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    authenticate: vi.fn(),
  }),
}));

const mockUser = {
  telegram_id: 123456789,
  first_name: 'Test',
  user_type: 'child' as const,
  age: 10,
  grade: 5,
  is_premium: false,
};

describe('MiniApp Navigation', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    // Устанавливаем пользователя в store
    useAppStore.setState({
      user: mockUser,
      currentScreen: 'ai-chat',
      isLoading: false,
      error: null,
    });

    vi.mocked(telegram.isInTelegram).mockReturnValue(true);
    vi.mocked(telegram.getInitData).mockReturnValue('test');
    vi.mocked(telegram.getUser).mockReturnValue(mockUser);
    vi.mocked(telegram.hapticFeedback).mockImplementation(() => {});
    vi.mocked(telegram.showBackButton).mockImplementation(() => {});
    vi.mocked(telegram.hideBackButton).mockImplementation(() => {});
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('переключает на экран игр при клике на кнопку PandaPalGo', async () => {
    const user = userEvent.setup();

    render(<MiniApp />, { wrapper });

    await waitFor(() => {
      const gamesButton = screen.getByLabelText('PandaPalGo');
      expect(gamesButton).toBeInTheDocument();
    });

    const gamesButton = screen.getByLabelText('PandaPalGo');
    await user.click(gamesButton);

    await waitFor(() => {
      expect(useAppStore.getState().currentScreen).toBe('games');
      expect(telegram.hapticFeedback).toHaveBeenCalledWith('medium');
    });
  });

  it('переключает на экран Premium при клике на кнопку Premium', async () => {
    const user = userEvent.setup();

    render(<MiniApp />, { wrapper });

    await waitFor(() => {
      const premiumButton = screen.getByLabelText('Premium');
      expect(premiumButton).toBeInTheDocument();
    });

    const premiumButton = screen.getByLabelText('Premium');
    await user.click(premiumButton);

    await waitFor(() => {
      expect(useAppStore.getState().currentScreen).toBe('premium');
      expect(telegram.hapticFeedback).toHaveBeenCalledWith('medium');
    });
  });

  it('переключает на экран достижений при клике на кнопку Достижения', async () => {
    const user = userEvent.setup();

    render(<MiniApp />, { wrapper });

    await waitFor(() => {
      const achievementsButton = screen.getByLabelText('Достижения');
      expect(achievementsButton).toBeInTheDocument();
    });

    const achievementsButton = screen.getByLabelText('Достижения');
    await user.click(achievementsButton);

    await waitFor(() => {
      expect(useAppStore.getState().currentScreen).toBe('achievements');
      expect(telegram.hapticFeedback).toHaveBeenCalledWith('medium');
    });
  });

  it('возвращается на экран чата при клике на кнопку Чат', async () => {
    const user = userEvent.setup();
    useAppStore.setState({ currentScreen: 'premium' });

    render(<MiniApp />, { wrapper });

    await waitFor(() => {
      const chatButton = screen.getByLabelText('Чат');
      expect(chatButton).toBeInTheDocument();
    });

    const chatButton = screen.getByLabelText('Чат');
    await user.click(chatButton);

    await waitFor(() => {
      expect(useAppStore.getState().currentScreen).toBe('ai-chat');
      expect(telegram.hapticFeedback).toHaveBeenCalledWith('medium');
    });
  });
});
