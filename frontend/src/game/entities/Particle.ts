import { GameObject } from './GameObject';
import { Easing } from '../utils/Easing';

/**
 * Частица для визуальных эффектов
 * Используется при разрушении кирпичей и других эффектах
 */
export class Particle extends GameObject {
  private readonly lifetime: number;
  private age: number = 0;
  private readonly color: string;
  private readonly gravity: number;

  constructor(
    x: number,
    y: number,
    size: number,
    vx: number,
    vy: number,
    color: string,
    lifetime: number = 1000,
    gravity: number = 0.0005
  ) {
    super(x, y, size, size);
    this.setVelocity(vx, vy);
    this.color = color;
    this.lifetime = lifetime;
    this.gravity = gravity;
  }

  /**
   * Обновление частицы
   */
  update(deltaTime: number): void {
    if (!this._active) return;

    this.age += deltaTime;

    // Проверка времени жизни
    if (this.age >= this.lifetime) {
      this.setActive(false);
      return;
    }

    // Применяем гравитацию
    const newVy = this._velocity.y + this.gravity * deltaTime;
    this.setVelocity(this._velocity.x, newVy);

    // Обновляем позицию
    const newX = this.x + this._velocity.x * deltaTime;
    const newY = this.y + this._velocity.y * deltaTime;
    this.setPosition(newX, newY);
  }

  /**
   * Отрисовка частицы
   */
  render(ctx: CanvasRenderingContext2D): void {
    const progress = this.age / this.lifetime;
    const alpha = Easing.easeOut(1 - progress);
    const size = this.width * (1 - progress * 0.5);

    ctx.fillStyle = this.color.replace('rgb', 'rgba').replace(')', `, ${alpha})`);
    ctx.beginPath();
    ctx.arc(this.x + size / 2, this.y + size / 2, size / 2, 0, Math.PI * 2);
    ctx.fill();
  }
}

/**
 * Менеджер частиц для управления множественными частицами
 */
export class ParticleSystem {
  private particles: Particle[] = [];

  /**
   * Создать взрыв частиц
   */
  createExplosion(
    x: number,
    y: number,
    count: number,
    color: string,
    speed: number = 0.3
  ): void {
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count;
      const vx = Math.cos(angle) * speed * (0.5 + Math.random() * 0.5);
      const vy = Math.sin(angle) * speed * (0.5 + Math.random() * 0.5);
      const size = 4 + Math.random() * 4;
      const lifetime = 500 + Math.random() * 500;

      this.particles.push(
        new Particle(x, y, size, vx, vy, color, lifetime)
      );
    }
  }

  /**
   * Создать фонтан частиц
   */
  createFountain(x: number, y: number, count: number, color: string): void {
    for (let i = 0; i < count; i++) {
      const angle = -Math.PI / 2 + (Math.random() - 0.5) * Math.PI * 0.5;
      const speed = 0.2 + Math.random() * 0.3;
      const vx = Math.cos(angle) * speed;
      const vy = Math.sin(angle) * speed;
      const size = 3 + Math.random() * 3;
      const lifetime = 800 + Math.random() * 400;

      this.particles.push(
        new Particle(x, y, size, vx, vy, color, lifetime, 0.0008)
      );
    }
  }

  /**
   * Обновить все частицы
   */
  update(deltaTime: number): void {
    // Обновляем и удаляем неактивные
    this.particles = this.particles.filter((particle) => {
      particle.update(deltaTime);
      return particle.active;
    });
  }

  /**
   * Отрисовать все частицы
   */
  render(ctx: CanvasRenderingContext2D): void {
    this.particles.forEach((particle) => particle.render(ctx));
  }

  /**
   * Очистить все частицы
   */
  clear(): void {
    this.particles = [];
  }

  /**
   * Получить количество активных частиц
   */
  getCount(): number {
    return this.particles.length;
  }
}
