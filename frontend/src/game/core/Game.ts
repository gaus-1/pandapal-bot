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
   * Установка обработчиков событий с улучшенной мобильной поддержкой
   */
  private setupEventListeners(): void {
    // Движение мыши (десктоп)
    this.canvas.addEventListener('mousemove', (e) => {
      if (this.stateManager.getStatus() === GameStatus.PLAYING && this.currentLevel) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const x = (e.clientX - rect.left) * scaleX;
        this.currentLevel.getPaddle().setTargetX(x, this.canvas.width);
      }
    });

    // Улучшенные тач-события для мобильных
    let isTouching = false;

    this.canvas.addEventListener('touchstart', (e) => {
      e.preventDefault();
      isTouching = true;

      const rect = this.canvas.getBoundingClientRect();
      const touch = e.touches[0];
      const scaleX = this.canvas.width / rect.width;
      const x = (touch.clientX - rect.left) * scaleX;

      if (this.stateManager.getStatus() === GameStatus.PLAYING && this.currentLevel) {
        this.currentLevel.getPaddle().setTargetX(x, this.canvas.width);
      } else if (this.stateManager.getStatus() === GameStatus.MENU) {
        this.startGame();
      } else if (this.stateManager.getStatus() === GameStatus.PAUSED) {
        this.togglePause();
      }
    }, { passive: false });

    this.canvas.addEventListener('touchmove', (e) => {
      e.preventDefault();
      if (isTouching && this.stateManager.getStatus() === GameStatus.PLAYING && this.currentLevel) {
        const rect = this.canvas.getBoundingClientRect();
        const touch = e.touches[0];
        const scaleX = this.canvas.width / rect.width;
        const x = (touch.clientX - rect.left) * scaleX;
        this.currentLevel.getPaddle().setTargetX(x, this.canvas.width);
      }
    }, { passive: false });

    this.canvas.addEventListener('touchend', (e) => {
      e.preventDefault();
      isTouching = false;
    }, { passive: false });

    // Предотвращаем прокрутку страницы при игре
    this.canvas.addEventListener('touchcancel', (e) => {
      e.preventDefault();
      isTouching = false;
    }, { passive: false });

    // Клик для десктопа (старт игры и пауза)
    this.canvas.addEventListener('click', (e) => {
      // Предотвращаем клик если это было касание
      if (e.detail === 0) return; // Это был программный клик от touch события

      const status = this.stateManager.getStatus();
      if (status === GameStatus.MENU) {
        this.startGame();
      } else if (status === GameStatus.PAUSED) {
        this.togglePause();
      }
    });

    // Пауза на пробел (только для десктопа)
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') {
        e.preventDefault();
        this.togglePause();
      }
    });

    // Ресайз окна
    window.addEventListener('resize', () => this.resize());
  }

  /**
   * Адаптивный ресайз canvas с поддержкой высокого разрешения
   */
  private resize(): void {
    const container = this.canvas.parentElement;
    if (!container) return;

    // Определяем оптимальные размеры для устройства
    const isMobile = window.innerWidth <= 768;
    const isTablet = window.innerWidth <= 1024;

    let targetWidth: number;
    let targetHeight: number;

    if (isMobile) {
      // Мобильные устройства - портретная ориентация
      targetWidth = Math.min(container.clientWidth - 32, 400); // 32px для отступов
      targetHeight = Math.min(targetWidth * 1.6, window.innerHeight * 0.7); // 16:10 соотношение
    } else if (isTablet) {
      // Планшеты
      targetWidth = Math.min(container.clientWidth - 48, 800);
      targetHeight = Math.min(targetWidth * 0.75, window.innerHeight * 0.8);
    } else {
      // Десктоп - КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ограничиваем высоту окном браузера
      targetWidth = Math.min(container.clientWidth - 64, 1200);
      // Ограничиваем высоту 70% от высоты окна браузера для гарантированной видимости
      targetHeight = Math.min(targetWidth * 0.75, window.innerHeight * 0.7);
    }

    // КРИТИЧЕСКАЯ ОТЛАДКА: Выводим размеры canvas
    console.log(`🎮 CANVAS DEBUG: targetWidth=${targetWidth}, targetHeight=${targetHeight}, window=${window.innerWidth}x${window.innerHeight}`);

    // Устанавливаем размеры canvas
    this.canvas.width = targetWidth;
    this.canvas.height = targetHeight;

    // Настройка высокого разрешения для четкой графики
    const devicePixelRatio = window.devicePixelRatio || 1;

    // Устанавливаем внутреннее разрешение
    this.canvas.width = targetWidth * devicePixelRatio;
    this.canvas.height = targetHeight * devicePixelRatio;

    // Масштабируем для отображения
    this.canvas.style.width = targetWidth + 'px';
    this.canvas.style.height = targetHeight + 'px';

    // Масштабируем контекст для четкости
    this.ctx.scale(devicePixelRatio, devicePixelRatio);

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
   * Запуск игры (алиас для совместимости)
   */
  startGame(): void {
    this.start();
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
      // Принудительное разделение (предотвращает застревание)
      CollisionDetector.separateBallFromPaddle(ball, paddle);

      // Обработка отскока от платформы
      CollisionDetector.resolveBallPaddleCollision(ball, paddle);
      ball.increaseSpeed(1.02); // Немного ускоряем мяч
    }

    // Столкновение с кирпичами
    for (const brick of bricks) {
      if (!brick.active) continue;

      const brickCollision = CollisionDetector.checkBallBrick(ball, brick);
      if (brickCollision.collided && brickCollision.normal) {
        // Принудительное разделение (предотвращает застревание)
        CollisionDetector.separateBallFromBrick(ball, brick);

        // Отскок от кирпича
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
    } else if (status === GameStatus.TRANSITION) {
      this.renderLevelTransition();
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
   * Отрисовка UI с адаптивными размерами
   */
  private renderUI(): void {
    const state = this.stateManager.getState();
    const isMobile = window.innerWidth <= 768;
    const baseFontSize = isMobile ? Math.max(16, this.canvas.width * 0.04) : Math.max(20, this.canvas.width * 0.025);

    // Фон для UI элементов для лучшей читаемости
    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
    this.ctx.fillRect(0, 0, this.canvas.width, 60);

    // Очки
    this.ctx.fillStyle = '#FFFFFF';
    this.ctx.font = `bold ${baseFontSize}px Arial`;
    this.ctx.textAlign = 'left';
    this.ctx.fillText(`Очки: ${state.totalScore}`, 15, 35);

    // Жизни
    this.ctx.textAlign = 'right';
    this.ctx.fillText(`❤️ ${state.lives}`, this.canvas.width - 15, 35);

    // Уровень
    this.ctx.textAlign = 'center';
    this.ctx.font = `bold ${baseFontSize * 0.9}px Arial`;
    this.ctx.fillStyle = '#FFD700';
    this.ctx.fillText(
      `Уровень ${state.currentLevel + 1}/${state.totalLevels}`,
      this.canvas.width / 2,
      35
    );
  }

  /**
   * Отрисовка меню с адаптивным дизайном
   */
  private renderMenu(): void {
    const isMobile = window.innerWidth <= 768;

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

    // Адаптивные размеры шрифтов
    const titleFontSize = isMobile ? Math.max(32, this.canvas.width * 0.08) : Math.max(48, this.canvas.width * 0.06);
    const subtitleFontSize = isMobile ? Math.max(18, this.canvas.width * 0.045) : Math.max(24, this.canvas.width * 0.03);
    const buttonFontSize = isMobile ? Math.max(20, this.canvas.width * 0.05) : Math.max(28, this.canvas.width * 0.035);

    // Название игры
    this.ctx.fillStyle = '#2D3748';
    this.ctx.font = `bold ${titleFontSize}px Arial`;
    this.ctx.textAlign = 'center';
    this.ctx.fillText('🎮 PandaPal Go', this.canvas.width / 2, this.canvas.height / 3);

    // Подзаголовок
    this.ctx.font = `${subtitleFontSize}px Arial`;
    this.ctx.fillStyle = '#4A5568';
    this.ctx.fillText(
      'Школьная головоломка',
      this.canvas.width / 2,
      this.canvas.height / 3 + (isMobile ? 40 : 50)
    );

    // Кнопка старт с адаптивным размером
    const buttonWidth = isMobile ? this.canvas.width * 0.7 : 200;
    const buttonHeight = isMobile ? 50 : 60;
    const buttonX = this.canvas.width / 2 - buttonWidth / 2;
    const buttonY = this.canvas.height / 2;

    this.ctx.fillStyle = '#48BB78';
    this.ctx.beginPath();
    this.ctx.roundRect(buttonX, buttonY, buttonWidth, buttonHeight, 10);
    this.ctx.fill();

    this.ctx.fillStyle = '#FFFFFF';
    this.ctx.font = `bold ${buttonFontSize}px Arial`;
    this.ctx.fillText('Начать игру', this.canvas.width / 2, buttonY + buttonHeight / 2 + 8);

    // Рекорд
    const highScore = this.stateManager.getHighScore();
    if (highScore > 0) {
      this.ctx.fillStyle = '#718096';
      this.ctx.font = `${Math.max(16, this.canvas.width * 0.025)}px Arial`;
      this.ctx.fillText(
        `🏆 Рекорд: ${highScore}`,
        this.canvas.width / 2,
        buttonY + buttonHeight + 40
      );
    }

    // Подсказки для управления (адаптивные)
    this.ctx.fillStyle = '#4A5568';
    const hintFontSize = isMobile ? Math.max(14, this.canvas.width * 0.035) : Math.max(18, this.canvas.width * 0.022);
    this.ctx.font = `${hintFontSize}px Arial`;

    const startY = buttonY + buttonHeight + (highScore > 0 ? 80 : 40);
    const lineHeight = isMobile ? 25 : 30;

    if (isMobile) {
      this.ctx.fillText(
        '📱 Двигай пальцем для управления',
        this.canvas.width / 2,
        startY
      );
      this.ctx.fillText(
        '⏸️ Тап для паузы',
        this.canvas.width / 2,
        startY + lineHeight
      );
    } else {
      this.ctx.fillText(
        '💻 На компьютере: двигай мышью',
        this.canvas.width / 2,
        startY
      );
      this.ctx.fillText(
        '📱 На телефоне: двигай пальцем',
        this.canvas.width / 2,
        startY + lineHeight
      );
      this.ctx.fillText(
        '⏸️ Пробел или тап - пауза',
        this.canvas.width / 2,
        startY + lineHeight * 2
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
   * Отрисовка перехода между уровнями с улучшенным дизайном
   */
  private renderLevelTransition(): void {
    // Оверлей с градиентом
    const gradient = this.ctx.createRadialGradient(
      this.canvas.width / 2,
      this.canvas.height / 2,
      0,
      this.canvas.width / 2,
      this.canvas.height / 2,
      Math.max(this.canvas.width, this.canvas.height) / 2
    );
    gradient.addColorStop(0, 'rgba(0, 0, 0, 0.6)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0.9)');

    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Анимированное сообщение о переходе
    const state = this.stateManager.getState();
    const nextLevelNumber = state.currentLevel + 1;

    this.ctx.fillStyle = '#FFFFFF';
    this.ctx.font = `bold ${Math.max(24, this.canvas.width * 0.04)}px Arial`;
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';

    // Основное сообщение
    this.ctx.fillText(
      '🎉 Отличная работа! 🎉',
      this.canvas.width / 2,
      this.canvas.height / 2 - 40
    );

    // Информация о следующем уровне
    this.ctx.font = `bold ${Math.max(20, this.canvas.width * 0.03)}px Arial`;
    this.ctx.fillStyle = '#FFD700';
    this.ctx.fillText(
      `Переходим к уровню ${nextLevelNumber}...`,
      this.canvas.width / 2,
      this.canvas.height / 2 + 20
    );

    // Автоматически переходим на следующий уровень
    setTimeout(() => {
      this.nextLevel();
    }, 2000); // 2 секунды на показ перехода
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
