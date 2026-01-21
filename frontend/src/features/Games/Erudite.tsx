/**
 * Erudite Game Component
 * Игра Эрудит - составление слов
 */

import { useState, useEffect } from 'react';
import { getGameSession, type UserProfile } from '../../services/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

interface EruditeProps {
  sessionId: number;
  user: UserProfile;
  onBack: () => void;
  onGameEnd: () => void;
}

interface EruditeState {
  board: string[][];
  bonus_cells: number[][];
  player_tiles: string[];
  ai_tiles: string[];
  player_score: number;
  ai_score: number;
  current_player: number;
  game_over: boolean;
  first_move: boolean;
  current_move: Array<[number, number, string]>;
  bag_count: number;
}

export function Erudite({ sessionId, onBack, onGameEnd }: EruditeProps) {
  const [state, setState] = useState<EruditeState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTile, setSelectedTile] = useState<string | null>(null);

  useEffect(() => {
    loadGame();
  }, [sessionId]);

  const loadGame = async () => {
    try {
      setLoading(true);
      const session = await getGameSession(sessionId);
      if (session.game_state) {
        const gameState = session.game_state as Record<string, unknown>;
        setState({
          board: (gameState.board as string[][]) || [],
          bonus_cells: (gameState.bonus_cells as number[][]) || [],
          player_tiles: (gameState.player_tiles as string[]) || [],
          ai_tiles: (gameState.ai_tiles as string[]) || [],
          player_score: (gameState.player_score as number) || 0,
          ai_score: (gameState.ai_score as number) || 0,
          current_player: (gameState.current_player as number) || 1,
          game_over: (gameState.game_over as boolean) || false,
          first_move: (gameState.first_move as boolean) || true,
          current_move: (gameState.current_move as Array<[number, number, string]>) || [],
          bag_count: (gameState.bag_count as number) || 0,
        });
      }
    } catch (err) {
      console.error('Ошибка загрузки Эрудита:', err);
      setError('Не удалось загрузить игру');
    } finally {
      setLoading(false);
    }
  };

  const handlePlaceTile = async (row: number, col: number) => {
    if (!state || !selectedTile || state.game_over || state.current_player !== 1) {
      return;
    }

    if (state.board[row][col]) {
      return; // Клетка уже занята
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/miniapp/games/erudite/${sessionId}/place-tile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ row, col, letter: selectedTile }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || 'Ошибка размещения фишки');
      }

      const data = await response.json();
      setState(data as EruditeState);
      setSelectedTile(null);
    } catch (err) {
      console.error('Ошибка размещения фишки:', err);
      alert(err instanceof Error ? err.message : 'Ошибка размещения фишки');
    }
  };

  const handleConfirmMove = async () => {
    if (!state || state.game_over || state.current_player !== 1) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/miniapp/games/erudite/${sessionId}/confirm-move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || 'Ошибка подтверждения хода');
      }

      const data = await response.json();
      setState(data as EruditeState);

      if (data.game_over) {
        setTimeout(() => {
          onGameEnd();
        }, 2000);
      }
    } catch (err) {
      console.error('Ошибка подтверждения хода:', err);
      alert(err instanceof Error ? err.message : 'Ошибка подтверждения хода');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-600 dark:text-gray-400">Загрузка...</div>
      </div>
    );
  }

  if (error || !state) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <div className="text-red-600 dark:text-red-400">{error || 'Ошибка загрузки игры'}</div>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          Назад
        </button>
      </div>
    );
  }

  const getBonusColor = (bonus: number) => {
    if (bonus === 1) return 'bg-blue-200 dark:bg-blue-800'; // x2 буквы
    if (bonus === 2) return 'bg-blue-300 dark:bg-blue-700'; // x3 буквы
    if (bonus === 3) return 'bg-pink-200 dark:bg-pink-800'; // x2 слова
    if (bonus === 4) return 'bg-red-200 dark:bg-red-800'; // x3 слова
    return 'bg-gray-100 dark:bg-gray-800';
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <h1 className="text-base font-bold text-gray-900 dark:text-slate-100">📚 Эрудит</h1>
        <button
          onClick={onBack}
          className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600"
        >
          Назад
        </button>
      </div>

      {/* Scores */}
      <div className="flex justify-between p-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div>
          <div className="text-xs text-gray-600 dark:text-gray-400">Вы</div>
          <div className="text-lg font-bold text-blue-600 dark:text-blue-400">{state.player_score}</div>
        </div>
        <div>
          <div className="text-xs text-gray-600 dark:text-gray-400">🐼 Панда</div>
          <div className="text-lg font-bold text-red-600 dark:text-red-400">{state.ai_score}</div>
        </div>
      </div>

      {/* Game Board */}
      <div className="flex-1 overflow-auto p-4">
        <div
          className="grid gap-0.5 max-w-full mx-auto"
          style={{ gridTemplateColumns: 'repeat(15, minmax(0, 1fr))', maxWidth: '100%' }}
        >
          {state.board.map((row, r) =>
            row.map((cell, c) => {
              const bonus = state.bonus_cells[r][c];
              const isInCurrentMove = state.current_move.some(([mr, mc]) => mr === r && mc === c);
              return (
                <div
                  key={`${r}-${c}`}
                  className={`
                    aspect-square flex items-center justify-center text-[10px] font-bold
                    border border-gray-300 dark:border-gray-600
                    ${getBonusColor(bonus)}
                    ${cell ? 'bg-white dark:bg-gray-700' : ''}
                    ${isInCurrentMove ? 'ring-2 ring-blue-500' : ''}
                    ${!cell && !state.game_over && state.current_player === 1 ? 'cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700' : ''}
                  `}
                  onClick={() => !cell && handlePlaceTile(r, c)}
                >
                  {cell || (bonus > 0 && !cell ? (bonus === 1 ? '2x' : bonus === 2 ? '3x' : bonus === 3 ? '2x' : bonus === 4 ? '3x' : '') : '')}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Player Tiles */}
      <div className="p-4 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="text-sm font-semibold mb-2 text-gray-700 dark:text-gray-300">Ваши фишки:</div>
        <div className="flex flex-wrap gap-2">
          {state.player_tiles.map((tile, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedTile(selectedTile === tile ? null : tile)}
              className={`
                w-10 h-10 flex items-center justify-center
                text-lg font-bold rounded
                border-2
                ${selectedTile === tile
                  ? 'bg-blue-500 text-white border-blue-600'
                  : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600'
                }
                hover:bg-blue-100 dark:hover:bg-blue-900
              `}
            >
              {tile === '*' ? '★' : tile}
            </button>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="p-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex-shrink-0">
        {state.current_move.length > 0 ? (
          <div className="flex gap-1.5">
            <button
              onClick={handleConfirmMove}
              className="flex-1 py-2 bg-green-500 text-white rounded-lg font-semibold text-xs hover:bg-green-600 active:scale-95"
            >
              ✅ Подтвердить ({state.current_move.length})
            </button>
            <button
              onClick={async () => {
                if (!state) return;
                try {
                  const response = await fetch(`${API_BASE_URL}/api/miniapp/games/erudite/${sessionId}/clear-move`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                  });
                  if (response.ok) {
                    const data = await response.json();
                    setState(data as EruditeState);
                    setSelectedTile(null);
                  }
                } catch (err) {
                  console.error('Ошибка очистки хода:', err);
                }
              }}
              className="px-3 py-2 bg-gray-500 text-white rounded-lg text-xs hover:bg-gray-600 active:scale-95"
            >
              🗑️
            </button>
          </div>
        ) : (
          <div className="text-[10px] text-gray-500 dark:text-gray-400 text-center">
            Выбери фишку и размести её на доске
          </div>
        )}
      </div>

      {/* Game Over */}
      {state.game_over && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg text-center">
            <div className="text-2xl font-bold mb-2">
              {state.player_score > state.ai_score ? 'Победа!' : 'Поражение'}
            </div>
            <div className="text-gray-600 dark:text-gray-400 mb-4">
              Вы: {state.player_score} | Панда: {state.ai_score}
            </div>
            <button
              onClick={onGameEnd}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Закрыть
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
