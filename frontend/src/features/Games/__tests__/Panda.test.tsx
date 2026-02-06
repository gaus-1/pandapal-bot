/**
 * Тесты для экрана Моя панда (Panda)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Panda } from '../Panda';
import * as pandaApi from '../../../services/api/panda';

vi.mock('../../../services/api/panda');
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
  display_state: 'neutral',
  achievements: [],
  can_feed: true,
  can_play: true,
  sleep_need_feed_first: true,
  total_fed_count: 0,
  total_played_count: 0,
  consecutive_visit_days: 0,
};

describe('Panda', () => {
  const onBack = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(pandaApi.getPandaState).mockResolvedValue(mockState);
  });

  it('загружает и отображает состояние панды', async () => {
    render(<Panda user={mockUser} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText('Моя панда')).toBeInTheDocument();
    });

    expect(pandaApi.getPandaState).toHaveBeenCalledWith(mockUser.telegram_id);
    expect(screen.getByText('Голод')).toBeInTheDocument();
    expect(screen.getByText('Настроение')).toBeInTheDocument();
    expect(screen.getByText('Энергия')).toBeInTheDocument();
  });

  it('отображает кнопки Покормить, Поиграть, Уложить спать', async () => {
    render(<Panda user={mockUser} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Покормить/ })).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /Поиграть/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Уложить спать/ })).toBeInTheDocument();
  });

  it('при клике Назад вызывает onBack', async () => {
    const user = userEvent.setup();
    render(<Panda user={mockUser} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Назад/ })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Назад/ }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('при клике Покормить вызывает pandaFeed и обновляет состояние', async () => {
    const user = userEvent.setup();
    vi.mocked(pandaApi.pandaFeed).mockResolvedValue({
      success: true,
      message: 'full',
      state: { ...mockState, hunger: 95, total_fed_count: 1 },
    });

    render(<Panda user={mockUser} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Покормить/ })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Покормить/ }));

    await waitFor(() => {
      expect(pandaApi.pandaFeed).toHaveBeenCalledWith(mockUser.telegram_id);
    });
  });
});
