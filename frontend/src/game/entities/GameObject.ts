import { Vector2D } from '../utils/Vector2D';

/**
 * Базовый класс для всех игровых объектов
 * Single Responsibility: управление позицией, размером и базовым поведением
 */
export abstract class GameObject {
  protected _position: Vector2D;
  protected _velocity: Vector2D;
  protected _size: Vector2D;
  protected _active: boolean;

  constructor(x: number, y: number, width: number, height: number) {
    this._position = new Vector2D(x, y);
    this._velocity = Vector2D.zero();
    this._size = new Vector2D(width, height);
    this._active = true;
  }

  /**
   * Геттеры для инкапсуляции
   */
  get position(): Vector2D {
    return this._position;
  }

  get velocity(): Vector2D {
    return this._velocity;
  }

  get size(): Vector2D {
    return this._size;
  }

  get active(): boolean {
    return this._active;
  }

  get x(): number {
    return this._position.x;
  }

  get y(): number {
    return this._position.y;
  }

  get width(): number {
    return this._size.x;
  }

  get height(): number {
    return this._size.y;
  }

  /**
   * Сеттеры с валидацией
   */
  setPosition(x: number, y: number): void {
    this._position = new Vector2D(x, y);
  }

  setVelocity(vx: number, vy: number): void {
    this._velocity = new Vector2D(vx, vy);
  }

  setActive(active: boolean): void {
    this._active = active;
  }

  /**
   * Обновление состояния (должно быть переопределено в наследниках)
   */
  abstract update(deltaTime: number): void;

  /**
   * Рендеринг (должен быть переопределен в наследниках)
   */
  abstract render(ctx: CanvasRenderingContext2D): void;

  /**
   * Проверка столкновения с другим объектом (AABB)
   */
  collidesWith(other: GameObject): boolean {
    return (
      this.x < other.x + other.width &&
      this.x + this.width > other.x &&
      this.y < other.y + other.height &&
      this.y + this.height > other.y
    );
  }

  /**
   * Получение центра объекта
   */
  getCenter(): Vector2D {
    return new Vector2D(
      this.x + this.width / 2,
      this.y + this.height / 2
    );
  }

  /**
   * Получение границ объекта
   */
  getBounds(): { left: number; right: number; top: number; bottom: number } {
    return {
      left: this.x,
      right: this.x + this.width,
      top: this.y,
      bottom: this.y + this.height,
    };
  }

  /**
   * Уничтожение объекта
   */
  destroy(): void {
    this._active = false;
  }
}
