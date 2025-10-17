/**
 * Игровой интерфейс для PandaPal Go
 * Отображает статистику, управление и информацию о игре
 *
 * @module components/GameUI
 */

import React, { useState, useEffect } from 'react';
import { useGameStore } from '../stores/gameStore';
import { GameUtils } from '../utils/gameMath';

/**
 * Свойства компонента игрового интерфейса
 */
interface GameUIProps {
  /** Видимость интерфейса */
  visible?: boolean;
  /** Обработчик закрытия игры */
  onClose?: () => void;
  /** Обработчик паузы */
  onPause?: () => void;
}

/**
 * Компонент статистики
 */
const GameStats: React.FC = React.memo(() => {
  const { stats } = useGameStore();
  const [showDetails, setShowDetails] = useState(false);

  const levelProgress = GameUtils.getLevelProgress(stats.experience, stats.level);

  return (
    <div className="bg-white/90 backdrop-blur rounded-lg p-4 shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-bold text-gray-800">Статистика</h3>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-blue-600 hover:text-blue-800 text-sm"
        >
          {showDetails ? 'Скрыть' : 'Подробнее'}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Основные показатели */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-2xl">⭐</span>
            <div>
              <div className="text-sm text-gray-600">Уровень</div>
              <div className="font-bold text-lg">{stats.level}</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-2xl">🪙</span>
            <div>
              <div className="text-sm text-gray-600">Монеты</div>
              <div className="font-bold text-lg">{stats.coins}</div>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-2xl">📊</span>
            <div>
              <div className="text-sm text-gray-600">Очки</div>
              <div className="font-bold text-lg">{stats.score}</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-2xl">🎯</span>
            <div>
              <div className="text-sm text-gray-600">Опыт</div>
              <div className="font-bold text-lg">{stats.experience}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Прогресс уровня */}
      <div className="mt-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Прогресс до уровня {stats.level + 1}</span>
          <span>{Math.round(levelProgress * 100)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${levelProgress * 100}%` }}
          />
        </div>
      </div>

      {/* Детальная статистика */}
      {showDetails && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            <div className="grid grid-cols-2 gap-2">
              <div>Достижений: {stats.achievements.length}</div>
              <div>Время игры: 0:00</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

GameStats.displayName = 'GameStats';

/**
 * Компонент управления
 */
const GameControls: React.FC<GameUIProps> = React.memo(({ onPause }) => {
  const { settings, toggleSound } = useGameStore();

  return (
    <div className="bg-white/90 backdrop-blur rounded-lg p-4 shadow-lg">
      <h3 className="text-lg font-bold text-gray-800 mb-3">Управление</h3>

      <div className="space-y-3">
        {/* Управление движением */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Движение</h4>
          <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
            <div>WASD / Стрелки - Движение</div>
            <div>Shift - Бег</div>
          </div>
        </div>

        {/* Настройки */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">Настройки</h4>
          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.soundEnabled}
                onChange={toggleSound}
                className="rounded"
              />
              <span className="text-sm">Звук</span>
            </label>
          </div>
        </div>

        {/* Действия */}
        <div className="flex gap-2">
          <button
            onClick={onPause}
            className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-2 rounded text-sm font-medium transition-colors"
          >
            ⏸️ Пауза
          </button>
        </div>
      </div>
    </div>
  );
});

GameControls.displayName = 'GameControls';

/**
 * Компонент состояния панды
 */
const PandaStatus: React.FC = React.memo(() => {
  const { panda } = useGameStore();

  const getStatusColor = (value: number) => {
    if (value > 80) return 'text-green-600';
    if (value > 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusEmoji = (value: number) => {
    if (value > 80) return '😊';
    if (value > 50) return '😐';
    return '😞';
  };

  return (
    <div className="bg-white/90 backdrop-blur rounded-lg p-4 shadow-lg">
      <h3 className="text-lg font-bold text-gray-800 mb-3">Состояние панды</h3>

      <div className="space-y-3">
        {/* Здоровье */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-gray-600">❤️ Здоровье</span>
            <span className={`text-sm font-medium ${getStatusColor(panda.health)}`}>
              {panda.health}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-red-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${panda.health}%` }}
            />
          </div>
        </div>

        {/* Счастье */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-gray-600">😊 Счастье</span>
            <span className={`text-sm font-medium ${getStatusColor(panda.happiness)}`}>
              {panda.happiness}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-yellow-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${panda.happiness}%` }}
            />
          </div>
        </div>

        {/* Энергия */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-gray-600">⚡ Энергия</span>
            <span className={`text-sm font-medium ${getStatusColor(panda.energy)}`}>
              {panda.energy}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${panda.energy}%` }}
            />
          </div>
        </div>

        {/* Текущая анимация */}
        <div className="pt-2 border-t border-gray-200">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Состояние:</span>
            <span className="text-sm font-medium">
              {getStatusEmoji(panda.happiness)} {panda.animation}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
});

