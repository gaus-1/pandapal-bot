import { GameObject } from './GameObject';
import { Easing } from '../utils/Easing';

/**
 * Деревянная платформа (игрок)
 * Отвечает за управление платформой и отрисовку деревянной доски
 */
export class Paddle extends GameObject {
  private targetX: number;
  private readonly speed: number = 0.15; // Плавное движение
  private animationTime: number = 0;

  constructor(x: number, y: number, width: number, height: number) {
    super(x, y, width, height);
    this.targetX = x;
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
   * Отрисовка улучшенной деревянной доски
   */
  render(ctx: CanvasRenderingContext2D): void {
    const { x, y, width, height } = this;

    // Отладочная информация - выводим позицию платформы
    console.log(`🎯 Paddle Render: x=${x}, y=${y}, width=${width}, height=${height}`);

    // Тень под платформой
    ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
    ctx.shadowBlur = 12;
    ctx.shadowOffsetY = 6;

    // Основная деревянная доска с градиентом
    const gradient = ctx.createLinearGradient(x, y, x, y + height);
    gradient.addColorStop(0, '#A0522D'); // SaddleBrown
    gradient.addColorStop(0.5, '#8B4513'); // SaddleBrown
    gradient.addColorStop(1, '#654321'); // Darker brown

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, height / 4);
    ctx.fill();

    // Сброс тени
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
    ctx.shadowOffsetY = 0;

    // Улучшенная деревянная текстура
    ctx.fillStyle = 'rgba(101, 67, 33, 0.6)'; // Полупрозрачный темный коричневый
    const stripeHeight = height / 6;
    for (let i = 0; i < 3; i++) {
      const stripeY = y + i * stripeHeight * 2 + stripeHeight / 2;
      ctx.fillRect(x + width * 0.05, stripeY, width * 0.9, stripeHeight);
    }

    // Металлические заклепки с улучшенным дизайном
    const rivetRadius = height * 0.2;
    const rivetY = y + height / 2;

    // Градиент для заклепок
    const rivetGradient = ctx.createRadialGradient(0, 0, 0, 0, 0, rivetRadius);
    rivetGradient.addColorStop(0, '#E8E8E8');
    rivetGradient.addColorStop(0.7, '#C0C0C0');
    rivetGradient.addColorStop(1, '#A0A0A0');

    // Левая заклепка
    ctx.fillStyle = rivetGradient;
    ctx.beginPath();
    ctx.arc(x + rivetRadius, rivetY, rivetRadius, 0, Math.PI * 2);
    ctx.fill();

    // Правая заклепка
    ctx.beginPath();
    ctx.arc(x + width - rivetRadius, rivetY, rivetRadius, 0, Math.PI * 2);
    ctx.fill();

    // Центральная заклепка
    ctx.beginPath();
    ctx.arc(x + width / 2, rivetY, rivetRadius * 0.9, 0, Math.PI * 2);
    ctx.fill();

    // Обводка доски с улучшенной толщиной
    ctx.strokeStyle = '#654321';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, height / 4);
    ctx.stroke();

    // КРИТИЧЕСКАЯ ОТЛАДКА: Яркая красная рамка для видимости платформы
    ctx.strokeStyle = '#FF0000';
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.rect(x - 2, y - 2, width + 4, height + 4);
    ctx.stroke();

    // Внутренняя обводка для глубины
    ctx.strokeStyle = 'rgba(139, 69, 19, 0.8)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(x + 1, y + 1, width - 2, height - 2, height / 4 - 1);
    ctx.stroke();
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
