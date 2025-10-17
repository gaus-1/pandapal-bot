/**
 * Игровой мир для PandaPal Go
 * Создает 3D окружение с элементами для взаимодействия
 *
 * @module components/GameWorld
 */

import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Mesh, Group } from 'three';
import { useGameStore } from '../stores/gameStore';
import { GameUtils } from '../utils/gameMath';

/**
 * Свойства компонента игрового мира
 */
interface GameWorldProps {
  /** Размер игрового мира */
  size?: number;
  /** Видимость мира */
  visible?: boolean;
}

/**
 * Игровые объекты
 */
interface GameObject {
  id: string;
  position: [number, number, number];
  type: 'bamboo' | 'coin' | 'flower' | 'tree';
  collected: boolean;
}

/**
 * 3D игровой мир
 */
export const GameWorld: React.FC<GameWorldProps> = React.memo(({
  size = 100,
  visible = true,
}) => {
  const worldRef = useRef<Group>(null);
  const { addCoins, addExperience } = useGameStore();

  // Игровые объекты
  const gameObjects = useRef<GameObject[]>([
    // Бамбук для еды
    { id: 'bamboo1', position: [-10, 0, -10], type: 'bamboo', collected: false },
    { id: 'bamboo2', position: [15, 0, -5], type: 'bamboo', collected: false },
    { id: 'bamboo3', position: [-5, 0, 20], type: 'bamboo', collected: false },

    // Монеты
    { id: 'coin1', position: [8, 1, 8], type: 'coin', collected: false },
    { id: 'coin2', position: [-15, 1, 12], type: 'coin', collected: false },
    { id: 'coin3', position: [20, 1, -15], type: 'coin', collected: false },
    { id: 'coin4', position: [-8, 1, -20], type: 'coin', collected: false },

    // Цветы для красоты
    { id: 'flower1', position: [12, 0, 18], type: 'flower', collected: false },
    { id: 'flower2', position: [-18, 0, -8], type: 'flower', collected: false },
    { id: 'flower3', position: [25, 0, 5], type: 'flower', collected: false },

    // Деревья
    { id: 'tree1', position: [30, 0, 30], type: 'tree', collected: false },
    { id: 'tree2', position: [-30, 0, 30], type: 'tree', collected: false },
    { id: 'tree3', position: [30, 0, -30], type: 'tree', collected: false },
    { id: 'tree4', position: [-30, 0, -30], type: 'tree', collected: false },
  ]);

  /**
   * Анимация игровых объектов
   */
  useFrame((state, delta) => {
    if (!worldRef.current) return;

    // Анимация монет (вращение)
    gameObjects.current.forEach((obj) => {
      if (obj.type === 'coin' && !obj.collected) {
        const coinElement = worldRef.current?.children.find(
          (child) => child.userData?.objectId === obj.id
        );
        if (coinElement) {
          coinElement.rotation.y += delta * 2;
        }
      }
    });
  });

  /**
   * Обработка сбора объекта
   */
  const handleObjectCollection = (objectId: string) => {
    const obj = gameObjects.current.find(o => o.id === objectId);
    if (!obj || obj.collected) return;

    obj.collected = true;

    // Добавляем награды
    switch (obj.type) {
      case 'bamboo':
        addExperience(5);
        break;
      case 'coin':
        addCoins(10);
        addExperience(2);
        break;
      case 'flower':
        addExperience(1);
        break;
    }
  };

  /**
   * Рендер бамбука
   */
  const renderBamboo = (obj: GameObject) => (
    <group key={obj.id} position={obj.position}>
      <mesh userData={{ objectId: obj.id, type: 'bamboo' }}>
        <cylinderGeometry args={[0.1, 0.1, 3, 8]} />
        <meshLambertMaterial color="#4a7c59" />
      </mesh>
      <mesh position={[0, 1.5, 0]}>
        <sphereGeometry args={[0.3, 8, 8]} />
        <meshLambertMaterial color="#2d5a3d" />
      </mesh>
    </group>
  );

  /**
   * Рендер монеты
   */
  const renderCoin = (obj: GameObject) => (
    <mesh key={obj.id} position={obj.position} userData={{ objectId: obj.id, type: 'coin' }}>
      <cylinderGeometry args={[0.5, 0.5, 0.1, 16]} />
      <meshLambertMaterial color="#ffd700" />
    </mesh>
  );

  /**
   * Рендер цветка
   */
  const renderFlower = (obj: GameObject) => (
    <group key={obj.id} position={obj.position}>
      <mesh position={[0, 0.1, 0]}>
        <cylinderGeometry args={[0.05, 0.05, 0.5, 8]} />
        <meshLambertMaterial color="#4a7c59" />
      </mesh>
      <mesh position={[0, 0.4, 0]}>
        <sphereGeometry args={[0.3, 8, 8]} />
        <meshLambertMaterial color="#ff69b4" />
      </mesh>
    </group>
  );

  /**
   * Рендер дерева
   */
  const renderTree = (obj: GameObject) => (
    <group key={obj.id} position={obj.position}>
      {/* Ствол */}
      <mesh position={[0, 2, 0]}>
        <cylinderGeometry args={[0.5, 0.8, 4, 8]} />
        <meshLambertMaterial color="#8b4513" />
      </mesh>
      {/* Крона */}
      <mesh position={[0, 5, 0]}>
        <sphereGeometry args={[2, 16, 16]} />
        <meshLambertMaterial color="#228b22" />
      </mesh>
    </group>
  );

  return (
    <group ref={worldRef} visible={visible}>
      {/* Земля */}
      <mesh position={[0, -0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[size, size]} />
        <meshLambertMaterial color="#90ee90" />
      </mesh>

      {/* Трава */}
      <mesh position={[0, -0.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[size * 0.8, size * 0.8]} />
        <meshLambertMaterial color="#32cd32" transparent opacity={0.7} />
      </mesh>

      {/* Границы мира (невидимые стены) */}
      <mesh position={[size / 2, 5, 0]} rotation={[0, 0, Math.PI / 2]}>
        <planeGeometry args={[10, size]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>
      <mesh position={[-size / 2, 5, 0]} rotation={[0, 0, -Math.PI / 2]}>
        <planeGeometry args={[10, size]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>
      <mesh position={[0, 5, size / 2]} rotation={[0, 0, 0]}>
        <planeGeometry args={[size, 10]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>
      <mesh position={[0, 5, -size / 2]} rotation={[0, 0, Math.PI]}>
        <planeGeometry args={[size, 10]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>

      {/* Игровые объекты */}
      {gameObjects.current.map((obj) => {
        if (obj.collected) return null;

        switch (obj.type) {
          case 'bamboo':
            return renderBamboo(obj);
          case 'coin':
            return renderCoin(obj);
          case 'flower':
            return renderFlower(obj);
          case 'tree':
            return renderTree(obj);
          default:
            return null;
        }
      })}

      {/* Декоративные элементы */}

      {/* Камни */}
      {Array.from({ length: 8 }, (_, i) => (
        <mesh key={`rock${i}`} position={[
          GameUtils.randomBetween(-size/2, size/2),
          0,
          GameUtils.randomBetween(-size/2, size/2)
        ]}>
          <sphereGeometry args={[0.3, 8, 8]} />
          <meshLambertMaterial color="#696969" />
        </mesh>
      ))}

      {/* Облака */}
      {Array.from({ length: 5 }, (_, i) => (
        <group key={`cloud${i}`} position={[
          GameUtils.randomBetween(-size/2, size/2),
          GameUtils.randomBetween(8, 15),
          GameUtils.randomBetween(-size/2, size/2)
        ]}>
          <mesh>
            <sphereGeometry args={[1, 8, 8]} />
            <meshLambertMaterial color="#ffffff" />
          </mesh>
          <mesh position={[1, 0, 0]}>
            <sphereGeometry args={[0.8, 8, 8]} />
            <meshLambertMaterial color="#ffffff" />
          </mesh>
          <mesh position={[-1, 0, 0]}>
            <sphereGeometry args={[0.6, 8, 8]} />
            <meshLambertMaterial color="#ffffff" />
          </mesh>
        </group>
      ))}

      {/* Освещение мира */}
      <ambientLight intensity={0.4} />
      <directionalLight position={[10, 10, 5]} intensity={0.6} />
      <pointLight position={[0, 10, 0]} intensity={0.3} />
    </group>
  );
});

GameWorld.displayName = 'GameWorld';
