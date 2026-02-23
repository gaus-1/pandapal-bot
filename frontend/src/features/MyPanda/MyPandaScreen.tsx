/**
 * Экран «Моя панда» — виртуальный питомец (тамагочи).
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  getPandaPetState,
  feedPandaPet,
  playPandaPet,
  sleepPandaPet,
  climbPandaPet,
  fallFromTreePandaPet,
  toiletPandaPet,
  type PandaPetState as ApiState,
} from '../../services/api';
import { telegram } from '../../services/telegram';
import type { UserProfile } from '../../services/api';
import {
  getPandaImagePath,
  getPandaVideoPath,
  PANDA_CLIMB_IMAGE,
  PANDA_FALL_IMAGE,
  PANDA_POOPS_IMAGE,
  PANDA_FEED_VIDEO,
} from './constants';
import {
  getPandaReactionKey,
  getLastActionFromState,
  getCooldownInfo,
  LAST_ACTION_DURATION_SEC,
} from './pandaStateUtils';
import { REACTIONS_WITH_VIDEO } from './generated/videoReactions';
import { logger } from '../../utils/logger';

/** Подписи для ключей достижений (бэкенд может добавлять свои) */
const ACHIEVEMENT_LABELS: Record<string, string> = {
  first_feed: 'Первое кормление',
  first_play: 'Первая игра',
  first_sleep: 'Первый сон',
  week_visit: 'Неделя подряд',
  ten_feed: '10 кормлений',
  ten_play: '10 игр',
  friend: 'Друг панды',
};
function getAchievementLabel(key: string): string {
  return ACHIEVEMENT_LABELS[key] ?? key;
}

interface MyPandaScreenProps {
  user: UserProfile;
}

const DEFAULT_STATE: ApiState = {
  hunger: 70,
  mood: 70,
  energy: 80,
  last_fed_at: null,
  last_played_at: null,
  last_slept_at: null,
  last_toilet_at: null,
  last_climb_at: null,
  last_fall_at: null,
  can_feed: true,
  can_play: true,
  can_sleep: true,
  can_toilet: true,
  can_climb: true,
  can_fall: true,
  consecutive_visit_days: 0,
  achievements: {},
};

