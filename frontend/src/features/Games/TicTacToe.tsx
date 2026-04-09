/**
 * TicTacToe Game Component
 * Крестики-нолики против панды (AI)
 */

import { useState, useEffect } from "react";
import { telegram } from "../../services/telegram";
import {
  ticTacToeMove,
  getGameSession,
  createGame,
  type UserProfile,
} from "../../services/api";
import { PandaReaction } from "../../components/PandaReaction";

interface TicTacToeProps {
  sessionId: number;
  user: UserProfile;
  onBack: () => void;
  onGameEnd: () => void;
}

export function TicTacToe({ sessionId, user, onBack, onGameEnd }: TicTacToeProps) {
  const [board, setBoard] = useState<(string | null)[]>(() => Array(9).fill(null));
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
    if (gameOver) return;
    if (sessionId == null || Number.isNaN(Number(sessionId))) return;

    try {
      const session = await getGameSession(sessionId);
      if (!session || typeof session !== 'object') {
        setBoard(Array(9).fill(null));
        setIsUserTurn(true);
        return;
      }
      const gameState = (session.game_state ?? {}) as { board?: (string | null)[] };

      if (Array.isArray(gameState.board) && gameState.board.length === 9) {
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
          ❌⭕ Крестики-нолики
        </h2>
        <div className="w-10" />
      </div>

      {/* Статус */}
      <div className="flex-shrink-0 text-center py-fib-2 px-fib-3">
        {winner && winner !== "draw" && (
          <div className="mb-1">
            <PandaReaction mood={winner === "user" ? "sad" : "happy"} size="small" />
          </div>
        )}
        <div className="font-display text-lg sm:text-xl font-bold text-gray-900 dark:text-slate-100">
          {getStatusMessage()}
        </div>
        {error && (
          <p className="text-xs sm:text-sm text-red-500 mt-1">{error}</p>
        )}
      </div>

      {/* Игровая доска */}
      <div className="flex-1 flex items-center justify-center px-fib-3 min-h-0">
        <div className="bg-gray-50 dark:bg-slate-800 rounded-xl p-1.5 w-full max-w-[280px] fold:max-w-[260px] xs:max-w-[320px] sm:max-w-[360px] md:max-w-[400px] mx-auto border border-gray-200 dark:border-slate-600 shadow-md">
          <div className="grid grid-cols-3 gap-1 w-full">
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
                    aspect-square rounded-lg text-4xl fold:text-3xl xs:text-5xl sm:text-6xl md:text-7xl font-bold
                    flex items-center justify-center
                    transition-all duration-300 touch-manipulation
                    w-full
                    ${isEmpty && !gameOver && !isLoading
                      ? "bg-blue-500 dark:bg-blue-600 text-white hover:opacity-80 dark:hover:opacity-70 active:scale-95"
                      : "bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 border border-gray-200 dark:border-slate-600"
                    }
                    ${isAiMove
                      ? "ring-2 ring-yellow-400 dark:ring-yellow-500 ring-opacity-60 dark:ring-opacity-70 animate-[fadeInScale_0.3s_ease-out]"
                      : ""
                    }
                    ${isUserMove
                      ? "ring-2 ring-blue-500 dark:ring-blue-400 ring-opacity-60 dark:ring-opacity-70"
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
      </div>

      {/* Инструкция / Кнопки */}
      <div className="flex-shrink-0 text-center px-fib-3 py-fib-2">
        {!gameOver ? (
          <div className="text-xs text-gray-600 dark:text-slate-400">
            <p>Ты играешь ❌, панда играет ⭕</p>
            <p className="mt-0.5">Нажми на клетку, чтобы сделать ход</p>
          </div>
        ) : (
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={async () => {
                try {
                  const result = await createGame(user.telegram_id, 'tic_tac_toe');
                  if (result?.session_id != null) window.location.reload();
                } catch { onGameEnd(); }
              }}
              className="px-5 py-2.5 bg-green-500 dark:bg-green-600 text-white rounded-xl font-semibold hover:opacity-90 transition-opacity touch-manipulation text-sm min-h-[44px]"
            >
              Играть снова
            </button>
            <button
              onClick={onBack}
              className="px-5 py-2.5 bg-blue-500 dark:bg-blue-600 text-white rounded-xl font-semibold hover:opacity-90 transition-opacity touch-manipulation text-sm min-h-[44px]"
            >
              К играм
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
