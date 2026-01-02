/**
 * Parent Dashboard - Дашборд для родителей с графиками прогресса
 */

import { useEffect, useState } from 'react';
import { telegram } from '../../services/telegram';
import type { UserProfile } from '../../services/api';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ParentDashboardProps {
  user: UserProfile;
}

interface ChildProgress {
  child_id: number;
  child_name: string;
  total_messages: number;
  learning_sessions: number;
  total_points: number;
  subjects_studied: number;
  current_streak: number;
  weekly_activity: Array<{ day: string; messages: number; sessions: number }>;
  subjects_progress: Array<{ subject: string; points: number; level: number }>;
  safety_score: number;
  last_active: string;
}

export function ParentDashboard({ user }: ParentDashboardProps) {
  const [children, setChildren] = useState<ChildProgress[]>([]);
  const [selectedChild, setSelectedChild] = useState<ChildProgress | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadChildrenData();
  }, [user.telegram_id]);

  const loadChildrenData = async () => {
    try {
      // Загружаем данные детей
      const response = await fetch(`/api/miniapp/parent/children/${user.telegram_id}`);
      const data = await response.json();

      if (data.success) {
        setChildren(data.children);
        if (data.children.length > 0) {
          setSelectedChild(data.children[0]);
        }
      }
      setIsLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки данных детей:', error);
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div>
      </div>
    );
  }

  if (children.length === 0) {
    return (
      <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4">
        <h1 className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-4">
          👨‍👩‍👧 Родительский дашборд
        </h1>
        <div className="text-center py-8">
          <div className="text-6xl mb-4">👶</div>
          <p className="text-[var(--tg-theme-hint-color)]">
            Нет связанных детских аккаунтов
          </p>
          <button
            onClick={() => telegram.showAlert('Свяжите аккаунт ребенка в настройках')}
            className="mt-4 px-6 py-3 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl"
          >
            Связать ребенка
          </button>
        </div>
      </div>
    );
  }

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4 pb-24">
      {/* Заголовок */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-2">
          👨‍👩‍👧 Родительский дашборд
        </h1>
        <p className="text-[var(--tg-theme-hint-color)]">
          Прогресс и безопасность ваших детей
        </p>
      </div>

      {/* Выбор ребенка */}
      {children.length > 1 && (
        <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
          {children.map((child) => (
            <button
              key={child.child_id}
              onClick={() => {
                setSelectedChild(child);
                telegram.hapticFeedback('light');
              }}
              className={`px-4 py-2 rounded-xl whitespace-nowrap transition-all ${
                selectedChild?.child_id === child.child_id
                  ? 'bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)]'
                  : 'bg-[var(--tg-theme-hint-color)]/10 text-[var(--tg-theme-text-color)]'
              }`}
            >
              {child.child_name}
            </button>
          ))}
        </div>
      )}

      {selectedChild && (
        <>
          {/* Общая статистика */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            <StatCard icon="💬" label="Сообщений" value={selectedChild.total_messages} />
            <StatCard icon="📚" label="Уроков" value={selectedChild.learning_sessions} />
            <StatCard icon="⭐" label="Очков" value={selectedChild.total_points} />
            <StatCard icon="🔥" label="Дней подряд" value={selectedChild.current_streak} />
          </div>

          {/* Безопасность */}
          <div className="mb-6 p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl">
            <h2 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-3 flex items-center gap-2">
              <span>🛡️</span>
              <span>Безопасность</span>
            </h2>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <div className="w-full h-3 bg-[var(--tg-theme-hint-color)]/20 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      selectedChild.safety_score >= 90
                        ? 'bg-green-500'
                        : selectedChild.safety_score >= 70
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${selectedChild.safety_score}%` }}
                  />
                </div>
              </div>
              <div className="text-2xl font-bold text-[var(--tg-theme-text-color)]">
                {selectedChild.safety_score}%
              </div>
            </div>
            <p className="text-sm text-[var(--tg-theme-hint-color)] mt-2">
              {selectedChild.safety_score >= 90
                ? '✅ Отличная безопасность'
                : selectedChild.safety_score >= 70
                ? '⚠️ Требуется внимание'
                : '🚨 Обнаружены проблемы'}
            </p>
          </div>

          {/* График активности за неделю */}
          <div className="mb-6 p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl">
            <h2 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-3">
              📊 Активность за неделю
            </h2>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={selectedChild.weekly_activity}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.1)" />
                <XAxis dataKey="day" stroke="var(--tg-theme-hint-color)" />
                <YAxis stroke="var(--tg-theme-hint-color)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--tg-theme-bg-color)',
                    border: '1px solid var(--tg-theme-hint-color)',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="messages"
                  stroke="#8884d8"
                  strokeWidth={2}
                  name="Сообщения"
                />
                <Line
                  type="monotone"
                  dataKey="sessions"
                  stroke="#82ca9d"
                  strokeWidth={2}
                  name="Уроки"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* График прогресса по предметам */}
          <div className="mb-6 p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl">
            <h2 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-3">
              📚 Прогресс по предметам
            </h2>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={selectedChild.subjects_progress}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.1)" />
                <XAxis dataKey="subject" stroke="var(--tg-theme-hint-color)" />
                <YAxis stroke="var(--tg-theme-hint-color)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--tg-theme-bg-color)',
                    border: '1px solid var(--tg-theme-hint-color)',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Bar dataKey="points" fill="#8884d8" name="Очки" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Распределение активности */}
          <div className="mb-6 p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl">
            <h2 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-3">
              🥧 Распределение по предметам
            </h2>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={selectedChild.subjects_progress}
                  dataKey="points"
                  nameKey="subject"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {selectedChild.subjects_progress.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Последняя активность */}
          <div className="p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl">
            <h2 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2">
              ⏰ Последняя активность
            </h2>
            <p className="text-[var(--tg-theme-hint-color)]">
              {new Date(selectedChild.last_active).toLocaleString('ru-RU')}
            </p>
          </div>
        </>
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
      <div className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-1">{value}</div>
      <div className="text-xs text-[var(--tg-theme-hint-color)]">{label}</div>
    </div>
  );
}
