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
import { PandaReaction } from "../../components/PandaReaction";

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
    // Оптимизация: не загружаем состояние если игра закончена
    if (gameOver) return;

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

      // Сбрасываем анимацию через 300ms (быстрее для лучшего UX)
      if (result.ai_move !== null && result.ai_move !== undefined) {
        setTimeout(() => {
          setAiMoveIndex(null);
        }, 300);
      }

      if (result.game_over) {
        setGameOver(true);
        if (result.winner === "user") {
          setWinner("user");
          telegram.notifySuccess();
        } else if (result.winner === "ai") {
          setWinner("ai");
          telegram.notifyWarning();
        } else {
          setWinner("draw");
          telegram.notifyWarning();
        }
        onGameEnd();
      } else {
        // Игра продолжается - пользователь может сделать следующий ход
        setIsUserTurn(true);
        setAiMoveIndex(null);
        setLastMoveIndex(null);
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
    if (board[index] === "X") return <span style={{ color: '#000', filter: 'brightness(0)' }}>❌</span>;
    if (board[index] === "O") return <span style={{ color: '#fff' }}>⭕</span>;
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
    <div className="w-full h-full bg-white dark:bg-slate-900 overflow-y-auto">
      <div className="max-w-md mx-auto px-3 sm:px-4 py-4 sm:py-6">
        {/* Заголовок */}
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={onBack}
            className="p-2.5 sm:p-3 rounded-lg bg-gray-50 dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 active:bg-gray-200 dark:active:bg-slate-600 transition-colors text-sm sm:text-base touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center text-gray-900 dark:text-slate-100"
            aria-label="Назад"
          >
            ← Назад
          </button>
          <h2 className="text-xl sm:text-2xl font-display font-bold text-gray-900 dark:text-slate-100">
            ❌⭕ Крестики-нолики
          </h2>
          <div className="w-10 sm:w-12" />
        </div>

        {/* Статус */}
        <div className="text-center mb-0">
          {winner && winner !== "draw" && (
            <div className="mb-3">
              <PandaReaction mood={winner === "user" ? "sad" : "happy"} />
            </div>
          )}
          <div className="text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-100 mb-0">
            {getStatusMessage()}
          </div>
          {error && (
            <p className="text-xs sm:text-sm text-red-500 mt-2">{error}</p>
          )}
        </div>

        {/* Игровая доска */}
        <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-1 mb-4 w-full max-w-[260px] mx-auto border border-gray-200 dark:border-slate-600">
          <div className="grid grid-cols-3 gap-0.5 w-full">
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
                    aspect-square rounded-md text-base font-bold
                    flex items-center justify-center
                    transition-all duration-300 touch-manipulation
                    w-full
                    ${
                      isEmpty && !gameOver && !isLoading
                        ? "bg-blue-500 dark:bg-blue-600 text-white hover:opacity-80 dark:hover:opacity-70 active:scale-95"
                        : "bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 border border-gray-200 dark:border-slate-600"
                    }
                    ${
                      isAiMove
                        ? "ring-2 sm:ring-4 ring-yellow-400 dark:ring-yellow-500 ring-opacity-60 dark:ring-opacity-70 animate-[fadeInScale_0.3s_ease-out]"
                        : ""
                    }
                    ${
                      isUserMove
                        ? "ring-2 sm:ring-4 ring-blue-500 dark:ring-blue-400 ring-opacity-60 dark:ring-opacity-70"
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
          <div className="text-center text-xs sm:text-sm text-gray-600 dark:text-slate-400 max-w-[260px] mx-auto px-2">
            <p>Ты играешь ❌, панда играет ⭕</p>
            <p className="mt-1">Нажми на клетку, чтобы сделать ход</p>
          </div>
        )}

        {/* Кнопка новой игры */}
        {gameOver && (
          <div className="text-center space-y-3">
            <button
              onClick={onBack}
              className="px-6 py-3 bg-blue-500 dark:bg-blue-600 text-white rounded-xl font-semibold hover:opacity-90 transition-opacity touch-manipulation text-sm sm:text-base min-h-[44px]"
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
