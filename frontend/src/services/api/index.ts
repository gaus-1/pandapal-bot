/**
 * API Service - главный модуль для взаимодействия с Backend.
 *
 * Реэкспортирует все API функции для обратной совместимости.
 */

// Config
export { API_BASE_URL, sendLogToServer } from './config';

// Types
export type {
  UserProfile,
  ProgressItem,
  Achievement,
  DashboardStats,
  AchievementUnlocked,
  GameSession,
  GameStats,
} from './types';

// Auth & Profile
export {
  authenticateUser,
  getUserProfile,
  getUserProgress,
  getUserAchievements,
  getDashboardStats,
  getSubjects,
  updateUserProfile,
} from './auth';

// Chat
export {
  sendAIMessage,
  getChatHistory,
  addGreetingMessage,
  clearChatHistory,
} from './chat';

// Games
export {
  createGame,
  ticTacToeMove,
  getCheckersValidMoves,
  checkersMove,
  game2048Move,
  getGameStats,
  getGameSession,
} from './games';

// Premium
export {
  createPremiumPayment,
  getPremiumStatus,
  removeSavedPaymentMethod,
} from './premium';
