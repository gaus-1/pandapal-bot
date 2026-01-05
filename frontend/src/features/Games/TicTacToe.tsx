/**
 * TicTacToe Game Component
 * Крестики-нолики против панды (AI)
 */

import { useState, useEffect } from "react";
import { telegram } from "../../services/telegram";
import {
  ticTacToeMove,
  getGameSession,
  type UserProfile,
} from "../../services/api";

interface TicTacToeProps {
  sessionId: number;
  user: UserProfile;
  onBack: () => void;
  onGameEnd: () => void;
}

export function TicTacToe({ sessionId, onBack, onGameEnd }: TicTacToeProps) {
  const [board, setBoard] = useState<(string | null)[]>(Array(9).fill(null));
  const [isUserTurn, setIsUserTurn] = useState(true);
  const [gameOver, setGameOver] = useState(false);
  const [winner, setWinner] = useState<"user" | "ai" | "draw" | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiMoveIndex, setAiMoveIndex] = useState<number | null>(null);
  const [lastMoveIndex, setLastMoveIndex] = useState<number | null>(null);

  useEffect(() => {
    loadGameState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const loadGameState = async () => {
    try {
      const session = await getGameSession(sessionId);
      const gameState = session.game_state as { board?: (string | null)[] };

      if (gameState.board) {
        setBoard(gameState.board);
        const hasEmptyCells = gameState.board.some((cell) => cell === null);
        setIsUserTurn(hasEmptyCells);
      } else {
        setBoard(Array(9).fill(null));
        setIsUserTurn(true);
      }

      if (session.result && session.result !== "in_progress") {
        setGameOver(true);
        if (session.result === "win") {
          setWinner("user");
        } else if (session.result === "loss") {
          setWinner("ai");
        } else {
          setWinner("draw");
        }
      }
    } catch (err) {
      console.error("Ошибка загрузки состояния игры:", err);
      setBoard(Array(9).fill(null));
      setIsUserTurn(true);
    }
  };

  const handleSquareClick = async (index: number) => {
    if (!isUserTurn || gameOver || board[index] !== null || isLoading) {
      return;
    }

    setIsLoading(true);
    setError(null);
    setLastMoveIndex(index);

    try {
      telegram.hapticFeedback("light");
      const result = await ticTacToeMove(sessionId, index);

      setBoard(result.board);
      setAiMoveIndex(result.ai_move);

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
                buttons: [
                  { type: "default", text: "Поделиться", id: "share" },
                  { type: "close", text: "Закрыть" },
                ],
              })
              .then((buttonId) => {
                if (buttonId === "share") {
                  telegram.shareGameResult("Крестики-нолики", "win");
                }
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
        } else {
          setWinner("draw");
          telegram.notifyWarning();
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
    } finally {
      setIsLoading(false);
    }
  };

  const getSquareContent = (index: number) => {
    if (board[index] === "X") return "❌";
    if (board[index] === "O") return "⭕";
    return null;
  };

  const getStatusMessage = () => {
    if (gameOver) {
      if (winner === "user") return "🎉 Ты победил!";
      if (winner === "ai") return "😔 Панда победила!";
      return "🤝 Ничья!";
    }
    if (isLoading) return "Панда думает...";
    return isUserTurn ? "Твой ход!" : "Ход панды...";
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
            ⭕ Крестики-нолики
          </h2>
          <div className="w-10 sm:w-12" />
        </div>

        {/* Статус */}
        <div className="text-center mb-4 sm:mb-6">
          <p className="text-base sm:text-lg font-semibold text-[var(--tg-theme-text-color)]">
            {getStatusMessage()}
          </p>
          {error && (
            <p className="text-xs sm:text-sm text-red-500 mt-2">{error}</p>
          )}
        </div>

        {/* Игровая доска */}
        <div className="bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] rounded-xl sm:rounded-2xl p-3 sm:p-4 mb-4 sm:mb-6">
          <div className="grid grid-cols-3 gap-1.5 sm:gap-2">
            {Array.from({ length: 9 }).map((_, index) => {
              const content = getSquareContent(index);
              const isAiMove = aiMoveIndex === index;
              const isUserMove = lastMoveIndex === index;
              const isEmpty = board[index] === null;

              return (
                <button
                  key={index}
                  onClick={() => handleSquareClick(index)}
                  disabled={!isEmpty || isLoading || gameOver}
                  className={`
                    aspect-square rounded-lg sm:rounded-xl text-3xl sm:text-4xl font-bold
                    flex items-center justify-center
                    transition-all duration-300 touch-manipulation
                    min-h-[60px] sm:min-h-[80px] min-w-[60px] sm:min-w-[80px]
                    ${
                      isEmpty && !gameOver && !isLoading
                        ? "bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] hover:opacity-80 active:scale-95"
                        : "bg-[var(--tg-theme-bg-color)] text-[var(--tg-theme-text-color)]"
                    }
                    ${
                      isAiMove
                        ? "ring-2 sm:ring-4 ring-yellow-400 ring-opacity-50 animate-pulse"
                        : ""
                    }
                    ${
                      isUserMove
                        ? "ring-2 sm:ring-4 ring-blue-400 ring-opacity-50"
                        : ""
                    }
                    disabled:opacity-50 disabled:cursor-not-allowed
                  `}
                  style={{
                    animation: isUserMove
                      ? "fadeInScale 0.3s ease-out"
                      : undefined,
                  }}
                  aria-label={`Клетка ${index + 1}`}
                >
                  {content}
                </button>
              );
            })}
          </div>
        </div>

        {/* Инструкция */}
        {!gameOver && (
          <div className="text-center text-xs sm:text-sm text-[var(--tg-theme-hint-color)]">
            <p>Ты играешь ❌, панда играет ⭕</p>
            <p className="mt-1">Нажми на клетку, чтобы сделать ход</p>
          </div>
        )}

        {/* Кнопка новой игры */}
        {gameOver && (
          <div className="text-center space-y-3">
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
        @keyframes fadeInScale {
          from {
            opacity: 0;
            transform: scale(0.8);
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
