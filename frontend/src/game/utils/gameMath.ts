/**
 * Утилиты для игровой математики PandaPal Go
 * Векторные операции, физика, анимации
 *
 * @module utils/gameMath
 */

import type { Vector3 } from '../stores/gameStore';

/**
 * Класс для работы с 3D векторами
 */
export class Vector3D {
  x: number;
  y: number;
  z: number;

  constructor(x: number = 0, y: number = 0, z: number = 0) {
    this.x = x;
    this.y = y;
    this.z = z;
  }

  /**
   * Создает вектор из объекта Vector3
   */
  static fromVector3(v: Vector3): Vector3D {
    return new Vector3D(v.x, v.y, v.z);
  }

  /**
   * Преобразует в объект Vector3
   */
  toVector3(): Vector3 {
    return { x: this.x, y: this.y, z: this.z };
  }

  /**
   * Добавляет другой вектор
   */
  add(other: Vector3D): Vector3D {
    return new Vector3D(this.x + other.x, this.y + other.y, this.z + other.z);
  }

  /**
   * Вычитает другой вектор
   */
  subtract(other: Vector3D): Vector3D {
    return new Vector3D(this.x - other.x, this.y - other.y, this.z - other.z);
  }

  /**
   * Умножает на скаляр
   */
  multiply(scalar: number): Vector3D {
    return new Vector3D(this.x * scalar, this.y * scalar, this.z * scalar);
  }

  /**
   * Вычисляет длину вектора
   */
  length(): number {
    return Math.sqrt(this.x * this.x + this.y * this.y + this.z * this.z);
  }

  /**
   * Нормализует вектор
   */
  normalize(): Vector3D {
    const len = this.length();
    if (len === 0) return new Vector3D(0, 0, 0);
    return new Vector3D(this.x / len, this.y / len, this.z / len);
  }

  /**
   * Вычисляет расстояние до другого вектора
   */
  distanceTo(other: Vector3D): number {
    return this.subtract(other).length();
  }

  /**
   * Линейная интерполяция между векторами
   */
  lerp(other: Vector3D, t: number): Vector3D {
    return new Vector3D(
      this.x + (other.x - this.x) * t,
      this.y + (other.y - this.y) * t,
      this.z + (other.z - this.z) * t
    );
  }
}

/**
 * Игровая физика
 */
export class GamePhysics {
  /**
   * Гравитация
   */
  static readonly GRAVITY = -9.81;

  /**
   * Максимальная скорость движения
   */
  static readonly MAX_SPEED = 5.0;

  /**
   * Ускорение движения
   */
  static readonly ACCELERATION = 10.0;

  /**
   * Трение
   */
  static readonly FRICTION = 0.8;

  /**
   * Вычисляет движение с учетом физики
   */
  static calculateMovement(
    currentPosition: Vector3D,
    velocity: Vector3D,
    inputDirection: Vector3D,
    deltaTime: number
  ): { position: Vector3D; velocity: Vector3D } {
    // Применяем ускорение в направлении ввода
    const acceleration = inputDirection.multiply(this.ACCELERATION);

    // Обновляем скорость
    let newVelocity = velocity.add(acceleration.multiply(deltaTime));

    // Ограничиваем максимальную скорость
    if (newVelocity.length() > this.MAX_SPEED) {
      newVelocity = newVelocity.normalize().multiply(this.MAX_SPEED);
    }

    // Применяем трение
    newVelocity = newVelocity.multiply(this.FRICTION);

    // Обновляем позицию
    const newPosition = currentPosition.add(newVelocity.multiply(deltaTime));

    // Применяем гравитацию к Y-координате
    newPosition.y += this.GRAVITY * deltaTime * deltaTime * 0.5;

    return { position: newPosition, velocity: newVelocity };
  }

  /**
   * Проверяет коллизию с границами
   */
  static checkBoundaries(position: Vector3D, bounds: {
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
    minZ: number;
    maxZ: number;
  }): Vector3D {
    let newPosition = position;

    if (newPosition.x < bounds.minX) newPosition.x = bounds.minX;
    if (newPosition.x > bounds.maxX) newPosition.x = bounds.maxX;
    if (newPosition.y < bounds.minY) newPosition.y = bounds.minY;
    if (newPosition.y > bounds.maxY) newPosition.y = bounds.maxY;
    if (newPosition.z < bounds.minZ) newPosition.z = bounds.minZ;
    if (newPosition.z > bounds.maxZ) newPosition.z = bounds.maxZ;

    return newPosition;
  }
}

/**
 * Анимационные утилиты
 */
export class AnimationUtils {
  /**
   * Ease-in-out функция для плавных анимаций
   */
  static easeInOut(t: number): number {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  }

  /**
   * Ease-out функция
   */
  static easeOut(t: number): number {
    return 1 - Math.pow(1 - t, 3);
  }

  /**
   * Ease-in функция
   */
  static easeIn(t: number): number {
    return t * t * t;
  }

  /**
   * Линейная интерполяция с easing
   */
  static lerpWithEasing(
    start: number,
    end: number,
    t: number,
    easing: (t: number) => number = AnimationUtils.easeInOut
  ): number {
    return start + (end - start) * easing(t);
  }

  /**
   * Пульсация (для дыхания, сердцебиения)
   */
  static pulse(t: number, frequency: number = 1): number {
    return Math.sin(t * frequency * Math.PI * 2) * 0.5 + 0.5;
  }

  /**
   * Покачивание (для idle анимации)
   */
  static sway(t: number, amplitude: number = 0.1, frequency: number = 0.5): number {
    return Math.sin(t * frequency * Math.PI * 2) * amplitude;
  }
}

/**
 * Игровые утилиты
 */
export class GameUtils {
  /**
   * Генерирует случайное число в диапазоне
   */
  static randomBetween(min: number, max: number): number {
    return Math.random() * (max - min) + min;
  }

  /**
   * Генерирует случайную позицию в сфере
   */
  static randomPositionInSphere(radius: number): Vector3D {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const r = Math.cbrt(Math.random()) * radius;

    return new Vector3D(
      r * Math.sin(phi) * Math.cos(theta),
      r * Math.sin(phi) * Math.sin(theta),
      r * Math.cos(phi)
    );
  }

  /**
   * Вычисляет направление к цели
   */
  static directionTo(from: Vector3D, to: Vector3D): Vector3D {
    return to.subtract(from).normalize();
  }

  /**
   * Проверяет, находится ли точка в радиусе
   */
  static isWithinRadius(point: Vector3D, center: Vector3D, radius: number): boolean {
    return point.distanceTo(center) <= radius;
  }

  /**
   * Форматирует время в игровой формат
   */
  static formatGameTime(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  /**
   * Вычисляет опыт для следующего уровня
   */
  static getExperienceForLevel(level: number): number {
    return level * 100;
  }

  /**
   * Вычисляет прогресс до следующего уровня
   */
  static getLevelProgress(currentExp: number, level: number): number {
    const currentLevelExp = this.getExperienceForLevel(level - 1);
    const nextLevelExp = this.getExperienceForLevel(level);
    return (currentExp - currentLevelExp) / (nextLevelExp - currentLevelExp);
  }
}
