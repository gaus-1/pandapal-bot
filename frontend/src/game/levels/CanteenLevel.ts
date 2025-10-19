import { Level } from './Level';
import type { ColorScheme } from '../utils/ColorPalette';
import { ColorPalette } from '../utils/ColorPalette';
import type { Game } from '../core/Game';

/**
 * Уровень 3: Столовая 🍎
 *
 * Эмоциональная кривая:
 * - Начало: Голод (пустой поднос)
 * - Середина: Радость (собираем полезный обед)
 * - Конец: Сытость (полный поднос, довольная панда)
 */
export class CanteenLevel extends Level {
  constructor(game: Game) {
    super(game);
  }
  protected initColorScheme(): ColorScheme {
    return ColorPalette.CANTEEN;
  }

  getLevelName(): string {
    return 'Столовая';
  }

  getLevelDescription(): string {
    return 'Собери полезный обед!';
  }

  protected getMathDifficulty(): number {
    return 3; // Сложнее
  }

  /**
   * Расположение в форме пирамиды еды
   */
  protected createBricksLayout(): Array<{ x: number; y: number; hits: number }> {
    const bricks: Array<{ x: number; y: number; hits: number }> = [];
    const brickWidth = this.canvasWidth * 0.12;
    const brickHeight = 30;
    const padding = 10;
    const offsetY = 70;

    // 5 рядов в форме пирамиды
    const rowsConfig = [5, 6, 5, 4, 3];

    rowsConfig.forEach((count, row) => {
      const offsetX = (this.canvasWidth - (brickWidth + padding) * count) / 2;

      for (let col = 0; col < count; col++) {
        bricks.push({
          x: offsetX + col * (brickWidth + padding),
          y: offsetY + row * (brickHeight + padding),
          hits: row >= 3 ? 2 : 1,
        });
      }
    });

    return bricks;
  }

  protected renderBackground(ctx: CanvasRenderingContext2D): void {
    super.renderBackground(ctx);

    // Столы
    for (let i = 0; i < 2; i++) {
      const x = 150 + i * 250;
      const y = this.canvasHeight - 140;

      ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.primary, 0.15);
      ctx.beginPath();
      ctx.ellipse(x, y, 60, 40, 0, 0, Math.PI * 2);
      ctx.fill();

      // Стулья
      for (let j = 0; j < 2; j++) {
        ctx.beginPath();
        ctx.arc(x - 40 + j * 80, y, 15, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Меню на стене
    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.secondary, 0.2);
    ctx.fillRect(this.canvasWidth - 150, 50, 120, 160);
    ctx.strokeStyle = this.colorScheme.text;
    ctx.lineWidth = 2;
    ctx.strokeRect(this.canvasWidth - 150, 50, 120, 160);

    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.text, 0.3);
    ctx.font = 'bold 20px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('МЕНЮ', this.canvasWidth - 90, 80);

    // Название
    ctx.font = 'bold 40px Arial';
    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.text, 0.2);
    ctx.fillText('СТОЛОВАЯ', this.canvasWidth / 2, this.canvasHeight - 30);
  }
}
