/**
 * Тесты для MyPandaScreen.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MyPandaScreen } from '../MyPandaScreen';
import * as api from '../../../services/api';
import { telegram } from '../../../services/telegram';

vi.mock('../../../services/api');
vi.mock('../../../services/telegram');

const mockUser = {
  telegram_id: 123456789,
  first_name: 'Test',
  user_type: 'child' as const,
  age: 10,
  grade: 5,
  is_premium: false,
};

const mockState = {
  hunger: 60,
  mood: 70,
  energy: 50,
  last_fed_at: null as string | null,
  last_played_at: null as string | null,
  last_slept_at: null as string | null,
  can_feed: true,
  can_play: true,
  can_sleep: true,
  consecutive_visit_days: 1,
  achievements: {},
};

describe('MyPandaScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getPandaPetState).mockResolvedValue(mockState);
    vi.mocked(telegram.notifyError).mockImplementation(() => {});
    vi.mocked(telegram.showAlert).mockResolvedValue();
  });

  it('отображает заголовок, панду, индикаторы и кнопки', async () => {
    render(<MyPandaScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByText('Моя панда')).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/Панда/)).toBeInTheDocument();
    expect(screen.getByText('Голод')).toBeInTheDocument();
    expect(screen.getByText('Настроение')).toBeInTheDocument();
    expect(screen.getByText('Энергия')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Покормить панду/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Играть с пандой/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Уложить панду спать/ })).toBeInTheDocument();
  });

  it('загружает состояние при монтировании', async () => {
    render(<MyPandaScreen user={mockUser} />);

    await waitFor(() => {
      expect(api.getPandaPetState).toHaveBeenCalledWith(mockUser.telegram_id);
    });
  });

  it('при клике «Покормить» вызывает feedPandaPet и обновляет состояние', async () => {
    const user = userEvent.setup();
    const nextState = { ...mockState, hunger: 85, can_feed: true };
    vi.mocked(api.feedPandaPet).mockResolvedValue(nextState);

    render(<MyPandaScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Покормить панду/ })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Покормить панду/ }));

    await waitFor(() => {
      expect(api.feedPandaPet).toHaveBeenCalledWith(mockUser.telegram_id);
    });
  });

  it('при клике «Играть» вызывает playPandaPet', async () => {
    const user = userEvent.setup();
    vi.mocked(api.playPandaPet).mockResolvedValue({ ...mockState, mood: 90 });

    render(<MyPandaScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Играть с пандой/ })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Играть с пандой/ }));

    await waitFor(() => {
      expect(api.playPandaPet).toHaveBeenCalledWith(mockUser.telegram_id);
    });
  });

  it('при клике «Уложить спать» вызывает sleepPandaPet', async () => {
    const user = userEvent.setup();
    vi.mocked(api.sleepPandaPet).mockResolvedValue({ ...mockState, energy: 80 });

    render(<MyPandaScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Уложить панду спать/ })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Уложить панду спать/ }));

    await waitFor(() => {
      expect(api.sleepPandaPet).toHaveBeenCalledWith(mockUser.telegram_id);
    });
  });

  it('при ошибке API показывает сообщение и notifyError', async () => {
    vi.mocked(api.getPandaPetState).mockRejectedValue(new Error('Network error'));

    render(<MyPandaScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByText(/Network error|Ошибка/)).toBeInTheDocument();
    });

    expect(telegram.notifyError).toHaveBeenCalled();
  });

  it('кнопка «Попробовать снова» перезапрашивает состояние', async () => {
    vi.mocked(api.getPandaPetState).mockRejectedValueOnce(new Error('Fail'));

    render(<MyPandaScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Попробовать снова/ })).toBeInTheDocument();
    });

    vi.mocked(api.getPandaPetState).mockResolvedValue(mockState);

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: /Попробовать снова/ }));

    await waitFor(() => {
      expect(api.getPandaPetState).toHaveBeenCalledTimes(2);
    });
  });
});
