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
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4 sm:p-6 md:p-8 max-w-4xl mx-auto">
      {/* Заголовок */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-[var(--tg-theme-text-color)] mb-2 sm:mb-3">
          🏆 Достижения
        </h1>
        <p className="text-sm sm:text-base md:text-lg text-[var(--tg-theme-hint-color)]">
          Получено {unlockedCount} из {totalCount}
        </p>

        {/* Progress bar */}
        <div className="w-full h-3 sm:h-4 md:h-5 bg-[var(--tg-theme-hint-color)]/20 rounded-full overflow-hidden mt-3 sm:mt-4">
          <div
            className="h-full bg-[var(--tg-theme-button-color)] transition-all duration-500"
            style={{ width: `${(unlockedCount / totalCount) * 100}%` }}
          />
        </div>
      </div>

      {/* Список достижений */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 sm:gap-4 md:gap-5">
        {achievements.map((achievement) => (
          <button
            key={achievement.id}
            onClick={() => handleAchievementClick(achievement)}
            className={`p-4 sm:p-5 md:p-6 rounded-2xl sm:rounded-3xl transition-all ${
              achievement.unlocked
                ? 'bg-[var(--tg-theme-button-color)]/20 active:scale-95'
                : 'bg-[var(--tg-theme-hint-color)]/10 opacity-50'
            }`}
          >
            <div className={`text-5xl sm:text-6xl md:text-7xl mb-2 sm:mb-3 ${!achievement.unlocked ? 'grayscale' : ''}`}>
              {achievement.icon}
            </div>
            <div className="text-sm sm:text-base md:text-lg font-semibold text-[var(--tg-theme-text-color)] mb-1 sm:mb-2">
              {achievement.title}
            </div>
            {achievement.unlocked && achievement.unlock_date && (
              <div className="text-xs sm:text-sm md:text-base text-[var(--tg-theme-hint-color)]">
                {new Date(achievement.unlock_date).toLocaleDateString('ru-RU')}
              </div>
            )}
            {!achievement.unlocked && (
              <div className="text-xs sm:text-sm md:text-base text-[var(--tg-theme-hint-color)]">🔒 Заблокировано</div>
            )}
          </button>
        ))}
      </div>

      {achievements.length === 0 && (
        <div className="text-center py-8">
          <div className="text-6xl mb-4">🏆</div>
          <p className="text-[var(--tg-theme-hint-color)]">
            Продолжай учиться, чтобы получать достижения!
          </p>
        </div>
      )}
    </div>
  );
}
