/**
 * Конфигурация игры PandaPal Go
 * Все настройки геймплея, скорости, сложности
 */

export const GAME_CONFIG = {
  // Размеры игры
  width: 800,
  height: 600,

  // Физика
  gravity: 1000,

  // Игрок (панда)
  player: {
    startX: 150,
    startY: 400,
    speed: 300,
    jumpForce: -500,
    slideSpeed: 400,
  },

  // Дорожки
  lanes: {
    count: 3,
    top: 200,
    middle: 350,
    bottom: 500,
  },

  // Игровой процесс
  gameplay: {
    initialSpeed: 200,
    maxSpeed: 600,
    speedIncreaseRate: 5, // Увеличение скорости каждую секунду
    startingLives: 3,
    questionInterval: 15000, // 15 секунд между вопросами
  },

  // Очки
  scoring: {
    book: 10,
    star: 50,
    medal: 100,
    correctAnswer: 200,
    comboMultiplier: {
      x2: 3,  // 3 правильных = x2
      x3: 5,  // 5 правильных = x3
      x5: 10, // 10 правильных = x5
    },
  },

  // Локации (8 школьных зон)
  locations: [
    { id: 'floor1', name: 'Школа - 1 этаж', duration: 30000 },
    { id: 'floor2', name: 'Школа - 2 этаж', duration: 30000 },
    { id: 'floor3', name: 'Школа - 3 этаж', duration: 30000 },
    { id: 'cafeteria', name: 'Столовая', duration: 20000 },
    { id: 'gym', name: 'Спортзал', duration: 25000 },
    { id: 'street', name: 'Улица', duration: 20000 },
    { id: 'playground', name: 'Спортплощадка', duration: 25000 },
    { id: 'school2', name: 'Другая школа', duration: 30000 },
  ],
} as const;
