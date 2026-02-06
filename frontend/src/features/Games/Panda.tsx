/**
 * Моя панда — экран питомца-тамагочи.
 * Панда по центру, шкалы справа, кнопки внизу. Светлая/тёмная тема, адаптив.
 *
 * Картинки: только 15 состояний тамагочи из папки panda-tamagotchi/ (panda-{state}.png).
 * Реакции *-in-game.png не подгружаются — они только для PandaReaction в других играх.
 */

import { useState, useEffect, useCallback } from 'react';
import { telegram } from '../../services/telegram';
import { getPandaState, pandaFeed, pandaPlay, pandaSleep, type PandaState as PandaStateType } from '../../services/api/panda';
import type { UserProfile } from '../../services/api';

interface PandaProps {
  user: UserProfile;
  onBack: () => void;
}

/** Состояния тамагочи; картинки в panda-tamagotchi/panda-{state}.png. */
const PANDA_STATES = [
  'neutral', 'happy', 'sad', 'bored', 'hungry', 'full', 'played',
  'sleepy', 'sleeping', 'wants_bamboo', 'no_bamboo', 'questioning',
  'offended', 'eating', 'excited',
] as const;

export function Panda({ user, onBack }: PandaProps) {
  const [state, setState] = useState<PandaStateType | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<'feed' | 'play' | 'sleep' | null>(null);

  const loadState = useCallback(async () => {
    try {
      setError(null);
      const data = await getPandaState(user.telegram_id);
      setState(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки');
      setState(null);
    } finally {
      setLoading(false);
    }
  }, [user.telegram_id]);

  useEffect(() => {
    loadState();
  }, [loadState]);

  const handleFeed = async () => {
    if (!state?.can_feed || actionLoading) return;
    setActionLoading('feed');
    setError(null);
    try {
      telegram.hapticFeedback('medium');
      const result = await pandaFeed(user.telegram_id);
      setState(result.state);
      setActionFeedback('feed');
      if (result.success) telegram.notifySuccess();
      else telegram.notifyWarning();
      setTimeout(() => setActionFeedback(null), 600);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка');
      telegram.notifyError();
    } finally {
      setActionLoading(null);
    }
  };

  const handlePlay = async () => {
    if (!state?.can_play || actionLoading) return;
    setActionLoading('play');
    setError(null);
    try {
      telegram.hapticFeedback('medium');
      const result = await pandaPlay(user.telegram_id);
      setState(result.state);
      setActionFeedback('play');
      telegram.notifySuccess();
      setTimeout(() => setActionFeedback(null), 600);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка');
      telegram.notifyError();
    } finally {
      setActionLoading(null);
    }
  };

  const handleSleep = async () => {
    if (actionLoading) return;
    setActionLoading('sleep');
    setError(null);
    try {
      telegram.hapticFeedback('light');
      const result = await pandaSleep(user.telegram_id);
      setState(result.state);
      if (result.success) {
        setActionFeedback('sleep');
        telegram.notifySuccess();
        setTimeout(() => setActionFeedback(null), 600);
      } else if (result.need_feed_first) {
        telegram.notifyWarning();
        setError('Панда хочет сначала поесть. Покорми её, потом уложи спать.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка');
      telegram.notifyError();
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="w-full h-full bg-white dark:bg-slate-800 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500 dark:border-blue-400" />
        <p className="mt-3 text-sm text-gray-600 dark:text-slate-400">Загружаю панду...</p>
      </div>
    );
  }

  if (error && !state) {
    return (
      <div className="w-full h-full bg-white dark:bg-slate-800 flex flex-col p-4">
        <button
          type="button"
          onClick={() => { telegram.hapticFeedback('light'); onBack(); }}
          className="self-start p-2 rounded-lg bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-200"
        >
          ← Назад
        </button>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-red-600 dark:text-red-400 text-center">{error}</p>
        </div>
      </div>
    );
  }

  const displayState = state?.display_state ?? 'neutral';
  const imgName = PANDA_STATES.includes(displayState as (typeof PANDA_STATES)[number])
    ? displayState
    : 'neutral';
  const imgSrc = `/panda-tamagotchi/panda-${imgName}.png`;

  return (
    <div className="w-full h-full bg-white dark:bg-slate-800 flex flex-col overflow-y-auto">
      {/* Шапка: sticky + z-20 чтобы не перекрывали нативный UI / жесты Telegram */}
      <div className="sticky top-0 z-20 flex-shrink-0 flex items-center justify-between p-2 sm:p-3 border-b border-gray-200 dark:border-slate-700 bg-gradient-to-r from-blue-100 to-cyan-100 dark:from-slate-800 dark:to-slate-800">
        <button
          type="button"
          onClick={() => { telegram.hapticFeedback('light'); onBack(); }}
          className="p-2 rounded-lg bg-white/80 dark:bg-slate-700/80 hover:bg-white dark:hover:bg-slate-600 text-gray-800 dark:text-slate-200"
          aria-label="Назад"
        >
          ← Назад
        </button>
        <h1 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-slate-100">
          Моя панда
        </h1>
        <div className="w-10" />
      </div>

      {error && state && (
        <div className="mx-3 mt-2 p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30 border border-amber-300 dark:border-amber-700 text-amber-800 dark:text-amber-200 text-sm">
          {error}
        </div>
      )}

      {/* Контент: панда + шкалы + кнопки */}
      <div className="flex-1 flex flex-col sm:flex-row min-h-0 p-3 sm:p-4 gap-4">
        {/* Панда по центру */}
        <div className="flex-1 flex items-center justify-center min-h-[200px] sm:min-h-0">
          <div
            className={`
              relative w-full max-w-[280px] sm:max-w-[320px] aspect-square
              flex items-center justify-center
              ${actionFeedback === 'feed' ? 'animate-panda-feed' : ''}
              ${actionFeedback === 'play' ? 'animate-panda-play' : ''}
              ${actionFeedback === 'sleep' ? 'opacity-90' : ''}
            `}
          >
            <div className="absolute inset-0 rounded-full bg-blue-50 dark:bg-slate-700/50 animate-pulse opacity-60" />
            <img
              src={imgSrc}
              alt="Панда"
              className="relative w-full h-full object-contain drop-shadow-lg"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                const fallback = target.nextElementSibling as HTMLElement | null;
                if (fallback) fallback.hidden = false;
              }}
            />
            <span
              className="absolute text-8xl sm:text-9xl select-none pointer-events-none"
              aria-hidden
              hidden
            >
              🐼
            </span>
          </div>
        </div>

        {/* Шкалы справа */}
        <div className="flex-shrink-0 w-full sm:w-48 flex flex-row sm:flex-col gap-3 sm:gap-4 justify-center sm:justify-start">
          <Bar label="Голод" value={state?.hunger ?? 0} icon="🎋" color="bg-amber-500" />
          <Bar label="Настроение" value={state?.mood ?? 0} icon="💚" color="bg-emerald-500" />
          <Bar label="Энергия" value={state?.energy ?? 0} icon="⚡" color="bg-blue-500" />
        </div>
      </div>

      {/* Кнопки действий */}
      <div className="flex-shrink-0 p-3 sm:p-4 border-t border-gray-200 dark:border-slate-700 bg-gray-50/50 dark:bg-slate-800/50">
        <div className="max-w-md mx-auto flex flex-wrap gap-2 sm:gap-3 justify-center">
          <button
            type="button"
            onClick={handleFeed}
            disabled={!state?.can_feed || !!actionLoading}
            className="flex-1 min-w-[100px] py-3 px-4 rounded-xl bg-amber-500 hover:bg-amber-600 active:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium shadow-lg transition-all touch-manipulation"
          >
            🎋 Покормить
          </button>
          <button
            type="button"
            onClick={handlePlay}
            disabled={!state?.can_play || !!actionLoading}
            className="flex-1 min-w-[100px] py-3 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium shadow-lg transition-all touch-manipulation"
          >
            🎾 Поиграть
          </button>
          <button
            type="button"
            onClick={handleSleep}
            disabled={!!actionLoading}
            className="flex-1 min-w-[100px] py-3 px-4 rounded-xl bg-blue-500 hover:bg-blue-600 active:bg-blue-700 disabled:opacity-50 text-white font-medium shadow-lg transition-all touch-manipulation"
          >
            😴 Уложить спать
          </button>
        </div>
      </div>

      {/* Достижения */}
      {state && state.achievements.length > 0 && (
        <div className="flex-shrink-0 p-3 border-t border-gray-200 dark:border-slate-700">
          <h2 className="text-sm font-bold text-gray-700 dark:text-slate-300 mb-2">
            🏆 Достижения
          </h2>
          <div className="flex flex-wrap gap-2">
            {state.achievements.map((a) => (
              <span
                key={a.id}
                className="px-2 py-1 rounded-lg bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 text-xs font-medium"
              >
                {a.title}
              </span>
            ))}
          </div>
        </div>
      )}

      <style>{`
        @keyframes panda-feed {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        @keyframes panda-play {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.08); }
        }
        .animate-panda-feed { animation: panda-feed 0.5s ease-out; }
        .animate-panda-play { animation: panda-play 0.5s ease-out; }
      `}</style>
    </div>
  );
}

function Bar({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: number;
  icon: string;
  color: string;
}) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="flex flex-col gap-1 min-w-[80px] sm:min-w-0">
      <div className="flex items-center gap-1.5">
        <span className="text-lg" aria-hidden>{icon}</span>
        <span className="text-xs font-medium text-gray-600 dark:text-slate-400">{label}</span>
      </div>
      <div className="h-3 sm:h-4 rounded-full bg-gray-200 dark:bg-slate-600 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 dark:text-slate-500">{pct}%</span>
    </div>
  );
}
