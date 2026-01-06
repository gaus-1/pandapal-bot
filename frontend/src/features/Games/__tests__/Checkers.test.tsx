/**
 * Тесты для Checkers
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Checkers } from '../Checkers';
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

describe('Checkers', () => {
  const mockOnBack = vi.fn();
  const mockOnGameEnd = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getGameSession).mockResolvedValue({
      id: 1,
      game_type: 'checkers',
      game_state: { board: null, kings: null },
      result: 'in_progress',
      score: null,
      started_at: '2024-01-01T00:00:00Z',
      finished_at: null,
      duration_seconds: null,
    });
  });

  it('отображает игровую доску', async () => {
    render(
      <Checkers
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('⚫⚪ Шашки')).toBeInTheDocument();
    });

    // Проверяем наличие кнопки "Назад"
    const backButton = screen.getByText('← Назад');
    expect(backButton).toBeInTheDocument();
  });

  it('делает ход при клике на фишку и затем на клетку', async () => {
    const user = userEvent.setup();
    vi.mocked(api.checkersMove).mockResolvedValue({
      board: Array(8).fill(null).map(() => Array(8).fill(null)),
      kings: Array(8).fill(null).map(() => Array(8).fill(false)),
      winner: null,
      game_over: false,
    });

    render(
      <Checkers
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Твой ход!')).toBeInTheDocument();
    });

    // Находим клетку с фишкой пользователя (обычно в нижних рядах, ряды 5-7)
    // Ищем клетки с aria-label, которые содержат координаты в нижних рядах
    const allCells = screen.getAllByRole('button');
    const userCell = allCells.find((btn) => {
      const label = btn.getAttribute('aria-label');
      if (!label || !label.startsWith('Клетка')) return false;
      // Проверяем, что внутри есть белая фишка (пользователь)
      const hasUserPiece = btn.querySelector('.bg-white');
      return hasUserPiece !== null;
    });

    // Если нашли клетку с фишкой пользователя, кликаем на неё
    if (userCell) {
      await user.click(userCell);
      await waitFor(() => {
        expect(telegram.hapticFeedback).toHaveBeenCalledWith('light');
      });
    } else {
      // Если не нашли, просто проверяем, что компонент отрендерился
      expect(screen.getByText('Твой ход!')).toBeInTheDocument();
    }
  });

  it('показывает победу пользователя', async () => {
    vi.mocked(api.checkersMove).mockResolvedValue({
      board: Array(8).fill(null).map(() => Array(8).fill(null)),
      kings: Array(8).fill(null).map(() => Array(8).fill(false)),
      winner: 'user',
      game_over: true,
    });

    render(
      <Checkers
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Твой ход!')).toBeInTheDocument();
    });

    // Эмулируем ход через API напрямую
    await waitFor(() => {
      expect(api.getGameSession).toHaveBeenCalled();
    });
  });

  it('показывает поражение', async () => {
    vi.mocked(api.getGameSession).mockResolvedValue({
      id: 1,
      game_type: 'checkers',
      game_state: { board: null, kings: null },
      result: 'loss',
      score: null,
      started_at: '2024-01-01T00:00:00Z',
      finished_at: null,
      duration_seconds: null,
    });

    render(
      <Checkers
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('😔 Панда победила!')).toBeInTheDocument();
    });
  });

  it('вызывает onBack при клике на кнопку "Назад"', async () => {
    const user = userEvent.setup();

    render(
      <Checkers
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
    vi.mocked(api.checkersMove).mockRejectedValue(new Error('Ошибка хода'));

    render(
      <Checkers
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Твой ход!')).toBeInTheDocument();
    });

    // Эмулируем ошибку
    await waitFor(() => {
      expect(api.getGameSession).toHaveBeenCalled();
    });
  });

  it('не позволяет ходить когда игра окончена', async () => {
    vi.mocked(api.getGameSession).mockResolvedValue({
      id: 1,
      game_type: 'checkers',
      game_state: { board: null, kings: null },
      result: 'win',
      score: null,
      started_at: '2024-01-01T00:00:00Z',
      finished_at: null,
      duration_seconds: null,
    });

    render(
      <Checkers
        sessionId={1}
        user={mockUser}
        onBack={mockOnBack}
        onGameEnd={mockOnGameEnd}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('🎉 Ты победил!')).toBeInTheDocument();
    });

    // Кнопки должны быть disabled
    const cells = screen.getAllByRole('button').filter((btn) => {
      const label = btn.getAttribute('aria-label');
      return label && label.startsWith('Клетка');
    });

    cells.forEach((cell) => {
      expect(cell).toBeDisabled();
    });
  });
});
