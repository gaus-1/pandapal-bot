/**
 * A/B тестирование для игровых механик PandaPal Go.
 *
 * Позволяет безопасно тестировать различные игровые механики,
 * уровни сложности и пользовательские интерфейсы.
 *
 * Особенности:
 * - Случайное распределение пользователей по группам
 * - Локальное хранение результатов
 * - Безопасное откат к базовой версии при ошибках
 * - Аналитика эффективности
 */

interface ABTestConfig {
  id: string;
  name: string;
  description: string;
  variants: ABTestVariant[];
  trafficAllocation: number; // Процент пользователей в тесте (0-100)
  enabled: boolean;
}

interface ABTestVariant {
  id: string;
  name: string;
  weight: number; // Вес для распределения (0-100)
  config: Record<string, any>;
}

interface ABTestResult {
  testId: string;
  variantId: string;
  userId: string;
  startTime: number;
  endTime?: number;
  events: ABTestEvent[];
  metrics: ABTestMetrics;
}

interface ABTestEvent {
  type: string;
  timestamp: number;
  data: Record<string, any>;
}

interface ABTestMetrics {
  playTime: number;
  levelsCompleted: number;
  score: number;
  errors: number;
  userSatisfaction?: number;
}

class ABTestManager {
  private tests: Map<string, ABTestConfig> = new Map();
  private results: Map<string, ABTestResult> = new Map();
  private userId: string;
  private isEnabled: boolean = false;

  constructor() {
    this.userId = this.generateUserId();
    this.loadConfiguration();
    this.initializeDefaultTests();
  }

  /**
   * Генерация уникального ID пользователя для A/B тестов.
   */
  private generateUserId(): string {
    const stored = localStorage.getItem('pandapal_ab_user_id');
    if (stored) {
      return stored;
    }

    const userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('pandapal_ab_user_id', userId);
    return userId;
  }

  /**
   * Загрузка конфигурации A/B тестов.
   */
  private loadConfiguration(): void {
    try {
      const config = localStorage.getItem('pandapal_ab_config');
      if (config) {
        const parsed = JSON.parse(config);
        this.isEnabled = parsed.enabled || false;

        if (parsed.tests) {
          parsed.tests.forEach((test: ABTestConfig) => {
            this.tests.set(test.id, test);
          });
        }
      }
    } catch (error) {
      console.warn('Ошибка загрузки конфигурации A/B тестов:', error);
      this.isEnabled = false;
    }
  }

  /**
   * Инициализация тестов по умолчанию.
   */
  private initializeDefaultTests(): void {
    // Тест сложности игры
    this.addTest({
      id: 'difficulty_test',
      name: 'Тест сложности игры',
      description: 'Сравнение разных уровней сложности математических задач',
      trafficAllocation: 50, // 50% пользователей участвуют в тесте
      enabled: true,
      variants: [
        {
          id: 'easy',
          name: 'Легкий уровень',
          weight: 50,
          config: {
            mathDifficulty: 'easy',
            timeLimit: 30,
            hints: 3
          }
        },
        {
          id: 'medium',
          name: 'Средний уровень',
          weight: 30,
          config: {
            mathDifficulty: 'medium',
            timeLimit: 20,
            hints: 2
          }
        },
        {
          id: 'hard',
          name: 'Сложный уровень',
          weight: 20,
          config: {
            mathDifficulty: 'hard',
            timeLimit: 15,
            hints: 1
          }
        }
      ]
    });

    // Тест UI элементов
    this.addTest({
      id: 'ui_test',
      name: 'Тест пользовательского интерфейса',
      description: 'Сравнение разных стилей UI элементов',
      trafficAllocation: 30,
      enabled: true,
      variants: [
        {
          id: 'modern',
          name: 'Современный стиль',
          weight: 50,
          config: {
            uiStyle: 'modern',
            animations: true,
            colors: 'vibrant'
          }
        },
        {
          id: 'classic',
          name: 'Классический стиль',
          weight: 50,
          config: {
            uiStyle: 'classic',
            animations: false,
            colors: 'muted'
          }
        }
      ]
    });

    // Тест игровых механик
    this.addTest({
      id: 'mechanics_test',
      name: 'Тест игровых механик',
      description: 'Сравнение разных игровых механик',
      trafficAllocation: 40,
      enabled: true,
      variants: [
        {
          id: 'power_ups',
          name: 'С бонусами',
          weight: 40,
          config: {
            powerUps: true,
            specialBlocks: true,
            comboMultiplier: true
          }
        },
        {
          id: 'simple',
          name: 'Простая механика',
          weight: 60,
          config: {
            powerUps: false,
            specialBlocks: false,
            comboMultiplier: false
          }
        }
      ]
    });
  }

  /**
   * Добавление нового A/B теста.
   */
  public addTest(test: ABTestConfig): void {
    this.tests.set(test.id, test);
    this.saveConfiguration();
  }

