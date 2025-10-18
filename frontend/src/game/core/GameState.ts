/**
 * Состояние игры
 * Centralized state management для игры
 */

export const GameStatus = {
  MENU: 'menu',
  PLAYING: 'playing',
  PAUSED: 'paused',
  LEVEL_COMPLETE: 'level_complete',
  GAME_OVER: 'game_over',
  TRANSITION: 'transition',
} as const;

export type GameStatus = typeof GameStatus[keyof typeof GameStatus];

export interface GameState {
  currentLevel: number;
  totalLevels: number;
  status: GameStatus;
  lives: number;
  totalScore: number;
  highScore: number;
}

export class GameStateManager {
  private state: GameState;
  private readonly MAX_LIVES = 3;
  private readonly TOTAL_LEVELS = 5;

  constructor() {
    this.state = this.getInitialState();
    this.loadHighScore();
  }

  private getInitialState(): GameState {
    return {
      currentLevel: 0,
      totalLevels: this.TOTAL_LEVELS,
      status: GameStatus.MENU,
      lives: this.MAX_LIVES,
      totalScore: 0,
      highScore: 0,
    };
  }

  /**
   * Загрузка рекорда из localStorage
   */
  private loadHighScore(): void {
    const saved = localStorage.getItem('pandapal_go_highscore');
    if (saved) {
      this.state.highScore = parseInt(saved, 10);
    }
  }

  /**
   * Сохранение рекорда
   */
  private saveHighScore(): void {
    if (this.state.totalScore > this.state.highScore) {
      this.state.highScore = this.state.totalScore;
      localStorage.setItem(
        'pandapal_go_highscore',
        this.state.highScore.toString()
      );
    }
  }

  /**
   * Геттеры
   */
  getState(): GameState {
    return { ...this.state };
  }

  getCurrentLevel(): number {
    return this.state.currentLevel;
  }

  getStatus(): GameStatus {
    return this.state.status;
  }

  getLives(): number {
    return this.state.lives;
  }

  getTotalScore(): number {
    return this.state.totalScore;
  }

  getHighScore(): number {
    return this.state.highScore;
  }

  /**
   * Сеттеры
   */
  setStatus(status: GameStatus): void {
    this.state.status = status;
  }

  /**
   * Начать новую игру
   */
  startNewGame(): void {
    this.state = {
      ...this.getInitialState(),
      highScore: this.state.highScore,
    };
    this.state.status = GameStatus.PLAYING;
  }

  /**
   * Следующий уровень
   */
  nextLevel(): void {
    this.state.currentLevel++;
    if (this.state.currentLevel >= this.TOTAL_LEVELS) {
      this.state.status = GameStatus.GAME_OVER;
      this.saveHighScore();
    } else {
      this.state.status = GameStatus.TRANSITION;
    }
  }

  /**
   * Потеря жизни
   */
  loseLife(): void {
    this.state.lives--;
    if (this.state.lives <= 0) {
      this.state.status = GameStatus.GAME_OVER;
      this.saveHighScore();
    }
  }

  /**
   * Добавить очки
   */
  addScore(points: number): void {
    this.state.totalScore += points;
    this.saveHighScore();
  }

  /**
   * Пауза/Продолжить
   */
  togglePause(): void {
    if (this.state.status === GameStatus.PLAYING) {
      this.state.status = GameStatus.PAUSED;
    } else if (this.state.status === GameStatus.PAUSED) {
      this.state.status = GameStatus.PLAYING;
    }
  }

  /**
   * Завершить уровень
   */
  completeLevel(levelScore: number): void {
    this.addScore(levelScore);
    this.state.status = GameStatus.LEVEL_COMPLETE;
    // Автоматически переходим на следующий уровень через небольшую задержку
    setTimeout(() => {
      this.nextLevel();
    }, 2000); // 2 секунды на показ сообщения
  }

  /**
   * Сброс игры
   */
  reset(): void {
    const highScore = this.state.highScore;
    this.state = this.getInitialState();
    this.state.highScore = highScore;
  }
}
