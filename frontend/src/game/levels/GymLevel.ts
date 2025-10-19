import { Level } from './Level';
import type { ColorScheme } from '../utils/ColorPalette';
import { ColorPalette } from '../utils/ColorPalette';
import type { Game } from '../core/Game';

/**
 * Уровень 1: Спортзал 🏀
 *
 * Эмоциональная кривая:
 * - Начало: Любопытство (пустой спортзал, тихо)
 * - Середина: Удивление (мяч оживает, начинает двигаться)
 * - Конец: Удовлетворение (все разложено по местам)
 */
export class GymLevel extends Level {
  constructor(game: Game) {
    super(game);
  }
  protected initColorScheme(): ColorScheme {
    return ColorPalette.GYM;
  }

  getLevelName(): string {
    return 'Спортзал';
  }

  getLevelDescription(): string {
    return 'Помоги панде разложить спортивный инвентарь!';
  }

  protected getMathDifficulty(): number {
    return 1; // Легкие примеры
  }

  /**
   * Создание расположения кирпичей в форме баскетбольной сетки
   */
  protected createBricksLayout(): Array<{ x: number; y: number; hits: number }> {
    const bricks: Array<{ x: number; y: number; hits: number }> = [];
    const brickWidth = this.canvasWidth * 0.12;
    const brickHeight = 30;
    const padding = 10;
    const offsetX = (this.canvasWidth - (brickWidth + padding) * 6) / 2;
    const offsetY = 80;

    // 3 ряда кирпичей
    for (let row = 0; row < 3; row++) {
      for (let col = 0; col < 6; col++) {
        bricks.push({
          x: offsetX + col * (brickWidth + padding),
          y: offsetY + row * (brickHeight + padding),
          hits: 1,
        });
      }
    }

    return bricks;
  }

  /**
   * Отрисовка фона спортзала
   */
  protected renderBackground(ctx: CanvasRenderingContext2D): void {
    // Базовый фон
    super.renderBackground(ctx);

    // Разметка пола
    ctx.strokeStyle = ColorPalette.withAlpha(this.colorScheme.secondary, 0.3);
    ctx.lineWidth = 2;

    // Горизонтальные линии
    for (let i = 1; i < 5; i++) {
      const y = (this.canvasHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(this.canvasWidth, y);
      ctx.stroke();
    }

    // Вертикальные линии
    for (let i = 1; i < 4; i++) {
      const x = (this.canvasWidth / 4) * i;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, this.canvasHeight);
      ctx.stroke();
    }

    // Центральный круг
    ctx.beginPath();
    ctx.arc(
      this.canvasWidth / 2,
      this.canvasHeight / 2,
      60,
      0,
      Math.PI * 2
    );
    ctx.stroke();

    // Название уровня
    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.text, 0.2);
    ctx.font = 'bold 48px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('СПОРТЗАЛ', this.canvasWidth / 2, this.canvasHeight - 30);
  }
}