function Bar({
  value,
  label,
  colorClass,
}: {
  value: number;
  label: string;
  colorClass: string;
}) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="flex flex-col gap-1 w-full min-w-0">
      <div className="flex justify-between text-xs sm:text-sm text-gray-700 dark:text-slate-300">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div
        className="h-2 sm:h-2.5 rounded-full bg-gray-200 dark:bg-slate-600 overflow-hidden"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label}: ${pct} процентов`}
      >
        <div
          className={`h-full rounded-full transition-all duration-300 ${colorClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function MyPandaScreen({ user }: MyPandaScreenProps) {
  const isMockUser = user.telegram_id === 0;
  const [state, setState] = useState<ApiState | null>(() => (isMockUser ? DEFAULT_STATE : null));
  const [loading, setLoading] = useState(!isMockUser);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showVideo, setShowVideo] = useState(true);
  const [cooldownTick, setCooldownTick] = useState(0);
  const [imageLoadError, setImageLoadError] = useState(false);
  const [showClimbUntil, setShowClimbUntil] = useState<number | null>(null);
  const [showFallUntil, setShowFallUntil] = useState<number | null>(null);
  const [showToiletHappyUntil, setShowToiletHappyUntil] = useState<number | null>(null);
  /** При кормлении: true = видео, false = картинка eating, null = ещё не выбрано */
  const [feedMediaIsVideo, setFeedMediaIsVideo] = useState<boolean | null>(null);

  const loadState = useCallback(async () => {
    try {
      setError(null);
      const data = await getPandaPetState(user.telegram_id);
      setState(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Ошибка загрузки';
      logger.debug('MyPanda load error:', err);
      if (user.telegram_id === 0) {
        setState(DEFAULT_STATE);
      } else {
        setError(msg);
        telegram.notifyError();
      }
    } finally {
      setLoading(false);
    }
  }, [user.telegram_id]);

  useEffect(() => {
    if (!isMockUser) loadState();
  }, [isMockUser, loadState]);

  // Хук всегда вызывается (правила React) — обновляет showVideo при смене реакции
  const lastAction = state ? getLastActionFromState(state) : null;
  const reactionKey = state
    ? getPandaReactionKey({
        hunger: state.hunger,
        mood: state.mood,
        energy: state.energy,
        lastAction,
      })
    : null;
  const hasVideo = reactionKey ? REACTIONS_WITH_VIDEO.includes(reactionKey) : false;
  const isFeedReaction =
    lastAction === 'feed' && (reactionKey === 'eating' || reactionKey === 'full');

  useEffect(() => {
    if (reactionKey && hasVideo) setShowVideo(true);
  }, [reactionKey, hasVideo]);
  useEffect(() => {
    if (isFeedReaction && feedMediaIsVideo === true) setShowVideo(true);
  }, [isFeedReaction, feedMediaIsVideo]);
  useEffect(() => {
    if (lastAction !== 'feed') setFeedMediaIsVideo(null);
  }, [lastAction]);
  useEffect(() => {
    if (isFeedReaction && feedMediaIsVideo === null) {
      setFeedMediaIsVideo(Math.random() < 0.5);
    }
  }, [isFeedReaction, feedMediaIsVideo]);
  useEffect(() => {
    setImageLoadError(false);
  }, [reactionKey]);

  // Обновление таймеров кулдауна раз в секунду
  useEffect(() => {
    if (!state) return;
    const hasCooldown =
      !state.can_feed ||
      !state.can_play ||
      !state.can_sleep ||
      (state.can_toilet === false) ||
      (state.can_climb === false) ||
      (state.can_fall === false);
    if (!hasCooldown) return;
    const t = setInterval(() => setCooldownTick((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, [state?.can_feed, state?.can_play, state?.can_sleep, state?.can_toilet, state?.can_climb, state?.can_fall, state]);

  // Сброс показа climb/fall/toilet по истечении времени (5 сек climb, 10 сек fall, 10 сек toilet happy)
  useEffect(() => {
    const t = setInterval(() => {
      const now = Date.now();
      setShowClimbUntil((prev) => (prev != null && now >= prev ? null : prev));
      setShowFallUntil((prev) => (prev != null && now >= prev ? null : prev));
      setShowToiletHappyUntil((prev) => (prev != null && now >= prev ? null : prev));
    }, 500);
    return () => clearInterval(t);
  }, []);

  const cooldown = useMemo(
    () =>
      state
        ? getCooldownInfo(state)
        : {
            playInSec: 0,
            sleepInSec: 0,
            toiletInSec: 0,
            feedInSec: 0,
            feedLabel: null as string | null,
            climbInSec: 0,
            fallInSec: 0,
          },
    [state, cooldownTick]
  );
  const achievementEntries = state && state.achievements && typeof state.achievements === 'object'
    ? Object.entries(state.achievements)
    : [];

  const handleFeed = async () => {
    if (!state?.can_feed || actionLoading) return;
    telegram.hapticFeedback('light');
    setFeedMediaIsVideo(Math.random() < 0.5);
    setActionLoading('feed');
    try {
      const next = await feedPandaPet(user.telegram_id);
      setState(next);
    } catch (err) {
      if (user.telegram_id === 0 && state) {
        setState({
          ...state,
          hunger: Math.min(100, state.hunger + 25),
          last_fed_at: new Date().toISOString(),
          can_feed: false,
        });
      } else {
        const msg = err instanceof Error ? err.message : 'Ошибка';
        setError(msg);
        telegram.notifyError();
        telegram.showAlert(msg);
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handlePlay = async () => {
    if (!state?.can_play || actionLoading) return;
    telegram.hapticFeedback('light');
    setActionLoading('play');
    try {
      const next = await playPandaPet(user.telegram_id);
      setState(next);
    } catch (err) {
      if (user.telegram_id === 0 && state) {
        setState({
          ...state,
          mood: Math.min(100, state.mood + 20),
          energy: Math.max(0, state.energy - 15),
          last_played_at: new Date().toISOString(),
          can_play: false,
        });
      } else {
        const msg = err instanceof Error ? err.message : 'Ошибка';
        setError(msg);
        telegram.notifyError();
        telegram.showAlert(msg);
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleSleep = async () => {
    if (!state?.can_sleep || actionLoading) return;
    telegram.hapticFeedback('light');
    setActionLoading('sleep');
    try {
      const next = await sleepPandaPet(user.telegram_id);
      setState(next);
    } catch (err) {
      if (user.telegram_id === 0 && state) {
        setState({
          ...state,
          energy: Math.min(100, state.energy + 40),
          last_slept_at: new Date().toISOString(),
          can_sleep: false,
        });
      } else {
        const msg = err instanceof Error ? err.message : 'Ошибка';
        setError(msg);
        telegram.notifyError();
        telegram.showAlert(msg);
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleToilet = async () => {
    if (!state || state.can_toilet === false || actionLoading) return;
    telegram.hapticFeedback('light');
    setActionLoading('toilet');
    try {
      const next = await toiletPandaPet(user.telegram_id);
      setState(next);
      setShowToiletHappyUntil(Date.now() + TOILET_HAPPY_DURATION_MS);
    } catch (err) {
      if (user.telegram_id === 0 && state) {
        setState({
          ...state,
          mood: Math.min(100, state.mood + 15),
          last_toilet_at: new Date().toISOString(),
          can_toilet: false,
        });
        setShowToiletHappyUntil(Date.now() + TOILET_HAPPY_DURATION_MS);
      } else {
        const msg = err instanceof Error ? err.message : 'Ошибка';
        setError(msg);
        telegram.notifyError();
        telegram.showAlert(msg);
      }
    } finally {
      setActionLoading(null);
    }
  };

  const CLIMB_DURATION_MS = 5000;
  const FALL_DURATION_MS = 10000;
  const TOILET_HAPPY_DURATION_MS = 10000;
  const MOOD_OFFENDED_MAX = 65;

  const handleClimb = async () => {
    if (!state || actionLoading || state.can_climb === false) return;
    const currentState = state;
    telegram.hapticFeedback('light');
    setActionLoading('climb');
    try {
      const next = await climbPandaPet(user.telegram_id);
      setState(next);
      setShowClimbUntil(Date.now() + CLIMB_DURATION_MS);
    } catch (err) {
      if (user.telegram_id === 0 && currentState) {
        setState({
          ...currentState,
          last_climb_at: new Date().toISOString(),
          can_climb: false,
        });
        setShowClimbUntil(Date.now() + CLIMB_DURATION_MS);
      } else {
        const msg = err instanceof Error ? err.message : 'Ошибка';
        setError(msg);
        telegram.notifyError();
        telegram.showAlert(msg);
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleFall = async () => {
    if (!state || actionLoading || state.can_fall === false) return;
    const currentState = state;
    telegram.hapticFeedback('light');
    setActionLoading('fall');
    try {
      const next = await fallFromTreePandaPet(user.telegram_id);
      setState(next);
      setShowFallUntil(Date.now() + FALL_DURATION_MS);
    } catch (err) {
      if (user.telegram_id === 0 && currentState) {
        setState({
          ...currentState,
          mood: Math.min(currentState.mood, MOOD_OFFENDED_MAX),
          last_fall_at: new Date().toISOString(),
          can_fall: false,
        });
        setShowFallUntil(Date.now() + FALL_DURATION_MS);
      } else {
        const msg = err instanceof Error ? err.message : 'Ошибка';
        setError(msg);
        telegram.notifyError();
        telegram.showAlert(msg);
      }
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-4 bg-white dark:bg-slate-800 safe-area-inset">
        <div className="animate-pulse w-48 h-48 rounded-2xl bg-gray-200 dark:bg-slate-600" />
        <div className="mt-4 h-4 w-32 bg-gray-200 dark:bg-slate-600 rounded animate-pulse" />
        <div className="mt-6 flex gap-3">
          <div className="h-12 w-24 bg-gray-200 dark:bg-slate-600 rounded-xl animate-pulse" />
          <div className="h-12 w-24 bg-gray-200 dark:bg-slate-600 rounded-xl animate-pulse" />
          <div className="h-12 w-24 bg-gray-200 dark:bg-slate-600 rounded-xl animate-pulse" />
        </div>
      </div>
    );
  }

  if (error && !state) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-4 bg-white dark:bg-slate-800 safe-area-inset">
        <p className="text-gray-600 dark:text-slate-400 text-center mb-4">{error}</p>
        <button
          type="button"
          onClick={() => { setLoading(true); loadState(); }}
          className="px-4 py-2 rounded-xl bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] min-h-[44px] touch-manipulation"
          aria-label="Попробовать снова"
        >
          Попробовать снова
        </button>
      </div>
    );
  }

  if (!state) return null;

  const now = Date.now();
  const showingFall = showFallUntil != null && now < showFallUntil;
  const showingToiletHappy =
    !showingFall && showToiletHappyUntil != null && now < showToiletHappyUntil;
  const showingClimb =
    !showingFall &&
    !showingToiletHappy &&
    showClimbUntil != null &&
    now < showClimbUntil;

  const imageSrc =
    reactionKey
      ? (imageLoadError ? getPandaImagePath('neutral') : getPandaImagePath(reactionKey))
      : '';
  const displayVideo = hasVideo && showVideo;
  const displayFeedVideo =
    isFeedReaction && feedMediaIsVideo === true && showVideo;
  const displayFeedImage =
    isFeedReaction && (feedMediaIsVideo === false || !showVideo);

  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-800 overflow-auto safe-area-inset">
      <header className="flex-shrink-0 py-2 px-3 xs:px-4 sm:px-4 md:px-5 border-b border-gray-200 dark:border-slate-700">
        <h1 className="text-lg sm:text-xl md:text-2xl font-display font-bold text-gray-900 dark:text-slate-100 text-center">
          Моя панда
        </h1>
        {state.consecutive_visit_days > 0 && (
          <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-400 text-center mt-0.5">
            Дней подряд: {state.consecutive_visit_days}
          </p>
        )}
      </header>

      <div className="flex-1 flex flex-col items-center px-3 xs:px-4 sm:px-4 md:px-5 py-2 sm:py-3 gap-2 sm:gap-3 md:gap-4 min-h-0 min-w-0 pb-20 max-w-full">
        {/* Реакция панды — контейнер компактнее, чтобы не скроллить */}
        <div
          className="flex-shrink-0 w-full max-w-[165px] fold:max-w-[190px] xs:max-w-[210px] sm:max-w-[260px] md:max-w-[300px] lg:max-w-[320px] max-h-[24vh] fold:max-h-[26vh] xs:max-h-[28vh] sm:max-h-[32vh] md:max-h-[34vh] aspect-square flex items-center justify-center bg-gray-50 dark:bg-slate-700/50 rounded-2xl"
          aria-label="Панда"
        >
          {showingFall ? (
            <img
              src={PANDA_FALL_IMAGE}
              alt="Панда упала с дерева"
              className="max-w-full max-h-full object-contain"
            />
          ) : showingToiletHappy ? (
            <img
              src={PANDA_POOPS_IMAGE}
              alt="Панда в туалете"
              className="max-w-full max-h-full object-contain"
            />
          ) : showingClimb ? (
            <img
              src={PANDA_CLIMB_IMAGE}
              alt="Панда залезает на дерево"
              className="max-w-full max-h-full object-contain"
            />
          ) : displayFeedVideo ? (
            <video
              src={PANDA_FEED_VIDEO}
              autoPlay
              muted
              playsInline
              className="max-w-full max-h-full w-full h-full object-contain"
              aria-label="Панда ест бамбук"
              onEnded={() => setShowVideo(false)}
            />
          ) : displayFeedImage ? (
            <img
              src={getPandaImagePath('eating')}
              alt="Панда ест"
              className="max-w-full max-h-full object-contain"
            />
          ) : displayVideo && reactionKey ? (
            <video
              src={getPandaVideoPath(reactionKey)}
              autoPlay
              muted
              playsInline
              className="max-w-full max-h-full object-contain"
              aria-label={`Панда: ${reactionKey}`}
              onEnded={() => setShowVideo(false)}
            />
          ) : imageSrc ? (
            <img
              src={imageSrc}
              alt={reactionKey ? `Панда: ${reactionKey}` : 'Панда'}
              className="max-w-full max-h-full object-contain"
              onError={() => {
                if (!imageLoadError) {
                  setImageLoadError(true);
                  logger.debug('MyPanda reaction image failed to load, using neutral');
                }
              }}
            />
          ) : null}
        </div>
        <p className="font-sans text-xs sm:text-sm text-gray-600 dark:text-slate-500 text-center -mt-0.5">
          После действия реакция панды меняется ~{LAST_ACTION_DURATION_SEC} сек.
        </p>
        <div className="w-full max-w-[280px] sm:max-w-[320px] md:max-w-[360px] space-y-2 sm:space-y-3">
          <Bar
            value={state.hunger}
            label="Голод"
            colorClass="bg-amber-500 dark:bg-amber-400"
          />
          <Bar
            value={state.mood}
            label="Настроение"
            colorClass="bg-rose-500 dark:bg-pink-400"
          />
          <Bar
            value={state.energy}
            label="Энергия"
            colorClass="bg-emerald-500 dark:bg-emerald-400"
          />
        </div>

        {/* Шесть кнопок: под каждой — место для подписи «через N мин» или «До 3 раз в час» */}
        <div className="grid grid-cols-3 gap-2 sm:gap-2.5 w-full max-w-[340px] sm:max-w-[380px] md:max-w-[420px] min-w-0 shrink-0">
          {/* Ряд 1: Покормить, Играть, Спать */}
          <div className="flex flex-col items-center gap-0.5 min-w-0">
            <button
              type="button"
              onClick={handleFeed}
              disabled={!state.can_feed || !!actionLoading}
              className="w-full min-h-[40px] sm:min-h-[44px] py-2 px-1 sm:px-2 rounded-xl font-medium touch-manipulation disabled:opacity-50 disabled:cursor-not-allowed bg-amber-600 hover:bg-amber-700 dark:bg-amber-500 dark:hover:bg-amber-600 text-white transition-all active:scale-95 text-xs sm:text-sm whitespace-nowrap overflow-hidden text-ellipsis"
              aria-label="Покормить панду"
              title="Покормить"
            >
              {actionLoading === 'feed' ? '...' : 'Покормить'}
            </button>
            <span className="min-h-[1.25rem] text-[10px] sm:text-xs text-gray-500 dark:text-slate-500 text-center leading-tight" aria-hidden="true">
              {cooldown.feedInSec > 0 ? `через ${Math.ceil(cooldown.feedInSec / 60)} мин` : state.can_feed ? 'каждые 30 мин' : '\u00A0'}
            </span>
          </div>
          <div className="flex flex-col items-center gap-0.5 min-w-0">
            <button
              type="button"
              onClick={handlePlay}
              disabled={!state.can_play || !!actionLoading}
              className="w-full min-h-[40px] sm:min-h-[44px] py-2 px-1 sm:px-2 rounded-xl font-medium touch-manipulation disabled:opacity-50 disabled:cursor-not-allowed bg-red-600 hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600 text-white transition-all active:scale-95 text-xs sm:text-sm whitespace-nowrap overflow-hidden text-ellipsis"
              aria-label="Играть с пандой"
              title="Играть"
            >
              {actionLoading === 'play' ? '...' : 'Играть'}
            </button>
            <span className="min-h-[1.25rem] text-[10px] sm:text-xs text-gray-500 dark:text-slate-500 text-center leading-tight" aria-hidden="true">
              {cooldown.playInSec > 0 ? `через ${Math.ceil(cooldown.playInSec / 60)} мин` : '\u00A0'}
            </span>
          </div>
          <div className="flex flex-col items-center gap-0.5 min-w-0">
            <button
              type="button"
              onClick={handleSleep}
              disabled={!state.can_sleep || !!actionLoading}
              className="w-full min-h-[40px] sm:min-h-[44px] py-2 px-1 sm:px-2 rounded-xl font-medium touch-manipulation disabled:opacity-50 disabled:cursor-not-allowed bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600 text-white transition-all active:scale-95 text-xs sm:text-sm whitespace-nowrap overflow-hidden text-ellipsis"
              aria-label="Уложить панду спать"
              title="Уложить спать"
            >
              {actionLoading === 'sleep' ? '...' : 'Спать'}
            </button>
            <span className="min-h-[1.25rem] text-[10px] sm:text-xs text-gray-500 dark:text-slate-500 text-center leading-tight" aria-hidden="true">
              {cooldown.sleepInSec > 0 ? `через ${Math.ceil(cooldown.sleepInSec / 60)} мин` : '\u00A0'}
            </span>
          </div>
          {/* Ряд 2: На дерево, Упасть, В туалет */}
          <div className="flex flex-col items-center gap-0.5 min-w-0">
            <button
              type="button"
              onClick={handleClimb}
              disabled={state.can_climb === false || !!actionLoading}
              className="w-full min-h-[38px] sm:min-h-[42px] py-1.5 px-1 rounded-xl font-medium touch-manipulation disabled:opacity-50 disabled:cursor-not-allowed bg-teal-600 hover:bg-teal-700 dark:bg-teal-500 dark:hover:bg-teal-600 text-white transition-all active:scale-95 text-[11px] sm:text-xs whitespace-nowrap overflow-hidden text-ellipsis"
              aria-label="На дерево"
              title="На дерево"
            >
              {actionLoading === 'climb' ? '...' : 'На дерево'}
            </button>
            <span className="min-h-[1.25rem] text-[10px] sm:text-xs text-gray-500 dark:text-slate-500 text-center leading-tight" aria-hidden="true">
              {cooldown.climbInSec > 0 ? `через ${Math.ceil(cooldown.climbInSec / 60)} мин` : (state.can_climb !== false ? 'раз в час' : '\u00A0')}
            </span>
          </div>
          <div className="flex flex-col items-center gap-0.5 min-w-0">
            <button
              type="button"
              onClick={handleFall}
              disabled={state.can_fall === false || !!actionLoading}
              className="w-full min-h-[38px] sm:min-h-[42px] py-1.5 px-1 rounded-xl font-medium touch-manipulation disabled:opacity-50 disabled:cursor-not-allowed bg-orange-600 hover:bg-orange-700 dark:bg-orange-500 dark:hover:bg-orange-600 text-white transition-all active:scale-95 text-[11px] sm:text-xs whitespace-nowrap overflow-hidden text-ellipsis"
              aria-label="Упасть"
              title="Упасть"
            >
              {actionLoading === 'fall' ? '...' : 'Упасть'}
            </button>
            <span className="min-h-[1.25rem] text-[10px] sm:text-xs text-gray-500 dark:text-slate-500 text-center leading-tight" aria-hidden="true">
              {cooldown.fallInSec > 0 ? `через ${Math.ceil(cooldown.fallInSec / 60)} мин` : (state.can_fall !== false ? 'раз в час' : '\u00A0')}
            </span>
          </div>
          <div className="flex flex-col items-center gap-0.5 min-w-0">
            <button
              type="button"
              onClick={handleToilet}
              disabled={state.can_toilet === false || !!actionLoading}
              className="w-full min-h-[38px] sm:min-h-[42px] py-1.5 px-1 rounded-xl font-medium touch-manipulation disabled:opacity-50 disabled:cursor-not-allowed bg-violet-600 hover:bg-violet-700 dark:bg-violet-500 dark:hover:bg-violet-600 text-white transition-all active:scale-95 text-[11px] sm:text-xs whitespace-nowrap overflow-hidden text-ellipsis"
              aria-label="В туалет"
              title="В туалет"
            >
              {actionLoading === 'toilet' ? '...' : 'В туалет'}
            </button>
            <span className="min-h-[1.25rem] text-[10px] sm:text-xs text-gray-500 dark:text-slate-500 text-center leading-tight" aria-hidden="true">
              {cooldown.toiletInSec > 0 ? `через ${Math.ceil(cooldown.toiletInSec / 60)} мин` : '\u00A0'}
            </span>
          </div>
        </div>

        {achievementEntries.length > 0 && (
          <div className="w-full max-w-[280px] xs:max-w-[300px] sm:max-w-[320px] mt-2 p-2.5 sm:p-3 rounded-xl bg-gray-50 dark:bg-slate-700/50 border border-gray-200 dark:border-slate-600">
            <h3 className="font-display text-xs sm:text-sm font-semibold text-gray-900 dark:text-slate-100 mb-2">
              Достижения
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {achievementEntries.map(([key]) => (
                <span
                  key={key}
                  className="inline-flex items-center px-2 py-0.5 rounded-md bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 text-xs font-medium"
                >
                  {getAchievementLabel(key)}
                </span>
              ))}
            </div>
          </div>
        )}

        {error && (
          <p className="text-sm text-red-600 dark:text-red-400 text-center">{error}</p>
        )}
      </div>
    </div>
  );
}
