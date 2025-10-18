import { GameObject } from './GameObject';
import { Vector2D } from '../utils/Vector2D';
import type { ColorScheme } from '../utils/ColorPalette';

/**
 * Мяч для игры
 * Отвечает за движение, отскоки и визуализацию
 */
export class Ball extends GameObject {
  private readonly baseSpeed: number;
  private readonly maxSpeed: number;
  private trail: Vector2D[] = [];
  private readonly trailLength: number = 8;
  private colorScheme: ColorScheme;

  constructor(
    x: number,
    y: number,
    radius: number,
    speed: number,
    colorScheme: ColorScheme
  ) {
    super(x, y, radius * 2, radius * 2);
    this.baseSpeed = speed;
    this.maxSpeed = speed * 1.5;
    this.colorScheme = colorScheme;
    this.resetVelocity();
  }

  /**
   * Получить радиус мяча
   */
  get radius(): number {
    return this.width / 2;
  }

  /**
   * Получить центр мяча
   */
  getCenter(): Vector2D {
    return new Vector2D(this.x + this.radius, this.y + this.radius);
  }

  /**
   * Сброс скорости в случайном направлении вверх
   */
  resetVelocity(): void {
    const angle = -Math.PI / 2 + (Math.random() - 0.5) * Math.PI * 0.5;
    this.setVelocity(
      Math.cos(angle) * this.baseSpeed,
      Math.sin(angle) * this.baseSpeed
    );
  }

  /**
   * Установка цветовой схемы
   */
  setColorScheme(colorScheme: ColorScheme): void {
    this.colorScheme = colorScheme;
  }

  /**
   * Обновление позиции мяча
   */
  update(deltaTime: number): void {
    if (!this._active) return;

    // Проверяем минимальную скорость (предотвращает застревание)
    const currentSpeed = this._velocity.length();
    if (currentSpeed < this.baseSpeed * 0.5) {
      // Если скорость слишком мала, придаем импульс
      const normalized = this._velocity.normalize();
      this.setVelocity(
        normalized.x * this.baseSpeed,
        normalized.y * this.baseSpeed
      );
    }

    // Обновляем след
    this.trail.push(this.getCenter());
    if (this.trail.length > this.trailLength) {
      this.trail.shift();
    }

    // Двигаем мяч
    const newX = this.x + this._velocity.x * deltaTime;
    const newY = this.y + this._velocity.y * deltaTime;
    this.setPosition(newX, newY);
  }

  /**
   * Отскок от платформы с учетом позиции удара
   */
  bounceOffPaddle(hitPosition: number): void {
    // hitPosition от -1 до 1
    const angle = hitPosition * (Math.PI / 3); // Максимум 60 градусов
    const speed = this._velocity.length();

    this.setVelocity(Math.sin(angle) * speed, -Math.abs(Math.cos(angle) * speed));
  }

  /**
   * Отскок от стены (вертикальный)
   */
  bounceX(): void {
    this.setVelocity(-this._velocity.x, this._velocity.y);
  }

  /**
   * Отскок от потолка (горизонтальный)
   */
  bounceY(): void {
    this.setVelocity(this._velocity.x, -this._velocity.y);
  }

  /**
   * Увеличение скорости (постепенное усложнение)
   */
  increaseSpeed(amount: number = 1.05): void {
    const currentSpeed = this._velocity.length();
    if (currentSpeed < this.maxSpeed) {
      const normalized = this._velocity.normalize();
      const newSpeed = Math.min(currentSpeed * amount, this.maxSpeed);
      this.setVelocity(normalized.x * newSpeed, normalized.y * newSpeed);
    }
  }

  /**
   * Отрисовка мяча с эффектом следа
   */
  render(ctx: CanvasRenderingContext2D): void {
    const center = this.getCenter();

    // Рисуем след (слабеющие круги)
    for (let i = 0; i < this.trail.length; i++) {
      const alpha = (i / this.trail.length) * 0.3;
      const trailRadius = this.radius * (0.5 + (i / this.trail.length) * 0.5);

      ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
      ctx.beginPath();
      ctx.arc(this.trail[i].x, this.trail[i].y, trailRadius, 0, Math.PI * 2);
      ctx.fill();
    }

    // Основной мяч с градиентом
    const gradient = ctx.createRadialGradient(
      center.x - this.radius * 0.3,
      center.y - this.radius * 0.3,
      0,
      center.x,
      center.y,
      this.radius
    );

    gradient.addColorStop(0, this.colorScheme.accent);
    gradient.addColorStop(1, this.colorScheme.primary);

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(center.x, center.y, this.radius, 0, Math.PI * 2);
    ctx.fill();

    // Обводка для четкости
    ctx.strokeStyle = this.colorScheme.text;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(center.x, center.y, this.radius, 0, Math.PI * 2);
    ctx.stroke();

    // Блик для объема
    ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.beginPath();
    ctx.arc(
      center.x - this.radius * 0.3,
      center.y - this.radius * 0.3,
      this.radius * 0.3,
      0,
      Math.PI * 2
    );
    ctx.fill();
  }

  /**
   * Сброс позиции мяча
   */
  reset(x: number, y: number): void {
    this.setPosition(x, y);
    this.resetVelocity();
    this.trail = [];
    this._active = true;
  }
}
