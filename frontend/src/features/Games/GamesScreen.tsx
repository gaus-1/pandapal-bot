/**
 * Games Screen - PandaPalGo
 * Главный экран со списком игр
 */

import { useState, useEffect } from 'react';
import { telegram } from '../../services/telegram';
import { createGame, getGameStats, type GameStats, type UserProfile } from '../../services/api';
import { useAppStore } from '../../store/appStore';
import { TicTacToe } from './TicTacToe';
import { Checkers } from './Checkers';
import { Game2048 } from './Game2048';
import { Erudite } from './Erudite';

interface GamesScreenProps {
  user: UserProfile;
}

type GameType = 'tic_tac_toe' | 'checkers' | '2048' | 'erudite' | null;

const GAMES = [
  {
    id: 'tic_tac_toe',
    name: 'Крестики-нолики',
    icon: '❌⭕',
    description: 'Играй против панды! Кто первым соберет линию?',
    color: 'from-blue-200 to-blue-100',
  },
  {
    id: 'checkers',
    name: 'Шашки',
    icon: '⚫⚪',
    description: 'Играй против панды! Кто первым возьмет все фишки?',
    color: 'from-blue-200 to-blue-100',
  },
  {
    id: '2048',
    name: '2048',
    icon: '🔢',
    description: 'Объединяй числа и достигни 2048!',
    color: 'from-blue-200 to-blue-100',
  },
  {
    id: 'erudite',
    name: 'эрудит',
    icon: '📚',
    description: 'Составляй слова и набирай очки!',
    color: 'from-blue-200 to-blue-100',
  },
  {
    id: 'my_panda',
    name: 'Моя панда',
    icon: '🐼',
    description: 'Тамагочи: корми, играй и укладывай панду спать!',
    color: 'from-blue-200 to-blue-100',
  },
] as const;

