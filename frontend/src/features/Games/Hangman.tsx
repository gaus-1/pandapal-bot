/**
 * Hangman Game Component
 * Виселица - угадывание слова
 */

import { useState, useEffect } from "react";
import { telegram } from "../../services/telegram";
import {
  hangmanGuess,
  getGameSession,
  type UserProfile,
} from "../../services/api";

interface HangmanProps {
  sessionId: number;
  user: UserProfile;
  onBack: () => void;
  onGameEnd: () => void;
}

const ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ".split("");

export function Hangman({ sessionId, onBack, onGameEnd }: HangmanProps) {
  const [word, setWord] = useState<string>("");
  const [guessedLetters, setGuessedLetters] = useState<string[]>([]);
  const [mistakes, setMistakes] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [won, setWon] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastGuessedLetter, setLastGuessedLetter] = useState<string | null>(
    null,
  );

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

      if (session.result && session.result !== "in_progress") {
        setGameOver(true);
        setWon(session.result === "win");
      }
    } catch (err) {
      console.error("Ошибка загрузки состояния игры:", err);
    }
  };

  const handleLetterClick = async (letter: string) => {
    if (gameOver || isLoading || guessedLetters.includes(letter)) {
      return;
    }

    setIsLoading(true);
    setError(null);
    setLastGuessedLetter(letter);

    try {
      telegram.hapticFeedback("light");
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
            telegram
              .showPopup({
                title: "🎉 Победа!",
                message: `Отлично! Слово было: ${result.word}`,
                buttons: [
                  { type: "default", text: "Поделиться", id: "share" },
                  { type: "close", text: "Закрыть" },
                ],
              })
              .then((buttonId) => {
                if (buttonId === "share") {
                  telegram.shareGameResult("Виселица", "win");
                }
              });
          }, 500);
        } else {
          telegram.notifyError();
          setTimeout(() => {
            telegram.showPopup({
              title: "😔 Поражение",
              message: `Слово было: ${result.word}. Попробуй еще раз!`,
              buttons: [{ type: "close", text: "Закрыть" }],
            });
          }, 500);
        }
        onGameEnd();
      } else {
        // Вибрация в зависимости от результата
        if (result.word.toUpperCase().includes(letter)) {
          telegram.hapticFeedback("light");
        } else {
          telegram.hapticFeedback("medium");
        }
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Ошибка угадывания";
      setError(errorMessage);
      telegram.notifyError();
      console.error("Ошибка угадывания:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const displayWord = () => {
    if (!word) return "";
    return word
      .split("")
      .map((char) => (guessedLetters.includes(char.toUpperCase()) ? char : "_"))
      .join(" ");
  };

  const getStatusMessage = () => {
    if (gameOver) {
      if (won) return "🎉 Ты угадал слово!";
      return "😔 Игра окончена";
    }
    if (isLoading) return "Проверяю...";
    return `Ошибок: ${mistakes}/6`;
  };

  const renderHangman = () => {
    const parts = [
      "head",
      "body",
      "rightArm",
      "leftArm",
      "rightLeg",
      "leftLeg",
    ];
    const visibleParts = parts.slice(0, mistakes);

    return (
      <div className="relative w-24 h-32 sm:w-32 sm:h-40 mx-auto mb-4">
        <svg viewBox="0 0 100 120" className="w-full h-full">
          <line
            x1="10"
            y1="110"
            x2="40"
            y2="110"
            stroke="currentColor"
            strokeWidth="2"
          />
          <line
            x1="25"
            y1="110"
            x2="25"
            y2="20"
            stroke="currentColor"
            strokeWidth="2"
          />
          <line
            x1="25"
            y1="20"
            x2="60"
            y2="20"
            stroke="currentColor"
            strokeWidth="2"
          />
          <line
            x1="60"
            y1="20"
            x2="60"
            y2="35"
            stroke="currentColor"
            strokeWidth="2"
          />

          {visibleParts.includes("head") && (
            <circle
              cx="60"
              cy="45"
              r="10"
              stroke="currentColor"
              strokeWidth="2"
              fill="none"
              style={{ animation: "fadeIn 0.3s ease-out" }}
            />
          )}

          {visibleParts.includes("body") && (
            <line
              x1="60"
              y1="55"
              x2="60"
              y2="85"
              stroke="currentColor"
              strokeWidth="2"
              style={{ animation: "fadeIn 0.3s ease-out" }}
            />
          )}

          {visibleParts.includes("rightArm") && (
            <line
              x1="60"
              y1="65"
              x2="75"
              y2="70"
              stroke="currentColor"
              strokeWidth="2"
              style={{ animation: "fadeIn 0.3s ease-out" }}
            />
          )}

          {visibleParts.includes("leftArm") && (
            <line
              x1="60"
              y1="65"
              x2="45"
              y2="70"
              stroke="currentColor"
              strokeWidth="2"
              style={{ animation: "fadeIn 0.3s ease-out" }}
            />
          )}

          {visibleParts.includes("rightLeg") && (
            <line
              x1="60"
              y1="85"
              x2="75"
              y2="100"
              stroke="currentColor"
              strokeWidth="2"
              style={{ animation: "fadeIn 0.3s ease-out" }}
            />
          )}

          {visibleParts.includes("leftLeg") && (
            <line
              x1="60"
              y1="85"
              x2="45"
              y2="100"
              stroke="currentColor"
              strokeWidth="2"
              style={{ animation: "fadeIn 0.3s ease-out" }}
            />
          )}
        </svg>
      </div>
    );
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
            🎯 Виселица
          </h2>
          <div className="w-10 sm:w-12" />
        </div>

        {/* Статус */}
        <div className="text-center mb-4 sm:mb-6">
          <p className="text-base sm:text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2">
            {getStatusMessage()}
          </p>
          {error && (
            <p className="text-xs sm:text-sm text-red-500 mt-2">{error}</p>
          )}
        </div>

        {/* Виселица */}
        <div className="bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] rounded-xl sm:rounded-2xl p-4 sm:p-6 mb-4 sm:mb-6">
          <div className="text-center text-[var(--tg-theme-text-color)]">
            {renderHangman()}
          </div>
        </div>

        {/* Слово */}
        <div className="bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] rounded-xl sm:rounded-2xl p-4 sm:p-6 mb-4 sm:mb-6">
          <div className="text-center">
            <div className="text-2xl sm:text-4xl font-mono font-bold text-[var(--tg-theme-text-color)] mb-2 sm:mb-4 break-all">
              {displayWord()}
            </div>
            <div className="text-xs sm:text-sm text-[var(--tg-theme-hint-color)]">
              {word && `Слово из ${word.length} букв`}
            </div>
          </div>
        </div>

        {/* Алфавит */}
        {!gameOver && (
          <div className="mb-4 sm:mb-6">
            <div className="text-xs sm:text-sm text-[var(--tg-theme-hint-color)] mb-2 sm:mb-3 text-center">
              Выбери букву:
            </div>
            <div className="grid grid-cols-6 sm:grid-cols-6 gap-1.5 sm:gap-2">
              {ALPHABET.map((letter) => {
                const isGuessed = guessedLetters.includes(letter);
                const isCorrect =
                  word.toUpperCase().includes(letter) && isGuessed;
                const isWrong =
                  isGuessed && !word.toUpperCase().includes(letter);
                const isLastGuessed = lastGuessedLetter === letter;

                return (
                  <button
                    key={letter}
                    onClick={() => handleLetterClick(letter)}
                    disabled={isGuessed || isLoading}
                    className={`
                      aspect-square rounded-lg font-bold text-sm sm:text-lg
                      transition-all duration-300 touch-manipulation
                      min-h-[44px] sm:min-h-[44px] min-w-[44px] sm:min-w-[44px]
                      ${
                        isCorrect
                          ? "bg-green-500 text-white"
                          : isWrong
                            ? "bg-red-500 text-white opacity-50"
                            : "bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] hover:opacity-80 active:scale-95"
                      }
                      ${
                        isLastGuessed
                          ? "ring-2 ring-blue-400 ring-opacity-75"
                          : ""
                      }
                      disabled:opacity-50 disabled:cursor-not-allowed
                    `}
                    style={{
                      animation: isLastGuessed
                        ? "fadeInScale 0.3s ease-out"
                        : undefined,
                    }}
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
          <div className="text-center text-xs sm:text-sm text-[var(--tg-theme-hint-color)] mb-4">
            <p>Угадай слово по буквам!</p>
            <p className="mt-1">У тебя есть 6 попыток</p>
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

      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
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
