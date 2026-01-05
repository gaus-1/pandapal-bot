/**
 * Checkers Game Component
 * Шашки - игра против панды (AI)
 */

import { useState, useEffect } from "react";
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
        // Инициализируем доску (пользователь внизу визуально, AI вверху)
        const initBoard: (string | null)[][] = Array(8)
          .fill(null)
          .map(() => Array(8).fill(null));
        // Пользователь (внизу визуально) - последние 3 ряда
        for (let row = 5; row < 8; row++) {
          for (let col = 0; col < 8; col++) {
            if ((row + col) % 2 === 1) {
              initBoard[row][col] = "user";
            }
          }
        }
        // AI (вверху визуально) - первые 3 ряда
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

    // Если выбрана клетка с фишкой пользователя
    if (board[row][col] === "user") {
      setSelectedCell([row, col]);
      telegram.hapticFeedback("light");
      return;
    }

    // Если выбрана клетка для хода
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
          // Игра продолжается
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
    <div className="w-full h-full bg-[var(--tg-theme-bg-color)] overflow-y-auto">
      <div className="w-full max-w-md mx-auto px-3 sm:px-4 py-4 sm:py-6">
        {/* Заголовок */}
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={onBack}
            className="p-2.5 sm:p-3 rounded-lg bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] hover:bg-[var(--tg-theme-hint-color)]/10 transition-colors text-sm sm:text-base touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Назад"
          >
            ← Назад
          </button>
          <h2 className="text-xl sm:text-2xl font-bold text-[var(--tg-theme-text-color)]">
            ⚫⚪ Шашки
          </h2>
          <div className="w-10 sm:w-12" />
        </div>

        {/* Статус */}
        <div className="text-center mb-0">
          <div className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-0">
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

        {/* Игровая доска */}
        <div className="bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] rounded-xl p-1 mb-4 overflow-hidden w-full">
          {board.length > 0 ? (
            <div className="w-full aspect-square">
              <div className="grid grid-cols-8 gap-0.5 w-full h-full">
                {board.map((row, rowIndex) =>
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
                          aspect-square rounded-md
                          relative flex items-center justify-center
                          transition-all duration-200 touch-manipulation
                          w-full h-full
                          ${
                            isDark
                              ? "bg-[var(--tg-theme-button-color)]"
                              : "bg-[var(--tg-theme-bg-color)]"
                          }
                          ${
                            selected
                              ? "ring-2 sm:ring-4 ring-yellow-400 ring-opacity-75"
                              : ""
                          }
                          ${
                            board[rowIndex][colIndex] === "user" && !gameOver && !isLoading
                              ? "hover:opacity-80 active:scale-95 cursor-pointer"
                              : ""
                          }
                          disabled:opacity-50 disabled:cursor-not-allowed
                        `}
                        aria-label={`Клетка ${rowIndex + 1}, ${colIndex + 1}`}
                      >
                        {cell === "user" && (
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-[85%] h-[85%] sm:w-[90%] sm:h-[90%] rounded-full bg-white border-[3px] border-gray-300 shadow-lg flex items-center justify-center">
                              {isKing(rowIndex, colIndex) && (
                                <span className="text-sm sm:text-base md:text-lg font-bold text-gray-700">♔</span>
                              )}
                            </div>
                          </div>
                        )}
                        {cell === "ai" && (
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-[85%] h-[85%] sm:w-[90%] sm:h-[90%] rounded-full bg-gray-800 border-[3px] border-gray-900 shadow-lg flex items-center justify-center">
                              {isKing(rowIndex, colIndex) && (
                                <span className="text-sm sm:text-base md:text-lg font-bold text-white">♚</span>
                              )}
                            </div>
                          </div>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          ) : (
            <div className="text-center text-[var(--tg-theme-hint-color)] py-8">
              Загрузка...
            </div>
          )}
        </div>

        {/* Инструкция */}
        {!gameOver && (
          <div className="text-center text-xs sm:text-sm text-[var(--tg-theme-hint-color)]">
            <p>Ты играешь белыми, панда играет черными</p>
            <p className="mt-1">Нажми на свою фишку, затем на клетку для хода</p>
            <p className="mt-1">Двигайся по диагонали вперед</p>
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
    </div>
  );
}
