/**
 * Глобальное состояние игры PandaPal Go
 * Использует Zustand для управления состоянием игры
 *
 * @module stores/gameStore
 */

import { create } from 'zustand';

/**
 * Типы игровых состояний
 */
export type GameState = 'loading' | 'playing' | 'paused' | 'gameOver';

/**
 * Типы анимаций панды
 */
export type PandaAnimation = 'idle' | 'walk' | 'eat' | 'play' | 'sleep' | 'happy';

/**
 * Позиция в 3D пространстве
 */
export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

/**
 * Игровая статистика
 */
export interface GameStats {
  score: number;
  level: number;
  coins: number;
  experience: number;
  achievements: string[];
}

/**
 * Состояние панды
 */
export interface PandaState {
  position: Vector3;
  rotation: Vector3;
  animation: PandaAnimation;
  health: number;
  happiness: number;
  energy: number;
  isMoving: boolean;
}

/**
 * Игровое состояние
 */
export interface GameStore {
  // Основное состояние
  gameState: GameState;
  isGameLoaded: boolean;

  // Состояние панды
  panda: PandaState;

  // Игровая статистика
  stats: GameStats;

  // Настройки игры
  settings: {
    soundEnabled: boolean;
    musicEnabled: boolean;
    difficulty: 'easy' | 'medium' | 'hard';
  };

  // Действия
  setGameState: (state: GameState) => void;
  updatePandaPosition: (position: Vector3) => void;
  updatePandaAnimation: (animation: PandaAnimation) => void;
  updateStats: (stats: Partial<GameStats>) => void;
  addCoins: (amount: number) => void;
  addExperience: (amount: number) => void;
  toggleSound: () => void;
  resetGame: () => void;
}

/**
 * Начальные значения
 */
const initialPandaState: PandaState = {
  position: { x: 0, y: 0, z: 0 },
  rotation: { x: 0, y: 0, z: 0 },
  animation: 'idle',
  health: 100,
  happiness: 80,
  energy: 90,
  isMoving: false,
};

const initialStats: GameStats = {
  score: 0,
  level: 1,
  coins: 0,
  experience: 0,
  achievements: [],
};

/**
 * Главный стор игры
 */
export const useGameStore = create<GameStore>((set, get) => ({
  // Начальное состояние
  gameState: 'loading',
  isGameLoaded: false,
  panda: initialPandaState,
  stats: initialStats,
  settings: {
    soundEnabled: true,
    musicEnabled: true,
    difficulty: 'easy',
  },

  // Действия
  setGameState: (state) => set({ gameState: state }),

  updatePandaPosition: (position) =>
    set((state) => ({
      panda: { ...state.panda, position }
    })),

  updatePandaAnimation: (animation) =>
    set((state) => ({
      panda: { ...state.panda, animation }
    })),

  updateStats: (newStats) =>
    set((state) => ({
      stats: { ...state.stats, ...newStats }
    })),

  addCoins: (amount) =>
    set((state) => ({
      stats: { ...state.stats, coins: state.stats.coins + amount }
    })),

  addExperience: (amount) => {
    set((state) => {
      const newExp = state.stats.experience + amount;
      const newLevel = Math.floor(newExp / 100) + 1;
      const newScore = state.stats.score + amount;

      return {
        stats: {
          ...state.stats,
          experience: newExp,
          level: newLevel,
          score: newScore,
        }
      };
    });
  },

  toggleSound: () =>
    set((state) => ({
      settings: { ...state.settings, soundEnabled: !state.settings.soundEnabled }
    })),

  resetGame: () =>
    set({
      gameState: 'loading',
      isGameLoaded: false,
      panda: initialPandaState,
      stats: initialStats,
    }),
}));