export function GamesScreen({ user }: GamesScreenProps) {
  const { setCurrentScreen } = useAppStore();
  const [selectedGame, setSelectedGame] = useState<GameType>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<Record<string, GameStats>>({});

  useEffect(() => {
    if (user.telegram_id !== 0) {
      loadStats();
    }
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
      <div className="w-full h-full bg-white dark:bg-slate-800 overflow-y-auto">
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
        {selectedGame === 'erudite' && (
          <Erudite
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
    <div className="w-full h-full bg-white dark:bg-slate-800 flex flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Заголовок */}
        <div className="text-center mb-3">
          <h1 className="font-display text-xl sm:text-2xl md:text-3xl font-bold text-gray-900 dark:text-slate-100 mb-1">
            🎮 PandaPalGo
          </h1>
          <p className="font-sans text-xs sm:text-sm md:text-base text-gray-600 dark:text-slate-400 leading-tight">
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
            const isMyPanda = game.id === 'my_panda';
            const gameStats = isMyPanda ? undefined : stats[game.id];
            const hasStats = gameStats && gameStats.total_games > 0;
            const hasBestScore = game.id === '2048' && gameStats?.best_score;
            return (
              <button
                key={game.id}
                onClick={() => {
                  if (isMyPanda) {
                    telegram.hapticFeedback('light');
                    setCurrentScreen('my-panda');
                  } else {
                    handleStartGame(game.id);
                  }
                }}
                disabled={isLoading && !isMyPanda}
                className={`
                  relative p-2.5 rounded-lg bg-gradient-to-br ${game.color} dark:from-slate-700 dark:to-slate-800
                  text-gray-800 dark:text-slate-100 shadow-lg hover:shadow-xl dark:hover:shadow-2xl transform hover:scale-105
                  active:scale-100 active:bg-gradient-to-br ${game.color} dark:active:from-slate-600 dark:active:to-slate-700 transition-all duration-200
                  disabled:opacity-50 disabled:cursor-not-allowed
                  text-left h-[150px] flex flex-col overflow-hidden border border-blue-200/50 dark:border-slate-600/50
                `}
              >
                <div className="text-2xl sm:text-3xl mb-1.5 flex-shrink-0 leading-none">{game.icon}</div>
                <h3 className="font-display text-sm sm:text-base font-bold mb-1 flex-shrink-0 leading-tight">{game.name}</h3>
                <p className="font-sans text-xs sm:text-sm opacity-90 mb-2 overflow-hidden leading-tight" style={{
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  minHeight: '40px',
                  maxHeight: '40px'
                }}>{game.description}</p>

                {/* Статистика - всегда резервируем место */}
                <div className="mt-auto min-h-[34px] flex-shrink-0">
                  {hasStats ? (
                    <div className="pt-2 border-t border-blue-300/40 dark:border-slate-600/50">
                      <div className="flex justify-between text-xs leading-tight text-gray-700 dark:text-slate-200 font-medium">
                        <span>Побед: {gameStats.wins}</span>
                        <span>Игр: {gameStats.total_games}</span>
                      </div>
                      {hasBestScore ? (
                        <div className="text-xs mt-0.5 leading-tight text-gray-700 dark:text-slate-200 font-medium">
                          Лучший счет: {gameStats.best_score}
                        </div>
                      ) : (
                        <div className="h-[14px]"></div>
                      )}
                    </div>
                  ) : (
                    <div></div>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Общая статистика */}
        {Object.keys(stats).length > 0 && (
          <div className="mt-4 p-3 bg-gray-50 dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700">
            <h2 className="font-display text-base sm:text-lg md:text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">
              📊 Твоя статистика
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {Object.values(stats).map((stat) => (
                <div
                  key={stat.game_type}
                  className="p-2 bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700"
                >
                  <div className="text-xs sm:text-sm text-gray-600 dark:text-slate-400 mb-1">
                    {stat.game_type === 'tic_tac_toe' && '❌⭕ Крестики-нолики'}
                    {stat.game_type === 'checkers' && '⚫⚪ Шашки'}
                    {stat.game_type === '2048' && '🔢 2048'}
                    {stat.game_type === 'erudite' && '📚 эрудит'}
                  </div>
                  <div className="text-sm sm:text-base font-bold text-gray-900 dark:text-slate-100">
                    {stat.wins} побед
                  </div>
                  <div className="text-xs sm:text-sm text-gray-600 dark:text-slate-400">
                    {stat.total_games} игр • {stat.win_rate}% побед
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        </div>
      </div>

      {/* Нижняя навигация */}
      <nav className="flex-shrink-0 bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 shadow-lg safe-area-inset-bottom">
        <div className="flex gap-1.5 sm:gap-2 md:gap-3 px-1.5 sm:px-2 md:px-3 py-2 sm:py-2.5 md:py-3 max-w-full overflow-x-auto">
          <button
            onClick={() => {
              telegram.hapticFeedback('light');
              setCurrentScreen('ai-chat');
            }}
            className="flex-1 flex flex-col items-center justify-center gap-1 p-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 active:bg-gray-200 dark:active:bg-slate-600 transition-colors touch-manipulation min-h-[60px] border border-gray-200 dark:border-slate-700"
          >
            <span className="text-2xl">💬</span>
            <span className="text-xs font-medium text-gray-900 dark:text-slate-100">Чат</span>
          </button>
          <button
            onClick={() => {
              telegram.hapticFeedback('light');
              setCurrentScreen('premium');
            }}
            className="flex-1 flex flex-col items-center justify-center gap-1 p-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 active:bg-gray-200 dark:active:bg-slate-600 transition-colors touch-manipulation min-h-[60px] border border-gray-200 dark:border-slate-700"
          >
            <span className="text-2xl">👑</span>
            <span className="text-xs font-medium text-gray-900 dark:text-slate-100">Premium</span>
          </button>
        </div>
      </nav>
    </div>
  );
}
