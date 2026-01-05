/**
 * Games Screen - PandaPalGo
 * Главный экран со списком игр
 */

import { useState, useEffect } from 'react';
import { telegram } from '../../services/telegram';
import { createGame, getGameStats, type GameStats, type UserProfile } from '../../services/api';
import { TicTacToe } from './TicTacToe';
import { Checkers } from './Checkers';
import { Game2048 } from './Game2048';

interface GamesScreenProps {
  user: UserProfile;
}

type GameType = 'tic_tac_toe' | 'checkers' | '2048' | null;

const GAMES = [
  {
    id: 'tic_tac_toe',
    name: 'Крестики-нолики',
    icon: '❌⭕',
    description: 'Играй против панды! Кто первым соберет линию?',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    id: 'checkers',
    name: 'Шашки',
    icon: '⚫⚪',
    description: 'Играй против панды! Кто первым возьмет все фишки?',
    color: 'from-purple-500 to-pink-500',
  },
  {
    id: '2048',
    name: '2048',
    icon: '🔢',
    description: 'Объединяй числа и достигни 2048!',
    color: 'from-orange-500 to-red-500',
  },
] as const;

export function GamesScreen({ user }: GamesScreenProps) {
  const [selectedGame, setSelectedGame] = useState<GameType>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<Record<string, GameStats>>({});

  useEffect(() => {
    loadStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.telegram_id]);

  const loadStats = async () => {
    try {
      const allStats = await getGameStats(user.telegram_id);
      if (typeof allStats === 'object' && !Array.isArray(allStats) && allStats !== null) {
        // Проверяем, что это Record<string, GameStats>, а не просто GameStats
        const statsRecord = allStats as Record<string, GameStats>;
        setStats(statsRecord);
      }
    } catch (err) {
      console.error('Ошибка загрузки статистики:', err);
    }
  };

  const handleStartGame = async (gameType: string) => {
    setIsLoading(true);
    setError(null);

    try {
      telegram.hapticFeedback('light');
      const result = await createGame(user.telegram_id, gameType);
      setSessionId(result.session_id);
      setSelectedGame(gameType as GameType);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка создания игры';
      setError(errorMessage);
      telegram.notifyError();
      console.error('Ошибка создания игры:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    telegram.hapticFeedback('light');
    setSelectedGame(null);
    setSessionId(null);
    setError(null);
    loadStats(); // Обновляем статистику после игры
  };

  const handleGameEnd = () => {
    loadStats(); // Обновляем статистику
  };

  if (selectedGame && sessionId) {
    return (
      <div className="w-full h-full bg-[var(--tg-theme-bg-color)] overflow-y-auto">
        {selectedGame === 'tic_tac_toe' && (
          <TicTacToe
            sessionId={sessionId}
            user={user}
            onBack={handleBack}
            onGameEnd={handleGameEnd}
          />
        )}
        {selectedGame === 'checkers' && (
          <Checkers
            sessionId={sessionId}
            user={user}
            onBack={handleBack}
            onGameEnd={handleGameEnd}
          />
        )}
        {selectedGame === '2048' && (
          <Game2048
            sessionId={sessionId}
            user={user}
            onBack={handleBack}
            onGameEnd={handleGameEnd}
          />
        )}
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-[var(--tg-theme-bg-color)] overflow-y-auto">
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Заголовок */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-[var(--tg-theme-text-color)] mb-2">
            🎮 PandaPalGo
          </h1>
          <p className="text-[var(--tg-theme-hint-color)]">
            Играй с пандой и зарабатывай достижения!
          </p>
        </div>

        {/* Ошибка */}
        {error && (
          <div className="mb-3 p-3 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-800 rounded-lg">
            <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
          </div>
        )}

        {/* Список игр */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
          {GAMES.map((game) => {
            const gameStats = stats[game.id];
            return (
              <button
                key={game.id}
                onClick={() => handleStartGame(game.id)}
                disabled={isLoading}
                className={`
                  relative p-2.5 rounded-lg bg-gradient-to-br ${game.color}
                  text-white shadow-lg hover:shadow-xl transform hover:scale-105
                  active:scale-100 transition-all duration-200
                  disabled:opacity-50 disabled:cursor-not-allowed
                  text-left min-h-[120px] flex flex-col
                `}
              >
                <div className="text-3xl mb-1.5">{game.icon}</div>
                <h3 className="text-base font-bold mb-1">{game.name}</h3>
                <p className="text-xs opacity-90 mb-2 flex-grow">{game.description}</p>

                {/* Статистика */}
                {gameStats && gameStats.total_games > 0 && (
                  <div className="mt-2 pt-2 border-t border-white/20">
                    <div className="flex justify-between text-xs">
                      <span>Побед: {gameStats.wins}</span>
                      <span>Игр: {gameStats.total_games}</span>
                    </div>
                    {game.id === '2048' && gameStats.best_score && (
                      <div className="text-xs mt-0.5">
                        Лучший счет: {gameStats.best_score}
                      </div>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Общая статистика */}
        {Object.keys(stats).length > 0 && (
          <div className="mt-6 p-4 bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] rounded-xl border border-[var(--tg-theme-hint-color)]/20">
            <h2 className="text-xl font-bold text-[var(--tg-theme-text-color)] mb-3">
              📊 Твоя статистика
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {Object.values(stats).map((stat) => (
                <div
                  key={stat.game_type}
                  className="p-3 bg-[var(--tg-theme-bg-color)] rounded-lg"
                >
                  <div className="text-sm text-[var(--tg-theme-hint-color)] mb-1">
                    {stat.game_type === 'tic_tac_toe' && '❌⭕ Крестики-нолики'}
                    {stat.game_type === 'checkers' && '⚫⚪ Шашки'}
                    {stat.game_type === '2048' && '🔢 2048'}
                  </div>
                  <div className="text-lg font-bold text-[var(--tg-theme-text-color)]">
                    {stat.wins} побед
                  </div>
                  <div className="text-xs text-[var(--tg-theme-hint-color)]">
                    {stat.total_games} игр • {stat.win_rate}% побед
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
