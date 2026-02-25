/**
 * Achievements Screen - Достижения
 */

import { useState, useEffect } from 'react';
import { telegram } from '../../services/telegram';
import { getUserAchievements, type UserProfile, type Achievement } from '../../services/api';

interface AchievementsScreenProps {
  user: UserProfile;
}

export function AchievementsScreen({ user }: AchievementsScreenProps) {
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getUserAchievements(user.telegram_id)
      .then((data) => {
        setAchievements(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Ошибка загрузки достижений:', err);
        setIsLoading(false);
      });
  }, [user.telegram_id]);

  const handleAchievementClick = (achievement: Achievement) => {
    telegram.hapticFeedback('light');
    telegram.showPopup({
      title: achievement.title,
      message: achievement.description,
      buttons: [{ type: 'close', text: 'Закрыть' }],
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div>
      </div>
    );
  }

  const unlockedCount = achievements.filter((a) => a.unlocked).length;
  const totalCount = achievements.length;

  return (
    <div className="w-full h-full bg-white dark:bg-slate-800 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-fib-2 fold:px-fib-3 xs:px-fib-4 sm:px-fib-5 md:px-fib-5 py-fib-4 sm:py-fib-5 md:py-fib-6 pb-20 sm:pb-24">
        {/* Заголовок */}
        <div className="mb-fib-4 sm:mb-fib-5 md:mb-fib-6">
          <div className="flex items-center gap-fib-2 sm:gap-fib-3 mb-fib-2 sm:mb-fib-3">
            <span className="text-3xl sm:text-4xl md:text-5xl">🏆</span>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-display font-bold text-gray-900 dark:text-slate-100">
              Достижения
            </h1>
          </div>
          <p className="text-sm sm:text-base md:text-lg text-gray-600 dark:text-slate-400 mb-fib-3 sm:mb-fib-4">
            Получено {unlockedCount} из {totalCount}
          </p>

          {/* Progress bar */}
          <div className="w-full h-3 sm:h-4 md:h-5 bg-[var(--tg-theme-hint-color)]/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-[var(--tg-theme-button-color)] transition-all duration-500 rounded-full"
              style={{ width: `${totalCount > 0 ? (unlockedCount / totalCount) * 100 : 0}%` }}
            />
          </div>
        </div>

        {/* Список достижений */}
        {achievements.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-fib-3 sm:gap-fib-4 md:gap-fib-5">
            {achievements.map((achievement) => (
              <button
                key={achievement.id}
                onClick={() => handleAchievementClick(achievement)}
                className={`flex flex-col items-center justify-center p-fib-3 sm:p-fib-4 md:p-fib-5 rounded-xl sm:rounded-2xl transition-all min-h-[100px] fold:min-h-[120px] sm:min-h-[140px] md:min-h-[160px] border ${
                  achievement.unlocked
                    ? 'bg-blue-500/20 dark:bg-blue-500/30 hover:bg-blue-500/30 dark:hover:bg-blue-500/40 active:bg-blue-500/40 dark:active:bg-blue-500/50 active:scale-95 border-blue-500/30 dark:border-blue-500/50'
                    : 'bg-gray-50 dark:bg-slate-800 opacity-60 border-gray-200 dark:border-slate-700 hover:bg-gray-100 dark:hover:bg-slate-700 active:bg-gray-200 dark:active:bg-slate-600'
                }`}
              >
                <div className={`text-4xl sm:text-5xl md:text-6xl mb-2 sm:mb-3 ${!achievement.unlocked ? 'grayscale opacity-50' : ''}`}>
                  {achievement.icon}
                </div>
                <div className="font-display text-xs sm:text-sm md:text-base font-semibold text-gray-900 dark:text-slate-100 mb-1 text-center leading-tight">
                  {achievement.title}
                </div>
                {achievement.unlocked && achievement.unlock_date && (
                  <div className="text-xs text-gray-600 dark:text-slate-400">
                    {new Date(achievement.unlock_date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
                  </div>
                )}
                {!achievement.unlocked && (
                  <div className="text-xs text-gray-600 dark:text-slate-400 flex items-center gap-1">
                    <span>🔒</span>
                    <span>Заблокировано</span>
                  </div>
                )}
              </button>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 sm:py-16">
            <div className="text-6xl sm:text-7xl mb-4 sm:mb-6">🏆</div>
            <p className="text-base sm:text-lg text-gray-600 dark:text-slate-400">
              Продолжай учиться, чтобы получать достижения!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
