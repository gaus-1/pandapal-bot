/**
 * Интеграция A/B тестирования с игрой PandaPal Go.
 *
 * Безопасно интегрирует A/B тесты в игровые механики
 * без нарушения основного функционала игры.
 */

import { abTestManager } from './ABTestManager';
import type { ABTestResult } from './ABTestManager';

interface GameABConfig {
  difficulty: 'easy' | 'medium' | 'hard';
  timeLimit: number;
  hints: number;
  powerUps: boolean;
  specialBlocks: boolean;
  comboMultiplier: boolean;
  uiStyle: 'modern' | 'classic';
  animations: boolean;
  colors: 'vibrant' | 'muted';
}

class GameABIntegration {
  private activeTests: Map<string, ABTestResult> = new Map();
  private gameConfig: GameABConfig | null = null;

  constructor() {
    this.initializeTests();
  }

  /**
   * Инициализация A/B тестов для игры.
   */
  private initializeTests(): void {
    // Запускаем тесты
    const difficultyTest = abTestManager.startTest('difficulty_test');
    const uiTest = abTestManager.startTest('ui_test');
    const mechanicsTest = abTestManager.startTest('mechanics_test');

    // Сохраняем активные тесты
    if (difficultyTest) this.activeTests.set('difficulty_test', difficultyTest);
    if (uiTest) this.activeTests.set('ui_test', uiTest);
    if (mechanicsTest) this.activeTests.set('mechanics_test', mechanicsTest);

    // Генерируем конфигурацию игры на основе A/B тестов
    this.gameConfig = this.generateGameConfig();
  }

  /**
   * Генерация конфигурации игры на основе A/B тестов.
   */
  private generateGameConfig(): GameABConfig {
    const baseConfig: GameABConfig = {
      difficulty: 'medium',
      timeLimit: 20,
      hints: 2,
      powerUps: false,
      specialBlocks: false,
      comboMultiplier: false,
      uiStyle: 'modern',
      animations: true,
      colors: 'vibrant'
    };

    // Применяем конфигурацию из A/B тестов
    const abConfig = abTestManager.getGameConfig();

    if (abConfig.mathDifficulty) {
      baseConfig.difficulty = abConfig.mathDifficulty;
    }

    if (abConfig.timeLimit) {
      baseConfig.timeLimit = abConfig.timeLimit;
    }

    if (abConfig.hints !== undefined) {
      baseConfig.hints = abConfig.hints;
    }

    if (abConfig.powerUps !== undefined) {
      baseConfig.powerUps = abConfig.powerUps;
    }

    if (abConfig.specialBlocks !== undefined) {
      baseConfig.specialBlocks = abConfig.specialBlocks;
    }

    if (abConfig.comboMultiplier !== undefined) {
      baseConfig.comboMultiplier = abConfig.comboMultiplier;
    }

    if (abConfig.uiStyle) {
      baseConfig.uiStyle = abConfig.uiStyle;
    }

    if (abConfig.animations !== undefined) {
      baseConfig.animations = abConfig.animations;
    }

    if (abConfig.colors) {
      baseConfig.colors = abConfig.colors;
    }

    return baseConfig;
  }

  /**
   * Получение конфигурации игры.
   */
  public getGameConfig(): GameABConfig {
    return this.gameConfig || this.generateGameConfig();
  }

  /**
   * Логирование игрового события.
   */
  public logGameEvent(eventType: string, data: Record<string, any> = {}): void {
    for (const [testId] of this.activeTests) {
      abTestManager.logEvent(testId, eventType, data);
    }
  }

  /**
   * Начало игровой сессии.
   */
  public startGameSession(): void {
    this.logGameEvent('game_session_started', {
      config: this.gameConfig
    });
  }

