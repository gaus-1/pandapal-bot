/**
 * Тесты для TicTacToe
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TicTacToe } from '../TicTacToe';
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

describe('TicTacToe', () => {
  const mockOnBack = vi.fn();
  const mockOnGameEnd = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getGameSession).mockResolvedValue({
      id: 1,
      game_type: 'tic_tac_toe',
      game_state: { board: Array(9).fill(null) },
      result: 'in_progress',
      score: null,
      started_at: '2024-01-01T00:00:00Z',
      finished_at: null,
      duration_seconds: null,
    });
  });

  it('отображает игровую доску', async () => {
    render(
      <TicTacToe
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/❌⭕ Крестики-нолики/)).toBeInTheDocument();
    });

    // Проверяем наличие 9 клеток
    const buttons = screen.getAllByRole('button');
    const gameButtons = buttons.filter((btn) =>
      btn.getAttribute('aria-label')?.startsWith('Клетка')
    );
    expect(gameButtons.length).toBe(9);
  });

  it('делает ход при клике на клетку', async () => {
    const user = userEvent.setup();
    vi.mocked(api.ticTacToeMove).mockResolvedValue({
      board: ['X', null, null, 'O', null, null, null, null, null],
      winner: null,
      game_over: false,
      ai_move: 3,
    });

    render(
      <TicTacToe
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Твой ход!')).toBeInTheDocument();
    });

    const firstCell = screen.getByLabelText('Клетка 1');
    await user.click(firstCell);

    await waitFor(() => {
      expect(api.ticTacToeMove).toHaveBeenCalledWith(1, 0);
      expect(telegram.hapticFeedback).toHaveBeenCalledWith('light');
    });
  });

  it('показывает победу пользователя', async () => {
    const user = userEvent.setup();
    vi.mocked(api.ticTacToeMove).mockResolvedValue({
      board: ['X', 'X', 'X', 'O', 'O', null, null, null, null],
      winner: 'user',
      game_over: true,
      ai_move: null,
    });

    render(
      <TicTacToe
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Твой ход!')).toBeInTheDocument();
    });

    const firstCell = screen.getByLabelText('Клетка 1');
    await user.click(firstCell);

    await waitFor(() => {
      expect(screen.getByText('🎉 Ты победил!')).toBeInTheDocument();
      expect(telegram.notifySuccess).toHaveBeenCalled();
      expect(mockOnGameEnd).toHaveBeenCalled();
    });
  });

  it('показывает поражение', async () => {
    const user = userEvent.setup();
    vi.mocked(api.ticTacToeMove).mockResolvedValue({
      board: ['O', 'O', 'O', 'X', 'X', null, null, null, null],
      winner: 'ai',
      game_over: true,
      ai_move: null,
    });

    render(
      <TicTacToe
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Твой ход!')).toBeInTheDocument();
    });

    const firstCell = screen.getByLabelText('Клетка 1');
    await user.click(firstCell);

    await waitFor(() => {
      expect(screen.getByText('😔 Панда победила!')).toBeInTheDocument();
      expect(telegram.notifyWarning).toHaveBeenCalled();
    });
  });

  it('не позволяет ходить в занятую клетку', async () => {
    vi.mocked(api.getGameSession).mockResolvedValue({
      id: 1,
      game_type: 'tic_tac_toe',
      game_state: { board: ['X', null, null, null, null, null, null, null, null] },
      result: 'in_progress',
      score: null,
      started_at: '2024-01-01T00:00:00Z',
      finished_at: null,
      duration_seconds: null,
    });

    render(
      <TicTacToe
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      const firstCell = screen.getByLabelText('Клетка 1');
      expect(firstCell).toBeDisabled();
    });
  });
});
