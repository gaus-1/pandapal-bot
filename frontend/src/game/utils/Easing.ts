/**
 * Функции плавности для анимаций
 * Все функции принимают t от 0 до 1 и возвращают значение от 0 до 1
 */
export class Easing {
  /**
   * Линейная интерполяция
   */
  static linear(t: number): number {
    return t;
  }

  /**
   * Плавное начало (ease-in)
   */
  static easeIn(t: number): number {
    return t * t;
  }

  /**
   * Плавное окончание (ease-out)
   */
  static easeOut(t: number): number {
    return t * (2 - t);
  }

  /**
   * Плавное начало и окончание (ease-in-out)
   */
  static easeInOut(t: number): number {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  }

  /**
   * Кубическая плавность (ease-in-out cubic)
   */
  static easeInOutCubic(t: number): number {
    return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
  }

  /**
   * Эластичный эффект (elastic)
   */
  static elastic(t: number): number {
    const p = 0.3;
    return Math.pow(2, -10 * t) * Math.sin(((t - p / 4) * (2 * Math.PI)) / p) + 1;
  }

  /**
   * Отскок (bounce)
   */
  static bounce(t: number): number {
    if (t < 1 / 2.75) {
      return 7.5625 * t * t;
    } else if (t < 2 / 2.75) {
      const t2 = t - 1.5 / 2.75;
      return 7.5625 * t2 * t2 + 0.75;
    } else if (t < 2.5 / 2.75) {
      const t2 = t - 2.25 / 2.75;
      return 7.5625 * t2 * t2 + 0.9375;
    } else {
      const t2 = t - 2.625 / 2.75;
      return 7.5625 * t2 * t2 + 0.984375;
    }
  }

  /**
   * Интерполяция между двумя значениями
   */
  static lerp(start: number, end: number, t: number): number {
    return start + (end - start) * t;
  }

  /**
   * Интерполяция с функцией плавности
   */
  static lerpWithEasing(
    start: number,
    end: number,
    t: number,
    easingFn: (t: number) => number = Easing.easeInOutCubic
  ): number {
    return start + (end - start) * easingFn(t);
  }
}
