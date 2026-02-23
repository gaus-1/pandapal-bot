/**
 * Константы и пути для «Моя панда».
 * Фаза 1: только PNG из panda-tamagotchi.
 * BASE учитывает деплой в подпапку (import.meta.env.BASE_URL).
 */
const BASE = (import.meta.env.BASE_URL ?? '/').replace(/\/+$/, '') || '';
export const PANDA_ASSETS_BASE = `${BASE}/panda-tamagotchi`;
export const PANDA_VIDEO_BASE = `${BASE}/panda-tamagotchi-video`;

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

/** Картинка: панда залезает на дерево (игровая сцена) */
export const PANDA_CLIMB_IMAGE = `${PANDA_ASSETS_BASE}/panda-climbs-a-tree.jpg`;

/** Картинка: панда упала с дерева (игровая сцена) */
export const PANDA_FALL_IMAGE = `${PANDA_ASSETS_BASE}/panda-falls.jpg`;

/** Картинка: панда в туалете (сцена «хочет в туалет») */
export const PANDA_POOPS_IMAGE = `${PANDA_ASSETS_BASE}/Panda-poops.jpg`;

/** Видео кормления: панда ест бамбук (показывается рандомно вместо картинки при Покормить) */
export const PANDA_FEED_VIDEO = `${PANDA_VIDEO_BASE}/panda_eats_bamboo.mp4`;
