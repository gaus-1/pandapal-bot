import { Brick } from '../entities/Brick';
import { Ball } from '../entities/Ball';
import { Paddle } from '../entities/Paddle';
import { ParticleSystem } from '../entities/Particle';
import { MathProblems } from '../utils/MathProblems';
import type { ColorScheme } from '../utils/ColorPalette';
import { ColorPalette } from '../utils/ColorPalette';
import type { Game } from '../core/Game';

/**
 * Базовый класс для уровня
 * Open/Closed Principle: открыт для расширения, закрыт для модификации
 */
export abstract class Level {
  protected bricks: Brick[] = [];
  protected ball: Ball;
  protected paddle: Paddle;
  protected particles: ParticleSystem;
  protected score: number = 0;
  protected colorScheme: ColorScheme;
  protected isComplete: boolean = false;

  constructor(protected game: Game) {
    console.log('🚧 Level Constructor Called!');
    this.colorScheme = this.initColorScheme();
    this.particles = new ParticleSystem();

    // Создаем базовые объекты
    console.log('🎯 Creating paddle...');
    this.paddle = this.createPaddle();
    console.log('⚽ Creating ball...');
    this.ball = this.createBall();
    console.log('🧱 Creating bricks...');
    this.bricks = this.createBricks();
    console.log('✅ Level Constructor Complete!');
  }

  /**
   * Получить цветовую схему уровня (должен быть переопределен в наследниках)
   */
  protected abstract initColorScheme(): ColorScheme;

  /**
   * Получить название уровня (должен быть переопределен)
   */
  abstract getLevelName(): string;

  /**
   * Получить описание уровня (должен быть переопределен)
   */
  abstract getLevelDescription(): string;

  /**
   * Получить сложность математических примеров
   */
  protected abstract getMathDifficulty(): number;

  /**
   * Создать расположение кирпичей (должен быть переопределен)
   */
  protected abstract createBricksLayout(): Array<{
    x: number;
    y: number;
    hits: number;
  }>;

  /**
   * Создание платформы
   */
  protected createPaddle(): Paddle {
    // Адаптивная ширина платформы - ИСПРАВЛЕНИЕ: используем актуальные размеры Canvas
    const paddleWidth = Math.max(80, this.game.canvas.width * 0.18);
    const paddleHeight = Math.max(16, this.game.canvas.width * 0.025);
    const paddleX = (this.game.canvas.width - paddleWidth) / 2;

    // КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Платформа должна быть ВСЕГДА видна
    // Используем window.innerWidth для более точного определения
    const isMobile = window.innerWidth <= 768;
    const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;

    let paddleY: number;
    if (isMobile) {
      paddleY = this.game.canvas.height - 60;  // Мобильные: отступ 60px от низа
    } else if (isTablet) {
      paddleY = this.game.canvas.height - 70;  // Планшеты: отступ 70px от низа
    } else {
      paddleY = this.game.canvas.height - 80;  // Десктопы: отступ 80px от низа - ГАРАНТИРОВАННО ВИДНА!
    }

    // Отладочная информация в консоль - ИСПРАВЛЕНИЕ: используем актуальные размеры
    console.log(`🔧 Paddle Debug: canvas=${this.game.canvas.width}x${this.game.canvas.height}, window=${window.innerWidth}x${window.innerHeight}, paddleY=${paddleY}`);

    return new Paddle(paddleX, paddleY, paddleWidth, paddleHeight);
  }

  /**
   * Создание мяча
   */
  protected createBall(): Ball {
    // Адаптивный размер мяча в зависимости от размера экрана - ИСПРАВЛЕНИЕ: используем актуальные размеры
    const baseRadius = Math.max(12, Math.min(20, this.game.canvas.width * 0.02));
    const x = this.game.canvas.width / 2 - baseRadius;

    // КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Мяч должен быть ВЫШЕ платформы
    const isMobile = window.innerWidth <= 768;
    const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;

    let y: number;
    if (isMobile) {
      y = this.game.canvas.height - 100;  // Мобильные: выше платформы (60px от низа)
    } else if (isTablet) {
      y = this.game.canvas.height - 110;  // Планшеты: выше платформы (70px от низа)
    } else {
      y = this.game.canvas.height - 120;  // Десктопы: выше платформы (80px от низа)
    }

    // Отладочная информация в консоль - ИСПРАВЛЕНИЕ: используем актуальные размеры
    console.log(`⚽ Ball Debug: canvas=${this.game.canvas.width}x${this.game.canvas.height}, ballY=${y}`);

    const speed = 0.5; // Немного быстрее для лучшего геймплея

    return new Ball(x, y, baseRadius, speed, this.colorScheme);
  }

