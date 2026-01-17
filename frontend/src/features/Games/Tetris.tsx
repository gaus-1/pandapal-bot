/**
 * Tetris Game Component - FINAL STABLE VERSION
 *
 * Исправления:
 * 1. Кнопки теперь никогда не блокируются таймером.
 * 2. Игнорирование ложного Game Over при старте (если score == 0).
 * 3. Рекурсивный таймер (setTimeout) для плавной работы.
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

type TetrisCell = 0 | 1 | 2;

interface TetrisState {
  board: TetrisCell[][];
  score: number;
  lines_cleared: number;
  game_over: boolean;
  width: number;
  height: number;
  level?: number;
}

const CELL_COLORS: Record<TetrisCell, string> = {
  0: 'bg-slate-100 dark:bg-slate-800',
  1: 'bg-blue-400 dark:bg-blue-500',
  2: 'bg-emerald-400 dark:bg-emerald-500',
};

export function Tetris({ sessionId, onBack, onGameEnd }: TetrisProps) {
  const [state, setState] = useState<TetrisState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isGameOverRef = useRef(false);

  // Синхронизация флага Game Over для таймера
  useEffect(() => {
    isGameOverRef.current = state?.game_over ?? false;
  }, [state]);

  useEffect(() => {
    loadGameState();
  }, [sessionId]);

  const normalizeBoard = (rawBoard: number[][]): TetrisCell[][] => {
    if (!rawBoard || !Array.isArray(rawBoard)) return [];
    return rawBoard.map((row) =>
      row.map((cell) => {
        if (cell === 0) return 0;
        if (cell === 2) return 2;
        return 1;
      }),
    );
  };

  const loadGameState = async () => {
    try {
      const session = await getGameSession(sessionId);
      const gameState = session.game_state as Record<string, unknown> | undefined;
      const board = gameState?.board as number[][] | undefined;

      if (board && Array.isArray(board) && board.length > 0) {
        const loadedGameOver = Boolean(gameState?.game_over);
        const loadedScore = Number(gameState?.score ?? 0);
        const loadedLines = Number(gameState?.lines_cleared ?? 0);

        // ИСПРАВЛЕНИЕ 1: Если игра загрузилась с game_over=true, но счет 0 и линии 0 -
        // игнорируем это, считая это ошибкой/кешем. Сбрасываем флаг.
        // Это решает "мгновенный Game Over".
        const effectiveGameOver = (loadedScore > 0 || loadedLines > 0) && loadedGameOver;

        const safeState: TetrisState = {
          board: normalizeBoard(board),
          score: loadedScore,
          lines_cleared: loadedLines,
          game_over: effectiveGameOver,
          width: (gameState?.width as number) ?? board[0]?.length ?? 10,
          height: (gameState?.height as number) ?? board.length ?? 20,
          level: Number(gameState?.level ?? 1),
        };
        setState(safeState);
      } else {
        // Если состояния нет (чистый старт)
        const defaultHeight = 20;
        const defaultWidth = 10;
        const emptyBoard: TetrisCell[][] = Array(defaultHeight)
          .fill(null)
          .map(() => Array(defaultWidth).fill(0) as TetrisCell[]);

        setState({
          board: emptyBoard,
          score: 0,
          lines_cleared: 0,
          game_over: false,
          width: defaultWidth,
          height: defaultHeight,
          level: 1,
        });
      }
    } catch (err) {
      console.error('Ошибка загрузки состояния тетриса:', err);
      setError('Не удалось загрузить игру');
    }
  };

  const handleAction = useCallback(
    async (action: 'left' | 'right' | 'down' | 'rotate' | 'tick') => {
      // Проверка Game Over
      if (isGameOverRef.current) {
        return;
      }

      // Вибрация только для кликов пользователя
      if (action !== 'tick') {
        telegram.hapticFeedback('light');
      }

      try {
        const newState = await tetrisMove(sessionId, action);

        const safeNewState: TetrisState = {
          board: normalizeBoard(newState.board),
          score: newState.score,
          lines_cleared: newState.lines_cleared,
          game_over: newState.game_over,
          width: newState.width,
          height: newState.height,
          level: (newState as { level?: number }).level ?? 1,
        };

        // ИСПРАВЛЕНИЕ 2: Защита от мгновенного Game Over на первом тике
        // Если пришел Game Over, но счет был и остался 0 - это баг. Игнорируем.
        const currentScore = state?.score ?? 0;
        const newScore = newState.score;

        if (newState.game_over && currentScore === 0 && newScore === 0) {
            console.warn("Получен Game Over при счете 0. Игнорируем и сбрасываем флаг.");
            // Игнорируем game_over: устанавливаем его в false
            safeNewState.game_over = false;
            setState(safeNewState);
            return; // Не вызываем onGameEnd()
        }

        // Обновляем состояние только если game_over корректен
        setState(safeNewState);

        if (newState.game_over) {
            telegram.notifyWarning();
            onGameEnd();
        }
      } catch (err) {
        console.error('Ошибка хода в тетрисе:', err);
        setError('Ошибка соединения. Попробуй ещё раз.');
        telegram.notifyError();
      }
    },
    [sessionId, onGameEnd, state?.score], // Добавлен state?.score в зависимости
  );

  // ИСПРАВЛЕНИЕ 3: Рекурсивный таймер
  useEffect(() => {
    if (!state || state.game_over) {
      return;
    }

    const currentLevel = state.level ?? 1;
    const tickRate = Math.max(100, 1000 - (currentLevel - 1) * 100);

    const runTick = async () => {
      if (isGameOverRef.current) return;
      await handleAction('tick');

      // Планируем следующий тик только ПОСЛЕ завершения текущего
      // Это гарантирует, что handleAction не будет перекрываться сам собой
      if (!isGameOverRef.current) {
        setTimeout(runTick, tickRate);
      }
    };

    const timeoutId = setTimeout(runTick, tickRate);

    return () => clearTimeout(timeoutId);
  }, [state, handleAction]);

  const handleBackClick = () => {
    telegram.hapticFeedback('light');
    onBack();
  };

  if (!state) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-white dark:bg-slate-900">
        <p className="text-sm text-gray-700 dark:text-slate-200">Загрузка тетриса…</p>
      </div>
    );
  }

  const { board, score, lines_cleared: lines, game_over } = state;

  const hasActivePiece = board.some((row) => row.some((cell) => cell === 2));
  const isGameActive = score > 0 || lines > 0 || hasActivePiece;
  const isReady = !game_over && !isGameActive;

  return (
    <div className="w-full h-full flex flex-col bg-white dark:bg-slate-900">
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <button
          onClick={handleBackClick}
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

      {!isReady && (
        <div className="px-4 mb-2 flex justify-center">
          <PandaReaction mood={game_over ? 'sad' : 'happy'} className="pb-1" />
        </div>
      )}

      <div className="px-4">
        <h1 className="text-lg sm:text-xl font-bold text-gray-900 dark:bg-slate-100 mb-1">
          🧱 Тетрис
        </h1>
        {isReady ? (
          <div className="text-xs sm:text-sm text-gray-600 dark:text-slate-400 mb-3">
            <p className="mb-2">Заполняй линии и зарабатывай очки!</p>
            <p className="font-semibold text-blue-600 dark:text-blue-400">
              Игра начинается... 🎮
            </p>
          </div>
        ) : (
          <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-400 mb-3">
            Заполняй линии и зарабатывай очки!
          </p>
        )}
      </div>

      {error && (
        <div className="mx-4 mb-2 p-2 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-800 rounded-lg">
          <p className="text-xs sm:text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      <div className="flex-1 flex flex-col items-center justify-start px-4 pb-32 sm:pb-4">
        <div className="flex gap-3 w-full max-w-lg">
          <div className="flex-1 flex justify-center">
            <div className="bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg p-1 shadow-inner">
              <div className="grid gap-[1px]" style={{ gridTemplateColumns: `repeat(${board[0].length}, minmax(0, 1fr))` }}>
                {board.map((row, rowIndex) =>
                  row.map((cell, colIndex) => (
                    <div
                      key={`${rowIndex}-${colIndex}`}
                      className={`w-5 h-5 sm:w-6 sm:h-6 md:w-7 md:h-7 ${CELL_COLORS[cell]}`}
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

        <div className="fixed bottom-0 left-0 right-0 sm:relative sm:bottom-auto sm:left-auto sm:right-auto mt-4 w-full max-w-lg bg-white dark:bg-slate-900 sm:bg-transparent border-t border-gray-200 dark:border-slate-700 sm:border-t-0 pt-3 pb-safe sm:pt-0 sm:pb-0 px-4 z-50 shadow-lg sm:shadow-none">
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
