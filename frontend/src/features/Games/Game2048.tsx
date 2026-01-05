/**
 * Game 2048 Component
 * Игра 2048 - объединение чисел
 */

import { useState, useEffect, useCallback } from 'react';
import { telegram } from '../../services/telegram';
import { game2048Move, getGameSession, type UserProfile } from '../../services/api';

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

      if (session.result && session.result !== 'in_progress') {
        setGameOver(true);
      }
    } catch (err) {
      console.error('Ошибка загрузки состояния игры:', err);
    }
  };

  const handleMove = useCallback(async (direction: 'up' | 'down' | 'left' | 'right') => {
    if (gameOver || isLoading) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      telegram.hapticFeedback('light');
      const result = await game2048Move(sessionId, direction);

      setBoard(result.board);
      setScore(result.score);
      setWon(result.won);

      if (result.game_over) {
        setGameOver(true);
        telegram.notifyError();
        setTimeout(() => {
          telegram.showPopup({
            title: '😔 Игра окончена',
            message: `Твой счет: ${result.score}. Попробуй еще раз!`,
            buttons: [{ type: 'close', text: 'Закрыть' }],
          });
        }, 500);
        onGameEnd();
      } else if (result.won && !won) {
        telegram.notifySuccess();
        setTimeout(() => {
          telegram.showPopup({
            title: '🎉 Победа!',
            message: 'Ты достиг 2048! Продолжай играть!',
            buttons: [{ type: 'close', text: 'Закрыть' }],
          });
        }, 500);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка хода';
      setError(errorMessage);
      telegram.notifyError();
      console.error('Ошибка хода:', err);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, gameOver, isLoading, won, onGameEnd]);

  // Обработка клавиатуры
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (gameOver || isLoading) return;

      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          handleMove('up');
          break;
        case 'ArrowDown':
          e.preventDefault();
          handleMove('down');
          break;
        case 'ArrowLeft':
          e.preventDefault();
          handleMove('left');
          break;
        case 'ArrowRight':
          e.preventDefault();
          handleMove('right');
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [gameOver, isLoading, handleMove]);

  const getTileColor = (value: number): string => {
    const colors: Record<number, string> = {
      2: 'bg-gray-200 dark:bg-gray-700',
      4: 'bg-gray-300 dark:bg-gray-600',
      8: 'bg-orange-200 dark:bg-orange-900',
      16: 'bg-orange-300 dark:bg-orange-800',
      32: 'bg-orange-400 dark:bg-orange-700',
      64: 'bg-orange-500 dark:bg-orange-600',
      128: 'bg-yellow-400 dark:bg-yellow-600',
      256: 'bg-yellow-500 dark:bg-yellow-500',
      512: 'bg-yellow-600 dark:bg-yellow-400',
      1024: 'bg-yellow-700 dark:bg-yellow-300',
      2048: 'bg-yellow-800 dark:bg-yellow-200',
    };
    return colors[value] || 'bg-gray-100 dark:bg-gray-800';
  };

  const getTileTextColor = (value: number): string => {
    return value <= 4 ? 'text-gray-800 dark:text-gray-200' : 'text-white';
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
            🔢 2048
          </h2>
          <div className="w-10" />
        </div>

        {/* Счет */}
        <div className="text-center mb-6">
          <div className="text-3xl font-bold text-[var(--tg-theme-text-color)] mb-2">
            {score}
          </div>
          {won && (
            <div className="text-sm text-green-500 font-semibold">
              🎉 Ты достиг 2048!
            </div>
          )}
          {error && (
            <p className="text-sm text-red-500 mt-2">{error}</p>
          )}
        </div>

        {/* Игровая доска */}
        <div className="bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] rounded-2xl p-4 mb-6">
          {board.length > 0 ? (
            <div className="grid grid-cols-4 gap-2">
              {board.flat().map((value, index) => (
                <div
                  key={index}
                  className={`
                    aspect-square rounded-lg flex items-center justify-center
                    font-bold text-xl
                    ${value === 0 ? 'bg-[var(--tg-theme-bg-color)]' : `${getTileColor(value)} ${getTileTextColor(value)}`}
                    transition-all duration-200
                  `}
                >
                  {value !== 0 && value}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-[var(--tg-theme-hint-color)] py-8">
              Загрузка...
            </div>
          )}
        </div>

        {/* Кнопки управления */}
        {!gameOver && (
          <div className="mb-6">
            <div className="grid grid-cols-3 gap-2 max-w-xs mx-auto">
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove('up')}
                disabled={isLoading}
                className="p-4 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50"
                aria-label="Вверх"
              >
                ↑
              </button>
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove('left')}
                disabled={isLoading}
                className="p-4 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50"
                aria-label="Влево"
              >
                ←
              </button>
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove('right')}
                disabled={isLoading}
                className="p-4 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50"
                aria-label="Вправо"
              >
                →
              </button>
              <div /> {/* Spacer */}
              <button
                onClick={() => handleMove('down')}
                disabled={isLoading}
                className="p-4 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-bold hover:opacity-80 active:scale-95 transition-all disabled:opacity-50"
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
          <div className="text-center text-sm text-[var(--tg-theme-hint-color)] mb-4">
            <p>Объединяй одинаковые числа!</p>
            <p className="mt-1">Используй стрелки или кнопки</p>
            <p className="mt-1">Цель: достичь 2048</p>
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
