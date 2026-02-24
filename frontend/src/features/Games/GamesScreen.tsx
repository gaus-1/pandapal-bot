/**
 * Games Screen - PandaPalGo
 * Главный экран со списком игр
 */

import { useState, useEffect } from 'react';
import { telegram } from '../../services/telegram';
import { createGame, getGameStats, type GameStats, type UserProfile } from '../../services/api';
import { useAppStore } from '../../store/appStore';
import { ErrorBoundary } from '../../components/ErrorBoundary';
import { TicTacToe } from './TicTacToe';
import { Checkers } from './Checkers';
import { Game2048 } from './Game2048';
import { Erudite } from './Erudite';

interface GamesScreenProps {
  user: UserProfile;
}

type GameType = 'tic_tac_toe' | 'checkers' | '2048' | 'erudite' | null;

/** Палитры карточек: гармоничные сочетания для детского интерфейса (тёплые и холодные тона, не перегружая) */
const GAMES = [
  {
    id: 'my_panda',
    name: 'Моя панда',
    icon: '🐼',
    description: 'Тамагочи: корми, играй и укладывай панду спать!',
    color: 'from-teal-200 to-teal-100',
  },
  {
    id: 'tic_tac_toe',
    name: 'Крестики-нолики',
    icon: '❌⭕',
    description: 'Играй против панды! Кто первым соберет линию?',
    color: 'from-sky-200 to-sky-100',
  },
  {
    id: 'checkers',
    name: 'Шашки',
    icon: '⚫⚪',
    description: 'Играй против панды! Кто первым возьмет все фишки?',
    color: 'from-amber-200 to-amber-100',
  },
  {
    id: '2048',
    name: '2048',
    icon: '🔢',
    description: 'Объединяй числа и достигни 2048!',
    color: 'from-violet-200 to-violet-100',
  },
  {
    id: 'erudite',
    name: 'эрудит',
    icon: '📚',
    description: 'Составляй слова и набирай очки!',
    color: 'from-emerald-200 to-emerald-100',
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
      const sid = result?.session_id != null ? Number(result.session_id) : null;
      if (sid == null || Number.isNaN(sid)) {
        setError('Ошибка: сервер не вернул сессию');
        return;
      }
      setSessionId(sid);
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
    const gameFallback = (
      <div className="flex flex-col items-center justify-center min-h-[50vh] p-4 text-center">
        <p className="text-gray-600 dark:text-slate-400 mb-4">Игра не загрузилась. Вернись и попробуй снова.</p>
        <button
          type="button"
          onClick={handleBack}
          className="px-5 py-2.5 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium"
        >
          ← Назад к играм
        </button>
      </div>
    );
    return (
      <div className="w-full h-full bg-white dark:bg-slate-800 overflow-y-auto">
        <ErrorBoundary fallback={gameFallback}>
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
        </ErrorBoundary>
      </div>
    );
  }

  const safeStats = typeof stats === 'object' && stats !== null ? stats : {};

  return (
    <div className="w-full h-full bg-white dark:bg-slate-800 flex flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-3 xs:px-4 sm:px-4 py-4 sm:py-6">
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

        {/* Список игр — адаптивная сетка без перекрытий */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-4 w-full min-w-0">
          {GAMES.map((game) => {
            const isMyPanda = game.id === 'my_panda';
            const gameStats = isMyPanda ? undefined : safeStats[game.id];
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
                  relative p-2 rounded-lg bg-gradient-to-br ${game.color} dark:from-slate-700 dark:to-slate-800
                  text-gray-800 dark:text-slate-100 shadow-lg hover:shadow-xl dark:hover:shadow-2xl transform hover:scale-[1.02] active:scale-100
                  active:bg-gradient-to-br ${game.color} dark:active:from-slate-600 dark:active:to-slate-700 transition-all duration-200
                  disabled:opacity-50 disabled:cursor-not-allowed min-w-0
                  text-left min-h-[120px] h-[120px] flex flex-col overflow-hidden border border-blue-200/50 dark:border-slate-600/50
                `}
              >
                <div className="text-xl sm:text-2xl mb-0.5 flex-shrink-0 leading-none">{game.icon}</div>
                <h3 className="font-display text-sm font-bold mb-0.5 flex-shrink-0 leading-tight">{game.name}</h3>
                <p className="font-sans text-xs opacity-90 mb-1 overflow-hidden leading-tight" style={{
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  minHeight: '28px',
                  maxHeight: '28px'
                }}>{game.description}</p>

                {/* Статистика - всегда резервируем место */}
                <div className="mt-auto min-h-[20px] flex-shrink-0">
                  {hasStats ? (
                    <div className="pt-1.5 border-t border-blue-300/40 dark:border-slate-600/50">
                      <div className="flex justify-between text-xs leading-tight text-gray-700 dark:text-slate-200 font-medium">
                        <span>Побед: {gameStats.wins}</span>
                        <span>Игр: {gameStats.total_games}</span>
                      </div>
                      {hasBestScore ? (
                        <div className="text-[10px] sm:text-xs mt-0.5 leading-tight text-gray-700 dark:text-slate-200 font-medium">
                          Лучший счет: {gameStats.best_score}
                        </div>
                      ) : (
                        <div className="h-[10px]"></div>
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
        {Object.keys(safeStats).length > 0 && (
          <div className="mt-4 p-3 bg-gray-50 dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700">
            <h2 className="font-display text-base sm:text-lg md:text-xl font-bold text-gray-900 dark:text-slate-100 mb-2">
              📊 Твоя статистика
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {Object.values(safeStats).map((stat) => (
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
      {/* Нижняя навигация убрана: из списка игр и из самой игры возврат только по стрелке вверху */}
    </div>
  );
}
