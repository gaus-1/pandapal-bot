/**
 * Tetris Game Component - SIMPLE WORKING VERSION
 * Простая рабочая реализация тетриса для детей
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { telegram } from '../../services/telegram';
import { getGameSession, tetrisMove, type UserProfile } from '../../services/api';
import { PandaReaction } from '../../components/PandaReaction';

interface TetrisProps {
  sessionId: number;
  user: UserProfile;
  onBack: () => void;
  onGameEnd: () => void;
}

interface TetrisState {
  board: number[][];
  score: number;
  lines_cleared: number;
  game_over: boolean;
  level?: number;
}

export function Tetris({ sessionId, onBack, onGameEnd }: TetrisProps) {
  const [state, setState] = useState<TetrisState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);
  const mountedRef = useRef(true);

  // Загрузка состояния
  const loadState = useCallback(async () => {
    try {
      const session = await getGameSession(sessionId);
      const gameState = session.game_state as Record<string, unknown>;
      const board = (gameState?.board as number[][]) || [];

      setState({
        board: board.length > 0 ? board : Array(20).fill(null).map(() => Array(10).fill(0)),
        score: Number(gameState?.score ?? 0),
        lines_cleared: Number(gameState?.lines_cleared ?? 0),
        game_over: false,
        level: Number(gameState?.level ?? 1),
      });
    } catch (err) {
      console.error('Ошибка загрузки тетриса:', err);
      setError('Не удалось загрузить игру');
    }
  }, [sessionId]);

  // Обработка действия
  const handleAction = useCallback(
    async (action: 'left' | 'right' | 'down' | 'rotate' | 'tick') => {
      if (!mountedRef.current || !state || state.game_over) return;

      try {
        const result = await tetrisMove(sessionId, action);

        if (!mountedRef.current) return;

        const newState: TetrisState = {
          board: result.board || Array(20).fill(null).map(() => Array(10).fill(0)),
          score: result.score ?? 0,
          lines_cleared: result.lines_cleared ?? 0,
          game_over: result.game_over || false,
          level: (result as { level?: number }).level ?? 1,
        };

        setState(newState);

        if (newState.game_over) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          telegram.notifyWarning();
          onGameEnd();
        }
      } catch (err) {
        console.error('Ошибка хода:', err);
        setError('Ошибка соединения');
        telegram.notifyError();
      }
    },
    [sessionId, state, onGameEnd],
  );

  // Инициализация
  useEffect(() => {
    mountedRef.current = true;
    loadState().then(() => {
      if (mountedRef.current) {
        // Первый тик для начала игры
        setTimeout(() => handleAction('tick'), 300);
      }
    });

    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [loadState, handleAction]);

  // Игровой цикл - используем useRef для handleAction чтобы избежать перезапуска
  const handleActionRef = useRef(handleAction);
  useEffect(() => {
    handleActionRef.current = handleAction;
  }, [handleAction]);

  useEffect(() => {
    if (!state || state.game_over) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    const level = state.level ?? 1;
    // Увеличиваем минимальную скорость для стабильности (1500ms для level=1)
    const speed = Math.max(800, 1500 - (level - 1) * 100);

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    intervalRef.current = window.setInterval(() => {
      if (mountedRef.current && state && !state.game_over) {
        handleActionRef.current('tick');
      }
    }, speed);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [state?.level, state?.game_over]); // Зависимости только от level и game_over, не от всего state

  if (!state) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-white dark:bg-slate-900">
        <p className="text-sm text-gray-700 dark:text-slate-200">Загрузка...</p>
      </div>
    );
  }

  const { board, score, lines_cleared: lines, game_over } = state;

  return (
    <div className="w-full h-full flex flex-col bg-white dark:bg-slate-900">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <button
          onClick={() => {
            telegram.hapticFeedback('light');
            onBack();
          }}
          className="px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-slate-800 text-xs sm:text-sm text-gray-800 dark:text-slate-100 border border-gray-200 dark:border-slate-700"
        >
          ← Назад
        </button>
        <div className="text-right">
          <div className="text-xs sm:text-sm text-gray-600 dark:text-slate-400">Счёт</div>
          <div className="text-sm sm:text-base font-bold text-gray-900 dark:text-slate-100">
            {score}
          </div>
        </div>
      </div>

      {!game_over && (
        <div className="px-4 mb-2 flex justify-center">
          <PandaReaction mood="happy" className="pb-1" />
        </div>
      )}

      <div className="px-4">
        <h1 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">
          🧱 Тетрис
        </h1>
        <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-400 mb-3">
          Заполняй линии и зарабатывай очки!
        </p>
      </div>

      {error && (
        <div className="mx-4 mb-2 p-2 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-800 rounded-lg">
          <p className="text-xs sm:text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Game Board */}
      <div className="flex-1 flex flex-col items-center justify-start px-4 pb-48 sm:pb-4">
        <div className="flex gap-3 w-full max-w-lg">
          <div className="flex-1 flex justify-center">
            <div className="bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg p-1 shadow-inner">
              <div className="grid gap-[1px]" style={{ gridTemplateColumns: `repeat(${board[0]?.length || 10}, minmax(0, 1fr))` }}>
                {board.map((row, rowIndex) =>
                  row.map((cell, colIndex) => (
                    <div
                      key={`${rowIndex}-${colIndex}`}
                      className={`w-5 h-5 sm:w-6 sm:h-6 md:w-7 md:h-7 ${
                        cell === 0
                          ? 'bg-slate-100 dark:bg-slate-800'
                          : cell === 2
                            ? 'bg-emerald-400 dark:bg-emerald-500'
                            : 'bg-blue-400 dark:bg-blue-500'
                      }`}
                    />
                  )),
                )}
              </div>
            </div>
          </div>

          <div className="w-24 flex flex-col text-xs text-gray-700 dark:text-slate-200">
            <div className="mb-2 p-2 rounded-lg bg-blue-50 dark:bg-slate-800 border border-blue-200 dark:border-slate-700">
              <div className="font-semibold mb-1">Линии</div>
              <div className="text-base">{lines}</div>
            </div>
            {game_over && (
              <div className="mt-1 p-2 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700">
                <div className="font-semibold mb-1">Конец игры</div>
                <div>Сыграй ещё!</div>
              </div>
            )}
          </div>
        </div>

        {/* Controls */}
        <div className="fixed bottom-0 left-0 right-0 sm:relative sm:bottom-auto sm:left-auto sm:right-auto mt-4 w-full max-w-lg bg-white dark:bg-slate-900 sm:bg-transparent border-t border-gray-200 dark:border-slate-700 sm:border-t-0 pt-3 px-4 z-50 shadow-lg sm:shadow-none" style={{ paddingBottom: 'calc(1rem + env(safe-area-inset-bottom))' }}>
          <div className="flex justify-between gap-2 mb-2">
            <button
              type="button"
              onClick={() => handleAction('left')}
              disabled={game_over}
              className="flex-1 py-3 sm:py-2.5 rounded-lg bg-white dark:bg-slate-800 border-2 border-gray-300 dark:border-slate-600 text-sm sm:text-sm font-semibold text-gray-900 dark:text-slate-100 active:bg-gray-100 dark:active:bg-slate-700 touch-manipulation shadow-md disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] sm:min-h-[48px]"
            >
              ← Влево
            </button>
            <button
              type="button"
              onClick={() => handleAction('rotate')}
              disabled={game_over}
              className="flex-1 py-3 sm:py-2.5 rounded-lg bg-white dark:bg-slate-800 border-2 border-gray-300 dark:border-slate-600 text-sm sm:text-sm font-semibold text-gray-900 dark:text-slate-100 active:bg-gray-100 dark:active:bg-slate-700 touch-manipulation shadow-md disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] sm:min-h-[48px]"
            >
              ⟳ Повернуть
            </button>
            <button
              type="button"
              onClick={() => handleAction('right')}
              disabled={game_over}
              className="flex-1 py-3 sm:py-2.5 rounded-lg bg-white dark:bg-slate-800 border-2 border-gray-300 dark:border-slate-600 text-sm sm:text-sm font-semibold text-gray-900 dark:text-slate-100 active:bg-gray-100 dark:active:bg-slate-700 touch-manipulation shadow-md disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] sm:min-h-[48px]"
            >
              Вправо →
            </button>
          </div>
          <button
            type="button"
            onClick={() => handleAction('down')}
            disabled={game_over}
            className="w-full py-3 sm:py-2.5 rounded-lg bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-sm sm:text-sm font-semibold text-white shadow-lg touch-manipulation disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] sm:min-h-[48px]"
          >
            ↓ Быстрее
          </button>
        </div>
      </div>
    </div>
  );
}
