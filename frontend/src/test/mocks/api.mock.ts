/**
 * API Mocks для тестирования
 * Реалистичные ответы от backend
 */

import type { UserProfile, ProgressItem, Achievement, DashboardStats } from '../../services/api';

/**
 * Mock данные пользователя
 */
export const mockUserProfile: UserProfile = {
  telegram_id: 123456789,
  first_name: 'Test',
  last_name: 'User',
  username: 'testuser',
  age: 10,
  grade: 5,
  user_type: 'child',
};

/**
 * Mock история чата
 */
export const mockChatHistory = [
  {
    role: 'user' as const,
    content: 'Привет, помоги с математикой',
    timestamp: new Date('2026-01-02T10:00:00Z').toISOString(),
  },
  {
    role: 'ai' as const,
    content: 'Привет! Конечно, помогу с математикой. Какая у тебя задача?',
    timestamp: new Date('2026-01-02T10:00:05Z').toISOString(),
  },
  {
    role: 'user' as const,
    content: 'Реши уравнение: 2x + 5 = 13',
    timestamp: new Date('2026-01-02T10:01:00Z').toISOString(),
  },
  {
    role: 'ai' as const,
    content: 'Хорошо! Решаем пошагово:\n\n1. Вычитаем 5 из обеих частей:\n   2x = 13 - 5\n   2x = 8\n\n2. Делим обе части на 2:\n   x = 8 ÷ 2\n   x = 4\n\nОтвет: x = 4\n\nПроверка: 2×4 + 5 = 8 + 5 = 13 ✓',
    timestamp: new Date('2026-01-02T10:01:10Z').toISOString(),
  },
];

/**
 * Mock прогресс обучения
 */
export const mockProgress: ProgressItem[] = [
  {
    subject: 'Математика',
    level: 5,
    points: 250,
    last_activity: new Date('2026-01-02T10:00:00Z').toISOString(),
  },
  {
    subject: 'Русский язык',
    level: 3,
    points: 150,
    last_activity: new Date('2026-01-01T15:00:00Z').toISOString(),
  },
  {
    subject: 'Окружающий мир',
    level: 4,
    points: 200,
    last_activity: new Date('2026-01-01T12:00:00Z').toISOString(),
  },
];

/**
 * Mock достижения
 */
export const mockAchievements: Achievement[] = [
  {
    id: 'first_question',
    title: 'Первый вопрос',
    description: 'Задал свой первый вопрос PandaPal',
    icon: '🎯',
    unlocked: true,
    unlock_date: new Date('2026-01-01T10:00:00Z').toISOString(),
  },
  {
    id: 'math_master_bronze',
    title: 'Математик Бронза',
    description: 'Решил 10 задач по математике',
    icon: '🥉',
    unlocked: true,
    unlock_date: new Date('2026-01-02T10:00:00Z').toISOString(),
  },
  {
    id: 'math_master_silver',
    title: 'Математик Серебро',
    description: 'Решил 50 задач по математике',
    icon: '🥈',
    unlocked: false,
  },
];

/**
 * Mock статистика дашборда
 */
export const mockDashboardStats: DashboardStats = {
  total_messages: 42,
  learning_sessions: 15,
  total_points: 600,
  subjects_studied: 3,
  current_streak: 7,
};

/**
 * Создаёт mock ответ AI
 */
export function createMockAIResponse(userMessage: string): string {
  // Реалистичные ответы на основе типа сообщения
  if (userMessage.includes('фото') || userMessage.includes('📷')) {
    return 'Вижу на фото задачу по математике. Решаю:\n\n**Условие:** 2x + 5 = 13\n\n**Решение:**\n1. Вычитаем 5 из обеих частей: 2x = 8\n2. Делим на 2: x = 4\n\n**Ответ: x = 4** ✅';
  }

  if (userMessage.includes('аудио') || userMessage.includes('🎤')) {
    return 'Услышал твой вопрос! Отвечаю:\n\nЭто отличный вопрос по русскому языку. Проверочное слово к "вода" - "воды". Ударение падает на "о", значит пишем "вода" через "о".';
  }

  // Обычный текстовый ответ
  return 'Отличный вопрос! Вот подробный ответ:\n\nЭто пример того, как AI помогает с учёбой. Я постараюсь объяснить максимально понятно.';
}

/**
 * Создаёт задержку для имитации сетевых запросов
 */
export const delay = (ms: number = 100) =>
  new Promise(resolve => setTimeout(resolve, ms));

/**
 * Mock API responses с задержкой (реалистичнее)
 */
export const mockApiResponses = {
  authenticateUser: async (): Promise<UserProfile> => {
    await delay(50);
    return mockUserProfile;
  },

  getChatHistory: async (_telegramId: number, limit: number = 50) => {
    await delay(30);
    return mockChatHistory.slice(-limit);
  },

  sendAIMessage: async (
    _telegramId: number,
    message?: string,
    photoBase64?: string,
    audioBase64?: string
  ) => {
    await delay(200); // AI немного думает

    let content = message || '';
    if (photoBase64) content = 'Пользователь отправил фото';
    if (audioBase64) content = 'Пользователь отправил аудио';

    return {
      success: true,
      response: createMockAIResponse(content),
    };
  },

  getUserProfile: async (_telegramId: number): Promise<UserProfile> => {
    await delay(30);
    return mockUserProfile;
  },

  getUserProgress: async (_telegramId: number): Promise<ProgressItem[]> => {
    await delay(50);
    return mockProgress;
  },

  getUserAchievements: async (_telegramId: number): Promise<Achievement[]> => {
    await delay(50);
    return mockAchievements;
  },

  getDashboardStats: async (_telegramId: number): Promise<DashboardStats> => {
    await delay(50);
    return mockDashboardStats;
  },
};
