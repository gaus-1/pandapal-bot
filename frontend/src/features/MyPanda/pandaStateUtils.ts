/**
 * Маппинг состояния панды (hunger, mood, energy) на ключ реакции для ассета.
 */

import type { PandaReactionKey } from './constants';

/** Секунды, в течение которых показываем реакцию на последнее действие (eating, played, sleeping и т.д.) */
export const LAST_ACTION_DURATION_SEC = 45;

/** Интервалы до следующего действия (минуты), синхронно с бэкендом */
export const MIN_PLAY_INTERVAL_MINUTES = 5;
export const MIN_SLEEP_INTERVAL_MINUTES = 10;
export const MIN_TOILET_INTERVAL_MINUTES = 20;
export const FEEDS_PER_HOUR = 3;

const HUNGER_LOW = 30;
const HUNGER_OK = 60;
const MOOD_LOW = 30;
const MOOD_OK = 60;
const ENERGY_LOW = 25;
const ENERGY_OK = 50;

export interface PandaStateInput {
  hunger: number;
  mood: number;
  energy: number;
  /** После кормления показываем eating/full */
  lastAction?: 'feed' | 'play' | 'sleep' | null;
}

/**
 * Возвращает ключ реакции для текущего состояния.
 * Пороги заданы константами выше.
 */
export function getPandaReactionKey(input: PandaStateInput): PandaReactionKey {
  const { hunger, mood, energy, lastAction } = input;

  if (lastAction === 'feed') {
    return hunger >= 90 ? 'full' : 'eating';
  }
  if (lastAction === 'play') {
    return 'played';
  }
  if (lastAction === 'sleep') {
    return energy >= 80 ? 'sleeping' : 'sleepy';
  }

  if (hunger < HUNGER_LOW) return 'hungry';
  if (hunger < HUNGER_OK) return 'wants_bamboo';
  if (hunger < 50 && mood < MOOD_OK) return 'no_bamboo';

  if (energy < ENERGY_LOW) return 'sleepy';
  if (energy < ENERGY_OK) return 'sleepy';

  if (mood < MOOD_LOW) return 'sad';
  if (mood < MOOD_OK) return 'bored';
  if (mood < 70) return 'offended';

  if (mood >= 85) return 'excited';
  if (mood >= 70) return 'happy';

  return 'neutral';
}

export interface PandaPetStateTimestamps {
  last_fed_at: string | null;
  last_played_at: string | null;
  last_slept_at: string | null;
}

/**
 * Определяет последнее действие по таймстемпам (в пределах LAST_ACTION_DURATION_SEC).
 * Нужно для отображения реакций eating, full, played, sleeping, sleepy.
 */
export function getLastActionFromState(state: PandaPetStateTimestamps): 'feed' | 'play' | 'sleep' | null {
  const now = Date.now();
  const cutoff = now - LAST_ACTION_DURATION_SEC * 1000;
  let lastTs = 0;
  let action: 'feed' | 'play' | 'sleep' | null = null;
  if (state.last_fed_at) {
    const ts = new Date(state.last_fed_at).getTime();
    if (ts >= cutoff && ts > lastTs) {
      lastTs = ts;
      action = 'feed';
    }
  }
  if (state.last_played_at) {
    const ts = new Date(state.last_played_at).getTime();
    if (ts >= cutoff && ts > lastTs) {
      lastTs = ts;
      action = 'play';
    }
  }
  if (state.last_slept_at) {
    const ts = new Date(state.last_slept_at).getTime();
    if (ts >= cutoff && ts > lastTs) {
      lastTs = ts;
      action = 'sleep';
    }
  }
  return action;
}

export interface CooldownInfo {
  playInSec: number;
  sleepInSec: number;
  toiletInSec: number;
  feedLabel: string | null;
}

/**
 * Секунды до следующего действия и подпись для кормления.
 * playInSec/sleepInSec/toiletInSec = 0 если действие уже доступно.
 */
export function getCooldownInfo(state: {
  last_fed_at: string | null;
  last_played_at: string | null;
  last_slept_at: string | null;
  last_toilet_at?: string | null;
  can_feed: boolean;
  can_play: boolean;
  can_sleep: boolean;
  can_toilet?: boolean;
}): CooldownInfo {
  const now = Date.now();
  let playInSec = 0;
  let sleepInSec = 0;
  let toiletInSec = 0;
  if (state.last_played_at && !state.can_play) {
    const next = new Date(state.last_played_at).getTime() + MIN_PLAY_INTERVAL_MINUTES * 60 * 1000;
    playInSec = Math.max(0, Math.ceil((next - now) / 1000));
  }
  if (state.last_slept_at && !state.can_sleep) {
    const next = new Date(state.last_slept_at).getTime() + MIN_SLEEP_INTERVAL_MINUTES * 60 * 1000;
    sleepInSec = Math.max(0, Math.ceil((next - now) / 1000));
  }
  if (state.last_toilet_at != null && state.can_toilet === false) {
    const next =
      new Date(state.last_toilet_at).getTime() + MIN_TOILET_INTERVAL_MINUTES * 60 * 1000;
    toiletInSec = Math.max(0, Math.ceil((next - now) / 1000));
  }
  const feedLabel = !state.can_feed ? `До ${FEEDS_PER_HOUR} раз в час` : null;
  return { playInSec, sleepInSec, toiletInSec, feedLabel };
}
