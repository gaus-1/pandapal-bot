/**
 * Двумерный вектор для физики и позиций
 * Immutable для безопасности
 */
export class Vector2D {
  public readonly x: number;
  public readonly y: number;

  constructor(x: number, y: number) {
    this.x = x;
    this.y = y;
  }

  /**
   * Сложение векторов
   */
  add(other: Vector2D): Vector2D {
    return new Vector2D(this.x + other.x, this.y + other.y);
  }

  /**
   * Вычитание векторов
   */
  subtract(other: Vector2D): Vector2D {
    return new Vector2D(this.x - other.x, this.y - other.y);
  }

  /**
   * Умножение на скаляр
   */
  multiply(scalar: number): Vector2D {
    return new Vector2D(this.x * scalar, this.y * scalar);
  }

  /**
   * Длина вектора
   */
  length(): number {
    return Math.sqrt(this.x * this.x + this.y * this.y);
  }

  /**
   * Нормализация вектора
   */
  normalize(): Vector2D {
    const len = this.length();
    if (len === 0) return new Vector2D(0, 0);
    return new Vector2D(this.x / len, this.y / len);
  }

  /**
   * Скалярное произведение
   */
  dot(other: Vector2D): number {
    return this.x * other.x + this.y * other.y;
  }

  /**
   * Отражение вектора относительно нормали
   */
  reflect(normal: Vector2D): Vector2D {
    const dot = this.dot(normal);
    return this.subtract(normal.multiply(2 * dot));
  }

  /**
   * Расстояние до другой точки
   */
  distanceTo(other: Vector2D): number {
    return this.subtract(other).length();
  }

  /**
   * Клонирование
   */
  clone(): Vector2D {
    return new Vector2D(this.x, this.y);
  }

  /**
   * Статические утилиты
   */
  static zero(): Vector2D {
    return new Vector2D(0, 0);
  }

  static one(): Vector2D {
    return new Vector2D(1, 1);
  }
}
