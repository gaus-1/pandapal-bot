/**
 * Settings Screen - Настройки
 */

import { useState } from 'react';
import { telegram } from '../../services/telegram';
import { updateUserProfile, type UserProfile } from '../../services/api';

interface SettingsScreenProps {
  user: UserProfile;
  onUserUpdate: (user: UserProfile) => void;
}

export function SettingsScreen({ user, onUserUpdate }: SettingsScreenProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [age, setAge] = useState(user.age || 10);
  const [grade, setGrade] = useState(user.grade || 1);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    telegram.hapticFeedback('medium');

    try {
      const updatedUser = await updateUserProfile(user.telegram_id, { age, grade });
      onUserUpdate(updatedUser);
      setIsEditing(false);
      telegram.notifySuccess();
      await telegram.showAlert('Настройки сохранены! ✅');
    } catch (error) {
      console.error('Ошибка сохранения:', error);
      telegram.notifyError();
      await telegram.showAlert('Не удалось сохранить настройки 😔');
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearHistory = async () => {
    const confirmed = await telegram.showConfirm(
      'Удалить всю историю сообщений? Это действие необратимо!'
    );

    if (confirmed) {
      telegram.hapticFeedback('heavy');
      telegram.showAlert('История очищена! 🗑️');
    }
  };

  return (
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4">
      {/* Заголовок */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-2">
          ⚙️ Настройки
        </h1>
        <p className="text-[var(--tg-theme-hint-color)]">
          Персонализация и управление
        </p>
      </div>

      {/* Профиль */}
      <div className="p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl mb-4">
        <h2 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-3">
          👤 Профиль
        </h2>

        <div className="space-y-3">
          <div>
            <label className="text-sm text-[var(--tg-theme-hint-color)] block mb-1">Имя</label>
            <div className="text-[var(--tg-theme-text-color)] font-medium">
              {user.first_name} {user.last_name || ''}
            </div>
          </div>

          {user.username && (
            <div>
              <label className="text-sm text-[var(--tg-theme-hint-color)] block mb-1">
                Username
              </label>
              <div className="text-[var(--tg-theme-text-color)] font-medium">@{user.username}</div>
            </div>
          )}

          {/* Возраст */}
          <div>
            <label className="text-sm text-[var(--tg-theme-hint-color)] block mb-1">Возраст</label>
            {isEditing ? (
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(parseInt(e.target.value))}
                min={6}
                max={18}
                className="w-full px-4 py-2 bg-[var(--tg-theme-bg-color)] border border-[var(--tg-theme-hint-color)]/30 rounded-xl text-[var(--tg-theme-text-color)] outline-none focus:ring-2 focus:ring-[var(--tg-theme-button-color)]"
              />
            ) : (
              <div className="text-[var(--tg-theme-text-color)] font-medium">
                {user.age || 'Не указан'} лет
              </div>
            )}
          </div>

          {/* Класс */}
          <div>
            <label className="text-sm text-[var(--tg-theme-hint-color)] block mb-1">Класс</label>
            {isEditing ? (
              <input
                type="number"
                value={grade}
                onChange={(e) => setGrade(parseInt(e.target.value))}
                min={1}
                max={11}
                className="w-full px-4 py-2 bg-[var(--tg-theme-bg-color)] border border-[var(--tg-theme-hint-color)]/30 rounded-xl text-[var(--tg-theme-text-color)] outline-none focus:ring-2 focus:ring-[var(--tg-theme-button-color)]"
              />
            ) : (
              <div className="text-[var(--tg-theme-text-color)] font-medium">
                {user.grade || 'Не указан'}
              </div>
            )}
          </div>

          {/* Кнопки редактирования */}
          <div className="pt-2">
            {isEditing ? (
              <div className="flex gap-2">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex-1 py-2 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-medium disabled:opacity-50"
                >
                  {isSaving ? 'Сохранение...' : 'Сохранить'}
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setAge(user.age || 10);
                    setGrade(user.grade || 1);
                  }}
                  disabled={isSaving}
                  className="flex-1 py-2 bg-[var(--tg-theme-hint-color)]/20 text-[var(--tg-theme-text-color)] rounded-xl font-medium disabled:opacity-50"
                >
                  Отмена
                </button>
              </div>
            ) : (
              <button
                onClick={() => {
                  setIsEditing(true);
                  telegram.hapticFeedback('light');
                }}
                className="w-full py-2 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-xl font-medium"
              >
                Редактировать
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Приватность */}
      <div className="p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl mb-4">
        <h2 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-3">
          🔒 Приватность
        </h2>
        <button
          onClick={handleClearHistory}
          className="w-full py-3 bg-red-500/10 text-red-500 rounded-xl font-medium border border-red-500/30"
        >
          Очистить историю сообщений
        </button>
      </div>

      {/* О приложении */}
      <div className="p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl">
        <h2 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-3">
          ℹ️ О приложении
        </h2>
        <div className="space-y-2 text-sm text-[var(--tg-theme-hint-color)]">
          <div className="flex justify-between">
            <span>Версия</span>
            <span className="text-[var(--tg-theme-text-color)]">1.0.0</span>
          </div>
          <div className="flex justify-between">
            <span>Платформа</span>
            <span className="text-[var(--tg-theme-text-color)]">{telegram.getPlatform()}</span>
          </div>
        </div>

        <button
          onClick={() => {
            telegram.hapticFeedback('light');
            telegram.openLink('https://pandapal.ru', { try_instant_view: true });
          }}
          className="w-full mt-3 py-2 bg-[var(--tg-theme-button-color)]/20 text-[var(--tg-theme-button-color)] rounded-xl font-medium"
        >
          Открыть сайт
        </button>
      </div>
    </div>
  );
}
