/**
 * Checkers Game Component
 * Шашки - игра против панды (AI)
 * Исправлено: Убрана серая зона (opacity-50), шашки оставлены на месте (-6px)
 */

import { useState, useEffect } from "react";
import { telegram } from "../../services/telegram";
import {
  checkersMove,
  getCheckersValidMoves,
  getGameSession,
  type UserProfile,
} from "../../services/api";
import { PandaReaction } from "../../components/PandaReaction";

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
  const [validMoves, setValidMoves] = useState<Array<{
    from: [number, number];
    to: [number, number];
    capture: [number, number] | null;
  }>>([]);

  useEffect(() => {
    loadGameState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  useEffect(() => {
    if (isUserTurn && !gameOver && board.length > 0) {
      loadValidMoves();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isUserTurn, gameOver, board, sessionId]);

  const loadGameState = async () => {
    // Оптимизация: не загружаем состояние если игра закончена
    if (gameOver) return;

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

  const loadValidMoves = async () => {
    try {
      const moves = await getCheckersValidMoves(sessionId);
      setValidMoves(Array.isArray(moves) ? moves : []);
    } catch (err) {
      console.error("Ошибка загрузки валидных ходов:", err);
      setValidMoves([]);
    }
  };

  const handleCellClick = async (row: number, col: number) => {
    if (gameOver || isLoading || !isUserTurn) {
      return;
    }

    const moves = validMoves ?? [];
    // Проверяем, можно ли выбрать эту фишку (есть ли у неё валидные ходы)
    if (board[row][col] === "user") {
      const canMove = moves.some(
        (move) => move.from[0] === row && move.from[1] === col
      );
      if (canMove) {
        setSelectedCell([row, col]);
        telegram.hapticFeedback("light");
      } else {
        telegram.hapticFeedback("heavy");
        const hasMandatoryCapture = moves.some((move) => move.capture !== null);
        if (hasMandatoryCapture) {
          setError("Сначала нужно съесть фишку противника");
        } else {
          setError("Эта фишка не может ходить");
        }
        setTimeout(() => setError(null), 2000);
      }
      return;
    }

    if (selectedCell) {
      const [fromRow, fromCol] = selectedCell;
      const isValidMove = moves.some(
        (move) =>
          move.from[0] === fromRow &&
          move.from[1] === fromCol &&
          move.to[0] === row &&
          move.to[1] === col
      );

      if (!isValidMove) {
        telegram.hapticFeedback("heavy");
        setError("Невалидный ход");
        setTimeout(() => setError(null), 2000);
        return;
      }

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
          } else if (result.winner === "ai") {
            setWinner("ai");
            telegram.notifyWarning();
          }
          setIsUserTurn(false);
          onGameEnd();
        } else {
          // После хода пользователя AI делает ход автоматически на бэкенде
          // Теперь снова очередь пользователя
          setIsUserTurn(true);
          // Загружаем новые валидные ходы
          await loadValidMoves();
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

  const isValidMoveTarget = (row: number, col: number) => {
    if (!selectedCell) return false;
    const m = validMoves ?? [];
    return m.some(
      (move) =>
        move.from[0] === selectedCell[0] &&
        move.from[1] === selectedCell[1] &&
        move.to[0] === row &&
        move.to[1] === col
    );
  };

  const hasMandatoryCapture = () => {
    return (validMoves ?? []).some((move) => move.capture !== null);
  };

  return (
    <div className="w-full h-full bg-white dark:bg-slate-800 flex flex-col overflow-hidden">
      {/* Заголовок */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-slate-700">
        <button
          onClick={onBack}
          className="p-2 rounded-lg bg-gray-50 dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 active:bg-gray-200 dark:active:bg-slate-600 transition-colors text-sm touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center text-gray-900 dark:text-slate-100"
          aria-label="Назад"
        >
          ← Назад
        </button>
        <h2 className="text-lg sm:text-xl font-display font-bold text-gray-900 dark:text-slate-100">
          ⚫⚪ Шашки
        </h2>
        <div className="w-10" />
      </div>

      {/* Статус */}
      <div className="flex-shrink-0 text-center py-2 px-4">
        {winner && (
          <div className="mb-3">
            <PandaReaction mood={winner === "user" ? "sad" : "happy"} />
          </div>
        )}
        <div className="text-lg sm:text-xl font-bold text-gray-900 dark:text-slate-100 mb-1">
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
        {isUserTurn && !gameOver && hasMandatoryCapture() && (
          <p className="text-xs sm:text-sm text-orange-500 font-semibold mt-1">
            ⚠️ Обязательное взятие!
          </p>
        )}
        {error && (
          <p className="text-xs sm:text-sm text-red-500 mt-1">{error}</p>
        )}
      </div>

      {/* Игровая доска */}
      <div className="flex-1 flex items-center justify-center px-2 sm:px-4 pb-2 min-h-0 w-full">
        <div className="w-full max-w-[600px] aspect-square relative">
          <div className="w-full h-full grid grid-cols-8 grid-rows-8 gap-[2px] bg-gray-400 dark:bg-slate-700 border-[4px] border-gray-400 dark:border-slate-700 rounded-xl shadow-2xl overflow-hidden">
            {board.length > 0 ? (
              board.map((row, rowIndex) =>
                row.map((_, colIndex) => {
                  const isDark = isDarkCell(rowIndex, colIndex);
                  const cell = board[rowIndex]?.[colIndex];
                  const selected = isSelected(rowIndex, colIndex);
                  const isValidTarget = isValidMoveTarget(rowIndex, colIndex);

                  return (
                    <button
                      key={`${rowIndex}-${colIndex}`}
                      onClick={() => handleCellClick(rowIndex, colIndex)}
                      disabled={!isUserTurn || isLoading || gameOver}
                      className={`
                        w-full h-full aspect-square
                        flex items-center justify-center
                        transition-all duration-200 touch-manipulation outline-none
                        ${
                          isDark
                            ? "bg-blue-500 dark:bg-blue-700"
                            : "bg-white dark:bg-slate-600"
                        }
                        ${
                          selected
                            ? "brightness-125 dark:brightness-110 ring-inset ring-4 ring-yellow-400 dark:ring-yellow-500 ring-opacity-60 dark:ring-opacity-70 z-10"
                            : ""
                        }
                        ${
                          isValidTarget
                            ? "ring-2 ring-green-400 dark:ring-green-500 ring-opacity-80 dark:ring-opacity-70 ring-inset brightness-110 dark:brightness-105"
                            : ""
                        }
                      `}
                      aria-label={`Клетка ${rowIndex + 1}, ${colIndex + 1}`}
                    >
                      {cell && (
                        <div
                          className={`
                            w-[85%] aspect-square rounded-full shadow-lg shrink-0 relative flex items-center justify-center
                            transition-transform active:scale-95
                            -mt-[6px]
                            ${cell === "user"
                              ? "bg-white dark:bg-slate-300 border-[3px] border-gray-300 dark:border-slate-500"
                              : "bg-gray-800 dark:bg-slate-800 border-[3px] border-gray-900 dark:border-slate-700"}
                          `}
                          style={{
                            boxShadow: cell === "user"
                              ? "inset 0 -2px 4px rgba(0,0,0,0.2), 0 4px 8px rgba(0,0,0,0.4)"
                              : "inset 0 -2px 4px rgba(0,0,0,0.5), 0 4px 8px rgba(0,0,0,0.6)",
                          }}
                        >
                          {/* Блик */}
                          <div className="absolute inset-[15%] rounded-full bg-gradient-to-tr from-black/5 to-white/40 dark:from-black/10 dark:to-white/30 pointer-events-none"></div>

                          {/* Корона */}
                          {isKing(rowIndex, colIndex) && (
                            <span
                              className={`
                                text-[1.4em] leading-none drop-shadow-sm relative z-10
                                ${cell === "user" ? "text-yellow-600 dark:text-yellow-500" : "text-yellow-400 dark:text-yellow-300"}
                              `}
                            >
                              👑
                            </span>
                          )}
                        </div>
                      )}
                    </button>
                  );
                })
              )
            ) : (
              <div className="col-span-8 row-span-8 flex items-center justify-center text-gray-600 dark:text-slate-300">
                Загрузка...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Инструкция */}
      {!gameOver && (
        <div className="flex-shrink-0 text-center text-xs sm:text-sm text-gray-600 dark:text-slate-400 px-4 py-2 space-y-1 bg-white dark:bg-slate-800">
          <p className="m-0">Ты играешь белыми, панда играет черными</p>
          <p className="m-0">Нажми на свою фишку, затем на клетку для хода</p>
        </div>
      )}

      {/* Кнопка новой игры */}
      {gameOver && (
        <div className="flex-shrink-0 text-center px-4 py-3 bg-white dark:bg-slate-800">
          <button
            onClick={onBack}
            className="px-8 py-3 bg-blue-500 dark:bg-blue-600 text-white rounded-xl font-semibold hover:opacity-90 transition-opacity touch-manipulation text-sm sm:text-base min-h-[44px] shadow-md"
          >
            Вернуться к играм
          </button>
        </div>
      )}
    </div>
  );
}
