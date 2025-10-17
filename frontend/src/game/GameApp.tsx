/**
 * Главный компонент игры PandaPal Go
 * Объединяет все игровые компоненты в единое приложение
 *
 * @module game/GameApp
 */

import React, { useEffect, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Sky } from '@react-three/drei';
import { useGameState } from './hooks/useGameState';
import { Panda3D } from './components/Panda3D';
import { GameWorld } from './components/GameWorld';
import { GameUI } from './components/GameUI';

/**
 * Компонент загрузки
 */
const LoadingScreen: React.FC = React.memo(() => (
  <div className="fixed inset-0 bg-gradient-to-b from-sky/20 to-pink/20 flex items-center justify-center z-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-pink mx-auto mb-4"></div>
      <h2 className="text-2xl font-bold text-gray-800 mb-2">🐼 PandaPal Go</h2>
      <p className="text-gray-600">Загрузка игры...</p>
    </div>
  </div>
));

LoadingScreen.displayName = 'LoadingScreen';

/**
 * Компонент ошибки
 */
const ErrorScreen: React.FC<{ error: Error; onRetry: () => void }> = React.memo(({ error, onRetry }) => (
  <div className="fixed inset-0 bg-gradient-to-b from-red-100 to-red-200 flex items-center justify-center z-50">
    <div className="text-center bg-white rounded-lg p-8 max-w-md mx-4 shadow-xl">
      <div className="text-6xl mb-4">😔</div>
      <h2 className="text-2xl font-bold text-gray-800 mb-2">Ошибка загрузки</h2>
      <p className="text-gray-600 mb-4">{error.message}</p>
      <button
        onClick={onRetry}
        className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded font-medium transition-colors"
      >
        Попробовать снова
      </button>
    </div>
  </div>
));

ErrorScreen.displayName = 'ErrorScreen';

/**
 * Основной игровой компонент
 */
const GameScene: React.FC = React.memo(() => {
  const {
    gameState,
    isGameActive,
    isGameLoaded,
    initializeGame,
    stopGame,
    resumeGame,
  } = useGameState();

  useEffect(() => {
    // Инициализация игры при монтировании
    initializeGame();
  }, [initializeGame]);

  const handlePause = () => {
    if (isGameActive) {
      stopGame();
    } else {
      resumeGame();
    }
  };

  const handleClose = () => {
    stopGame();
    // Здесь можно добавить логику возврата к основному сайту
    window.history.back();
  };

  return (
    <>
      {/* 3D Canvas */}
      <Canvas
        camera={{
          position: [10, 8, 10],
          fov: 60,
        }}
        shadows
        className="w-full h-full"
      >
        {/* Освещение сцены */}
        <ambientLight intensity={0.4} />
        <directionalLight
          position={[10, 10, 5]}
          intensity={1}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-camera-far={50}
          shadow-camera-left={-25}
          shadow-camera-right={25}
          shadow-camera-top={25}
          shadow-camera-bottom={-25}
        />
        <pointLight position={[0, 10, 0]} intensity={0.5} />

        {/* Небо */}
        <Sky
          distance={450000}
          sunPosition={[0, 1, 0]}
          inclination={0.49}
          azimuth={0.25}
        />

        {/* Управление камерой */}
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          maxPolarAngle={Math.PI / 2}
          minDistance={5}
          maxDistance={50}
          target={[0, 0, 0]}
        />

        {/* Игровой мир */}
        <Suspense fallback={null}>
          <GameWorld size={100} />
        </Suspense>

        {/* Панда */}
        <Suspense fallback={null}>
          <Panda3D position={[0, 0, 0]} scale={1} />
        </Suspense>
      </Canvas>

      {/* Игровой интерфейс */}
      <GameUI
        visible={isGameLoaded}
        onClose={handleClose}
        onPause={handlePause}
      />
    </>
  );
});

GameScene.displayName = 'GameScene';

/**
 * Главный компонент игры с обработкой ошибок
 */
export const GameApp: React.FC = React.memo(() => {
  const [error, setError] = React.useState<Error | null>(null);

  const handleError = (error: Error) => {
    console.error('Game error:', error);
    setError(error);
  };

  const handleRetry = () => {
    setError(null);
  };

  // Обработка глобальных ошибок
  useEffect(() => {
    const handleGlobalError = (event: ErrorEvent) => {
      handleError(new Error(event.message));
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      handleError(new Error(event.reason?.toString() || 'Unknown error'));
    };

    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleGlobalError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  // Отображение экрана ошибки
  if (error) {
    return <ErrorScreen error={error} onRetry={handleRetry} />;
  }

  return (
    <div className="w-full h-screen bg-gradient-to-b from-sky/20 to-pink/20 relative overflow-hidden">
      {/* Фоновый градиент */}
      <div className="absolute inset-0 bg-gradient-to-br from-sky/10 via-transparent to-pink/10" />

      {/* Игровая сцена */}
      <Suspense fallback={<LoadingScreen />}>
        <GameScene />
      </Suspense>

      {/* Дополнительные эффекты */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Частицы (можно добавить позже) */}
      </div>
    </div>
  );
});

GameApp.displayName = 'GameApp';