  /**
   * Завершение игровой сессии.
   */
  public endGameSession(metrics: {
    playTime: number;
    levelsCompleted: number;
    score: number;
    errors: number;
  }): void {
    this.logGameEvent('game_session_ended', metrics);

    // Завершаем A/B тесты
    for (const [testId] of this.activeTests) {
      abTestManager.endTest(testId, metrics);
    }
  }

  /**
   * Логирование уровня.
   */
  public logLevelStart(levelNumber: number, levelName: string): void {
    this.logGameEvent('level_started', {
      levelNumber,
      levelName
    });
  }

  /**
   * Логирование завершения уровня.
   */
  public logLevelComplete(levelNumber: number, score: number, timeSpent: number): void {
    this.logGameEvent('level_completed', {
      levelNumber,
      score,
      timeSpent
    });
  }

  /**
   * Логирование ошибки.
   */
  public logError(errorType: string, errorData: Record<string, any> = {}): void {
    this.logGameEvent('error_occurred', {
      errorType,
      ...errorData
    });
  }

  /**
   * Логирование взаимодействия с UI.
   */
  public logUIInteraction(element: string, action: string, data: Record<string, any> = {}): void {
    this.logGameEvent('ui_interaction', {
      element,
      action,
      ...data
    });
  }

  /**
   * Применение стилей UI на основе A/B теста.
   */
  public applyUIStyles(element: HTMLElement): void {
    if (!this.gameConfig) return;

    const { uiStyle, animations, colors } = this.gameConfig;

    // Применяем стили
    if (uiStyle === 'classic') {
      element.classList.add('ui-classic');
      element.classList.remove('ui-modern');
    } else {
      element.classList.add('ui-modern');
      element.classList.remove('ui-classic');
    }

    if (!animations) {
      element.classList.add('no-animations');
    } else {
      element.classList.remove('no-animations');
    }

    if (colors === 'muted') {
      element.classList.add('colors-muted');
      element.classList.remove('colors-vibrant');
    } else {
      element.classList.add('colors-vibrant');
      element.classList.remove('colors-muted');
    }
  }

  /**
   * Проверка, включены ли игровые механики.
   */
  public isFeatureEnabled(feature: keyof GameABConfig): boolean {
    if (!this.gameConfig) return false;
    return Boolean(this.gameConfig[feature]);
  }

  /**
   * Получение значения параметра.
   */
  public getConfigValue<K extends keyof GameABConfig>(key: K): GameABConfig[K] {
    if (!this.gameConfig) {
      // Возвращаем значения по умолчанию
      const defaults: GameABConfig = {
        difficulty: 'medium',
        timeLimit: 20,
        hints: 2,
        powerUps: false,
        specialBlocks: false,
        comboMultiplier: false,
        uiStyle: 'modern',
        animations: true,
        colors: 'vibrant'
      };
      return defaults[key];
    }
    return this.gameConfig[key];
  }

  /**
   * Получение статистики A/B тестов.
   */
  public getTestStatistics(): Record<string, any> {
    return abTestManager.getTestStats();
  }

  /**
   * Экспорт результатов A/B тестов.
   */
  public exportTestResults(): string {
    return abTestManager.exportResults();
  }

  /**
   * Включение/отключение A/B тестирования.
   */
  public setABTestingEnabled(enabled: boolean): void {
    abTestManager.setEnabled(enabled);

    if (enabled) {
      this.initializeTests();
    } else {
      this.activeTests.clear();
      this.gameConfig = null;
    }
  }

  /**
   * Проверка, активно ли A/B тестирование.
   */
  public isABTestingActive(): boolean {
    return this.activeTests.size > 0;
  }

  /**
   * Получение информации об активных тестах.
   */
  public getActiveTests(): Array<{ testId: string; variantId: string }> {
    return Array.from(this.activeTests.entries()).map(([testId, test]) => ({
      testId,
      variantId: test.variantId
    }));
  }
}

// Глобальный экземпляр интеграции A/B тестов
export const gameABIntegration = new GameABIntegration();

// Экспорт типов
export type { GameABConfig };
