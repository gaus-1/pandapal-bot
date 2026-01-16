import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Tetris } from '../Tetris';

// Лёгкий smoke-тест на монтирование и базовые кнопки

vi.mock('../../../services/telegram', () => ({
  telegram: {
    hapticFeedback: vi.fn(),
    notifyError: vi.fn(),
    notifyWarning: vi.fn(),
  },
}));

vi.mock('../../../services/api', () => ({
  getGameSession: vi.fn().mockResolvedValue({
    game_state: {
      board: Array.from({ length: 20 }, () => Array(10).fill(0)),
      score: 0,
      lines_cleared: 0,
      game_over: false,
      width: 10,
      height: 20,
    },
  }),
  tetrisMove: vi.fn().mockResolvedValue({
    board: Array.from({ length: 20 }, () => Array(10).fill(0)),
    score: 0,
    lines_cleared: 0,
    game_over: false,
    width: 10,
    height: 20,
  }),
}));

const mockUser = {
  telegram_id: 1,
  user_type: 'child',
  is_premium: false,
} as const;

describe('Tetris', () => {
  it('рендерит поле и кнопки управления', async () => {
    render(
      <Tetris
        sessionId={123}
        user={mockUser}
        onBack={vi.fn()}
        onGameEnd={vi.fn()}
      />,
    );

    expect(await screen.findByText('🧱 Тетрис')).toBeInTheDocument();

    expect(screen.getByText('← Влево')).toBeInTheDocument();
    expect(screen.getByText('⟳ Повернуть')).toBeInTheDocument();
    expect(screen.getByText('Вправо →')).toBeInTheDocument();
    expect(screen.getByText('↓ Быстрее')).toBeInTheDocument();

    fireEvent.click(screen.getByText('↓ Быстрее'));
  });
});
