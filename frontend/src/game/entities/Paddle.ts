import { GameObject } from './GameObject';
import { ColorPalette } from '../utils/ColorPalette';
import { Easing } from '../utils/Easing';

/**
 * Платформа-панда (игрок)
 * Отвечает за управление платформой и отрисовку панды
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
   * Отрисовка панды в минималистичном стиле
   */
  render(ctx: CanvasRenderingContext2D): void {
    const { x, y, width, height } = this;
    const centerX = x + width / 2;

    // Основное тело (белый прямоугольник с закругленными углами)
    ctx.fillStyle = this.colorScheme.body;
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, height / 2);
    ctx.fill();

    // Черные ушки
    const earRadius = height * 0.4;
    const earY = y + earRadius * 0.6;

    // Левое ухо
    ctx.fillStyle = this.colorScheme.spots;
    ctx.beginPath();
    ctx.arc(x + earRadius, earY, earRadius, 0, Math.PI * 2);
    ctx.fill();

    // Правое ухо
    ctx.beginPath();
    ctx.arc(x + width - earRadius, earY, earRadius, 0, Math.PI * 2);
    ctx.fill();

    // Лицо
    const faceY = y + height * 0.6;

    // Глаза (черные овалы)
    const eyeWidth = height * 0.25;
    const eyeHeight = height * 0.35;
    const eyeOffsetX = width * 0.25;

    // Левый глаз
    ctx.fillStyle = this.colorScheme.eyes;
    ctx.beginPath();
    ctx.ellipse(
      centerX - eyeOffsetX,
      faceY,
      eyeWidth,
      eyeHeight,
      0,
      0,
      Math.PI * 2
    );
    ctx.fill();

    // Правый глаз
    ctx.beginPath();
    ctx.ellipse(
      centerX + eyeOffsetX,
      faceY,
      eyeWidth,
      eyeHeight,
      0,
      0,
      Math.PI * 2
    );
    ctx.fill();

    // Нос (маленький розовый треугольник)
    const noseSize = height * 0.15;
    const noseY = faceY + eyeHeight;

    ctx.fillStyle = this.colorScheme.nose;
    ctx.beginPath();
    ctx.moveTo(centerX, noseY);
    ctx.lineTo(centerX - noseSize, noseY - noseSize);
    ctx.lineTo(centerX + noseSize, noseY - noseSize);
    ctx.closePath();
    ctx.fill();

    // Тень для глубины
    ctx.shadowColor = 'rgba(0, 0, 0, 0.1)';
    ctx.shadowBlur = 10;
    ctx.shadowOffsetY = 5;

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
