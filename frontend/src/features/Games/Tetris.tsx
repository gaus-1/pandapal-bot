/**
 * Tetris Game Component - SIMPLE WORKING VERSION
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { telegram } from '../../services/telegram';
import { getGameSession, tetrisMove, type UserProfile } from '../../services/api';

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

      // КРИТИЧНО: Фильтруем ложные game_over при счете 0 (первый запуск)
      const loadedScore = Number(gameState?.score ?? 0);
      const loadedLines = Number(gameState?.lines_cleared ?? 0);
      const loadedGameOver = Boolean(gameState?.game_over);
      // Игнорируем game_over если счет 0 и линии 0 (это первый запуск)
      const effectiveGameOver = loadedGameOver && (loadedScore > 0 || loadedLines > 0);

      setState({
        board: board.length > 0 ? board : Array(20).fill(null).map(() => Array(10).fill(0)),
        score: loadedScore,
        lines_cleared: loadedLines,
        game_over: effectiveGameOver,
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

        // КРИТИЧНО: Фильтруем ложные game_over при счете 0 (первый запуск)
        const loadedScore = result.score ?? 0;
        const loadedLines = result.lines_cleared ?? 0;
        const loadedGameOver = result.game_over || false;
        // Игнорируем game_over если счет 0 и линии 0 (это первый запуск)
        const effectiveGameOver = loadedGameOver && (loadedScore > 0 || loadedLines > 0);

        const newState: TetrisState = {
          board: result.board || Array(20).fill(null).map(() => Array(10).fill(0)),
          score: loadedScore,
          lines_cleared: loadedLines,
          game_over: effectiveGameOver,
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

  const { board, score, game_over } = state;

  return (
    <div className="w-full h-full flex flex-col overflow-hidden bg-white dark:bg-slate-900">
      {/* Header - компактный */}
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
        <h1 className="text-sm font-bold text-gray-900 dark:text-slate-100">🧱 Тетрис</h1>
      </div>

      {error && (
        <div className="mx-3 mb-1 p-1.5 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-800 rounded text-xs text-red-700 dark:text-red-300 flex-shrink-0">
          {error}
        </div>
      )}

      {/* Game Board - АДАПТИВНЫЙ РАЗМЕР */}
      <div className="flex items-center justify-center px-2 sm:px-3 py-2 w-full h-full overflow-hidden" style={{ height: 'calc(100vh - 240px)' }}>
        {/*
           ИСПРАВЛЕНИЕ:
           1. width: '100%' - занимает всю доступную ширину.
           2. maxWidth: 'calc((100vh - 240px) / 2)' - НО! Ширина не может превышать половину высоты экрана.
              Это гарантирует, что доска с пропорцией 0.5 (ширина/высота) всегда поместится в высоту экрана.
              На широких экранах: ширина будет 100%.
              На узких/высоких экранах: ширина сожмется, чтобы не обрезать дно.
        */}
        <div
          className="bg-slate-100 dark:bg-slate-900 border-2 border-slate-300 dark:border-slate-700 rounded-lg p-1 shadow-inner mx-auto overflow-hidden"
          style={{
            width: '100%',
            maxWidth: 'calc((100vh - 240px) / 2)',
            aspectRatio: '0.5'
          }}
        >
          {/* gap: 2px делает блоки визуально чуть меньше и раздельнее */}
          <div className="grid w-full h-full" style={{ gridTemplateColumns: `repeat(${board[0]?.length || 10}, 1fr)`, gridTemplateRows: `repeat(${board.length || 20}, 1fr)`, gap: '2px' }}>
            {board.map((row, rowIndex) =>
              row.map((cell, colIndex) => (
                <div
                  key={`${rowIndex}-${colIndex}`}
                  className={`w-full h-full ${
                    cell === 0
                      ? 'bg-slate-100 dark:bg-slate-800'
                      : cell === 2
                        ? 'bg-emerald-400 dark:bg-emerald-500'
                        : 'bg-blue-400 dark:bg-blue-500'
                  }`}
                  style={{ aspectRatio: '1' }}
                />
              )),
            )}
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex-shrink-0 pt-0 pb-2 bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-700" style={{ paddingBottom: 'calc(0.5rem + env(safe-area-inset-bottom))' }}>
        <div className="mx-auto px-3" style={{ maxWidth: '330px' }}>
          <div className="flex gap-1.5 mb-1.5">
            <button
              type="button"
              onClick={() => handleAction('left')}
              disabled={game_over}
              className="flex-1 py-2 rounded-lg bg-white dark:bg-slate-800 border-2 border-gray-300 dark:border-slate-600 text-xs font-semibold text-gray-900 dark:text-slate-100 active:bg-gray-100 dark:active:bg-slate-700 touch-manipulation shadow-md disabled:opacity-50 disabled:cursor-not-allowed min-h-[40px]"
            >
              ← Влево
            </button>
            <button
              type="button"
              onClick={() => handleAction('rotate')}
              disabled={game_over}
              className="flex-1 py-2 rounded-lg bg-white dark:bg-slate-800 border-2 border-gray-300 dark:border-slate-600 text-xs font-semibold text-gray-900 dark:text-slate-100 active:bg-gray-100 dark:active:bg-slate-700 touch-manipulation shadow-md disabled:opacity-50 disabled:cursor-not-allowed min-h-[40px]"
            >
              ⟳ Повернуть
            </button>
            <button
              type="button"
              onClick={() => handleAction('right')}
              disabled={game_over}
              className="flex-1 py-2 rounded-lg bg-white dark:bg-slate-800 border-2 border-gray-300 dark:border-slate-600 text-xs font-semibold text-gray-900 dark:text-slate-100 active:bg-gray-100 dark:active:bg-slate-700 touch-manipulation shadow-md disabled:opacity-50 disabled:cursor-not-allowed min-h-[40px]"
            >
              Вправо →
            </button>
          </div>
          <button
            type="button"
            onClick={() => handleAction('down')}
            disabled={game_over}
            className="w-full py-2 rounded-lg bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-xs font-semibold text-white shadow-lg touch-manipulation disabled:opacity-50 disabled:cursor-not-allowed min-h-[40px]"
          >
            ↓ Быстрее
          </button>
        </div>
      </div>
    </div>
  );
}
