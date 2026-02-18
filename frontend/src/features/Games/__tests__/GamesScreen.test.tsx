/**
 * Тесты для GamesScreen
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GamesScreen } from '../GamesScreen';
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

describe('GamesScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getGameStats).mockResolvedValue({});
  });

  it('отображает список игр', async () => {
    render(<GamesScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByText('🎮 PandaPalGo')).toBeInTheDocument();
      expect(screen.getByText('Крестики-нолики')).toBeInTheDocument();
      expect(screen.getByText('Шашки')).toBeInTheDocument();
      expect(screen.getByText('2048')).toBeInTheDocument();
      expect(screen.getByText('эрудит')).toBeInTheDocument();
    });
  });

  it('создает игру при клике на карточку', async () => {
    const user = userEvent.setup();
    vi.mocked(api.createGame).mockResolvedValue({
      session_id: 1,
      game_type: 'tic_tac_toe',
      game_state: { board: Array(9).fill(null) },
    });

    render(<GamesScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByText('Крестики-нолики')).toBeInTheDocument();
    });

    const gameButton = screen.getByText('Крестики-нолики').closest('button');
    if (gameButton) {
      await user.click(gameButton);
    }

    await waitFor(() => {
      expect(api.createGame).toHaveBeenCalledWith(mockUser.telegram_id, 'tic_tac_toe');
    });
  });

  it('отображает статистику игр', async () => {
    vi.mocked(api.getGameStats).mockResolvedValue({
      tic_tac_toe: {
        game_type: 'tic_tac_toe',
        total_games: 10,
        wins: 7,
        losses: 3,
        draws: 0,
        win_rate: 70.0,
        best_score: null,
        total_score: 0,
        last_played_at: '2024-01-01T00:00:00Z',
      },
    });

    render(<GamesScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByText('📊 Твоя статистика')).toBeInTheDocument();
      expect(screen.getByText('7 побед')).toBeInTheDocument();
    });
  });

  it('обрабатывает ошибки при создании игры', async () => {
    const user = userEvent.setup();
    vi.mocked(api.createGame).mockRejectedValue(new Error('Ошибка создания игры'));

    render(<GamesScreen user={mockUser} />);

    await waitFor(() => {
      expect(screen.getByText('Крестики-нолики')).toBeInTheDocument();
    });

    const gameButton = screen.getByText('Крестики-нолики').closest('button');
    if (gameButton) {
      await user.click(gameButton);
    }

    await waitFor(() => {
      expect(telegram.notifyError).toHaveBeenCalled();
    });
  });
});
