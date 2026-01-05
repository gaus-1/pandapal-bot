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

  // Реф для контейнера доски
  const boardContainerRef = useRef<HTMLDivElement>(null);
  // Состояние для хранения размера доски (width = height)
  const [boardSize, setBoardSize] = useState<number>(0);

  // Эффект для отслеживания ширины контейнера и установки точной высоты
  useEffect(() => {
    const container = boardContainerRef.current;
    if (!container) return;

    const updateSize = () => {
      const width = container.offsetWidth;
      setBoardSize(width);
    };

    // Инициализация
    updateSize();

    // ResizeObserver для отслеживания изменений (поворот экрана, изменение размера окна)
    const resizeObserver = new ResizeObserver(() => {
      updateSize();
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  // ... (остальной код инициализации игры без изменений)
  useEffect(() => {
    loadGameState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

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
    <div className="w-full h-full bg-[var(--tg-theme-bg-color)] overflow-y-auto flex flex-col items-center pt-4 pb-8">
      <div className="w-full max-w-md px-4 flex flex-col items-center">
        {/* Заголовок */}
        <div className="w-full flex items-center justify-between mb-4">
          <button
            onClick={onBack}
            className="p-2.5 rounded-lg bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] hover:bg-[var(--tg-theme-hint-color)]/10 transition-colors text-sm sm:text-base touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Назад"
          >
            ← Назад
          </button>
          <h2 className="text-xl sm:text-2xl font-bold text-[var(--tg-theme-text-color)]">
            ⚫⚪ Шашки
          </h2>
          <div className="w-10" />
        </div>

        {/* Статус */}
        <div className="text-center mb-4 w-full">
          <div className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-1">
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
            <p className="text-xs sm:text-sm text-red-500 mt-2">{error}</p>
          )}
        </div>

        {/* Контейнер для измерения ширины */}
        {/*
           w-[90%] и max-w-[400px] задают желаемую ширину.
           boardSize устанавливает высоту равной этой ширине.
        */}
        <div
          ref={boardContainerRef}
          className="w-[90%] max-w-[400px] relative mb-6"
          style={{ height: `${boardSize}px` }}
        >
          {/* Сетка занимает весь контейнер */}
          <div className="w-full h-full grid grid-cols-8 grid-rows-8 gap-[1px] bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] border-[4px] border-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] rounded-xl shadow-xl overflow-hidden">
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
                        w-full h-full relative
                        transition-all duration-200 touch-manipulation
                        flex items-center justify-center
                        ${
                          isDark
                            ? "bg-[var(--tg-theme-button-color)]"
                            : "bg-[var(--tg-theme-bg-color)]"
                        }
                        ${
                          selected
                            ? "ring-inset ring-4 ring-yellow-400/60 z-10"
                            : ""
                        }
                        ${
                          board[rowIndex][colIndex] === "user" && !gameOver && !isLoading
                            ? "hover:opacity-80 cursor-pointer"
                            : ""
                        }
                        disabled:opacity-50 disabled:cursor-not-allowed
                      `}
                      aria-label={`Клетка ${rowIndex + 1}, ${colIndex + 1}`}
                    >
                      {cell && (
                        <div className="absolute inset-0 flex items-center justify-center p-[12%]">
                          <div
                            className={`
                              w-full aspect-square rounded-full shadow-lg shrink-0 relative flex items-center justify-center
                              ${cell === "user"
                                ? "bg-white border-[2px] border-gray-300"
                                : "bg-gray-800 border-[2px] border-gray-900"}
                            `}
                          >
                            <div className="absolute inset-[4px] rounded-full border border-white/20 pointer-events-none"></div>

                            {isKing(rowIndex, colIndex) && (
                              <span className={`
                                text-[0.7em] font-bold relative z-10 leading-none
                                ${cell === "user" ? "text-gray-700" : "text-white"}
                              `}>
                                {cell === "user" ? "♔" : "♚"}
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
        </div>

        {/* Инструкция */}
        {!gameOver && (
          <div className="text-center text-xs sm:text-sm text-[var(--tg-theme-hint-color)] leading-relaxed px-2">
            <p className="m-0">Ты играешь белыми, панда играет черными</p>
            <p className="m-0">Нажми на свою фишку, затем на клетку для хода</p>
          </div>
        )}

        {/* Кнопка новой игры */}
        {gameOver && (
          <div className="text-center w-full mt-2">
            <button
              onClick={onBack}
              className="px-8 py-3 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-semibold hover:opacity-90 transition-opacity touch-manipulation text-sm sm:text-base min-h-[44px]"
            >
              Вернуться к играм
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
