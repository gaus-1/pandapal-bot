export interface MiniAppScreenshotItem {
  id: number;
  src: string;
  title: string;
}

/**
 * Список скриншотов Mini App.
 * Добавь файлы в frontend/public/screenshots/miniapp/
 * и оставь имена 01.webp ... 10.webp (или поменяй пути тут).
 */
export const MINIAPP_SCREENSHOTS: readonly MiniAppScreenshotItem[] = [
  { id: 1, src: '/screenshots/miniapp/01.webp', title: 'Главный экран' },
  { id: 2, src: '/screenshots/miniapp/02.webp', title: 'AI-чат' },
  { id: 3, src: '/screenshots/miniapp/03.webp', title: 'Вопрос по фото' },
  { id: 4, src: '/screenshots/miniapp/04.webp', title: 'Голосовой вопрос' },
  { id: 5, src: '/screenshots/miniapp/05.webp', title: 'Проверка ДЗ' },
  { id: 6, src: '/screenshots/miniapp/06.webp', title: 'Визуализации' },
  { id: 7, src: '/screenshots/miniapp/07.webp', title: 'Игры PandaPalGo' },
  { id: 8, src: '/screenshots/miniapp/08.webp', title: 'Достижения' },
  { id: 9, src: '/screenshots/miniapp/09.webp', title: 'Premium' },
  { id: 10, src: '/screenshots/miniapp/10.webp', title: 'Профиль и прогресс' },
] as const;
