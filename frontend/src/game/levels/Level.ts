import { Brick } from '../entities/Brick';
import { Ball } from '../entities/Ball';
import { Paddle } from '../entities/Paddle';
import { ParticleSystem } from '../entities/Particle';
import { MathProblems } from '../utils/MathProblems';
import type { ColorScheme } from '../utils/ColorPalette';
import { ColorPalette } from '../utils/ColorPalette';

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
  protected canvasWidth: number;
  protected canvasHeight: number;
  protected isComplete: boolean = false;

  constructor(canvasWidth: number, canvasHeight: number) {
    this.canvasWidth = canvasWidth;
    this.canvasHeight = canvasHeight;
    this.colorScheme = this.initColorScheme();
    this.particles = new ParticleSystem();

    // Создаем базовые объекты
    this.paddle = this.createPaddle();
    this.ball = this.createBall();
    this.bricks = this.createBricks();
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
    // Адаптивная ширина платформы
    const paddleWidth = Math.max(80, this.canvasWidth * 0.18);
    const paddleHeight = Math.max(16, this.canvasWidth * 0.025);
    const paddleX = (this.canvasWidth - paddleWidth) / 2;
    const paddleY = this.canvasHeight - 80;

    return new Paddle(paddleX, paddleY, paddleWidth, paddleHeight);
  }

  /**
   * Создание мяча
   */
  protected createBall(): Ball {
    // Адаптивный размер мяча в зависимости от размера экрана
    const baseRadius = Math.max(12, Math.min(20, this.canvasWidth * 0.02));
    const x = this.canvasWidth / 2 - baseRadius;
    const y = this.canvasHeight - 120;
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
    // Градиентный фон
    const gradient = ctx.createLinearGradient(
      0,
      0,
      0,
      this.canvasHeight
    );
    gradient.addColorStop(0, this.colorScheme.background);
    gradient.addColorStop(1, ColorPalette.withAlpha(this.colorScheme.primary, 0.3));

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);
  }

  /**
   * Отрисовка уровня
   */
  render(ctx: CanvasRenderingContext2D): void {
    this.renderBackground(ctx);
    this.bricks.forEach((brick) => brick.render(ctx));
    this.particles.render(ctx);
    this.paddle.render(ctx);
    this.ball.render(ctx);
  }

  /**
   * Сброс уровня
   */
  reset(): void {
    this.score = 0;
    this.isComplete = false;
    this.bricks = this.createBricks();
    this.particles.clear();

    // Сбрасываем мяч
    const radius = 10;
    const x = this.canvasWidth / 2 - radius;
    const y = this.canvasHeight - 100;
    this.ball.reset(x, y);
  }
}
