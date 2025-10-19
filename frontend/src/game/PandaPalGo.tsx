import { useEffect, useRef, useState } from 'react';
import { Game } from './core/Game';
import { GameStatus } from './core/GameState';

/**
 * React-компонент для игры PandaPal Go
 * Интегрирует Canvas-игру в React-приложение
 */
export function PandaPalGo() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const gameRef = useRef<Game | null>(null);
  const [gameStatus, setGameStatus] = useState<GameStatus>(GameStatus.MENU);
  const [score, setScore] = useState(0);
  const [lives, setLives] = useState(3);

  // Инициализация игры
  useEffect(() => {
    if (!canvasRef.current) return;

    const game = new Game(canvasRef.current);
    gameRef.current = game;

    // АВТОМАТИЧЕСКИЙ ЗАПУСК ИГРЫ ДЛЯ ТЕСТИРОВАНИЯ
    setTimeout(() => {
      game.start();
      console.log('🚀 Игра автоматически запущена для тестирования!');
    }, 1000);

    // Обновление UI из игры
    const updateUI = () => {
      if (gameRef.current) {
        const state = gameRef.current.getState().getState();
        setGameStatus(state.status);
        setScore(state.totalScore);
        setLives(state.lives);
      }
    };

    // Обновляем UI каждые 100мс
    const intervalId = setInterval(updateUI, 100);

    return () => {
      clearInterval(intervalId);
      game.stop();
    };
  }, []);

  // Обработчики кнопок
  const handleStart = () => {
    gameRef.current?.start();
  };

  const handleRestart = () => {
    gameRef.current?.getState().reset();
    gameRef.current?.start();
  };

  const handleNextLevel = () => {
    gameRef.current?.nextLevel();
  };

  const handlePause = () => {
    gameRef.current?.togglePause();
  };

  const handleRestartLevel = () => {
    gameRef.current?.restartLevel();
  };

  return (
    <div className="game-container flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-blue-50 to-purple-50 p-4" style={{
      // Предотвращаем прокрутку на мобильных устройствах
      touchAction: 'none',
      userSelect: 'none',
      WebkitUserSelect: 'none',
      WebkitTouchCallout: 'none',
      WebkitTapHighlightColor: 'transparent'
    }}>
      {/* Заголовок */}
      <div className="text-center mb-4">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">
          🎮 PandaPal Go
        </h1>
        <p className="text-lg text-gray-600">
          Школьная головоломка с математикой
        </p>
      </div>

      {/* Canvas игры */}
      <div className="game-canvas-wrapper relative shadow-2xl rounded-lg overflow-hidden bg-white" style={{
        // Предотвращаем проблемы с касанием на мобильных
        touchAction: 'none',
        userSelect: 'none',
        WebkitUserSelect: 'none'
      }}>
        <canvas
          ref={canvasRef}
          className="game-canvas block w-full max-w-4xl h-auto"
          width={1200}
          height={800}
          style={{
            // Дополнительные стили для мобильных браузеров
            touchAction: 'none',
            userSelect: 'none',
            WebkitUserSelect: 'none',
            WebkitTouchCallout: 'none',
            WebkitTapHighlightColor: 'transparent',
            // Улучшенное сглаживание для четкой графики
            imageRendering: 'pixelated',
            // Предотвращаем выделение текста при касании
            // @ts-ignore - WebkitUserDrag не в типах, но поддерживается браузерами
            WebkitUserDrag: 'none',
            // КРИТИЧЕСКАЯ ОТЛАДКА: Делаем canvas видимым
            border: '5px solid red',
            backgroundColor: 'yellow'
          }}
        />

        {/* Кнопки управления поверх canvas */}
        {gameStatus === GameStatus.MENU && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <button
              onClick={handleStart}
              className="pointer-events-auto bg-green-500 hover:bg-green-600 text-white font-bold py-4 px-8 rounded-lg text-2xl transform transition hover:scale-105 shadow-lg"
            >
              Начать игру
            </button>
          </div>
        )}

        {gameStatus === GameStatus.LEVEL_COMPLETE && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none bg-black bg-opacity-50">
            <div className="pointer-events-auto bg-white rounded-lg p-8 text-center">
              <h2 className="text-3xl font-bold text-green-600 mb-4">
                🎉 Уровень пройден!
              </h2>
              <p className="text-xl text-gray-700 mb-6">
                Очки: {score}
              </p>
              <button
                onClick={handleNextLevel}
                className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-lg text-xl transform transition hover:scale-105"
              >
                Следующий уровень →
              </button>
            </div>
          </div>
        )}

        {gameStatus === GameStatus.GAME_OVER && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none bg-black bg-opacity-50">
            <div className="pointer-events-auto bg-white rounded-lg p-8 text-center">
              <h2 className="text-3xl font-bold text-purple-600 mb-4">
                {lives === 0 ? '💫 Игра окончена' : '🎊 Победа!'}
              </h2>
              <p className="text-xl text-gray-700 mb-6">
                Всего очков: {score}
              </p>
              <button
                onClick={handleRestart}
                className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg text-xl transform transition hover:scale-105"
              >
                Играть снова
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Панель управления */}
      {(gameStatus === GameStatus.PLAYING || gameStatus === GameStatus.PAUSED) && (
        <div className="controls mt-4 flex gap-4">
          <button
            onClick={handlePause}
            className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-6 rounded-lg transform transition hover:scale-105"
          >
            {gameStatus === GameStatus.PAUSED ? '▶️ Продолжить' : '⏸️ Пауза'}
          </button>
          <button
            onClick={handleRestartLevel}
            className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-6 rounded-lg transform transition hover:scale-105"
          >
            🔄 Заново
          </button>
          <button
            onClick={() => window.location.href = '/'}
            className="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transform transition hover:scale-105"
          >
            ← Выход
          </button>
        </div>
      )}

      {/* Инструкции */}
      <div className="instructions mt-6 max-w-2xl text-center">
        <h3 className="text-xl font-bold text-gray-800 mb-2">
          Как играть:
        </h3>
        <div className="text-gray-600 space-y-1">
          <p>🖱️ <strong>Мышь/Тач:</strong> управляй пандой</p>
          <p>🎯 <strong>Цель:</strong> разбивай все кирпичи с примерами</p>
          <p>⌨️ <strong>Пробел:</strong> пауза</p>
          <p>❤️ <strong>Жизни:</strong> не дай мячу упасть</p>
          <p>📚 <strong>Образование:</strong> решай математические примеры!</p>
        </div>
      </div>

      {/* Копирайт */}
      <div className="mt-8 text-center text-sm text-gray-500">
        <p>© 2025 PandaPal. Игра создана с 💚 для детей</p>
      </div>
    </div>
  );
}

export default PandaPalGo;
