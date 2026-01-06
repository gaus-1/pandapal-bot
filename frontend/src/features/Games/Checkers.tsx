/**
 * Checkers Game Component
 * Шашки - игра против панды (AI)
 */

import { useState, useEffect, useRef } from "react";
import { telegram } from "../../services/telegram";
import {
  checkersMove,
  getGameSession,
  type UserProfile,
} from "../../services/api";

interface CheckersProps {
  sessionId: number;
  user: UserProfile;
  onBack: () => void;
  onGameEnd: () => void;
}

export function Checkers({ sessionId, onBack, onGameEnd }: CheckersProps) {
  const [board, setBoard] = useState<(string | null)[][]>([]);
  const [selectedCell, setSelectedCell] = useState<[number, number] | null>(null);
  const [gameOver, setGameOver] = useState(false);
  const [winner, setWinner] = useState<"user" | "ai" | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUserTurn, setIsUserTurn] = useState(true);
  const [kings, setKings] = useState<boolean[][]>([]);

  const boardContainerRef = useRef<HTMLDivElement>(null);
  const [boardSize, setBoardSize] = useState(0);

  useEffect(() => {
    loadGameState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  useEffect(() => {
    const container = boardContainerRef.current;
    if (!container) return;

    const updateBoardSize = () => {
      if (container) {
        // Используем getBoundingClientRect для точных размеров
        const rect = container.getBoundingClientRect();
        const containerWidth = rect.width;
        const containerHeight = rect.height;

        // Берем минимум, чтобы доска была квадратной, и оставляем небольшой отступ
        const size = Math.floor(Math.min(containerWidth, containerHeight));
        if (size > 0 && size !== boardSize) {
          setBoardSize(size);
        }
      }
    };

    // Инициализация с небольшой задержкой, чтобы DOM успел отрисоваться
    const timer = setTimeout(updateBoardSize, 50);

    // Используем ResizeObserver для более точного отслеживания изменений размера контейнера
    const resizeObserver = new ResizeObserver(() => {
      updateBoardSize();
    });
    resizeObserver.observe(container);

    return () => {
      clearTimeout(timer);
      resizeObserver.disconnect();
    };
  }, [boardSize]); // Добавил boardSize в зависимости, чтобы избежать лишних перерисовок

  const loadGameState = async () => {
    try {
      const session = await getGameSession(sessionId);
      const gameState = session.game_state as {
        board?: (string | null)[][];
        kings?: boolean[][];
      };

      if (gameState.board) {
        setBoard(gameState.board);
        if (gameState.kings) {
          setKings(gameState.kings);
        }
      } else {
        // Стандартная инициализация доски
        const initBoard: (string | null)[][] = Array(8)
          .fill(null)
          .map(() => Array(8).fill(null));
        for (let row = 5; row < 8; row++) {
          for (let col = 0; col < 8; col++) {
            if ((row + col) % 2 === 1) {
              initBoard[row][col] = "user";
            }
          }
        }
        for (let row = 0; row < 3; row++) {
          for (let col = 0; col < 8; col++) {
            if ((row + col) % 2 === 1) {
              initBoard[row][col] = "ai";
            }
          }
        }
        setBoard(initBoard);
      }

      if (session.result && session.result !== "in_progress") {
        setGameOver(true);
        if (session.result === "win") {
          setWinner("user");
        } else if (session.result === "loss") {
          setWinner("ai");
        }
      }
    } catch (err) {
      console.error("Ошибка загрузки состояния игры:", err);
    }
  };

  const handleCellClick = async (row: number, col: number) => {
    if (gameOver || isLoading || !isUserTurn) {
      return;
    }

    if (board[row][col] === "user") {
      setSelectedCell([row, col]);
      telegram.hapticFeedback("light");
      return;
    }

    if (selectedCell) {
      const [fromRow, fromCol] = selectedCell;
      setIsLoading(true);
      setError(null);

      try {
        telegram.hapticFeedback("light");
        const result = await checkersMove(sessionId, fromRow, fromCol, row, col);

        setBoard(result.board);
        if (result.kings) {
          setKings(result.kings);
        }
        setSelectedCell(null);

        if (result.game_over) {
          setGameOver(true);
          if (result.winner === "user") {
            setWinner("user");
            telegram.notifySuccess();
            setTimeout(() => {
              telegram
                .showPopup({
                  title: "🎉 Победа!",
                  message: "Ты победил панду! Отличная игра!",
                  buttons: [{ type: "close", text: "Закрыть" }],
                });
            }, 500);
          } else if (result.winner === "ai") {
            setWinner("ai");
            telegram.notifyWarning();
            setTimeout(() => {
              telegram.showPopup({
                title: "😔 Поражение",
                message: "Панда выиграла! Попробуй еще раз!",
                buttons: [{ type: "close", text: "Закрыть" }],
              });
            }, 500);
          }
          onGameEnd();
        } else {
          setIsUserTurn(true);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Ошибка хода";
        setError(errorMessage);
        telegram.notifyError();
        console.error("Ошибка хода:", err);
        setSelectedCell(null);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const isKing = (row: number, col: number) => {
    return kings[row]?.[col] === true;
  };

  const isDarkCell = (row: number, col: number) => {
    return (row + col) % 2 === 1;
  };

  const isSelected = (row: number, col: number) => {
    return selectedCell && selectedCell[0] === row && selectedCell[1] === col;
  };

  return (
    <div className="w-full h-full bg-[var(--tg-theme-bg-color)] flex flex-col overflow-hidden">
      {/* Заголовок */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-[var(--tg-theme-hint-color)]/20">
        <button
          onClick={onBack}
          className="p-2 rounded-lg bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] hover:bg-[var(--tg-theme-hint-color)]/10 transition-colors text-sm touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label="Назад"
        >
          ← Назад
        </button>
        <h2 className="text-lg sm:text-xl font-bold text-[var(--tg-theme-text-color)]">
          ⚫⚪ Шашки
        </h2>
        <div className="w-10" />
      </div>

      {/* Статус */}
      <div className="flex-shrink-0 text-center py-2 px-4">
        <div className="text-lg sm:text-xl font-bold text-[var(--tg-theme-text-color)] mb-1">
          {gameOver
            ? winner === "user"
              ? "🎉 Ты победил!"
              : winner === "ai"
                ? "😔 Панда победила!"
                : "🤝 Ничья!"
            : isLoading
              ? "Панда думает..."
              : isUserTurn
                ? "Твой ход!"
                : "Ход панды..."}
        </div>
        {error && (
          <p className="text-xs sm:text-sm text-red-500 mt-1">{error}</p>
        )}
      </div>

      {/* Игровая доска - идеальный квадрат */}
      <div className="flex-1 flex items-center justify-center px-2 sm:px-4 pb-2 min-h-0 w-full">
        <div
          ref={boardContainerRef}
          className="w-full h-full flex items-center justify-center relative"
        >
          {/* Отрисовка доски только если размер вычислен */}
          {boardSize > 0 && (
            <div
              className="grid grid-cols-8 grid-rows-8 gap-[2px] bg-[var(--tg-theme-hint-color)] border-[4px] border-[var(--tg-theme-hint-color)] rounded-xl shadow-2xl overflow-hidden"
              style={{
                width: `${boardSize}px`,
                height: `${boardSize}px`,
              }}
            >
              {board.length > 0 ? (
                board.map((row, rowIndex) =>
                  row.map((_, colIndex) => {
                    const isDark = isDarkCell(rowIndex, colIndex);
                    const cell = board[rowIndex]?.[colIndex];
                    const selected = isSelected(rowIndex, colIndex);

                    return (
                      <button
                        key={`${rowIndex}-${colIndex}`}
                        onClick={() => handleCellClick(rowIndex, colIndex)}
                        disabled={!isUserTurn || isLoading || gameOver}
                        className={`
                          w-full h-full relative flex items-center justify-center
                          transition-all duration-200 touch-manipulation outline-none
                          ${
                            isDark
                              ? "bg-[var(--tg-theme-button-color)]"
                              : "bg-[var(--tg-theme-bg-color)]"
                          }
                          ${
                            selected
                              ? "brightness-125 ring-inset ring-4 ring-yellow-400/60 z-10"
                              : ""
                          }
                        `}
                        aria-label={`Клетка ${rowIndex + 1}, ${colIndex + 1}`}
                      >
                        {cell && (
                          <div className="w-[85%] h-[85%] aspect-square flex items-center justify-center relative">
                            {/* Основное тело шашки */}
                            <div
                              className={`
                                w-full h-full rounded-full shadow-lg shrink-0 relative flex items-center justify-center
                                transition-transform active:scale-95
                                ${cell === "user"
                                  ? "bg-white border-[4px] border-gray-300 shadow-gray-400/50"
                                  : "bg-gray-800 border-[4px] border-gray-900 shadow-black/50"}
                              `}
                              style={{
                                boxShadow: cell === "user"
                                  ? "inset 0 -3px 5px rgba(0,0,0,0.2), 0 3px 6px rgba(0,0,0,0.3)"
                                  : "inset 0 -3px 5px rgba(0,0,0,0.5), 0 3px 6px rgba(0,0,0,0.5)",
                              }}
                            >
                              {/* Блик для объема */}
                              <div className="absolute inset-[10%] rounded-full bg-gradient-to-tr from-black/10 to-white/30 pointer-events-none"></div>

                              {/* Иконка Короля */}
                              {isKing(rowIndex, colIndex) && (
                                <span
                                  className={`
                                    text-[1.2em] font-bold relative z-10 leading-none drop-shadow-sm
                                    ${cell === "user" ? "text-yellow-600" : "text-yellow-400"}
                                  `}
                                >
                                  👑
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </button>
                    );
                  })
                )
              ) : (
                <div className="col-span-8 row-span-8 flex items-center justify-center text-[var(--tg-theme-hint-color)]">
                  Загрузка...
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Инструкция */}
      {!gameOver && (
        <div className="flex-shrink-0 text-center text-xs sm:text-sm text-[var(--tg-theme-hint-color)] px-4 py-2 space-y-1 bg-[var(--tg-theme-bg-color)]">
          <p className="m-0">Ты играешь белыми, панда играет черными</p>
          <p className="m-0">Нажми на свою фишку, затем на клетку для хода</p>
        </div>
      )}

      {/* Кнопка новой игры */}
      {gameOver && (
        <div className="flex-shrink-0 text-center px-4 py-3 bg-[var(--tg-theme-bg-color)]">
          <button
            onClick={onBack}
            className="px-8 py-3 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-semibold hover:opacity-90 transition-opacity touch-manipulation text-sm sm:text-base min-h-[44px] shadow-md"
          >
            Вернуться к играм
          </button>
        </div>
      )}
    </div>
  );
}
