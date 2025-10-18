import { Ball } from '../entities/Ball';
import { Brick } from '../entities/Brick';
import { Paddle } from '../entities/Paddle';
import { Vector2D } from '../utils/Vector2D';

/**
 * Результат столкновения
 */
export interface CollisionResult {
  collided: boolean;
  normal?: Vector2D;
  point?: Vector2D;
}

/**
 * Система обнаружения и обработки столкновений
 * Single Responsibility: только логика столкновений
 */
export class CollisionDetector {
  /**
   * Проверка столкновения мяча с кирпичом
   */
  static checkBallBrick(ball: Ball, brick: Brick): CollisionResult {
    if (!brick.active) {
      return { collided: false };
    }

    const ballCenter = ball.getCenter();
    const brickBounds = brick.getBounds();

    // Находим ближайшую точку на кирпиче к центру мяча
    const closestX = Math.max(
      brickBounds.left,
      Math.min(ballCenter.x, brickBounds.right)
    );
    const closestY = Math.max(
      brickBounds.top,
      Math.min(ballCenter.y, brickBounds.bottom)
    );

    const closestPoint = new Vector2D(closestX, closestY);
    const distance = ballCenter.distanceTo(closestPoint);

    if (distance < ball.radius) {
      // Вычисляем нормаль столкновения
      let normal = ballCenter.subtract(closestPoint);

      // Если мяч точно в центре кирпича, используем направление движения
      if (normal.length() < 0.1) {
        normal = ball.velocity.normalize();
      } else {
        normal = normal.normalize();
      }

      return {
        collided: true,
        normal,
        point: closestPoint,
      };
    }

    return { collided: false };
  }

  /**
   * Проверка столкновения мяча с платформой
   */
  static checkBallPaddle(ball: Ball, paddle: Paddle): CollisionResult {
    const ballCenter = ball.getCenter();
    const paddleBounds = paddle.getBounds();

    // Проверяем, что мяч движется вниз
    if (ball.velocity.y <= 0) {
      return { collided: false };
    }

    // Находим ближайшую точку
    const closestX = Math.max(
      paddleBounds.left,
      Math.min(ballCenter.x, paddleBounds.right)
    );
    const closestY = Math.max(
      paddleBounds.top,
      Math.min(ballCenter.y, paddleBounds.bottom)
    );

    const closestPoint = new Vector2D(closestX, closestY);
    const distance = ballCenter.distanceTo(closestPoint);

    if (distance < ball.radius) {
      // Особая обработка для платформы - всегда отскакиваем вверх
      const normal = new Vector2D(0, -1);

      return {
        collided: true,
        normal,
        point: closestPoint,
      };
    }

    return { collided: false };
  }

  /**
   * Проверка столкновения мяча со стенами
   */
  static checkBallWalls(
    ball: Ball,
    canvasWidth: number,
    canvasHeight: number
  ): {
    left: boolean;
    right: boolean;
    top: boolean;
    bottom: boolean;
  } {
    const ballCenter = ball.getCenter();
    const radius = ball.radius;

    return {
      left: ballCenter.x - radius <= 0,
      right: ballCenter.x + radius >= canvasWidth,
      top: ballCenter.y - radius <= 0,
      bottom: ballCenter.y + radius >= canvasHeight,
    };
  }

  /**
   * Обработка отскока мяча от нормали
   */
  static resolveBallCollision(ball: Ball, normal: Vector2D): void {
    const reflected = ball.velocity.reflect(normal);
    ball.setVelocity(reflected.x, reflected.y);
  }

  /**
   * Обработка столкновения с платформой (с учетом позиции удара)
   */
  static resolveBallPaddleCollision(ball: Ball, paddle: Paddle): void {
    const ballCenter = ball.getCenter();
    const hitPosition = paddle.getHitPosition(ballCenter.x);
    ball.bounceOffPaddle(hitPosition);
  }

  /**
   * Принудительное разделение мяча и кирпича (предотвращает застревание)
   */
  static separateBallFromBrick(ball: Ball, brick: Brick): void {
    const ballCenter = ball.getCenter();
    const brickBounds = brick.getBounds();

    // Вычисляем перекрытие
    const overlapX = Math.min(
      ballCenter.x + ball.radius - brickBounds.left,
      brickBounds.right - (ballCenter.x - ball.radius)
    );
    const overlapY = Math.min(
      ballCenter.y + ball.radius - brickBounds.top,
      brickBounds.bottom - (ballCenter.y - ball.radius)
    );

    // Двигаем мяч в направлении наименьшего перекрытия
    if (overlapX < overlapY) {
      // Горизонтальное разделение
      const brickCenterX = brickBounds.left + (brickBounds.right - brickBounds.left) / 2;
      if (ballCenter.x < brickCenterX) {
        ball.setPosition(ball.x - overlapX - 1, ball.y);
      } else {
        ball.setPosition(ball.x + overlapX + 1, ball.y);
      }
    } else {
      // Вертикальное разделение
      const brickCenterY = brickBounds.top + (brickBounds.bottom - brickBounds.top) / 2;
      if (ballCenter.y < brickCenterY) {
        ball.setPosition(ball.x, ball.y - overlapY - 1);
      } else {
        ball.setPosition(ball.x, ball.y + overlapY + 1);
      }
    }
  }

  /**
   * Принудительное разделение мяча и платформы
   */
  static separateBallFromPaddle(ball: Ball, paddle: Paddle): void {
    const paddleBounds = paddle.getBounds();

    // Всегда поднимаем мяч над платформой
    const newY = paddleBounds.top - ball.radius - 1;
    ball.setPosition(ball.x, newY);
  }

  /**
   * Проверка, находится ли точка внутри прямоугольника
   */
  static pointInRect(
    px: number,
    py: number,
    rx: number,
    ry: number,
    rw: number,
    rh: number
  ): boolean {
    return px >= rx && px <= rx + rw && py >= ry && py <= ry + rh;
  }

  /**
   * Проверка столкновения двух прямоугольников (AABB)
   */
  static rectRect(
    x1: number,
    y1: number,
    w1: number,
    h1: number,
    x2: number,
    y2: number,
    w2: number,
    h2: number
  ): boolean {
    return x1 < x2 + w2 && x1 + w1 > x2 && y1 < y2 + h2 && y1 + h1 > y2;
  }
}
