/**
 * Telegram Mini App - главный компонент
 * Навигация и экраны для всех функций бота
 */

import { useEffect, useState } from 'react';
import { telegram } from './services/telegram';
import { authenticateUser, type UserProfile } from './services/api';

// Импорт экранов
import { AIChat } from './features/AIChat/AIChat';
import { LocationScreen } from './features/Location/LocationScreen';
import { EmergencyScreen } from './features/Emergency/EmergencyScreen';

type Screen = 'ai-chat' | 'location' | 'emergency';

export function MiniApp() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('ai-chat');
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Инициализация Telegram Mini App
    telegram.init();

    // Отладочная информация
    console.log('🔍 DEBUG: Telegram initData:', telegram.getInitData());
    console.log('🔍 DEBUG: Telegram user:', telegram.getUser());
    console.log('🔍 DEBUG: Telegram platform:', telegram.getPlatform());
    console.log('🔍 DEBUG: Is Telegram WebApp:', telegram.isTelegramWebApp());

    // Аутентификация пользователя
    authenticateUser()
      .then((userProfile) => {
        console.log('✅ Аутентификация успешна:', userProfile);
        setUser(userProfile);
        setIsLoading(false);
        telegram.notifySuccess();
      })
      .catch((err) => {
        console.error('❌ Ошибка аутентификации:', err);
        console.error('❌ Детали ошибки:', err.message);
        setError(`Не удалось загрузить данные пользователя: ${err.message}`);
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
    <div className="h-screen flex flex-col bg-[var(--tg-theme-bg-color)]">
      {/* Основной контент */}
      <div className="flex-1 overflow-y-auto">
        {currentScreen === 'ai-chat' && <AIChat user={user} />}
        {currentScreen === 'location' && <LocationScreen user={user} />}
        {currentScreen === 'emergency' && <EmergencyScreen />}
      </div>

      {/* Нижняя навигация - ТОЛЬКО безопасность */}
      <nav className="bg-[var(--tg-theme-bg-color)] border-t border-[var(--tg-theme-hint-color)]/20">
        <div className="grid grid-cols-3 gap-2 p-2">
          <NavButton
            icon="💬"
            label="AI Чат"
            isActive={currentScreen === 'ai-chat'}
            onClick={() => navigateTo('ai-chat')}
          />
          <NavButton
            icon="📍"
            label="Где я?"
            isActive={currentScreen === 'location'}
            onClick={() => navigateTo('location')}
          />
          <NavButton
            icon="🚨"
            label="SOS"
            isActive={currentScreen === 'emergency'}
            onClick={() => navigateTo('emergency')}
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
      className={`flex flex-col items-center justify-center p-3 rounded-xl transition-all ${
        isActive
          ? 'bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)]'
          : 'text-[var(--tg-theme-text-color)] hover:bg-[var(--tg-theme-hint-color)]/10'
      }`}
    >
      <span className="text-2xl mb-1">{icon}</span>
      <span className="text-xs font-semibold leading-tight">{label}</span>
    </button>
  );
}
