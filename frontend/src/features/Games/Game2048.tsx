/**
 * Game 2048 Component
 * Игра 2048 - объединение чисел
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { telegram } from "../../services/telegram";
import {
  game2048Move,
  getGameSession,
  createGame,
  type UserProfile,
} from "../../services/api";
import { PandaReaction } from "../../components/PandaReaction";

interface Game2048Props {
  sessionId: number;
  user: UserProfile;
  onBack: () => void;
  onGameEnd: () => void;
}

export function Game2048({ sessionId, user, onBack, onGameEnd }: Game2048Props) {
  const [board, setBoard] = useState<number[][]>([]);
  const [prevBoard, setPrevBoard] = useState<number[][]>([]);
  const [score, setScore] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [won, setWon] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newTileIndices, setNewTileIndices] = useState<Set<number>>(new Set());

  // Для swipe жестов
  const touchStartX = useRef<number | null>(null);
  const touchStartY = useRef<number | null>(null);
  const touchEndX = useRef<number | null>(null);
  const touchEndY = useRef<number | null>(null);

  useEffect(() => {
    loadGameState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const loadGameState = async () => {
    // Оптимизация: не загружаем состояние если игра закончена
    if (gameOver) return;

    try {
      const session = await getGameSession(sessionId);
      const gameState = session.game_state as {
        board?: number[][];
        score?: number;
        won?: boolean;
      };

      if (gameState.board) {
        setBoard(gameState.board);
        setPrevBoard(gameState.board);
      }
      if (gameState.score !== undefined) {
        setScore(gameState.score);
      }
      if (gameState.won) {
        setWon(true);
      }

      if (session.result && session.result !== "in_progress") {
        setGameOver(true);
      }
    } catch (err) {
      console.error("Ошибка загрузки состояния игры:", err);
    }
  };

  const handleMove = useCallback(
    async (direction: "up" | "down" | "left" | "right") => {
      if (gameOver || isLoading) {
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        telegram.hapticFeedback("light");
        const result = await game2048Move(sessionId, direction);

        // Определяем новые плитки для анимации
        const newTiles = new Set<number>();
        if (prevBoard.length > 0) {
          result.board.flat().forEach((value, index) => {
            const prevValue = prevBoard.flat()[index];
            if (value !== prevValue && value !== 0) {
              newTiles.add(index);
            }
          });
        }
        setNewTileIndices(newTiles);
        setPrevBoard(result.board);

        // Очищаем анимацию через 300ms
        setTimeout(() => setNewTileIndices(new Set()), 300);

        setBoard(result.board);
        setScore(result.score);
        setWon(result.won);

        if (result.game_over) {
          setGameOver(true);
          telegram.notifyError();
          onGameEnd();
        } else if (result.won && !won) {
          telegram.notifySuccess();
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Ошибка хода";
        setError(errorMessage);
        telegram.notifyError();
        console.error("Ошибка хода:", err);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, gameOver, isLoading, won, onGameEnd, prevBoard],
  );

  // Обработка клавиатуры
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (gameOver || isLoading) return;

      switch (e.key) {
        case "ArrowUp":
          e.preventDefault();
          handleMove("up");
          break;
        case "ArrowDown":
          e.preventDefault();
          handleMove("down");
          break;
        case "ArrowLeft":
          e.preventDefault();
          handleMove("left");
          break;
        case "ArrowRight":
          e.preventDefault();
          handleMove("right");
          break;
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [gameOver, isLoading, handleMove]);

  // Swipe жесты для мобильных
  const minSwipeDistance = 50;

  const onTouchStart = (e: React.TouchEvent) => {
    touchEndX.current = null;
    touchEndY.current = null;
    touchStartX.current = e.targetTouches[0].clientX;
    touchStartY.current = e.targetTouches[0].clientY;
  };

  const onTouchMove = (e: React.TouchEvent) => {
    touchEndX.current = e.targetTouches[0].clientX;
    touchEndY.current = e.targetTouches[0].clientY;
  };

  const onTouchEnd = () => {
    if (
      !touchStartX.current ||
      !touchEndX.current ||
      !touchStartY.current ||
      !touchEndY.current
    )
      return;

    const distanceX = touchStartX.current - touchEndX.current;
    const distanceY = touchStartY.current - touchEndY.current;
    const isLeftSwipe = distanceX > minSwipeDistance;
    const isRightSwipe = distanceX < -minSwipeDistance;
    const isUpSwipe = distanceY > minSwipeDistance;
    const isDownSwipe = distanceY < -minSwipeDistance;

    if (Math.abs(distanceX) > Math.abs(distanceY)) {
      // Горизонтальный swipe
      if (isLeftSwipe) {
        handleMove("left");
      } else if (isRightSwipe) {
        handleMove("right");
      }
    } else {
      // Вертикальный swipe
      if (isUpSwipe) {
        handleMove("up");
      } else if (isDownSwipe) {
        handleMove("down");
      }
    }
  };

  const getTileColor = (value: number): string => {
    const colors: Record<number, string> = {
      2: "bg-gray-200 dark:bg-slate-700",
      4: "bg-gray-300 dark:bg-slate-600",
      8: "bg-orange-200 dark:bg-orange-800",
      16: "bg-orange-300 dark:bg-orange-700",
      32: "bg-orange-400 dark:bg-orange-600",
      64: "bg-orange-500 dark:bg-orange-500",
      128: "bg-yellow-400 dark:bg-yellow-600",
      256: "bg-yellow-500 dark:bg-yellow-500",
      512: "bg-yellow-600 dark:bg-yellow-400",
      1024: "bg-yellow-700 dark:bg-yellow-300",
      2048: "bg-yellow-800 dark:bg-yellow-200",
    };
    return colors[value] || "bg-gray-100 dark:bg-slate-800";
  };

  const getTileTextColor = (value: number): string => {
    if (value <= 4) {
      return "text-gray-800 dark:text-slate-100";
    }
    if (value >= 128 && value <= 512) {
      return "text-white dark:text-slate-900";
    }
    return "text-white dark:text-slate-800";
  };

  const getTileFontSize = (value: number): string => {
    if (value >= 1000) return "text-xs sm:text-sm";
    if (value >= 100) return "text-sm sm:text-base";
    return "text-base sm:text-lg";
  };

  return (
    <div className="w-full h-full bg-white dark:bg-slate-800 flex flex-col overflow-hidden">
      {/* Заголовок */}
      <div className="flex-shrink-0 flex items-center justify-between px-fib-3 py-fib-2 border-b border-gray-200 dark:border-slate-700">
        <button
          onClick={onBack}
          className="p-2 rounded-lg bg-gray-50 dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 active:bg-gray-200 dark:active:bg-slate-600 transition-colors text-sm touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center text-gray-900 dark:text-slate-100"
          aria-label="Назад"
        >
          ← Назад
        </button>
        <h2 className="text-lg sm:text-xl font-display font-bold text-gray-900 dark:text-slate-100">
          🔢 2048
        </h2>
        <div className="w-10" />
      </div>

      {/* Счёт */}
      <div className="flex-shrink-0 text-center py-fib-2 px-fib-3">
        {won && (
          <div className="mb-1">
            <PandaReaction mood="happy" size="small" />
          </div>
        )}
        {gameOver && (
          <div className="mb-1">
            <PandaReaction mood="sad" size="small" />
          </div>
        )}
        <div className="font-display text-lg sm:text-xl font-bold text-gray-900 dark:text-slate-100">
          {score}
        </div>
        {won && (
          <div className="text-xs text-green-500 font-semibold">
            🎉 Ты достиг 2048!
          </div>
        )}
        {gameOver && (
          <div className="text-xs text-red-500 font-semibold">
            Игра окончена
          </div>
        )}
        {error && (
          <p className="text-xs text-red-500 mt-1">{error}</p>
        )}
      </div>

      {/* Игровая доска */}
      <div className="flex-1 flex items-center justify-center px-fib-3 min-h-0">
        <div
          className="bg-gray-50 dark:bg-slate-800 rounded-xl p-1 touch-none select-none w-full max-w-[220px] mx-auto border border-gray-200 dark:border-slate-600"
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
        >
          {board.length > 0 ? (
            <div className="grid grid-cols-4 gap-0.5 w-full">
              {board.flat().map((value, index) => {
                const isNewTile = newTileIndices.has(index);
                return (
                  <div
                    key={index}
                    className={`
                      aspect-square rounded-md flex items-center justify-center
                      font-bold text-sm sm:text-base
                      w-full h-full
                      ${value === 0
                        ? "bg-white dark:bg-slate-700"
                        : `${getTileColor(value)} ${getTileTextColor(
                          value,
                        )} ${getTileFontSize(value)}`
                      }
                      transition-all duration-300
                    `}
                    style={{
                      animation: isNewTile
                        ? "tileAppear 0.3s ease-out"
                        : undefined,
                    }}
                  >
                    {value !== 0 && value}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center text-gray-600 dark:text-slate-300 py-8">
              Загрузка...
            </div>
          )}
        </div>
      </div>

      {/* Кнопки управления / Game Over */}
      <div className="flex-shrink-0 px-fib-3 py-fib-2">
        {!gameOver ? (
          <div>
            <div className="text-[10px] text-gray-500 dark:text-slate-400 text-center mb-1">
              Свайп по доске или кнопки ↑↓←→
            </div>
            <div className="grid grid-cols-3 gap-1 max-w-[180px] mx-auto">
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove("up")}
                disabled={isLoading}
                className="p-1 bg-blue-500 dark:bg-blue-600 text-white rounded-lg font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50 touch-manipulation min-h-[40px] flex items-center justify-center shadow-md"
                aria-label="Вверх"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.5">
                  <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
                </svg>
              </button>
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove("left")}
                disabled={isLoading}
                className="p-1 bg-blue-500 dark:bg-blue-600 text-white rounded-lg font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50 touch-manipulation min-h-[40px] flex items-center justify-center shadow-md"
                aria-label="Влево"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.5">
                  <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </button>
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove("right")}
                disabled={isLoading}
                className="p-1 bg-blue-500 dark:bg-blue-600 text-white rounded-lg font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50 touch-manipulation min-h-[40px] flex items-center justify-center shadow-md"
                aria-label="Вправо"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.5">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove("down")}
                disabled={isLoading}
                className="p-1 bg-blue-500 dark:bg-blue-600 text-white rounded-lg font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50 touch-manipulation min-h-[40px] flex items-center justify-center shadow-md"
                aria-label="Вниз"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" stroke="currentColor" strokeWidth="1.5">
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
              <div /> {/* Spacer */}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={async () => {
                try {
                  const result = await createGame(user.telegram_id, '2048');
                  if (result?.session_id != null) window.location.reload();
                } catch { onGameEnd(); }
              }}
              className="px-5 py-2.5 bg-green-500 text-white rounded-xl font-semibold hover:opacity-90 transition-opacity touch-manipulation text-sm min-h-[44px]"
            >
              Играть снова
            </button>
            <button
              onClick={onBack}
              className="px-5 py-2.5 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-semibold hover:opacity-90 transition-opacity touch-manipulation text-sm min-h-[44px]"
            >
              К играм
            </button>
          </div>
        )}
      </div>

      <style>{`
        @keyframes tileAppear {
          from {
            opacity: 0;
            transform: scale(0.5);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
}
