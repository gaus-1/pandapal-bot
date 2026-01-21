/**
 * Two Dots Game Component
 * Игра Two Dots - соединение точек одного цвета
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { telegram } from '../../services/telegram';
import { getGameSession, twoDotsMove, type UserProfile } from '../../services/api';

interface TwoDotsProps {
  sessionId: number;
  user: UserProfile;
  onBack: () => void;
  onGameEnd: () => void;
}

interface TwoDotsState {
  grid: number[][];
  score: number;
  moves_left: number;
  level: number;
  game_over: boolean;
  selected_path: Array<[number, number]>;
  width: number;
  height: number;
}

const COLORS = [
  '#ef4444', // red (1)
  '#3b82f6', // blue (2)
  '#10b981', // green (3)
  '#f59e0b', // yellow (4)
  '#8b5cf6', // purple (5)
];

export function TwoDots({ sessionId, onBack, onGameEnd }: TwoDotsProps) {
  const [state, setState] = useState<TwoDotsState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const mountedRef = useRef(true);
  const isSelectingRef = useRef(false);

  const loadState = useCallback(async () => {
    try {
      const session = await getGameSession(sessionId);
      const gameState = session.game_state as Record<string, unknown>;
      const grid = (gameState?.grid as number[][]) || [];

      setState({
        grid: grid.length > 0 ? grid : Array(8).fill(null).map(() => Array(8).fill(0)),
        score: Number(gameState?.score ?? 0),
        moves_left: Number(gameState?.moves_left ?? 30),
        level: Number(gameState?.level ?? 1),
        game_over: Boolean(gameState?.game_over),
        selected_path: (gameState?.selected_path as Array<[number, number]>) || [],
        width: Number(gameState?.width ?? 8),
        height: Number(gameState?.height ?? 8),
      });
    } catch (err) {
      console.error('Ошибка загрузки Two Dots:', err);
      setError('Не удалось загрузить игру');
    }
  }, [sessionId]);

  const handleAction = useCallback(
    async (action: 'select' | 'add' | 'clear' | 'confirm', row?: number, col?: number) => {
      if (!mountedRef.current || !state || state.game_over || isLoading) return;

      setIsLoading(true);
      setError(null);

      try {
        const result = await twoDotsMove(sessionId, action, row, col);

        if (!mountedRef.current) return;

        setState({
          grid: result.grid || Array(8).fill(null).map(() => Array(8).fill(0)),
          score: result.score ?? 0,
          moves_left: result.moves_left ?? 30,
          level: result.level ?? 1,
          game_over: result.game_over || false,
          selected_path: (result.selected_path as Array<[number, number]>) || [],
          width: result.width ?? 8,
          height: result.height ?? 8,
        });

        if (result.game_over) {
          telegram.notifyWarning();
          onGameEnd();
        }
      } catch (err) {
        console.error('Ошибка хода:', err);
        setError('Ошибка соединения');
        telegram.notifyError();
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, state, isLoading, onGameEnd],
  );

  useEffect(() => {
    mountedRef.current = true;
    loadState();

    return () => {
      mountedRef.current = false;
    };
  }, [loadState]);

  const getCellColor = (color: number): string => {
    if (color === 0) return 'transparent';
    return COLORS[(color - 1) % COLORS.length] || COLORS[0];
  };

  const isInPath = (row: number, col: number): boolean => {
    if (!state) return false;
    return state.selected_path.some(([r, c]) => r === row && c === col);
  };

  const handleCellTouchStart = (row: number, col: number) => {
    if (!state || state.game_over || isLoading) return;
    isSelectingRef.current = true;
    telegram.hapticFeedback('light');
    handleAction('select', row, col);
  };

  const handleCellTouchMove = (row: number, col: number) => {
    if (!isSelectingRef.current || !state || state.game_over || isLoading) return;
    handleAction('add', row, col);
  };

  const handleCellTouchEnd = () => {
    if (!isSelectingRef.current) return;
    isSelectingRef.current = false;
    if (state && state.selected_path.length >= 2) {
      handleAction('confirm');
    } else {
      handleAction('clear');
    }
  };

  const handleCellClick = (row: number, col: number) => {
    if (!state || state.game_over || isLoading) return;

    // Если путь пустой - начинаем новый путь
    if (state.selected_path.length === 0) {
      handleAction('select', row, col);
      return;
    }

    // Проверяем, кликнули ли на последнюю точку пути - подтверждаем
    const lastPos = state.selected_path[state.selected_path.length - 1];
    const [lastRow, lastCol] = lastPos;
    if (row === lastRow && col === lastCol && state.selected_path.length >= 2) {
      handleAction('confirm');
      return;
    }

    // Проверяем, соседняя ли точка
    const isAdjacent = Math.abs(row - lastRow) + Math.abs(col - lastCol) === 1;
    if (isAdjacent) {
      handleAction('add', row, col);
    } else {
      // Если кликнули на другую точку - начинаем новый путь
      handleAction('clear');
      handleAction('select', row, col);
    }
  };

  if (!state) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-white dark:bg-slate-900">
        <p className="text-sm text-gray-700 dark:text-slate-200">Загрузка...</p>
      </div>
    );
  }

  const { grid, score, moves_left } = state;

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-white dark:bg-slate-900 border-r border-l border-gray-300 dark:border-slate-600">
      {/* Header */}
      <div className="flex items-center justify-between px-3 pt-2 pb-1 flex-shrink-0">
        <button
          onClick={() => {
            telegram.hapticFeedback('light');
            onBack();
          }}
          className="px-2 py-1 rounded-lg bg-gray-100 dark:bg-slate-800 text-xs text-gray-800 dark:text-slate-100 border border-gray-200 dark:border-slate-700"
        >
          ← Назад
        </button>
        <div className="text-right">
          <div className="text-xs text-gray-600 dark:text-slate-400">Счёт</div>
          <div className="text-sm font-bold text-gray-900 dark:text-slate-100">{score}</div>
        </div>
      </div>

      <div className="px-3 pb-1 flex-shrink-0">
        <div className="flex items-center justify-between">
          <h1 className="text-sm font-bold text-gray-900 dark:text-slate-100">🔴 Two Dots</h1>
          {moves_left > 0 && (
            <p className="text-xs text-gray-600 dark:text-slate-400">Ходов: {moves_left}</p>
          )}
        </div>
      </div>

      {error && (
        <div className="mx-3 mb-1 p-1.5 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-800 rounded text-xs text-red-700 dark:text-red-300 flex-shrink-0">
          {error}
        </div>
      )}

      {/* Game Grid */}
      <div className="flex items-center justify-center px-2 sm:px-3 py-2 w-full flex-1 overflow-hidden min-h-0">
        <div className="relative w-full max-w-[95vw] mx-auto">
          <div
            className="bg-slate-100 dark:bg-slate-900 border-2 border-slate-300 dark:border-slate-700 rounded-lg p-2 sm:p-3 shadow-inner mx-auto"
            style={{
              aspectRatio: '1',
              width: 'min(90vw, calc((100vh - 160px) * 0.85))',
              maxHeight: 'calc(100vh - 160px)'
            }}
          >
            <div
              className="grid w-full h-full"
              style={{
                gridTemplateColumns: `repeat(${state.width}, 1fr)`,
                gridTemplateRows: `repeat(${state.height}, 1fr)`,
                gap: '2px'
              }}
            >
              {grid.map((row, rowIndex) =>
                row.map((cell, colIndex) => {
                  const color = getCellColor(cell);
                  const inPath = isInPath(rowIndex, colIndex);

                  return (
                    <div
                      key={`${rowIndex}-${colIndex}`}
                      className={`w-full h-full rounded-full transition-all touch-manipulation ${
                        inPath ? 'ring-2 ring-white ring-offset-1 scale-110 z-10' : ''
                      } ${state.game_over ? 'opacity-50' : 'cursor-pointer'}`}
                      style={{
                        backgroundColor: color,
                        opacity: cell === 0 ? 0 : 1,
                      }}
                      onClick={() => handleCellClick(rowIndex, colIndex)}
                      onTouchStart={(e) => {
                        e.preventDefault();
                        handleCellTouchStart(rowIndex, colIndex);
                      }}
                      onTouchMove={(e) => {
                        e.preventDefault();
                        const touch = e.touches[0];
                        const element = document.elementFromPoint(touch.clientX, touch.clientY);
                        if (element) {
                          const parentRect = element.parentElement?.getBoundingClientRect();
                          if (parentRect) {
                            const relX = touch.clientX - parentRect.left;
                            const relY = touch.clientY - parentRect.top;
                            const cellSize = parentRect.width / state.width;
                            const col = Math.floor(relX / cellSize);
                            const row = Math.floor(relY / cellSize);
                            if (0 <= row && row < state.height && 0 <= col && col < state.width) {
                              handleCellTouchMove(row, col);
                            }
                          }
                        }
                      }}
                      onTouchEnd={(e) => {
                        e.preventDefault();
                        handleCellTouchEnd();
                      }}
                    />
                  );
                }),
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex-shrink-0 pt-0 pb-2 bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-700" style={{ paddingBottom: 'calc(0.5rem + env(safe-area-inset-bottom))' }}>
        <div className="mx-auto px-3 w-full max-w-[400px] space-y-2">
          {state.selected_path.length >= 2 && (
            <button
              onClick={() => handleAction('confirm')}
              disabled={isLoading || state.game_over}
              className="w-full py-2 px-4 bg-green-500 hover:bg-green-600 dark:bg-green-600 dark:hover:bg-green-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Подтвердить ({state.selected_path.length} точек)
            </button>
          )}
          <button
            type="button"
            onClick={() => handleAction('clear')}
            disabled={state.game_over || !state.selected_path.length}
            className="w-full py-3 rounded-lg bg-gray-500 hover:bg-gray-600 active:bg-gray-700 text-xs font-semibold text-white shadow-lg touch-manipulation disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px]"
          >
            Очистить выбор
          </button>
          {state.selected_path.length === 0 && (
            <p className="text-xs text-center text-gray-500 dark:text-slate-400 px-2">
              Кликни на точку, чтобы начать. Кликни на последнюю точку пути, чтобы подтвердить.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
