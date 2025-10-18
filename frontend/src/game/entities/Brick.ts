import { GameObject } from './GameObject';
import type { MathProblem } from '../utils/MathProblems';
import type { ColorScheme } from '../utils/ColorPalette';
import { Easing } from '../utils/Easing';

/**
 * Кирпич с математическим примером
 * Отвечает за отображение примера и анимацию разрушения
 */
export class Brick extends GameObject {
  private readonly mathProblem: MathProblem;
  private readonly colorScheme: ColorScheme;
  private readonly color: string;
  private hits: number;
  private readonly maxHits: number;
  private destroyAnimation: number = 0;
  private readonly isDestroying: boolean = false;

  constructor(
    x: number,
    y: number,
    width: number,
    height: number,
    mathProblem: MathProblem,
    colorScheme: ColorScheme,
    hits: number = 1
  ) {
    super(x, y, width, height);
    this.mathProblem = mathProblem;
    this.colorScheme = colorScheme;
    this.hits = hits;
    this.maxHits = hits;

    // Цвет зависит от сложности примера
    this.color = this.getColorByDifficulty(mathProblem.difficulty);
  }

  /**
   * Получить цвет кирпича по сложности
   */
  private getColorByDifficulty(difficulty: number): string {
    const colors = [
      this.colorScheme.primary,
      this.colorScheme.secondary,
      this.colorScheme.accent,
    ];
    return colors[Math.min(difficulty - 1, colors.length - 1)];
  }

  /**
   * Получить математический пример
   */
  getMathProblem(): MathProblem {
    return this.mathProblem;
  }

  /**
   * Удар по кирпичу
   */
  hit(): boolean {
    this.hits--;
    if (this.hits <= 0) {
      this.startDestroyAnimation();
      return true; // Кирпич разрушен
    }
    return false; // Кирпич еще цел
  }

  /**
   * Начать анимацию разрушения
   */
  private startDestroyAnimation(): void {
    (this as unknown as { isDestroying: boolean }).isDestroying = true;
    this.destroyAnimation = 0;
  }

  /**
   * Проверка, разрушается ли кирпич
   */
  isBeingDestroyed(): boolean {
    return this.isDestroying;
  }

  /**
   * Обновление состояния кирпича
   */
  update(deltaTime: number): void {
    if (this.isDestroying) {
      this.destroyAnimation += deltaTime * 0.003;
      if (this.destroyAnimation >= 1) {
        this.setActive(false);
      }
    }
  }

  /**
   * Отрисовка кирпича
   */
  render(ctx: CanvasRenderingContext2D): void {
    const { x, y, width, height } = this;

    ctx.save();

    // Анимация разрушения
    if (this.isDestroying) {
      const progress = Easing.easeOut(this.destroyAnimation);
      const alpha = 1 - progress;
      const scale = 1 + progress * 0.5;
      const offsetX = width * (scale - 1) / 2;
      const offsetY = height * (scale - 1) / 2;

      ctx.globalAlpha = alpha;
      ctx.translate(x + width / 2, y + height / 2);
      ctx.scale(scale, scale);
      ctx.translate(-width / 2, -height / 2);

      this.renderBrick(ctx, -offsetX, -offsetY, width, height);
    } else {
      this.renderBrick(ctx, x, y, width, height);
    }

    ctx.restore();
  }

  /**
   * Отрисовка самого кирпича
   */
  private renderBrick(
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    width: number,
    height: number
  ): void {
    // Основной прямоугольник
    ctx.fillStyle = this.color;
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, 8);
    ctx.fill();

    // Обводка
    ctx.strokeStyle = this.colorScheme.text;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Индикатор прочности (если больше 1 удара)
    if (this.maxHits > 1) {
      const healthPercent = this.hits / this.maxHits;
      const barWidth = width * 0.8;
      const barHeight = 4;
      const barX = x + (width - barWidth) / 2;
      const barY = y + height - barHeight - 4;

      // Фон полоски
      ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
      ctx.fillRect(barX, barY, barWidth, barHeight);

      // Заполненная часть
      ctx.fillStyle = this.colorScheme.accent;
      ctx.fillRect(barX, barY, barWidth * healthPercent, barHeight);
    }

    // Математический пример
    ctx.fillStyle = this.colorScheme.text;
    ctx.font = `bold ${Math.min(height * 0.4, 20)}px Arial`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(
      this.mathProblem.question,
      x + width / 2,
      y + height / 2 - (this.maxHits > 1 ? 4 : 0)
    );

    // Тень для глубины
    ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
    ctx.shadowBlur = 8;
    ctx.shadowOffsetY = 4;
  }

  /**
   * Получить очки за разрушение
   */
  getPoints(): number {
    return this.mathProblem.difficulty * 10;
  }
}
