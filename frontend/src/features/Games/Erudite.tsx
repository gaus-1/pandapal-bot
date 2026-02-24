/**
 * Erudite Game Component
 * Игра Эрудит - составление слов
 */

import { useState, useEffect } from 'react';
import {
  getGameSession,
  eruditePlaceTile,
  eruditeConfirmMove,
  eruditeClearMove,
  type UserProfile,
  type EruditeStateResponse,
} from '../../services/api';

interface EruditeProps {
  sessionId: number;
  user: UserProfile;
  onBack: () => void;
  onGameEnd: () => void;
}

type EruditeState = EruditeStateResponse;

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
      const data = await eruditePlaceTile(sessionId, row, col, selectedTile);
      setState(data);
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
      const data = await eruditeConfirmMove(sessionId);
      setState(data);

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
      <div className="flex items-center justify-between px-2 py-1 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <h1 className="font-display text-sm font-bold text-gray-900 dark:text-slate-100">📚 эрудит</h1>
        <button
          onClick={onBack}
          className="px-2 py-0.5 text-xs bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600"
        >
          Назад
        </button>
      </div>

      {/* Scores */}
      <div className="flex justify-between px-2 py-1 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div>
          <div className="text-[10px] text-gray-600 dark:text-gray-400">Вы</div>
          <div className="text-base font-bold text-blue-600 dark:text-blue-400">{state.player_score}</div>
        </div>
        <div>
          <div className="text-[10px] text-gray-600 dark:text-gray-400">🐼 Панда</div>
          <div className="text-base font-bold text-red-600 dark:text-red-400">{state.ai_score}</div>
        </div>
      </div>

      {/* Правило первого хода */}
      {state.first_move && state.current_player === 1 && (
        <div className="px-2 py-1 bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800 flex-shrink-0">
          <div className="text-xs text-yellow-800 dark:text-yellow-200">
            ⭐ Первый ход: разместите слово так, чтобы оно проходило через центральную клетку (⭐)
          </div>
        </div>
      )}

      {/* Game Board */}
      <div className="flex-1 overflow-hidden flex items-center justify-center p-1 min-h-0">
        <div
          className="grid gap-0.5 w-full h-full"
          style={{ gridTemplateColumns: 'repeat(15, minmax(0, 1fr))', aspectRatio: '1', maxWidth: '100%', maxHeight: '100%' }}
        >
          {state.board.map((row, r) =>
            row.map((cell, c) => {
              const bonus = state.bonus_cells[r][c];
              const currentMoveTile = state.current_move.find(([mr, mc]) => mr === r && mc === c);
              const isInCurrentMove = !!currentMoveTile;
              const displayTile = cell || (currentMoveTile ? currentMoveTile[2] : null);
              const isCenter = r === 7 && c === 7;
              return (
                <div
                  key={`${r}-${c}`}
                  className={`
                    aspect-square flex items-center justify-center text-sm font-bold
                    border-2 transition-all
                    ${isCenter && !displayTile ? 'border-yellow-400 bg-yellow-100 dark:bg-yellow-900/30' : 'border-gray-300 dark:border-gray-600'}
                    ${getBonusColor(bonus)}
                    ${displayTile ? 'bg-white dark:bg-gray-700 shadow-sm' : ''}
                    ${isInCurrentMove ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900/30' : ''}
                    ${!displayTile && !state.game_over && state.current_player === 1 ? 'cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700' : ''}
                  `}
                  onClick={() => !displayTile && handlePlaceTile(r, c)}
                  title={isCenter && state.first_move ? 'Центр доски - первый ход должен проходить здесь' : ''}
                >
                  {displayTile ? (
                    <span className={`text-base font-extrabold ${isInCurrentMove ? 'text-blue-600 dark:text-blue-300' : 'text-gray-900 dark:text-gray-100'}`}>
                      {displayTile}
                    </span>
                  ) : isCenter && state.first_move ? (
                    <span className="text-yellow-500 text-base">⭐</span>
                  ) : bonus > 0 ? (
                    <span className="text-xs">{bonus === 1 ? '2x' : bonus === 2 ? '3x' : bonus === 3 ? '2x' : bonus === 4 ? '3x' : ''}</span>
                  ) : null}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Player Tiles */}
      <div className="p-2 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div className="text-xs font-semibold mb-1.5 text-gray-700 dark:text-gray-300">Ваши фишки:</div>
        <div className="flex flex-wrap gap-1.5">
          {state.player_tiles.map((tile, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedTile(selectedTile === tile ? null : tile)}
              className={`
                w-9 h-9 flex items-center justify-center
                text-sm font-bold rounded-lg shadow-sm
                border-2 transition-all
                ${selectedTile === tile
                  ? 'bg-blue-500 text-white border-blue-600 scale-110 shadow-md'
                  : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600'
                }
                hover:bg-blue-100 dark:hover:bg-blue-900 hover:scale-105 active:scale-95
              `}
            >
              {tile === '*' ? '★' : tile}
            </button>
          ))}
        </div>
        {selectedTile && (
          <div className="text-xs text-blue-600 dark:text-blue-400 mt-1.5 font-medium">
            ✅ Выбрано: <strong className="text-blue-700 dark:text-blue-300">{selectedTile === '*' ? '★ (джокер)' : selectedTile}</strong> → Нажми на пустую клетку доски
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="px-2 py-1 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex-shrink-0">
        {state.current_move.length > 0 ? (
          <div className="flex gap-1">
            <button
              onClick={handleConfirmMove}
              className="flex-1 py-1.5 bg-green-500 text-white rounded font-semibold text-xs hover:bg-green-600"
            >
              ✅ Подтвердить ({state.current_move.length})
            </button>
            <button
              onClick={async () => {
                if (!state) return;
                try {
                  const data = await eruditeClearMove(sessionId);
                  setState(data);
                  setSelectedTile(null);
                } catch (err) {
                  console.error('Ошибка очистки хода:', err);
                }
              }}
              className="px-2 py-1.5 bg-gray-500 text-white rounded text-xs hover:bg-gray-600"
            >
              🗑️
            </button>
          </div>
        ) : null}
      </div>

      {/* Game Over */}
      {state.game_over && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg text-center">
            <div className="font-display text-2xl font-bold mb-2">
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
