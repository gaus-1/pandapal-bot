import { Level } from '../levels/Level';
import { GymLevel } from '../levels/GymLevel';
import { ClassroomLevel } from '../levels/ClassroomLevel';
import { CanteenLevel } from '../levels/CanteenLevel';
import { PlaygroundLevel } from '../levels/PlaygroundLevel';
import { LibraryLevel } from '../levels/LibraryLevel';
import { CollisionDetector } from '../physics/Collision';
import { GameStateManager, GameStatus } from './GameState';
import { PandaMessages } from '../utils/PandaMessages';

/**
 * Главный класс игры
 * Single Responsibility: управление игровым циклом и координация всех систем
 */
export class Game {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private levels: Level[];
  private currentLevel: Level | null = null;
  private stateManager: GameStateManager;
  private lastTime: number = 0;
  private animationId: number | null = null;
  private isRunning: boolean = false;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Failed to get 2D context');
    }
    this.ctx = ctx;

    this.stateManager = new GameStateManager();
    this.levels = this.initializeLevels();

    this.setupEventListeners();
    this.resize();
  }

  /**
   * Инициализация всех уровней
   */
  private initializeLevels(): Level[] {
    const width = this.canvas.width;
    const height = this.canvas.height;

    return [
      new GymLevel(width, height),
      new ClassroomLevel(width, height),
      new CanteenLevel(width, height),
      new PlaygroundLevel(width, height),
      new LibraryLevel(width, height),
    ];
  }

  /**
   * Установка обработчиков событий
   */
  private setupEventListeners(): void {
    // Движение мыши
    this.canvas.addEventListener('mousemove', (e) => {
      if (this.stateManager.getStatus() === GameStatus.PLAYING && this.currentLevel) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        this.currentLevel.getPaddle().setTargetX(x, this.canvas.width);
      }
    });

    // Тач-события для мобильных
    this.canvas.addEventListener('touchmove', (e) => {
      e.preventDefault();
      if (this.stateManager.getStatus() === GameStatus.PLAYING && this.currentLevel) {
        const rect = this.canvas.getBoundingClientRect();
        const touch = e.touches[0];
        const x = touch.clientX - rect.left;
        this.currentLevel.getPaddle().setTargetX(x, this.canvas.width);
      }
    });

    // Пауза на пробел
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') {
        this.togglePause();
      }
    });

    // Ресайз окна
    window.addEventListener('resize', () => this.resize());
  }

  /**
   * Адаптивный ресайз canvas
   */
  private resize(): void {
    const container = this.canvas.parentElement;
    if (!container) return;

    const width = Math.min(container.clientWidth, 800);
    const height = Math.min(container.clientHeight, 600);

    this.canvas.width = width;
    this.canvas.height = height;

    // Пересоздаем уровни с новыми размерами
    if (this.currentLevel) {
      const levelIndex = this.stateManager.getCurrentLevel();
      this.levels = this.initializeLevels();
      this.currentLevel = this.levels[levelIndex];
    }
  }

  /**
   * Запуск игры
   */
  start(): void {
    if (this.isRunning) return;

    this.stateManager.startNewGame();
    this.currentLevel = this.levels[0];
    this.isRunning = true;
    this.lastTime = performance.now();
    this.gameLoop(this.lastTime);
  }

  /**
   * Остановка игры
   */
  stop(): void {
    this.isRunning = false;
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  /**
   * Пауза/Продолжить
   */
  togglePause(): void {
    if (this.stateManager.getStatus() === GameStatus.PLAYING ||
        this.stateManager.getStatus() === GameStatus.PAUSED) {
      this.stateManager.togglePause();
    }
  }

  /**
   * Следующий уровень
   */
  nextLevel(): void {
    this.stateManager.nextLevel();
    const levelIndex = this.stateManager.getCurrentLevel();

    if (levelIndex < this.levels.length) {
      this.currentLevel = this.levels[levelIndex];
      this.stateManager.setStatus(GameStatus.PLAYING);
    }
  }

  /**
   * Рестарт уровня
   */
  restartLevel(): void {
    if (this.currentLevel) {
      this.currentLevel.reset();
      this.stateManager.setStatus(GameStatus.PLAYING);
    }
  }

  /**
   * Главный игровой цикл
   */
  private gameLoop(currentTime: number): void {
    if (!this.isRunning) return;

    const deltaTime = currentTime - this.lastTime;
    this.lastTime = currentTime;

    // Обновление и отрисовка
    this.update(deltaTime);
    this.render();

    // Следующий кадр
    this.animationId = requestAnimationFrame((time) => this.gameLoop(time));
  }

  /**
   * Обновление состояния игры
   */
  private update(deltaTime: number): void {
    const status = this.stateManager.getStatus();

    // Обновляем только если игра активна
    if (status !== GameStatus.PLAYING || !this.currentLevel) {
      return;
    }

    // Обновляем уровень
    this.currentLevel.update(deltaTime);

    // Проверяем столкновения
    this.checkCollisions();

    // Проверяем завершение уровня
    if (this.currentLevel.isLevelComplete()) {
      const score = this.currentLevel.getScore();
      this.stateManager.completeLevel(score);
    }

    // Проверяем потерю мяча
    const ball = this.currentLevel.getBall();
    if (ball.y > this.canvas.height) {
      this.stateManager.loseLife();
      if (this.stateManager.getLives() > 0) {
        this.restartLevel();
      }
    }
  }

  /**
   * Проверка всех столкновений
   */
  private checkCollisions(): void {
    if (!this.currentLevel) return;

    const ball = this.currentLevel.getBall();
    const paddle = this.currentLevel.getPaddle();
    const bricks = this.currentLevel.getBricks();
    const particles = this.currentLevel.getParticles();

    // Столкновение со стенами
    const walls = CollisionDetector.checkBallWalls(
      ball,
      this.canvas.width,
      this.canvas.height
    );

    if (walls.left || walls.right) {
      ball.bounceX();
    }

    if (walls.top) {
      ball.bounceY();
    }

    // Столкновение с платформой
    const paddleCollision = CollisionDetector.checkBallPaddle(ball, paddle);
    if (paddleCollision.collided) {
      CollisionDetector.resolveBallPaddleCollision(ball, paddle);
      ball.increaseSpeed(1.02); // Немного ускоряем мяч
    }

    // Столкновение с кирпичами
    for (const brick of bricks) {
      if (!brick.active) continue;

      const brickCollision = CollisionDetector.checkBallBrick(ball, brick);
      if (brickCollision.collided && brickCollision.normal) {
        CollisionDetector.resolveBallCollision(ball, brickCollision.normal);

        const destroyed = brick.hit();
        if (destroyed) {
          // Создаем эффект частиц
          const center = brick.getCenter();
          const colorScheme = this.currentLevel.getColorScheme();
          particles.createExplosion(
            center.x,
            center.y,
            15,
            colorScheme.particle,
            0.5
          );
        }

        // Только одно столкновение за кадр
        break;
      }
    }
  }

  /**
   * Отрисовка
   */
  private render(): void {
    // Очистка canvas
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    const status = this.stateManager.getStatus();

    if (status === GameStatus.MENU) {
      this.renderMenu();
    } else if (status === GameStatus.PLAYING || status === GameStatus.PAUSED) {
      this.renderGame();
      if (status === GameStatus.PAUSED) {
        this.renderPause();
      }
    } else if (status === GameStatus.LEVEL_COMPLETE) {
      this.renderLevelComplete();
    } else if (status === GameStatus.GAME_OVER) {
      this.renderGameOver();
    }
  }

  /**
   * Отрисовка игры
   */
  private renderGame(): void {
    if (!this.currentLevel) return;

    // Рендерим уровень
    this.currentLevel.render(this.ctx);

    // Рендерим UI
    this.renderUI();
  }

  /**
   * Отрисовка UI
   */
  private renderUI(): void {
    const state = this.stateManager.getState();

    // Очки
    this.ctx.fillStyle = '#2D3748';
    this.ctx.font = 'bold 24px Arial';
    this.ctx.textAlign = 'left';
    this.ctx.fillText(`Очки: ${state.totalScore}`, 20, 35);

    // Жизни
    this.ctx.textAlign = 'right';
    this.ctx.fillText(`❤️ ${state.lives}`, this.canvas.width - 20, 35);

    // Уровень
    this.ctx.textAlign = 'center';
    this.ctx.font = 'bold 20px Arial';
    this.ctx.fillText(
      `Уровень ${state.currentLevel + 1}/${state.totalLevels}`,
      this.canvas.width / 2,
      35
    );
  }

  /**
   * Отрисовка меню
   */
  private renderMenu(): void {
    // Градиентный фон
    const gradient = this.ctx.createLinearGradient(
      0,
      0,
      0,
      this.canvas.height
    );
    gradient.addColorStop(0, '#E8F4F8');
    gradient.addColorStop(1, '#A8D8EA');
    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Название игры
    this.ctx.fillStyle = '#2D3748';
    this.ctx.font = 'bold 48px Arial';
    this.ctx.textAlign = 'center';
    this.ctx.fillText('PandaPal Go', this.canvas.width / 2, this.canvas.height / 3);

    // Подзаголовок
    this.ctx.font = '24px Arial';
    this.ctx.fillStyle = '#4A5568';
    this.ctx.fillText(
      'Школьная головоломка',
      this.canvas.width / 2,
      this.canvas.height / 3 + 50
    );

    // Кнопка старт
    this.ctx.fillStyle = '#48BB78';
    this.ctx.beginPath();
    this.ctx.roundRect(
      this.canvas.width / 2 - 100,
      this.canvas.height / 2,
      200,
      60,
      10
    );
    this.ctx.fill();

    this.ctx.fillStyle = '#FFFFFF';
    this.ctx.font = 'bold 28px Arial';
    this.ctx.fillText('Начать игру', this.canvas.width / 2, this.canvas.height / 2 + 40);

    // Рекорд
    const highScore = this.stateManager.getHighScore();
    if (highScore > 0) {
      this.ctx.fillStyle = '#718096';
      this.ctx.font = '20px Arial';
      this.ctx.fillText(
        `Рекорд: ${highScore}`,
        this.canvas.width / 2,
        this.canvas.height / 2 + 120
      );
    }
  }

  /**
   * Отрисовка паузы
   */
  private renderPause(): void {
    // Полупрозрачный оверлей
    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Текст паузы
    this.ctx.fillStyle = '#FFFFFF';
    this.ctx.font = 'bold 48px Arial';
    this.ctx.textAlign = 'center';
    this.ctx.fillText('ПАУЗА', this.canvas.width / 2, this.canvas.height / 2);

    this.ctx.font = '24px Arial';
    this.ctx.fillText(
      'Нажми ПРОБЕЛ для продолжения',
      this.canvas.width / 2,
      this.canvas.height / 2 + 50
    );
  }

  /**
   * Отрисовка завершения уровня
   */
  private renderLevelComplete(): void {
    if (!this.currentLevel) return;

    this.currentLevel.render(this.ctx);

    // Оверлей
    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Доска (школьная доска для текста)
    const boardWidth = this.canvas.width * 0.8;
    const boardHeight = this.canvas.height * 0.5;
    const boardX = (this.canvas.width - boardWidth) / 2;
    const boardY = (this.canvas.height - boardHeight) / 2;

    // Рисуем доску
    this.ctx.fillStyle = '#2D5016';
    this.ctx.fillRect(boardX, boardY, boardWidth, boardHeight);
    this.ctx.strokeStyle = '#8B4513';
    this.ctx.lineWidth = 8;
    this.ctx.strokeRect(boardX, boardY, boardWidth, boardHeight);

    // Сообщение от панды
    const levelIndex = this.stateManager.getCurrentLevel();
    const pandaMessage = PandaMessages.getLevelMessage(levelIndex);

    // Рисуем текст "мелом" на доске
    this.ctx.fillStyle = '#FFFFFF';
    this.ctx.font = 'bold 36px Arial';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';

    // Разбиваем сообщение на строки
    const lines = pandaMessage.split('\n');
    const lineHeight = 50;
    const startY = this.canvas.height / 2 - ((lines.length - 1) * lineHeight) / 2;

    lines.forEach((line, index) => {
      this.ctx.fillText(line, this.canvas.width / 2, startY + index * lineHeight);
    });

    // Очки внизу доски
    this.ctx.font = '28px Arial';
    this.ctx.fillStyle = '#FFD700';
    this.ctx.fillText(
      `Очки: ${this.currentLevel.getScore()}`,
      this.canvas.width / 2,
      boardY + boardHeight - 40
    );
  }

  /**
   * Отрисовка game over
   */
  private renderGameOver(): void {
    // Градиентный фон
    const gradient = this.ctx.createLinearGradient(
      0,
      0,
      0,
      this.canvas.height
    );
    gradient.addColorStop(0, '#FFF0E0');
    gradient.addColorStop(1, '#FFB4A2');
    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    const state = this.stateManager.getState();
    const isWin = state.currentLevel >= state.totalLevels;

    // Доска для финального сообщения
    const boardWidth = this.canvas.width * 0.85;
    const boardHeight = this.canvas.height * 0.6;
    const boardX = (this.canvas.width - boardWidth) / 2;
    const boardY = (this.canvas.height - boardHeight) / 2;

    // Рисуем доску
    this.ctx.fillStyle = '#2D5016';
    this.ctx.fillRect(boardX, boardY, boardWidth, boardHeight);
    this.ctx.strokeStyle = '#8B4513';
    this.ctx.lineWidth = 10;
    this.ctx.strokeRect(boardX, boardY, boardWidth, boardHeight);

    // Сообщение от панды
    this.ctx.fillStyle = '#FFFFFF';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';

    if (isWin) {
      // Победное сообщение
      const victoryMessage = PandaMessages.getVictoryMessage();
      const lines = victoryMessage.split('\n');
      this.ctx.font = 'bold 42px Arial';
      const lineHeight = 60;
      const startY = this.canvas.height / 2 - ((lines.length - 1) * lineHeight) / 2 - 30;

      lines.forEach((line, index) => {
        this.ctx.fillText(line, this.canvas.width / 2, startY + index * lineHeight);
      });
    } else {
      // Сообщение поддержки
      const encouragement = PandaMessages.getEncouragementMessage();
      this.ctx.font = 'bold 40px Arial';
      this.ctx.fillText(encouragement, this.canvas.width / 2, this.canvas.height / 2 - 40);
    }

    // Итоговые очки
    this.ctx.font = '32px Arial';
    this.ctx.fillStyle = '#FFD700';
    this.ctx.fillText(
      `Всего очков: ${state.totalScore}`,
      this.canvas.width / 2,
      boardY + boardHeight - 60
    );

    // Рекорд
    if (state.totalScore >= state.highScore && state.highScore > 0) {
      this.ctx.fillStyle = '#FFD700';
      this.ctx.font = 'bold 24px Arial';
      this.ctx.fillText(
        '⭐ Новый рекорд! ⭐',
        this.canvas.width / 2,
        boardY + boardHeight - 20
      );
    }
  }

  /**
   * Получить состояние игры
   */
  getState(): GameStateManager {
    return this.stateManager;
  }
}
