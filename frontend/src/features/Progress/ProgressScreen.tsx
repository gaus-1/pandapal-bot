/**
 * Progress Screen - Мой прогресс
 */

import { useState, useEffect } from 'react';
import { getUserProgress, getDashboardStats, type UserProfile, type ProgressItem, type DashboardStats } from '../../services/api';

interface ProgressScreenProps {
  user: UserProfile;
}

export function ProgressScreen({ user }: ProgressScreenProps) {
  const [progress, setProgress] = useState<ProgressItem[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getUserProgress(user.telegram_id),
      getDashboardStats(user.telegram_id),
    ])
      .then(([progressData, statsData]) => {
        setProgress(progressData);
        setStats(statsData);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Ошибка загрузки прогресса:', err);
        setIsLoading(false);
      });
  }, [user.telegram_id]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4">
      {/* Заголовок */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-2">
          📊 Мой прогресс
        </h1>
        <p className="text-[var(--tg-theme-hint-color)]">
          Твои успехи в обучении
        </p>
      </div>

      {/* Общая статистика */}
      {stats && (
        <div className="grid grid-cols-2 gap-3 mb-6">
          <StatCard icon="💬" label="Сообщений" value={stats.total_messages} />
          <StatCard icon="📚" label="Уроков" value={stats.learning_sessions} />
          <StatCard icon="⭐" label="Очков" value={stats.total_points} />
          <StatCard icon="🔥" label="Дней подряд" value={stats.current_streak} />
        </div>
      )}

      {/* Прогресс по предметам */}
      <h2 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-3">
        Прогресс по предметам
      </h2>

      {progress.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-6xl mb-4">📖</div>
          <p className="text-[var(--tg-theme-hint-color)]">
            Начни изучать предметы, чтобы увидеть прогресс!
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {progress.map((item) => (
            <div
              key={item.subject}
              className="p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-[var(--tg-theme-text-color)]">
                  {item.subject}
                </h3>
                <span className="text-sm text-[var(--tg-theme-hint-color)]">
                  Уровень {item.level}
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full h-3 bg-[var(--tg-theme-hint-color)]/20 rounded-full overflow-hidden mb-2">
                <div
                  className="h-full bg-[var(--tg-theme-button-color)] transition-all duration-500"
                  style={{ width: `${Math.min((item.points / 1000) * 100, 100)}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-xs text-[var(--tg-theme-hint-color)]">
                <span>{item.points} очков</span>
                <span>
                  {new Date(item.last_activity).toLocaleDateString('ru-RU')}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface StatCardProps {
  icon: string;
  label: string;
  value: number;
}

function StatCard({ icon, label, value }: StatCardProps) {
  return (
    <div className="p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl text-center">
      <div className="text-3xl mb-1">{icon}</div>
      <div className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-1">
        {value}
      </div>
      <div className="text-xs text-[var(--tg-theme-hint-color)]">{label}</div>
    </div>
  );
}
