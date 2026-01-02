/**
 * Telegram Mini App - главный компонент
 * Навигация и экраны для всех функций бота
 */

import { useEffect, useState } from 'react';
import { telegram } from './services/telegram';
import { authenticateUser, type UserProfile } from './services/api';

// Импорт экранов
import { AIChat } from './features/AIChat/AIChat';
import { LessonsScreen } from './features/Lessons/LessonsScreen';
import { ProgressScreen } from './features/Progress/ProgressScreen';
import { AchievementsScreen } from './features/Achievements/AchievementsScreen';
import { LocationScreen } from './features/Location/LocationScreen';
import { SettingsScreen } from './features/Settings/SettingsScreen';
import { ParentDashboard } from './features/ParentDashboard/ParentDashboard';
import { PremiumScreen } from './features/Premium/PremiumScreen';

type Screen = 'ai-chat' | 'lessons' | 'progress' | 'achievements' | 'location' | 'settings' | 'parent-dashboard' | 'premium';

export function MiniApp() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('ai-chat');
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Инициализация Telegram Mini App
    telegram.init();

    // Аутентификация пользователя
    authenticateUser()
      .then((userProfile) => {
        setUser(userProfile);
        setIsLoading(false);
        telegram.notifySuccess();
      })
      .catch((err) => {
        console.error('Ошибка аутентификации:', err);
        setError('Не удалось загрузить данные пользователя');
        setIsLoading(false);
        telegram.notifyError();
      });

    // Показываем кнопку "Назад" для навигации
    telegram.showBackButton(() => {
      if (currentScreen !== 'ai-chat') {
        setCurrentScreen('ai-chat');
        telegram.hapticFeedback('light');
      }
    });

    return () => {
      telegram.hideBackButton();
    };
  }, []);

  // Обновляем кнопку "Назад" при смене экрана
  useEffect(() => {
    if (currentScreen === 'ai-chat') {
      telegram.hideBackButton();
    } else {
      telegram.showBackButton(() => {
        setCurrentScreen('ai-chat');
        telegram.hapticFeedback('light');
      });
    }
  }, [currentScreen]);

  const navigateTo = (screen: Screen) => {
    setCurrentScreen(screen);
    telegram.hapticFeedback('medium');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--tg-theme-bg-color)]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div>
          <p className="mt-4 text-[var(--tg-theme-text-color)]">Загрузка...</p>
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--tg-theme-bg-color)] p-4">
        <div className="text-center">
          <div className="text-6xl mb-4">😔</div>
          <h2 className="text-xl font-bold text-[var(--tg-theme-text-color)] mb-2">
            Ошибка загрузки
          </h2>
          <p className="text-[var(--tg-theme-hint-color)]">
            {error || 'Не удалось загрузить данные'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-6 py-2 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-lg"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)]">
      {/* Основной контент */}
      <div className="pb-20">
        {currentScreen === 'ai-chat' && <AIChat user={user} />}
        {currentScreen === 'lessons' && <LessonsScreen user={user} />}
        {currentScreen === 'progress' && <ProgressScreen user={user} />}
        {currentScreen === 'achievements' && <AchievementsScreen user={user} />}
        {currentScreen === 'location' && <LocationScreen user={user} />}
        {currentScreen === 'settings' && <SettingsScreen user={user} onUserUpdate={setUser} />}
        {currentScreen === 'parent-dashboard' && <ParentDashboard user={user} />}
        {currentScreen === 'premium' && <PremiumScreen user={user} />}
      </div>

      {/* Нижняя навигация (как в Telegram боте) */}
      <nav className="fixed bottom-0 left-0 right-0 bg-[var(--tg-theme-bg-color)] border-t border-[var(--tg-theme-hint-color)]/20">
        <div className="grid grid-cols-4 gap-1 p-2">
          {/* Первый ряд */}
          <NavButton
            icon="💬"
            label="Общение с AI"
            isActive={currentScreen === 'ai-chat'}
            onClick={() => navigateTo('ai-chat')}
          />
          <NavButton
            icon="📚"
            label="Помощь с уроками"
            isActive={currentScreen === 'lessons'}
            onClick={() => navigateTo('lessons')}
          />
          <NavButton
            icon="📊"
            label="Мой прогресс"
            isActive={currentScreen === 'progress'}
            onClick={() => navigateTo('progress')}
          />
          <NavButton
            icon="🏆"
            label="Достижения"
            isActive={currentScreen === 'achievements'}
            onClick={() => navigateTo('achievements')}
          />

          {/* Второй ряд */}
          <NavButton
            icon="📍"
            label="Где я"
            isActive={currentScreen === 'location'}
            onClick={() => navigateTo('location')}
          />
          <NavButton
            icon="⚙️"
            label="Настройки"
            isActive={currentScreen === 'settings'}
            onClick={() => navigateTo('settings')}
          />
          {user.user_type === 'parent' && (
            <NavButton
              icon="👨‍👩‍👧"
              label="Дашборд"
              isActive={currentScreen === 'parent-dashboard'}
              onClick={() => navigateTo('parent-dashboard')}
            />
          )}
          <NavButton
            icon="👑"
            label="Premium"
            isActive={currentScreen === 'premium'}
            onClick={() => navigateTo('premium')}
          />
        </div>
      </nav>
    </div>
  );
}

interface NavButtonProps {
  icon: string;
  label: string;
  isActive: boolean;
  onClick: () => void;
}

function NavButton({ icon, label, isActive, onClick }: NavButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center justify-center p-2 rounded-lg transition-colors ${
        isActive
          ? 'bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)]'
          : 'text-[var(--tg-theme-text-color)] hover:bg-[var(--tg-theme-hint-color)]/10'
      }`}
    >
      <span className="text-2xl mb-1">{icon}</span>
      <span className="text-[10px] leading-tight text-center">{label}</span>
    </button>
  );
}
