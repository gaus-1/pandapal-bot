/**
 * Константы игры PandaPal Go
 * Цвета, размеры спрайтов, UI элементы
 */

// Цвета
export const COLORS = {
  primary: '#FFC0CB',    // Розовый
  secondary: '#87CEEB',  // Голубой
  success: '#4ADE80',    // Зеленый
  danger: '#EF4444',     // Красный
  warning: '#FBBF24',    // Желтый
  white: '#FFFFFF',
  black: '#000000',
  text: '#1F2937',       // Темно-серый
} as const;

// Размеры спрайтов
export const SPRITE_SIZES = {
  player: { width: 64, height: 64 },
  obstacle: { width: 48, height: 48 },
  collectible: { width: 32, height: 32 },
  answer: { width: 80, height: 80 },
} as const;

// Слои (Z-index)
export const LAYERS = {
  background: 0,
  backgroundDetails: 1,
  obstacles: 2,
  collectibles: 3,
  player: 4,
  ui: 5,
  quiz: 6,
} as const;

// Ключи для LocalStorage
export const STORAGE_KEYS = {
  highScore: 'pandapal_go_high_score',
  settings: 'pandapal_go_settings',
  achievements: 'pandapal_go_achievements',
} as const;

// События игры
export const EVENTS = {
  scoreUpdate: 'score:update',
  livesUpdate: 'lives:update',
  comboUpdate: 'combo:update',
  questionShow: 'question:show',
  questionAnswer: 'question:answer',
  locationChange: 'location:change',
  gameOver: 'game:over',
  gamePause: 'game:pause',
} as const;
