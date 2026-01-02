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
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4">
      {/* Заголовок */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-2">
          🏆 Достижения
        </h1>
        <p className="text-[var(--tg-theme-hint-color)]">
          Получено {unlockedCount} из {totalCount}
        </p>

        {/* Progress bar */}
        <div className="w-full h-3 bg-[var(--tg-theme-hint-color)]/20 rounded-full overflow-hidden mt-3">
          <div
            className="h-full bg-[var(--tg-theme-button-color)] transition-all duration-500"
            style={{ width: `${(unlockedCount / totalCount) * 100}%` }}
          />
        </div>
      </div>

      {/* Список достижений */}
      <div className="grid grid-cols-2 gap-3">
        {achievements.map((achievement) => (
          <button
            key={achievement.id}
            onClick={() => handleAchievementClick(achievement)}
            className={`p-4 rounded-2xl transition-all ${
              achievement.unlocked
                ? 'bg-[var(--tg-theme-button-color)]/20 active:scale-95'
                : 'bg-[var(--tg-theme-hint-color)]/10 opacity-50'
            }`}
          >
            <div className={`text-5xl mb-2 ${!achievement.unlocked ? 'grayscale' : ''}`}>
              {achievement.icon}
            </div>
            <div className="text-sm font-semibold text-[var(--tg-theme-text-color)] mb-1">
              {achievement.title}
            </div>
            {achievement.unlocked && achievement.unlock_date && (
              <div className="text-xs text-[var(--tg-theme-hint-color)]">
                {new Date(achievement.unlock_date).toLocaleDateString('ru-RU')}
              </div>
            )}
            {!achievement.unlocked && (
              <div className="text-xs text-[var(--tg-theme-hint-color)]">🔒 Заблокировано</div>
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
