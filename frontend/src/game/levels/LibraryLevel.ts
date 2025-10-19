import { Level } from './Level';
import type { ColorScheme } from '../utils/ColorPalette';
import { ColorPalette } from '../utils/ColorPalette';
import type { Game } from '../core/Game';

/**
 * Уровень 5: Библиотека 📚
 *
 * Эмоциональная кривая:
 * - Начало: Тишина (темная библиотека)
 * - Середина: Знание (книги светятся)
 * - Конец: Мудрость (все книги разложены)
 */
export class LibraryLevel extends Level {
  constructor(game: Game) {
    super(game);
  }
  protected initColorScheme(): ColorScheme {
    return ColorPalette.LIBRARY;
  }

  getLevelName(): string {
    return 'Библиотека';
  }

  getLevelDescription(): string {
    return 'Разложи книги по полкам!';
  }

  protected getMathDifficulty(): number {
    return 5; // Самые сложные примеры
  }

  /**
   * Расположение в форме книжных полок
   */
  protected createBricksLayout(): Array<{ x: number; y: number; hits: number }> {
    const bricks: Array<{ x: number; y: number; hits: number }> = [];
    const brickWidth = this.canvasWidth * 0.12;
    const brickHeight = 30;
    const padding = 10;
    const offsetX = (this.canvasWidth - (brickWidth + padding) * 6) / 2;
    const offsetY = 60;

    // 6 рядов кирпичей (как книги на полках)
    for (let row = 0; row < 6; row++) {
      for (let col = 0; col < 6; col++) {
        bricks.push({
          x: offsetX + col * (brickWidth + padding),
          y: offsetY + row * (brickHeight + padding),
          hits: row >= 4 ? 3 : row >= 2 ? 2 : 1,
        });
      }
    }

    return bricks;
  }

  protected renderBackground(ctx: CanvasRenderingContext2D): void {
    super.renderBackground(ctx);

    // Книжные полки по бокам
    const shelfColor = ColorPalette.withAlpha(this.colorScheme.secondary, 0.2);
    const shelfWidth = 80;

    // Левые полки
    for (let i = 0; i < 4; i++) {
      const y = 100 + i * 70;
      ctx.fillStyle = shelfColor;
      ctx.fillRect(20, y, shelfWidth, 15);

      // "Книги" на полках
      for (let j = 0; j < 3; j++) {
        ctx.fillStyle = ColorPalette.withAlpha(
          [this.colorScheme.primary, this.colorScheme.accent, this.colorScheme.secondary][j],
          0.4
        );
        ctx.fillRect(25 + j * 25, y - 30, 20, 30);
      }
    }

    // Правые полки
    for (let i = 0; i < 4; i++) {
      const y = 100 + i * 70;
      ctx.fillStyle = shelfColor;
      ctx.fillRect(this.canvasWidth - shelfWidth - 20, y, shelfWidth, 15);

      // "Книги" на полках
      for (let j = 0; j < 3; j++) {
        ctx.fillStyle = ColorPalette.withAlpha(
          [this.colorScheme.accent, this.colorScheme.primary, this.colorScheme.secondary][j],
          0.4
        );
        ctx.fillRect(
          this.canvasWidth - shelfWidth - 15 + j * 25,
          y - 30,
          20,
          30
        );
      }
    }

    // Читальный стол внизу
    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.primary, 0.2);
    ctx.beginPath();
    ctx.ellipse(
      this.canvasWidth / 2,
      this.canvasHeight - 110,
      120,
      60,
      0,
      0,
      Math.PI * 2
    );
    ctx.fill();

    // Лампа на столе
    ctx.strokeStyle = ColorPalette.withAlpha(this.colorScheme.accent, 0.6);
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(this.canvasWidth / 2, this.canvasHeight - 130);
    ctx.lineTo(this.canvasWidth / 2, this.canvasHeight - 160);
    ctx.stroke();

    // Абажур лампы
    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.accent, 0.4);
    ctx.beginPath();
    ctx.moveTo(this.canvasWidth / 2 - 20, this.canvasHeight - 160);
    ctx.lineTo(this.canvasWidth / 2 + 20, this.canvasHeight - 160);
    ctx.lineTo(this.canvasWidth / 2 + 30, this.canvasHeight - 140);
    ctx.lineTo(this.canvasWidth / 2 - 30, this.canvasHeight - 140);
    ctx.closePath();
    ctx.fill();

    // Свечение от лампы
    const gradient = ctx.createRadialGradient(
      this.canvasWidth / 2,
      this.canvasHeight - 150,
      0,
      this.canvasWidth / 2,
      this.canvasHeight - 150,
      150
    );
    gradient.addColorStop(0, ColorPalette.withAlpha(this.colorScheme.accent, 0.3));
    gradient.addColorStop(1, 'transparent');
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(this.canvasWidth / 2, this.canvasHeight - 150, 150, 0, Math.PI * 2);
    ctx.fill();

    // Название
    ctx.fillStyle = ColorPalette.withAlpha(this.colorScheme.text, 0.3);
    ctx.font = 'bold 32px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('БИБЛИОТЕКА', this.canvasWidth / 2, this.canvasHeight - 30);
  }
}
