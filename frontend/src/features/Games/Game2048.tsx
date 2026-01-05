/**
 * Game 2048 Component
 * Игра 2048 - объединение чисел
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { telegram } from "../../services/telegram";
import {
  game2048Move,
  getGameSession,
  type UserProfile,
} from "../../services/api";

interface Game2048Props {
  sessionId: number;
  user: UserProfile;
  onBack: () => void;
  onGameEnd: () => void;
}

export function Game2048({ sessionId, onBack, onGameEnd }: Game2048Props) {
  const [board, setBoard] = useState<number[][]>([]);
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
    try {
      const session = await getGameSession(sessionId);
      const gameState = session.game_state as {
        board?: number[][];
        score?: number;
        won?: boolean;
      };

      if (gameState.board) {
        setBoard(gameState.board);
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
          setTimeout(() => {
            telegram
              .showPopup({
                title: "😔 Игра окончена",
                message: `Твой счет: ${result.score}. Попробуй еще раз!`,
                buttons: [
                  { type: "default", text: "Поделиться", id: "share" },
                  { type: "close", text: "Закрыть" },
                ],
              })
              .then((buttonId) => {
                if (buttonId === "share") {
                  telegram.shareGameResult("2048", "loss", result.score);
                }
              });
          }, 500);
          onGameEnd();
        } else if (result.won && !won) {
          telegram.notifySuccess();
          setTimeout(() => {
            telegram
              .showPopup({
                title: "🎉 Победа!",
                message: "Ты достиг 2048! Продолжай играть!",
                buttons: [
                  { type: "default", text: "Поделиться", id: "share" },
                  { type: "close", text: "Закрыть" },
                ],
              })
              .then((buttonId) => {
                if (buttonId === "share") {
                  telegram.shareGameResult("2048", "win", result.score);
                }
              });
          }, 500);
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
    [sessionId, gameOver, isLoading, won, onGameEnd],
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
      2: "bg-gray-200 dark:bg-gray-700",
      4: "bg-gray-300 dark:bg-gray-600",
      8: "bg-orange-200 dark:bg-orange-900",
      16: "bg-orange-300 dark:bg-orange-800",
      32: "bg-orange-400 dark:bg-orange-700",
      64: "bg-orange-500 dark:bg-orange-600",
      128: "bg-yellow-400 dark:bg-yellow-600",
      256: "bg-yellow-500 dark:bg-yellow-500",
      512: "bg-yellow-600 dark:bg-yellow-400",
      1024: "bg-yellow-700 dark:bg-yellow-300",
      2048: "bg-yellow-800 dark:bg-yellow-200",
    };
    return colors[value] || "bg-gray-100 dark:bg-gray-800";
  };

  const getTileTextColor = (value: number): string => {
    return value <= 4 ? "text-gray-800 dark:text-gray-200" : "text-white";
  };

  const getTileFontSize = (value: number): string => {
    if (value >= 1000) return "text-xs sm:text-sm";
    if (value >= 100) return "text-sm sm:text-base";
    return "text-base sm:text-lg";
  };

  return (
    <div className="w-full h-full bg-[var(--tg-theme-bg-color)] overflow-y-auto">
      <div className="max-w-md mx-auto px-3 sm:px-4 py-4 sm:py-6">
        {/* Заголовок */}
        <div className="flex items-center justify-between mb-4 sm:mb-6">
          <button
            onClick={onBack}
            className="p-2.5 sm:p-3 rounded-lg bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] hover:bg-[var(--tg-theme-hint-color)]/10 transition-colors text-sm sm:text-base touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Назад"
          >
            ← Назад
          </button>
          <h2 className="text-xl sm:text-2xl font-bold text-[var(--tg-theme-text-color)]">
            🔢 2048
          </h2>
          <div className="w-10 sm:w-12" />
        </div>

        {/* Счет */}
        <div className="text-center mb-4 sm:mb-6">
          <div className="text-2xl sm:text-3xl font-bold text-[var(--tg-theme-text-color)] mb-2">
            {score}
          </div>
          {won && (
            <div className="text-xs sm:text-sm text-green-500 font-semibold">
              🎉 Ты достиг 2048!
            </div>
          )}
          {error && (
            <p className="text-xs sm:text-sm text-red-500 mt-2">{error}</p>
          )}
        </div>

        {/* Игровая доска с поддержкой swipe */}
        <div
          className="bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] rounded-xl sm:rounded-2xl p-2 sm:p-4 mb-4 sm:mb-6 touch-none select-none"
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
        >
          {board.length > 0 ? (
            <div className="grid grid-cols-4 gap-1.5 sm:gap-2">
              {board.flat().map((value, index) => {
                const isNewTile = newTileIndices.has(index);
                return (
                  <div
                    key={index}
                    className={`
                      aspect-square rounded-md sm:rounded-lg flex items-center justify-center
                      font-bold min-h-[50px] sm:min-h-[70px]
                      ${
                        value === 0
                          ? "bg-[var(--tg-theme-bg-color)]"
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
            <div className="text-center text-[var(--tg-theme-hint-color)] py-8">
              Загрузка...
            </div>
          )}
        </div>

        {/* Кнопки управления */}
        {!gameOver && (
          <div className="mb-4 sm:mb-6">
            <div className="text-xs sm:text-sm text-[var(--tg-theme-hint-color)] mb-2 sm:mb-3 text-center">
              Используй кнопки или свайп по доске
            </div>
            <div className="grid grid-cols-3 gap-2 max-w-xs mx-auto">
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove("up")}
                disabled={isLoading}
                className="p-3 sm:p-4 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50 touch-manipulation text-lg sm:text-xl min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="Вверх"
              >
                ↑
              </button>
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove("left")}
                disabled={isLoading}
                className="p-3 sm:p-4 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50 touch-manipulation text-lg sm:text-xl min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="Влево"
              >
                ←
              </button>
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove("right")}
                disabled={isLoading}
                className="p-3 sm:p-4 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50 touch-manipulation text-lg sm:text-xl min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="Вправо"
              >
                →
              </button>
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove("down")}
                disabled={isLoading}
                className="p-3 sm:p-4 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50 touch-manipulation text-lg sm:text-xl min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="Вниз"
              >
                ↓
              </button>
              <div /> {/* Spacer */}
            </div>
          </div>
        )}

        {/* Инструкция */}
        {!gameOver && (
          <div className="text-center text-xs sm:text-sm text-[var(--tg-theme-hint-color)] mb-4">
            <p>Объединяй одинаковые числа!</p>
            <p className="mt-1">Свайп по доске или используй кнопки</p>
            <p className="mt-1">Цель: достичь 2048</p>
          </div>
        )}

        {/* Кнопка новой игры */}
        {gameOver && (
          <div className="text-center">
            <button
              onClick={onBack}
              className="px-6 py-3 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-semibold hover:opacity-90 transition-opacity touch-manipulation text-sm sm:text-base min-h-[44px]"
            >
              Вернуться к играм
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
