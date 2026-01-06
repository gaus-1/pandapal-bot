/**
 * Тесты для Game2048
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Game2048 } from '../Game2048';
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

describe('Game2048', () => {
  const mockOnBack = vi.fn();
  const mockOnGameEnd = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getGameSession).mockResolvedValue({
      id: 1,
      game_type: '2048',
      game_state: { board: null, score: 0 },
      result: 'in_progress',
      score: null,
      started_at: '2024-01-01T00:00:00Z',
      finished_at: null,
      duration_seconds: null,
    });
  });

  it('отображает игровую доску', async () => {
    render(
      <Game2048
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('🔢 2048')).toBeInTheDocument();
    });

    // Проверяем наличие кнопки "Назад"
    const backButton = screen.getByText('← Назад');
    expect(backButton).toBeInTheDocument();
  });

  it('делает ход при клике на кнопку направления', async () => {
    const user = userEvent.setup();
    vi.mocked(api.game2048Move).mockResolvedValue({
      board: Array(4).fill(null).map(() => Array(4).fill(0)),
      score: 0,
      won: false,
      game_over: false,
    });

    render(
      <Game2048
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Вверх')).toBeInTheDocument();
    });

    const upButton = screen.getByLabelText('Вверх');
    await user.click(upButton);

    await waitFor(() => {
      expect(api.game2048Move).toHaveBeenCalledWith(1, 'up');
      expect(telegram.hapticFeedback).toHaveBeenCalledWith('light');
    });
  });

  it('обрабатывает все направления движения', async () => {
    const user = userEvent.setup();
    vi.mocked(api.game2048Move).mockResolvedValue({
      board: Array(4).fill(null).map(() => Array(4).fill(0)),
      score: 0,
      won: false,
      game_over: false,
    });

    render(
      <Game2048
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Вверх')).toBeInTheDocument();
    });

    const directions = ['Вверх', 'Вниз', 'Влево', 'Вправо'];
    const directionKeys: ('up' | 'down' | 'left' | 'right')[] = ['up', 'down', 'left', 'right'];

    for (let i = 0; i < directions.length; i++) {
      const button = screen.getByLabelText(directions[i]);
      await user.click(button);

      await waitFor(() => {
        expect(api.game2048Move).toHaveBeenCalledWith(1, directionKeys[i]);
      });
    }
  });

  it('показывает победу при достижении 2048', async () => {
    const user = userEvent.setup();
    vi.mocked(api.game2048Move).mockResolvedValue({
      board: Array(4).fill(null).map(() => Array(4).fill(0)),
      score: 2048,
      won: true,
      game_over: false,
    });

    render(
      <Game2048
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Вверх')).toBeInTheDocument();
    });

    const upButton = screen.getByLabelText('Вверх');
    await user.click(upButton);

    await waitFor(() => {
      expect(telegram.notifySuccess).toHaveBeenCalled();
    });
  });

  it('показывает окончание игры', async () => {
    const user = userEvent.setup();
    vi.mocked(api.game2048Move).mockResolvedValue({
      board: Array(4).fill(null).map(() => Array(4).fill(0)),
      score: 100,
      won: false,
      game_over: true,
    });

    render(
      <Game2048
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Вверх')).toBeInTheDocument();
    });

    const upButton = screen.getByLabelText('Вверх');
    await user.click(upButton);

    await waitFor(() => {
      expect(telegram.notifyError).toHaveBeenCalled();
      expect(mockOnGameEnd).toHaveBeenCalled();
    });
  });

  it('вызывает onBack при клике на кнопку "Назад"', async () => {
    const user = userEvent.setup();

    render(
      <Game2048
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('← Назад')).toBeInTheDocument();
    });

    const backButton = screen.getByText('← Назад');
    await user.click(backButton);

    expect(mockOnBack).toHaveBeenCalled();
  });

  it('обрабатывает ошибки при ходе', async () => {
    const user = userEvent.setup();
    vi.mocked(api.game2048Move).mockRejectedValue(new Error('Ошибка хода'));

    render(
      <Game2048
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Вверх')).toBeInTheDocument();
    });

    const upButton = screen.getByLabelText('Вверх');
    await user.click(upButton);

    await waitFor(() => {
      expect(telegram.notifyError).toHaveBeenCalled();
    });
  });

  it('блокирует кнопки во время загрузки', async () => {
    const user = userEvent.setup();
    vi.mocked(api.game2048Move).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        board: Array(4).fill(null).map(() => Array(4).fill(0)),
        score: 0,
        won: false,
        game_over: false,
      }), 100))
    );

    render(
      <Game2048
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Вверх')).toBeInTheDocument();
    });

    const upButton = screen.getByLabelText('Вверх');
    await user.click(upButton);

    // Кнопки должны быть disabled во время загрузки
    expect(upButton).toBeDisabled();
  });
});
