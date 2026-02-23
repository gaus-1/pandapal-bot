/**
 * Константы и пути для «Моя панда».
 * Фаза 1: только PNG из panda-tamagotchi.
 */

export const PANDA_ASSETS_BASE = '/panda-tamagotchi';
export const PANDA_VIDEO_BASE = '/panda-tamagotchi-video';

/** Ключи реакций (имена файлов без panda- и .png) */
export const PANDA_REACTION_KEYS = [
  'excited',
  'played',
  'wants_bamboo',
  'neutral',
  'sleepy',
  'sad',
  'hungry',
  'no_bamboo',
  'eating',
  'full',
  'bored',
  'offended',
  'happy',
  'questioning',
  'sleeping',
] as const;

export type PandaReactionKey = (typeof PANDA_REACTION_KEYS)[number];

/** Путь к PNG по ключу */
export function getPandaImagePath(key: PandaReactionKey): string {
  return `${PANDA_ASSETS_BASE}/panda-${key}.png`;
}

/** Путь к видео по ключу (Фаза 2) */
export function getPandaVideoPath(key: PandaReactionKey): string {
  return `${PANDA_VIDEO_BASE}/panda-${key}.mp4`;
}
