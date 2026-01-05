/**
 * TicTacToe Game Component
 * Крестики-нолики против панды (AI)
 */

import { useState, useEffect } from 'react';
import { telegram } from '../../services/telegram';
import { ticTacToeMove, type UserProfile } from '../../services/api';

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
  const [winner, setWinner] = useState<'user' | 'ai' | 'draw' | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiMoveIndex, setAiMoveIndex] = useState<number | null>(null);

  useEffect(() => {
    // Загружаем начальное состояние игры
    loadGameState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const loadGameState = async () => {
    try {
      const session = await getGameSession(sessionId);
      const gameState = session.game_state as { board?: (string | null)[] };

      if (gameState.board) {
        setBoard(gameState.board);
        // Проверяем, есть ли свободные клетки
        const hasEmptyCells = gameState.board.some(cell => cell === null);
        setIsUserTurn(hasEmptyCells);
      } else {
        setBoard(Array(9).fill(null));
        setIsUserTurn(true);
      }

      if (session.result && session.result !== 'in_progress') {
        setGameOver(true);
        if (session.result === 'win') {
          setWinner('user');
        } else if (session.result === 'loss') {
          setWinner('ai');
        } else {
          setWinner('draw');
        }
      }
    } catch (err) {
      console.error('Ошибка загрузки состояния игры:', err);
      // Fallback к начальному состоянию
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

    try {
      telegram.hapticFeedback('light');
      const result = await ticTacToeMove(sessionId, index);

      setBoard(result.board);
      setAiMoveIndex(result.ai_move);

      if (result.game_over) {
        setGameOver(true);
        if (result.winner === 'user') {
          setWinner('user');
          telegram.notifySuccess();
          setTimeout(() => {
            telegram.showPopup({
              title: '🎉 Победа!',
              message: 'Ты победил панду! Отличная игра!',
              buttons: [{ type: 'close', text: 'Закрыть' }],
            });
          }, 500);
        } else if (result.winner === 'ai') {
          setWinner('ai');
          telegram.notifyWarning();
          setTimeout(() => {
            telegram.showPopup({
              title: '😔 Поражение',
              message: 'Панда выиграла! Попробуй еще раз!',
              buttons: [{ type: 'close', text: 'Закрыть' }],
            });
          }, 500);
        } else {
          setWinner('draw');
          telegram.notifyWarning();
        }
        onGameEnd();
      } else {
        setIsUserTurn(true); // Следующий ход пользователя
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка хода';
      setError(errorMessage);
      telegram.notifyError();
      console.error('Ошибка хода:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getSquareContent = (index: number) => {
    if (board[index] === 'X') return '❌';
    if (board[index] === 'O') return '⭕';
    return null;
  };

  const getStatusMessage = () => {
    if (gameOver) {
      if (winner === 'user') return '🎉 Ты победил!';
      if (winner === 'ai') return '😔 Панда победила!';
      return '🤝 Ничья!';
    }
    if (isLoading) return 'Панда думает...';
    return isUserTurn ? 'Твой ход!' : 'Ход панды...';
  };

  return (
    <div className="w-full h-full bg-[var(--tg-theme-bg-color)] overflow-y-auto">
      <div className="max-w-md mx-auto px-4 py-6">
        {/* Заголовок */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={onBack}
            className="p-2 rounded-lg bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] hover:bg-[var(--tg-theme-hint-color)]/10 transition-colors"
            aria-label="Назад"
          >
            ← Назад
          </button>
          <h2 className="text-2xl font-bold text-[var(--tg-theme-text-color)]">
            ⭕ Крестики-нолики
          </h2>
          <div className="w-10" /> {/* Spacer */}
        </div>

        {/* Статус */}
        <div className="text-center mb-6">
          <p className="text-lg font-semibold text-[var(--tg-theme-text-color)]">
            {getStatusMessage()}
          </p>
          {error && (
            <p className="text-sm text-red-500 mt-2">{error}</p>
          )}
        </div>

        {/* Игровая доска */}
        <div className="bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] rounded-2xl p-4 mb-6">
          <div className="grid grid-cols-3 gap-2">
            {Array.from({ length: 9 }).map((_, index) => {
              const content = getSquareContent(index);
              const isAiMove = aiMoveIndex === index;
              const isEmpty = board[index] === null;

              return (
                <button
                  key={index}
                  onClick={() => handleSquareClick(index)}
                  disabled={!isEmpty || isLoading || gameOver}
                  className={`
                    aspect-square rounded-xl text-4xl font-bold
                    flex items-center justify-center
                    transition-all duration-200
                    ${isEmpty && !gameOver && !isLoading
                      ? 'bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] hover:opacity-80 active:scale-95'
                      : 'bg-[var(--tg-theme-bg-color)] text-[var(--tg-theme-text-color)]'
                    }
                    ${isAiMove ? 'ring-4 ring-yellow-400 ring-opacity-50' : ''}
                    disabled:opacity-50 disabled:cursor-not-allowed
                  `}
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
          <div className="text-center text-sm text-[var(--tg-theme-hint-color)]">
            <p>Ты играешь ❌, панда играет ⭕</p>
            <p className="mt-1">Нажми на клетку, чтобы сделать ход</p>
          </div>
        )}

        {/* Кнопка новой игры */}
        {gameOver && (
          <div className="text-center">
            <button
              onClick={onBack}
              className="px-6 py-3 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-semibold hover:opacity-90 transition-opacity"
            >
              Вернуться к играм
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
