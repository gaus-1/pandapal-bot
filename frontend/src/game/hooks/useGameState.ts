/**
 * Хук для управления состоянием игры PandaPal Go
 * Обрабатывает логику игры, физику, анимации
 *
 * @module hooks/useGameState
 */

import { useEffect, useRef, useCallback } from 'react';
import { useGameStore, type Vector3, type PandaAnimation } from '../stores/gameStore';
import { Vector3D, GamePhysics, AnimationUtils, GameUtils } from '../utils/gameMath';

/**
 * Конфигурация игры
 */
const GAME_CONFIG = {
  // Границы игрового мира
  bounds: {
    minX: -50,
    maxX: 50,
    minY: 0,
    maxY: 20,
    minZ: -50,
    maxZ: 50,
  },
  // Скорость движения
  moveSpeed: 5.0,
  // Скорость поворота
  rotationSpeed: 2.0,
  // Интервал обновления анимации
  animationInterval: 100, // мс
  // Интервал обновления AI
  aiInterval: 2000, // мс
} as const;

/**
 * Состояние управления
 */
interface ControlState {
  forward: boolean;
  backward: boolean;
  left: boolean;
  right: boolean;
  running: boolean;
}

/**
 * Хук для управления состоянием игры
 */
export const useGameState = () => {
  const {
    gameState,
    panda,
    stats,
    settings,
    setGameState,
    updatePandaPosition,
    updatePandaAnimation,
    updateStats,
    addCoins,
    addExperience,
  } = useGameStore();

  // Ссылки для анимации
  const animationFrameRef = useRef<number>();
  const lastTimeRef = useRef<number>(0);
  const velocityRef = useRef<Vector3D>(new Vector3D());
  const controlsRef = useRef<ControlState>({
    forward: false,
    backward: false,
    left: false,
    right: false,
    running: false,
  });

  // AI таймеры
  const aiTimerRef = useRef<NodeJS.Timeout>();
  const lastAiActionRef = useRef<number>(0);

  /**
   * Обновляет позицию панды
   */
  const updatePosition = useCallback((newPosition: Vector3) => {
    updatePandaPosition(newPosition);
  }, [updatePandaPosition]);

  /**
   * Обновляет анимацию панды
   */
  const updateAnimation = useCallback((animation: PandaAnimation) => {
    updatePandaAnimation(animation);
  }, [updatePandaAnimation]);

  /**
   * Обрабатывает пользовательский ввод
   */
  const handleInput = useCallback((controls: Partial<ControlState>) => {
    controlsRef.current = { ...controlsRef.current, ...controls };
  }, []);

  /**
   * Обрабатывает движение панды
   */
  const processMovement = useCallback((deltaTime: number) => {
    const controls = controlsRef.current;
    let inputDirection = new Vector3D();

    // Вычисляем направление движения
    if (controls.forward) inputDirection.z -= 1;
    if (controls.backward) inputDirection.z += 1;
    if (controls.left) inputDirection.x -= 1;
    if (controls.right) inputDirection.x += 1;

    // Нормализуем направление
    if (inputDirection.length() > 0) {
      inputDirection = inputDirection.normalize();

      // Увеличиваем скорость при беге
      const speed = controls.running ? GAME_CONFIG.moveSpeed * 1.5 : GAME_CONFIG.moveSpeed;
      inputDirection = inputDirection.multiply(speed);
    }

    // Применяем физику
    const currentPos = Vector3D.fromVector3(panda.position);
    const physics = GamePhysics.calculateMovement(
      currentPos,
      velocityRef.current,
      inputDirection,
      deltaTime
    );

    // Проверяем границы
    const boundedPosition = GamePhysics.checkBoundaries(
      physics.position,
      GAME_CONFIG.bounds
    );

    // Обновляем состояние
    updatePosition(boundedPosition.toVector3());
    velocityRef.current = physics.velocity;

    // Обновляем анимацию
    const isMoving = inputDirection.length() > 0;
    if (isMoving !== panda.isMoving) {
      updateAnimation(isMoving ? 'walk' : 'idle');
    }

    // Обновляем поворот
    if (isMoving) {
      const targetRotation = Math.atan2(inputDirection.x, inputDirection.z);
      const currentRotation = panda.rotation.y;
      const rotationDiff = targetRotation - currentRotation;

      // Нормализуем разность углов
      let normalizedDiff = rotationDiff;
      while (normalizedDiff > Math.PI) normalizedDiff -= 2 * Math.PI;
      while (normalizedDiff < -Math.PI) normalizedDiff += 2 * Math.PI;

      const newRotation = currentRotation + normalizedDiff * GAME_CONFIG.rotationSpeed * deltaTime;
      updatePosition({ ...panda.position, y: newRotation });
    }
  }, [panda.position, panda.rotation.y, panda.isMoving, updatePosition, updateAnimation]);

  /**
   * Обрабатывает AI поведение панды
   */
  const processPandaAI = useCallback(() => {
    const now = Date.now();

    // Случайные действия панды
    if (now - lastAiActionRef.current > 5000) {
      const actions: PandaAnimation[] = ['idle', 'play', 'eat'];
      const randomAction = actions[Math.floor(Math.random() * actions.length)];

      if (randomAction !== panda.animation) {
        updateAnimation(randomAction);

        // Добавляем опыт за активность
        addExperience(1);
      }

      lastAiActionRef.current = now;
    }

    // Случайные движения
    if (Math.random() < 0.01) { // 1% шанс каждую секунду
      const randomDirection = GameUtils.randomPositionInSphere(10);
      const newPosition = Vector3D.fromVector3(panda.position)
        .add(randomDirection.multiply(0.1));

      updatePosition(newPosition.toVector3());
    }
  }, [panda.animation, panda.position, updateAnimation, updatePosition, addExperience]);

  /**
   * Основной игровой цикл
   */
  const gameLoop = useCallback((currentTime: number) => {
    if (gameState !== 'playing') {
      return;
    }

    const deltaTime = (currentTime - lastTimeRef.current) / 1000; // в секундах
    lastTimeRef.current = currentTime;

    // Обрабатываем движение
    processMovement(deltaTime);

    // Обрабатываем AI
    processPandaAI();

    // Продолжаем цикл
    animationFrameRef.current = requestAnimationFrame(gameLoop);
  }, [gameState, processMovement, processPandaAI]);

  /**
   * Инициализация игры
   */
  const initializeGame = useCallback(() => {
    setGameState('loading');

    // Сброс состояния панды
    updatePosition({ x: 0, y: 0, z: 0 });
    updateAnimation('idle');

    // Запуск игрового цикла
    setTimeout(() => {
      setGameState('playing');
      lastTimeRef.current = performance.now();
      animationFrameRef.current = requestAnimationFrame(gameLoop);
    }, 1000);
  }, [setGameState, updatePosition, updateAnimation, gameLoop]);

  /**
   * Остановка игры
   */
  const stopGame = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (aiTimerRef.current) {
      clearTimeout(aiTimerRef.current);
    }
    setGameState('paused');
  }, [setGameState]);

  /**
   * Возобновление игры
   */
  const resumeGame = useCallback(() => {
    setGameState('playing');
    lastTimeRef.current = performance.now();
    animationFrameRef.current = requestAnimationFrame(gameLoop);
  }, [setGameState, gameLoop]);

  /**
   * Обработка событий клавиатуры
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      switch (event.code) {
        case 'KeyW':
        case 'ArrowUp':
          handleInput({ forward: true });
          break;
        case 'KeyS':
        case 'ArrowDown':
          handleInput({ backward: true });
          break;
        case 'KeyA':
        case 'ArrowLeft':
          handleInput({ left: true });
          break;
        case 'KeyD':
        case 'ArrowRight':
          handleInput({ right: true });
          break;
        case 'ShiftLeft':
        case 'ShiftRight':
          handleInput({ running: true });
          break;
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      switch (event.code) {
        case 'KeyW':
        case 'ArrowUp':
          handleInput({ forward: false });
          break;
        case 'KeyS':
        case 'ArrowDown':
          handleInput({ backward: false });
          break;
        case 'KeyA':
        case 'ArrowLeft':
          handleInput({ left: false });
          break;
        case 'KeyD':
        case 'ArrowRight':
          handleInput({ right: false });
          break;
        case 'ShiftLeft':
        case 'ShiftRight':
          handleInput({ running: false });
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [handleInput]);

  /**
   * Очистка при размонтировании
   */
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (aiTimerRef.current) {
        clearTimeout(aiTimerRef.current);
      }
    };
  }, []);

  return {
    // Состояние
    gameState,
    panda,
    stats,
    settings,

    // Действия
    initializeGame,
    stopGame,
    resumeGame,
    handleInput,

    // Утилиты
    isGameActive: gameState === 'playing',
    isGameLoaded: gameState !== 'loading',
  };
};
