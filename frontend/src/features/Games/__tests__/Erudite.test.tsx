/**
 * Тесты для компонента Erudite (игра Эрудит)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Erudite } from '../Erudite';
import * as api from '../../../services/api';

vi.mock('../../../services/api');
vi.mock('../../../services/telegram', () => ({
  telegram: {
    hapticFeedback: vi.fn(),
    showPopup: vi.fn(),
    getInitData: vi.fn(() => ''),
  },
}));

const mockOnBack = vi.fn();
const mockOnGameEnd = vi.fn();

function makeEruditeState(overrides: Partial<api.EruditeStateResponse> = {}): api.EruditeStateResponse {
  const emptyBoard = Array(15)
    .fill(null)
    .map(() => Array(15).fill(''));
  const emptyBonus = Array(15)
    .fill(null)
    .map(() => Array(15).fill(0));
  return {
    board: emptyBoard,
    bonus_cells: emptyBonus,
    player_tiles: ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж'],
    ai_tiles: [],
    player_score: 0,
    ai_score: 0,
    current_player: 1,
    game_over: false,
    first_move: true,
    current_move: [],
    bag_count: 90,
    ...overrides,
  };
}

function makeGameSession(gameState: api.EruditeStateResponse) {
  return {
    id: 1,
    game_type: 'erudite' as const,
    game_state: gameState,
    result: 'in_progress' as const,
    score: null,
    started_at: '2024-01-01T00:00:00Z',
    finished_at: null,
    duration_seconds: null,
  };
}

describe('Erudite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getGameSession).mockResolvedValue(
      makeGameSession(makeEruditeState())
    );
  });

  it('показывает загрузку при получении данных', async () => {
    const bag: { resolve: ((v: Awaited<ReturnType<typeof api.getGameSession>>) => void) | null } = { resolve: null };
    vi.mocked(api.getGameSession).mockImplementation(
      () =>
        new Promise((resolve) => {
          bag.resolve = resolve;
        })
    );

    render(
      <Erudite sessionId={1} user={{} as api.UserProfile} onBack={mockOnBack} onGameEnd={mockOnGameEnd} />
    );

    expect(screen.getByText('Загрузка...')).toBeInTheDocument();

    bag.resolve!(makeGameSession(makeEruditeState()));
    await waitFor(() => {
      expect(screen.queryByText('Загрузка...')).not.toBeInTheDocument();
    });
  });

  it('отображает заголовок «эрудит», доску 15x15, блок «Ваши фишки», кнопку «Назад»', async () => {
    render(
      <Erudite sessionId={1} user={{} as api.UserProfile} onBack={mockOnBack} onGameEnd={mockOnGameEnd} />
    );

    await waitFor(() => {
      expect(screen.getByText(/эрудит/)).toBeInTheDocument();
      expect(screen.getByText('Ваши фишки:')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Назад' })).toBeInTheDocument();
    });

    const cells = document.querySelectorAll('[class*="aspect-square"]');
    expect(cells.length).toBe(15 * 15);
  });

  it('после загрузки отображает состояние (очки, фишки)', async () => {
    const state = makeEruditeState({ player_score: 10, ai_score: 5 });
    vi.mocked(api.getGameSession).mockResolvedValue(makeGameSession(state));

    render(
      <Erudite sessionId={1} user={{} as api.UserProfile} onBack={mockOnBack} onGameEnd={mockOnGameEnd} />
    );

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('А')).toBeInTheDocument();
    });
  });

  it('выбор фишки и клик по клетке вызывает eruditePlaceTile', async () => {
    const user = userEvent.setup();
    const nextState = makeEruditeState({
      player_tiles: ['Б', 'В', 'Г', 'Д', 'Е', 'Ж'],
      current_move: [[7, 7, 'А']],
    });
    vi.mocked(api.eruditePlaceTile).mockResolvedValue(nextState);

    render(
      <Erudite sessionId={1} user={{} as api.UserProfile} onBack={mockOnBack} onGameEnd={mockOnGameEnd} />
    );

    await waitFor(() => {
      expect(screen.getByText('Ваши фишки:')).toBeInTheDocument();
    });

    const tileA = screen.getByText('А').closest('button');
    expect(tileA).toBeTruthy();
    await user.click(tileA!);

    const centerCell = document.querySelector(
      '[class*="border-yellow-400"]'
    ) as HTMLElement;
    expect(centerCell).toBeTruthy();
    await user.click(centerCell);

    await waitFor(() => {
      expect(api.eruditePlaceTile).toHaveBeenCalledWith(1, 7, 7, 'А');
    });
  });

  it('при наличии current_move кнопка «Подтвердить» вызывает eruditeConfirmMove', async () => {
    const user = userEvent.setup();
    const stateWithMove = makeEruditeState({
      current_move: [[7, 7, 'А']],
      first_move: false,
    });
    vi.mocked(api.getGameSession).mockResolvedValue(makeGameSession(stateWithMove));
    vi.mocked(api.eruditeConfirmMove).mockResolvedValue(
      makeEruditeState({ current_move: [], current_player: 2 })
    );

    render(
      <Erudite sessionId={1} user={{} as api.UserProfile} onBack={mockOnBack} onGameEnd={mockOnGameEnd} />
    );

    await waitFor(() => {
      expect(screen.getByText(/Подтвердить/)).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /Подтвердить/ }));

    await waitFor(() => {
      expect(api.eruditeConfirmMove).toHaveBeenCalledWith(1);
    });
  });

  it('кнопка очистки хода вызывает eruditeClearMove', async () => {
    const user = userEvent.setup();
    const stateWithMove = makeEruditeState({
      current_move: [[7, 7, 'А']],
    });
    vi.mocked(api.getGameSession).mockResolvedValue(makeGameSession(stateWithMove));
    vi.mocked(api.eruditeClearMove).mockResolvedValue(
      makeEruditeState({ current_move: [] })
    );

    render(
      <Erudite sessionId={1} user={{} as api.UserProfile} onBack={mockOnBack} onGameEnd={mockOnGameEnd} />
    );

    await waitFor(() => {
      const clearBtn = screen.getByRole('button', { name: /🗑️/ });
      expect(clearBtn).toBeInTheDocument();
      return user.click(clearBtn);
    });

    await waitFor(() => {
      expect(api.eruditeClearMove).toHaveBeenCalledWith(1);
    });
  });

  it('при ошибке загрузки показывается сообщение и кнопка «Назад»', async () => {
    vi.mocked(api.getGameSession).mockRejectedValue(new Error('Network error'));

    render(
      <Erudite sessionId={1} user={{} as api.UserProfile} onBack={mockOnBack} onGameEnd={mockOnGameEnd} />
    );

    await waitFor(() => {
      expect(screen.getByText(/Не удалось загрузить игру|Ошибка загрузки игры/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Назад' })).toBeInTheDocument();
    });

    await userEvent.setup().click(screen.getByRole('button', { name: 'Назад' }));
    expect(mockOnBack).toHaveBeenCalled();
  });
});
