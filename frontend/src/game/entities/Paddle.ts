import { GameObject } from './GameObject';
import { ColorPalette } from '../utils/ColorPalette';
import { Easing } from '../utils/Easing';

/**
 * Деревянная платформа (игрок)
 * Отвечает за управление платформой и отрисовку деревянной доски
 */
export class Paddle extends GameObject {
  private targetX: number;
  private readonly speed: number = 0.15; // Плавное движение
  private readonly colorScheme: typeof ColorPalette.PANDA;
  private animationTime: number = 0;

  constructor(x: number, y: number, width: number, height: number) {
    super(x, y, width, height);
    this.targetX = x;
    this.colorScheme = ColorPalette.PANDA;
  }

  /**
   * Установка целевой позиции (для плавного движения)
   */
  setTargetX(x: number, canvasWidth: number): void {
    // Ограничиваем движение в пределах экрана
    this.targetX = Math.max(
      0,
      Math.min(x - this.width / 2, canvasWidth - this.width)
    );
  }

  /**
   * Обновление позиции с плавной интерполяцией
   */
  update(deltaTime: number): void {
    this.animationTime += deltaTime * 0.003; // Медленная анимация для плавности

    // Плавное движение к целевой позиции
    const currentX = this._position.x;
    const diff = this.targetX - currentX;

    if (Math.abs(diff) > 0.5) {
      const newX = Easing.lerp(currentX, this.targetX, this.speed);
      this.setPosition(newX, this._position.y);
    } else {
      this.setPosition(this.targetX, this._position.y);
    }
  }

  /**
   * Отрисовка деревянной доски в минималистичном стиле
   */
  render(ctx: CanvasRenderingContext2D): void {
    const { x, y, width, height } = this;

    // Основная деревянная доска
    const woodColor = '#8B4513'; // Коричневый цвет дерева
    const darkWood = '#654321'; // Темный коричневый для текстуры

    // Основа доски
    ctx.fillStyle = woodColor;
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, height / 4);
    ctx.fill();

    // Деревянная текстура (горизонтальные полосы)
    ctx.fillStyle = darkWood;
    const stripeHeight = height / 8;
    for (let i = 0; i < 4; i++) {
      const stripeY = y + i * stripeHeight * 2 + stripeHeight / 2;
      ctx.fillRect(x + width * 0.1, stripeY, width * 0.8, stripeHeight);
    }

    // Металлические заклепки по краям
    ctx.fillStyle = '#C0C0C0'; // Серебристый цвет
    const rivetRadius = height * 0.15;
    const rivetY = y + height / 2;

    // Левая заклепка
    ctx.beginPath();
    ctx.arc(x + rivetRadius, rivetY, rivetRadius, 0, Math.PI * 2);
    ctx.fill();

    // Правая заклепка
    ctx.beginPath();
    ctx.arc(x + width - rivetRadius, rivetY, rivetRadius, 0, Math.PI * 2);
    ctx.fill();

    // Центральная заклепка
    ctx.beginPath();
    ctx.arc(x + width / 2, rivetY, rivetRadius * 0.8, 0, Math.PI * 2);
    ctx.fill();

    // Обводка доски
    ctx.strokeStyle = '#654321';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, height / 4);
    ctx.stroke();

    // Тень для глубины
    ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
    ctx.shadowBlur = 8;
    ctx.shadowOffsetY = 4;

    // Сброс тени
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;
  }

  /**
   * Получение позиции для отскока мяча
   */
  getHitPosition(ballX: number): number {
    // Возвращаем позицию от -1 до 1 (центр платформы = 0)
    const centerX = this.x + this.width / 2;
    const relativeX = ballX - centerX;
    return (relativeX / (this.width / 2)) * 0.8; // 0.8 для ограничения макс угла
  }
}