  /**
   * Получение варианта для пользователя в конкретном тесте.
   */
  public getVariant(testId: string): ABTestVariant | null {
    if (!this.isEnabled) {
      return null;
    }

    const test = this.tests.get(testId);
    if (!test || !test.enabled) {
      return null;
    }

    // Проверяем, должен ли пользователь участвовать в тесте
    const userHash = this.hashUserId(this.userId);
    const allocation = Math.floor(userHash % 100);

    if (allocation >= test.trafficAllocation) {
      return null; // Пользователь не участвует в тесте
    }

    // Выбираем вариант на основе весов
    const variantHash = this.hashUserId(this.userId + testId);
    const variantAllocation = Math.floor(variantHash % 100);

    let cumulativeWeight = 0;
    for (const variant of test.variants) {
      cumulativeWeight += variant.weight;
      if (variantAllocation < cumulativeWeight) {
        return variant;
      }
    }

    // Fallback на первый вариант
    return test.variants[0];
  }

  /**
   * Начало A/B теста.
   */
  public startTest(testId: string): ABTestResult | null {
    const variant = this.getVariant(testId);
    if (!variant) {
      return null;
    }

    const result: ABTestResult = {
      testId,
      variantId: variant.id,
      userId: this.userId,
      startTime: Date.now(),
      events: [],
      metrics: {
        playTime: 0,
        levelsCompleted: 0,
        score: 0,
        errors: 0
      }
    };

    this.results.set(testId, result);
    this.logEvent(testId, 'test_started', { variant: variant.id });

    return result;
  }

  /**
   * Завершение A/B теста.
   */
  public endTest(testId: string, metrics: Partial<ABTestMetrics>): void {
    const result = this.results.get(testId);
    if (!result) {
      return;
    }

    result.endTime = Date.now();
    result.metrics = { ...result.metrics, ...metrics };
    this.logEvent(testId, 'test_ended', { metrics: result.metrics });

    this.saveResults();
  }

  /**
   * Логирование события в A/B тесте.
   */
  public logEvent(testId: string, eventType: string, data: Record<string, any> = {}): void {
    const result = this.results.get(testId);
    if (!result) {
      return;
    }

    result.events.push({
      type: eventType,
      timestamp: Date.now(),
      data
    });
  }

  /**
   * Получение конфигурации для игрового компонента.
   */
  public getGameConfig(): Record<string, any> {
    const config: Record<string, any> = {};

    // Собираем конфигурацию из всех активных тестов
    for (const [testId, test] of this.tests) {
      if (test.enabled) {
        const variant = this.getVariant(testId);
        if (variant) {
          Object.assign(config, variant.config);
        }
      }
    }

    return config;
  }

  /**
   * Получение статистики A/B тестов.
   */
  public getTestStats(): Record<string, any> {
    const stats: Record<string, any> = {};

    for (const [testId, test] of this.tests) {
      const testResults = Array.from(this.results.values()).filter(r => r.testId === testId);

      stats[testId] = {
        name: test.name,
        totalParticipants: testResults.length,
        variants: {}
      };

      // Статистика по вариантам
      for (const variant of test.variants) {
        const variantResults = testResults.filter(r => r.variantId === variant.id);

        if (variantResults.length > 0) {
          const avgPlayTime = variantResults.reduce((sum, r) => sum + r.metrics.playTime, 0) / variantResults.length;
          const avgScore = variantResults.reduce((sum, r) => sum + r.metrics.score, 0) / variantResults.length;
          const avgLevelsCompleted = variantResults.reduce((sum, r) => sum + r.metrics.levelsCompleted, 0) / variantResults.length;
          const totalErrors = variantResults.reduce((sum, r) => sum + r.metrics.errors, 0);

          stats[testId].variants[variant.id] = {
            participants: variantResults.length,
            avgPlayTime,
            avgScore,
            avgLevelsCompleted,
            totalErrors,
            errorRate: totalErrors / variantResults.length
          };
        }
      }
    }

    return stats;
  }

  /**
   * Сохранение конфигурации.
   */
  private saveConfiguration(): void {
    try {
      const config = {
        enabled: this.isEnabled,
        tests: Array.from(this.tests.values())
      };
      localStorage.setItem('pandapal_ab_config', JSON.stringify(config));
    } catch (error) {
      console.warn('Ошибка сохранения конфигурации A/B тестов:', error);
    }
  }

  /**
   * Сохранение результатов тестов.
   */
  private saveResults(): void {
    try {
      const results = Array.from(this.results.values());
      localStorage.setItem('pandapal_ab_results', JSON.stringify(results));
    } catch (error) {
      console.warn('Ошибка сохранения результатов A/B тестов:', error);
    }
  }

  /**
   * Хеширование ID пользователя для детерминированного распределения.
   */
  private hashUserId(userId: string): number {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      const char = userId.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Конвертируем в 32-битное число
    }
    return Math.abs(hash);
  }

  /**
   * Включение/отключение A/B тестирования.
   */
  public setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
    this.saveConfiguration();
  }

  /**
   * Экспорт результатов для анализа.
   */
  public exportResults(): string {
    const data = {
      userId: this.userId,
      timestamp: new Date().toISOString(),
      tests: Array.from(this.tests.values()),
      results: Array.from(this.results.values()),
      stats: this.getTestStats()
    };

    return JSON.stringify(data, null, 2);
  }
}

// Глобальный экземпляр менеджера A/B тестов
export const abTestManager = new ABTestManager();

// Экспорт типов для использования в других модулях
export type {
  ABTestConfig,
  ABTestVariant,
  ABTestResult,
  ABTestEvent,
  ABTestMetrics
};