PandaStatus.displayName = 'PandaStatus';

/**
 * Главный компонент игрового интерфейса
 */
export const GameUI: React.FC<GameUIProps> = React.memo(({
  visible = true,
  onClose,
  onPause,
}) => {
  const { gameState } = useGameStore();
  const [showHelp, setShowHelp] = useState(false);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      {/* Основной интерфейс */}
      <div className="absolute top-4 left-4 pointer-events-auto">
        <GameStats />
      </div>

      <div className="absolute top-4 right-4 pointer-events-auto">
        <GameControls onPause={onPause} />
      </div>

      <div className="absolute bottom-4 left-4 pointer-events-auto">
        <PandaStatus />
      </div>

      {/* Заголовок игры */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 pointer-events-auto">
        <div className="bg-white/90 backdrop-blur rounded-lg px-6 py-3 shadow-lg">
          <h1 className="text-2xl font-bold text-gray-800 text-center">
            🐼 PandaPal Go
          </h1>
          <p className="text-sm text-gray-600 text-center">
            {gameState === 'playing' ? 'Игра идет' :
             gameState === 'paused' ? 'Пауза' :
             gameState === 'loading' ? 'Загрузка...' : 'Остановлено'}
          </p>
        </div>
      </div>

      {/* Кнопка закрытия */}
      {onClose && (
        <div className="absolute top-4 right-4 pointer-events-auto">
          <button
            onClick={onClose}
            className="bg-red-500 hover:bg-red-600 text-white p-2 rounded-full shadow-lg transition-colors"
            title="Закрыть игру"
          >
            ✕
          </button>
        </div>
      )}

      {/* Кнопка помощи */}
      <div className="absolute bottom-4 right-4 pointer-events-auto">
        <button
          onClick={() => setShowHelp(!showHelp)}
          className="bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-full shadow-lg transition-colors"
          title="Помощь"
        >
          ❓
        </button>
      </div>

      {/* Модальное окно помощи */}
      {showHelp && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center pointer-events-auto">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Как играть?</h3>

            <div className="space-y-3 text-sm text-gray-600">
              <div>
                <strong>Движение:</strong> Используйте WASD или стрелки для движения панды по миру.
              </div>
              <div>
                <strong>Бег:</strong> Удерживайте Shift для быстрого движения.
              </div>
              <div>
                <strong>Сбор предметов:</strong> Подходите к предметам, чтобы их собрать.
              </div>
              <div>
                <strong>Бамбук:</strong> Дает опыт и поддерживает здоровье панды.
              </div>
              <div>
                <strong>Монеты:</strong> Дают очки и опыт.
              </div>
              <div>
                <strong>Цель:</strong> Исследуйте мир, собирайте предметы и заботьтесь о панде!
              </div>
            </div>

            <button
              onClick={() => setShowHelp(false)}
              className="w-full mt-4 bg-blue-500 hover:bg-blue-600 text-white py-2 rounded font-medium transition-colors"
            >
              Понятно!
            </button>
          </div>
        </div>
      )}
    </div>
  );
});

GameUI.displayName = 'GameUI';
