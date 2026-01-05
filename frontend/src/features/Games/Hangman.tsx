/**
 * Hangman Game Component
 * Виселица - угадывание слова
 */

import { useState, useEffect } from 'react';
import { telegram } from '../../services/telegram';
import { hangmanGuess, getGameSession, type UserProfile } from '../../services/api';

interface HangmanProps {
  sessionId: number;
  user: UserProfile;
  onBack: () => void;
  onGameEnd: () => void;
}

const ALPHABET = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'.split('');

export function Hangman({ sessionId, onBack, onGameEnd }: HangmanProps) {
  const [word, setWord] = useState<string>('');
  const [guessedLetters, setGuessedLetters] = useState<string[]>([]);
  const [mistakes, setMistakes] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [won, setWon] = useState<boolean | null>(null);
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
        word?: string;
        guessed_letters?: string[];
        mistakes?: number;
      };

      if (gameState.word) {
        setWord(gameState.word);
      }
      if (gameState.guessed_letters) {
        setGuessedLetters(gameState.guessed_letters);
      }
      if (gameState.mistakes !== undefined) {
        setMistakes(gameState.mistakes);
      }

      if (session.result && session.result !== 'in_progress') {
        setGameOver(true);
        setWon(session.result === 'win');
      }
    } catch (err) {
      console.error('Ошибка загрузки состояния игры:', err);
    }
  };

  const handleLetterClick = async (letter: string) => {
    if (gameOver || isLoading || guessedLetters.includes(letter)) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      telegram.hapticFeedback('light');
      const result = await hangmanGuess(sessionId, letter);

      setWord(result.word);
      setGuessedLetters(result.guessed_letters);
      setMistakes(result.mistakes);

      if (result.game_over) {
        setGameOver(true);
        setWon(result.won);
        if (result.won) {
          telegram.notifySuccess();
          setTimeout(() => {
            telegram.showPopup({
              title: '🎉 Победа!',
              message: `Отлично! Слово было: ${result.word}`,
              buttons: [{ type: 'close', text: 'Закрыть' }],
            });
          }, 500);
        } else {
          telegram.notifyError();
          setTimeout(() => {
            telegram.showPopup({
              title: '😔 Поражение',
              message: `Слово было: ${result.word}. Попробуй еще раз!`,
              buttons: [{ type: 'close', text: 'Закрыть' }],
            });
          }, 500);
        }
        onGameEnd();
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка угадывания';
      setError(errorMessage);
      telegram.notifyError();
      console.error('Ошибка угадывания:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const displayWord = () => {
    if (!word) return '';
    return word
      .split('')
      .map((char) => (guessedLetters.includes(char) ? char : '_'))
      .join(' ');
  };

  const getStatusMessage = () => {
    if (gameOver) {
      if (won) return '🎉 Ты угадал слово!';
      return '😔 Игра окончена';
    }
    if (isLoading) return 'Проверяю...';
    return `Ошибок: ${mistakes}/6`;
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
            🎯 Виселица
          </h2>
          <div className="w-10" />
        </div>

        {/* Статус */}
        <div className="text-center mb-6">
          <p className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2">
            {getStatusMessage()}
          </p>
          {error && (
            <p className="text-sm text-red-500 mt-2">{error}</p>
          )}
        </div>

        {/* Слово */}
        <div className="bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] rounded-2xl p-6 mb-6">
          <div className="text-center">
            <div className="text-4xl font-mono font-bold text-[var(--tg-theme-text-color)] mb-4">
              {displayWord()}
            </div>
            <div className="text-sm text-[var(--tg-theme-hint-color)]">
              {word && `Слово из ${word.length} букв`}
            </div>
          </div>
        </div>

        {/* Алфавит */}
        {!gameOver && (
          <div className="mb-6">
            <div className="text-sm text-[var(--tg-theme-hint-color)] mb-3 text-center">
              Выбери букву:
            </div>
            <div className="grid grid-cols-6 gap-2">
              {ALPHABET.map((letter) => {
                const isGuessed = guessedLetters.includes(letter);
                const isCorrect = word.includes(letter) && isGuessed;
                const isWrong = isGuessed && !word.includes(letter);

                return (
                  <button
                    key={letter}
                    onClick={() => handleLetterClick(letter)}
                    disabled={isGuessed || isLoading}
                    className={`
                      aspect-square rounded-lg font-bold text-lg
                      transition-all duration-200
                      ${isCorrect
                        ? 'bg-green-500 text-white'
                        : isWrong
                        ? 'bg-red-500 text-white opacity-50'
                        : 'bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] hover:opacity-80 active:scale-95'
                      }
                      disabled:opacity-50 disabled:cursor-not-allowed
                    `}
                    aria-label={`Буква ${letter}`}
                  >
                    {letter}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Инструкция */}
        {!gameOver && (
          <div className="text-center text-sm text-[var(--tg-theme-hint-color)] mb-4">
            <p>Угадай слово по буквам!</p>
            <p className="mt-1">У тебя есть 6 попыток</p>
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