  /**
   * Создание кирпичей
   */
  protected createBricks(): Brick[] {
    const layout = this.createBricksLayout();
    const difficulty = this.getMathDifficulty();
    const problems = MathProblems.generateSet(layout.length, difficulty);

    return layout.map((brick, index) => {
      // Адаптивные размеры кирпичей
      const brickWidth = Math.max(60, this.canvasWidth * 0.14);
      const brickHeight = Math.max(24, this.canvasWidth * 0.03);

      return new Brick(
        brick.x,
        brick.y,
        brickWidth,
        brickHeight,
        problems[index],
        this.colorScheme,
        brick.hits
      );
    });
  }

  /**
   * Обработка разрушения кирпича
   */
  protected onBrickDestroyed(brick: Brick): void {
    const center = brick.getCenter();
    this.particles.createExplosion(
      center.x,
      center.y,
      12,
      this.colorScheme.particle,
      0.4
    );

    this.score += brick.getPoints();

    // Проверяем завершение уровня
    if (this.bricks.filter((b) => b.active).length === 0) {
      this.isComplete = true;
    }
  }

  /**
   * Геттеры
   */
  getBricks(): Brick[] {
    return this.bricks;
  }

  getBall(): Ball {
    return this.ball;
  }

  getPaddle(): Paddle {
    return this.paddle;
  }

  getParticles(): ParticleSystem {
    return this.particles;
  }

  getScore(): number {
    return this.score;
  }

  public getColorScheme(): ColorScheme {
    return this.colorScheme;
  }

  isLevelComplete(): boolean {
    return this.isComplete;
  }

  /**
   * Обновление уровня
   */
  update(deltaTime: number): void {
    this.paddle.update(deltaTime);
    this.ball.update(deltaTime);
    this.bricks.forEach((brick) => brick.update(deltaTime));
    this.particles.update(deltaTime);
  }

  /**
   * Отрисовка фона уровня (может быть переопределена)
   */
  protected renderBackground(ctx: CanvasRenderingContext2D): void {
    // Градиентный фон - ИСПРАВЛЕНИЕ: используем актуальные размеры
    const gradient = ctx.createLinearGradient(
      0,
      0,
      0,
      this.game.canvas.height
    );
    gradient.addColorStop(0, this.colorScheme.background);
    gradient.addColorStop(1, ColorPalette.withAlpha(this.colorScheme.primary, 0.3));

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, this.game.canvas.width, this.game.canvas.height);
  }

  /**
   * Отрисовка уровня
   */
  render(ctx: CanvasRenderingContext2D): void {
    console.log('🎨 Level Render Called!');
    this.renderBackground(ctx);
    this.bricks.forEach((brick) => brick.render(ctx));
    this.particles.render(ctx);
    console.log('🎯 Rendering paddle...');
    this.paddle.render(ctx);
    console.log('⚽ Rendering ball...');
    this.ball.render(ctx);
    console.log('✅ Level Render Complete!');
  }

  /**
   * Сброс уровня
   */
  reset(): void {
    this.score = 0;
    this.isComplete = false;
    this.bricks = this.createBricks();
    this.particles.clear();

    // Сбрасываем мяч с правильной позицией - ИСПРАВЛЕНИЕ: используем актуальные размеры
    const radius = this.ball.radius;
    const x = this.game.canvas.width / 2 - radius;

    // Используем ту же логику позиционирования что и при создании
    const isMobile = window.innerWidth <= 768;
    const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;

    let y: number;
    if (isMobile) {
      y = this.game.canvas.height - 100;  // Мобильные: выше платформы (60px от низа)
    } else if (isTablet) {
      y = this.game.canvas.height - 110;  // Планшеты: выше платформы (70px от низа)
    } else {
      y = this.game.canvas.height - 120;  // Десктопы: выше платформы (80px от низа)
    }

    this.ball.reset(x, y);
  }
}
