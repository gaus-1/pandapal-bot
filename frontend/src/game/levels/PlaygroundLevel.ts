import { Level } from './Level';
import type { ColorScheme } from '../utils/ColorPalette';
import { ColorPalette } from '../utils/ColorPalette';

/**
 * Уровень 4: Школьный двор 🌳
 *
 * Эмоциональная кривая:
 * - Начало: Энергия (много игрушек)
 * - Середина: Игра (веселое движение)
 * - Конец: Порядок (все убрано)
 */
export class PlaygroundLevel extends Level {
  protected initColorScheme(): ColorScheme {
    return ColorPalette.PLAYGROUND;
  }

  getLevelName(): string {
    return 'Школьный двор';
  }

  getLevelDescription(): string {
    return 'Убери игрушки после игры!';
  }

  protected getMathDifficulty(): number {
    return 4; // Сложные примеры
  }

  /**
   * Расположение в форме дерева
   */
  protected createBricksLayout(): Array<{ x: number; y: number; hits: number }> {
    const bricks: Array<{ x: number; y: number; hits: number }> = [];
    const brickWidth = this.canvasWidth * 0.12;
    const brickHeight = 30;
    const padding = 10;
    const offsetY = 60;

    // Крона дерева (5 рядов)
    const rowsConfig = [3, 5, 6, 5, 4];

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

    // "Ствол" дерева (1 кирпич по центру)
    const centerX = (this.canvasWidth - brickWidth) / 2;
    bricks.push({
      x: centerX,
      y: offsetY + 5 * (brickHeight + padding),
      hits: 3,
    });

    return bricks;
  }

  protected renderBackground(ctx: CanvasRenderingContext2D): void {
    super.renderBackground(ctx);

    // Небо с облаками
    ctx.fillStyle = ColorPalette.withAlpha('#FFFFFF', 0.3);

    // Облака
    const drawCloud = (x: number, y: number, scale: number) => {
      ctx.beginPath();
      ctx.arc(x, y, 20 * scale, 0, Math.PI * 2);
      ctx.arc(x + 25 * scale, y, 25 * scale, 0, Math.PI * 2);
      ctx.arc(x + 50 * scale, y, 20 * scale, 0, Math.PI * 2);
      ctx.fill();
    };

    drawCloud(100, 80, 0.8);
    drawCloud(this.canvasWidth - 150, 120, 1);
    drawCloud(this.canvasWidth / 2, 60, 0.6);

    // Трава внизу
    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.secondary, 0.3);
    ctx.beginPath();
    ctx.moveTo(0, this.canvasHeight - 80);
    for (let i = 0; i < this.canvasWidth; i += 20) {
      ctx.lineTo(i, this.canvasHeight - 80 + Math.sin(i * 0.1) * 5);
    }
    ctx.lineTo(this.canvasWidth, this.canvasHeight);
    ctx.lineTo(0, this.canvasHeight);
    ctx.closePath();
    ctx.fill();

    // Качели (силуэт)
    const swingX = 100;
    const swingY = this.canvasHeight - 150;

    ctx.strokeStyle = ColorPalette.withAlpha(this.colorScheme.accent, 0.4);
    ctx.lineWidth = 4;

    // Стойки
    ctx.beginPath();
    ctx.moveTo(swingX, swingY);
    ctx.lineTo(swingX + 60, swingY - 60);
    ctx.moveTo(swingX + 120, swingY);
    ctx.lineTo(swingX + 60, swingY - 60);
    ctx.stroke();

    // Сиденье
    ctx.beginPath();
    ctx.moveTo(swingX + 40, swingY - 20);
    ctx.lineTo(swingX + 40, swingY);
    ctx.moveTo(swingX + 80, swingY - 20);
    ctx.lineTo(swingX + 80, swingY);
    ctx.stroke();

    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.primary, 0.5);
    ctx.fillRect(swingX + 30, swingY, 60, 10);

    // Название
    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.text, 0.25);
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('ДВОР', this.canvasWidth / 2, this.canvasHeight - 30);
  }
}
