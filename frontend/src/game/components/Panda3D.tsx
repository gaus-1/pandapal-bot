/**
 * 3D модель панды для игры PandaPal Go
 * Создана на основе логотипа проекта с реалистичными пропорциями
 *
 * @module components/Panda3D
 */

import React, { useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { Mesh, Group } from 'three';
import { useGameStore, type PandaAnimation } from '../stores/gameStore';
import { AnimationUtils } from '../utils/gameMath';

/**
 * Свойства компонента панды
 */
interface Panda3DProps {
  /** Позиция панды */
  position?: [number, number, number];
  /** Масштаб модели */
  scale?: number;
  /** Видимость модели */
  visible?: boolean;
}

/**
 * 3D модель панды с анимациями
 */
export const Panda3D: React.FC<Panda3DProps> = React.memo(({
  position = [0, 0, 0],
  scale = 1,
  visible = true,
}) => {
  const groupRef = useRef<Group>(null);
  const bodyRef = useRef<Mesh>(null);
  const headRef = useRef<Mesh>(null);
  const leftEarRef = useRef<Mesh>(null);
  const rightEarRef = useRef<Mesh>(null);
  const leftEyeRef = useRef<Mesh>(null);
  const rightEyeRef = useRef<Mesh>(null);
  const noseRef = useRef<Mesh>(null);
  const leftArmRef = useRef<Mesh>(null);
  const rightArmRef = useRef<Mesh>(null);
  const leftLegRef = useRef<Mesh>(null);
  const rightLegRef = useRef<Mesh>(null);
  const tailRef = useRef<Mesh>(null);

  // Получаем состояние панды из стора
  const { panda } = useGameStore();
  const { animation, position: pandaPosition, rotation } = panda;

  // Анимационные переменные
  const timeRef = useRef(0);
  const breathingRef = useRef(0);
  const idleSwayRef = useRef(0);

  /**
   * Обновление анимаций
   */
  useFrame((state, delta) => {
    if (!groupRef.current) return;

    timeRef.current += delta;
    breathingRef.current += delta;
    idleSwayRef.current += delta;

    // Обновляем позицию и поворот
    groupRef.current.position.set(
      pandaPosition.x,
      pandaPosition.y,
      pandaPosition.z
    );
    groupRef.current.rotation.y = rotation.y;

    // Анимация дыхания (всегда активна)
    const breathingScale = 1 + Math.sin(breathingRef.current * 2) * 0.02;
    if (bodyRef.current) {
      bodyRef.current.scale.y = breathingScale;
    }
    if (headRef.current) {
      headRef.current.scale.y = breathingScale;
    }

    // Анимации в зависимости от состояния
    switch (animation) {
      case 'idle':
        handleIdleAnimation();
        break;
      case 'walk':
        handleWalkAnimation();
        break;
      case 'eat':
        handleEatAnimation();
        break;
      case 'play':
        handlePlayAnimation();
        break;
      case 'sleep':
        handleSleepAnimation();
        break;
      case 'happy':
        handleHappyAnimation();
        break;
    }
  });

  /**
   * Анимация покоя (idle)
   */
  const handleIdleAnimation = () => {
    // Покачивание из стороны в сторону
    const sway = AnimationUtils.sway(idleSwayRef.current, 0.05, 0.3);
    if (groupRef.current) {
      groupRef.current.rotation.z = sway;
    }

    // Покачивание головы
    const headSway = AnimationUtils.sway(idleSwayRef.current + 1, 0.03, 0.2);
    if (headRef.current) {
      headRef.current.rotation.z = headSway;
    }
  };

  /**
   * Анимация ходьбы
   */
  const handleWalkAnimation = () => {
    const walkCycle = Math.sin(timeRef.current * 8) * 0.5 + 0.5;

    // Покачивание тела
    if (bodyRef.current) {
      bodyRef.current.rotation.x = Math.sin(timeRef.current * 8) * 0.1;
    }

    // Движение лап
    const legSwing = Math.sin(timeRef.current * 8) * 0.3;
    if (leftLegRef.current) {
      leftLegRef.current.rotation.x = legSwing;
    }
    if (rightLegRef.current) {
      rightLegRef.current.rotation.x = -legSwing;
    }

    // Движение рук
    if (leftArmRef.current) {
      leftArmRef.current.rotation.x = -legSwing;
    }
    if (rightArmRef.current) {
      rightArmRef.current.rotation.x = legSwing;
    }

    // Движение хвоста
    if (tailRef.current) {
      tailRef.current.rotation.y = Math.sin(timeRef.current * 6) * 0.2;
    }
  };

  /**
   * Анимация еды
   */
  const handleEatAnimation = () => {
    const eatCycle = Math.sin(timeRef.current * 4) * 0.5 + 0.5;

    // Наклон головы вниз
    if (headRef.current) {
      headRef.current.rotation.x = AnimationUtils.lerpWithEasing(
        0, -0.5, eatCycle
      );
    }

    // Движение рук к лицу
    if (leftArmRef.current) {
      leftArmRef.current.rotation.x = AnimationUtils.lerpWithEasing(
        0, -1, eatCycle
      );
    }
    if (rightArmRef.current) {
      rightArmRef.current.rotation.x = AnimationUtils.lerpWithEasing(
        0, -1, eatCycle
      );
    }

    // Жевательные движения челюсти
    const jawMovement = Math.sin(timeRef.current * 8) * 0.1;
    if (headRef.current) {
      headRef.current.scale.y = 1 + jawMovement;
    }
  };

  /**
   * Анимация игры
   */
  const handlePlayAnimation = () => {
    const playCycle = Math.sin(timeRef.current * 6) * 0.5 + 0.5;

    // Прыжки
    if (groupRef.current) {
      groupRef.current.position.y = pandaPosition.y + Math.sin(timeRef.current * 6) * 0.3;
    }

    // Вращение
    groupRef.current!.rotation.y += 0.02;

    // Активное движение лап
    const legSwing = Math.sin(timeRef.current * 12) * 0.5;
    if (leftLegRef.current) {
      leftLegRef.current.rotation.x = legSwing;
    }
    if (rightLegRef.current) {
      rightLegRef.current.rotation.x = -legSwing;
    }
  };

  /**
   * Анимация сна
   */
  const handleSleepAnimation = () => {
    // Лежание
    if (bodyRef.current) {
      bodyRef.current.rotation.z = Math.PI / 2;
    }

    // Наклон головы
    if (headRef.current) {
      headRef.current.rotation.x = 0.5;
      headRef.current.rotation.z = 0.3;
    }

    // Медленное дыхание
    const slowBreathing = 1 + Math.sin(breathingRef.current * 0.5) * 0.05;
    if (bodyRef.current) {
      bodyRef.current.scale.y = slowBreathing;
    }
  };

  /**
   * Анимация счастья
   */
  const handleHappyAnimation = () => {
    // Подпрыгивание
    if (groupRef.current) {
      groupRef.current.position.y = pandaPosition.y + Math.sin(timeRef.current * 4) * 0.2;
    }

    // Вращение головы
    if (headRef.current) {
      headRef.current.rotation.y = Math.sin(timeRef.current * 3) * 0.2;
    }

    // Махание руками
    const armWave = Math.sin(timeRef.current * 5) * 0.4;
    if (leftArmRef.current) {
      leftArmRef.current.rotation.z = armWave;
    }
    if (rightArmRef.current) {
      rightArmRef.current.rotation.z = -armWave;
    }

    // Активное движение хвоста
    if (tailRef.current) {
      tailRef.current.rotation.y = Math.sin(timeRef.current * 8) * 0.5;
    }
  };

  return (
    <group ref={groupRef} position={position} scale={scale} visible={visible}>
      {/* Тело панды */}
      <mesh ref={bodyRef} position={[0, 0, 0]}>
        <sphereGeometry args={[1.2, 16, 16]} />
        <meshLambertMaterial color="#ffffff" />
      </mesh>

      {/* Голова */}
      <mesh ref={headRef} position={[0, 1.5, 0]}>
        <sphereGeometry args={[0.8, 16, 16]} />
        <meshLambertMaterial color="#ffffff" />
      </mesh>

      {/* Левое ухо */}
      <mesh ref={leftEarRef} position={[-0.6, 2, 0]}>
        <sphereGeometry args={[0.3, 8, 8]} />
        <meshLambertMaterial color="#000000" />
      </mesh>

      {/* Правое ухо */}
      <mesh ref={rightEarRef} position={[0.6, 2, 0]}>
        <sphereGeometry args={[0.3, 8, 8]} />
        <meshLambertMaterial color="#000000" />
      </mesh>

      {/* Левое ухо (белая часть) */}
      <mesh position={[-0.6, 2.1, 0]}>
        <sphereGeometry args={[0.15, 8, 8]} />
        <meshLambertMaterial color="#ffffff" />
      </mesh>

      {/* Правое ухо (белая часть) */}
      <mesh position={[0.6, 2.1, 0]}>
        <sphereGeometry args={[0.15, 8, 8]} />
        <meshLambertMaterial color="#ffffff" />
      </mesh>

      {/* Левая глазная область */}
      <mesh position={[-0.3, 1.7, 0.6]}>
        <sphereGeometry args={[0.25, 8, 8]} />
        <meshLambertMaterial color="#000000" />
      </mesh>

      {/* Правая глазная область */}
      <mesh position={[0.3, 1.7, 0.6]}>
        <sphereGeometry args={[0.25, 8, 8]} />
        <meshLambertMaterial color="#000000" />
      </mesh>

      {/* Левый глаз */}
      <mesh ref={leftEyeRef} position={[-0.3, 1.7, 0.65]}>
        <sphereGeometry args={[0.08, 8, 8]} />
        <meshLambertMaterial color="#ffffff" />
      </mesh>

      {/* Правый глаз */}
      <mesh ref={rightEyeRef} position={[0.3, 1.7, 0.65]}>
        <sphereGeometry args={[0.08, 8, 8]} />
        <meshLambertMaterial color="#ffffff" />
      </mesh>

      {/* Нос */}
      <mesh ref={noseRef} position={[0, 1.4, 0.7]}>
        <sphereGeometry args={[0.1, 8, 8]} />
        <meshLambertMaterial color="#000000" />
      </mesh>

      {/* Левая рука */}
      <mesh ref={leftArmRef} position={[-1.3, 0.5, 0]}>
        <sphereGeometry args={[0.4, 12, 12]} />
        <meshLambertMaterial color="#000000" />
      </mesh>

      {/* Правая рука */}
      <mesh ref={rightArmRef} position={[1.3, 0.5, 0]}>
        <sphereGeometry args={[0.4, 12, 12]} />
        <meshLambertMaterial color="#000000" />
      </mesh>

      {/* Левая нога */}
      <mesh ref={leftLegRef} position={[-0.4, -1.2, 0]}>
        <sphereGeometry args={[0.4, 12, 12]} />
        <meshLambertMaterial color="#000000" />
      </mesh>

      {/* Правая нога */}
      <mesh ref={rightLegRef} position={[0.4, -1.2, 0]}>
        <sphereGeometry args={[0.4, 12, 12]} />
        <meshLambertMaterial color="#000000" />
      </mesh>

      {/* Хвост */}
      <mesh ref={tailRef} position={[0, -0.8, -1]}>
        <sphereGeometry args={[0.3, 8, 8]} />
        <meshLambertMaterial color="#ffffff" />
      </mesh>

      {/* Освещение для панды */}
      <pointLight position={[0, 3, 2]} intensity={0.5} />
      <ambientLight intensity={0.3} />
    </group>
  );
});

Panda3D.displayName = 'Panda3D';
