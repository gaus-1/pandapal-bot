import { Level } from './Level';
import type { ColorScheme } from '../utils/ColorPalette';
import { ColorPalette } from '../utils/ColorPalette';
import type { Game } from '../core/Game';

/**
 * Уровень 2: Класс математики 📐
 *
 * Эмоциональная кривая:
 * - Начало: Интерес (доска с примерами)
 * - Середина: Открытие (решаем примеры, они оживают)
 * - Конец: Гордость (все примеры решены)
 */
export class ClassroomLevel extends Level {
  constructor(game: Game) {
    super(game);
  }
  protected initColorScheme(): ColorScheme {
    return ColorPalette.CLASSROOM;
  }

  getLevelName(): string {
    return 'Класс математики';
  }

  getLevelDescription(): string {
    return 'Реши все примеры на доске!';
  }

  protected getMathDifficulty(): number {
    return 2; // Средняя сложность
  }

  /**
   * Расположение в форме классной доски
   */
  protected createBricksLayout(): Array<{ x: number; y: number; hits: number }> {
    const bricks: Array<{ x: number; y: number; hits: number }> = [];
    const brickWidth = this.canvasWidth * 0.12;
    const brickHeight = 30;
    const padding = 10;
    const offsetX = (this.canvasWidth - (brickWidth + padding) * 6) / 2;
    const offsetY = 60;

    // 4 ряда кирпичей
    for (let row = 0; row < 4; row++) {
      for (let col = 0; col < 6; col++) {
        bricks.push({
          x: offsetX + col * (brickWidth + padding),
          y: offsetY + row * (brickHeight + padding),
          hits: row === 3 ? 2 : 1, // Нижний ряд требует 2 удара
        });
      }
    }

    return bricks;
  }

  protected renderBackground(ctx: CanvasRenderingContext2D): void {
    super.renderBackground(ctx);

    // Доска
    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.secondary, 0.2);
    ctx.fillRect(50, 40, this.canvasWidth - 100, 200);
    ctx.strokeStyle = this.colorScheme.text;
    ctx.lineWidth = 3;
    ctx.strokeRect(50, 40, this.canvasWidth - 100, 200);

    // Парты (силуэты)
    for (let i = 0; i < 3; i++) {
      const x = 100 + i * 150;
      const y = this.canvasHeight - 150;

      ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.primary, 0.15);
      ctx.fillRect(x, y, 80, 40);
      ctx.fillRect(x + 20, y + 40, 40, 60);
    }

    // Название
    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.text, 0.2);
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('КЛАСС', this.canvasWidth / 2, this.canvasHeight - 30);
  }
}
