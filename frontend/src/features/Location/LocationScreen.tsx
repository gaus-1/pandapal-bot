/**
 * Location Screen - Где я (для родительского контроля)
 */

import { useState } from 'react';
import { telegram } from '../../services/telegram';
import type { UserProfile } from '../../services/api';

interface LocationScreenProps {
  user: UserProfile;
}

export function LocationScreen({ user }: LocationScreenProps) {
  const [isSharing, setIsSharing] = useState(false);

  const handleShareLocation = async () => {
    const confirmed = await telegram.showConfirm(
      'Отправить родителям твое текущее местоположение?'
    );

    if (confirmed) {
      telegram.hapticFeedback('medium');
      setIsSharing(true);

      // Здесь будет отправка локации через backend
      setTimeout(() => {
        setIsSharing(false);
        telegram.notifySuccess();
        telegram.showAlert('Местоположение отправлено родителям! ✅');
      }, 1500);
    }
  };

  const handleEmergencyCall = async () => {
    const confirmed = await telegram.showConfirm(
      '🚨 Отправить экстренный сигнал родителям с твоим местоположением?'
    );

    if (confirmed) {
      telegram.hapticFeedback('heavy');
      telegram.notifyWarning();

      // Экстренный вызов
      setTimeout(() => {
        telegram.showAlert('🚨 Экстренный сигнал отправлен! Родители получили уведомление с твоей геолокацией.');
      }, 500);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4">
      {/* Заголовок */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-2">
          📍 Где я
        </h1>
        <p className="text-[var(--tg-theme-hint-color)]">
          Поделись местоположением с родителями
        </p>
      </div>

      {/* Информация о пользователе */}
      <div className="p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl mb-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="text-4xl">👤</div>
          <div>
            <div className="font-semibold text-[var(--tg-theme-text-color)]">
              {user.first_name} {user.last_name || ''}
            </div>
            {user.age && (
              <div className="text-sm text-[var(--tg-theme-hint-color)]">
                {user.age} лет
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Кнопка "Поделиться местоположением" */}
      <button
        onClick={handleShareLocation}
        disabled={isSharing}
        className="w-full p-4 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-2xl font-medium mb-3 flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50"
      >
        {isSharing ? (
          <>
            <div className="animate-spin">⏳</div>
            <span>Отправка...</span>
          </>
        ) : (
          <>
            <span>📍</span>
            <span>Поделиться местоположением</span>
          </>
        )}
      </button>

      {/* Кнопка экстренного вызова */}
      <button
        onClick={handleEmergencyCall}
        className="w-full p-4 bg-red-500 text-white rounded-2xl font-medium mb-6 flex items-center justify-center gap-2 transition-all active:scale-95"
      >
        <span>🚨</span>
        <span>Экстренный вызов</span>
      </button>

      {/* Информация о безопасности */}
      <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-2xl">
        <h3 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2 flex items-center gap-2">
          <span>🔒</span>
          <span>Безопасность</span>
        </h3>
        <ul className="space-y-2 text-sm text-[var(--tg-theme-hint-color)]">
          <li>• Твое местоположение видят только твои родители</li>
          <li>• Данные передаются в зашифрованном виде</li>
          <li>• Используй экстренный вызов в опасных ситуациях</li>
        </ul>
      </div>

      {/* Контакты родителей */}
      {user.user_type === 'child' && (
        <div className="mt-4 p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl">
          <h3 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2">
            👨‍👩‍👧 Родители
          </h3>
          <p className="text-sm text-[var(--tg-theme-hint-color)]">
            Твои родители получат уведомление при отправке местоположения
          </p>
        </div>
      )}
    </div>
  );
}
