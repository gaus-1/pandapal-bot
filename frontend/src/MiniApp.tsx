/**
 * Telegram Mini App - главный компонент
 * Использует Zustand для состояния и TanStack Query для данных
 */

import { useEffect, lazy, Suspense } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './lib/queryClient';
import { useAppStore, selectUser, selectCurrentScreen, selectIsLoading, selectError } from './store/appStore';
import { useAuth } from './hooks/useAuth';
import { telegram } from './services/telegram';

// Lazy loading экранов для оптимизации
const AIChat = lazy(() => import('./features/AIChat/AIChat').then(m => ({ default: m.AIChat })));
const EmergencyScreen = lazy(() => import('./features/Emergency/EmergencyScreen').then(m => ({ default: m.EmergencyScreen })));

export function MiniApp() {
  return (
    <QueryClientProvider client={queryClient}>
      <MiniAppContent />
      {/* DevTools только в development */}
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}

function MiniAppContent() {
  // Используем Zustand селекторы для оптимизации re-renders
  const user = useAppStore(selectUser);
  const currentScreen = useAppStore(selectCurrentScreen);
  const isLoading = useAppStore(selectIsLoading);
  const error = useAppStore(selectError);
  const { setCurrentScreen } = useAppStore();
  const { authenticate } = useAuth();

  useEffect(() => {
    // Инициализация Telegram Mini App
    telegram.init();

    // Отладочная информация
    console.log('🔍 DEBUG: Telegram initData:', telegram.getInitData());
    console.log('🔍 DEBUG: Telegram user:', telegram.getUser());
    console.log('🔍 DEBUG: Telegram platform:', telegram.getPlatform());
    console.log('🔍 DEBUG: Is Telegram WebApp:', telegram.isTelegramWebApp());

    // Проверяем что initData доступен
    const initData = telegram.getInitData();
    if (!initData) {
      console.error('❌ КРИТИЧНО: initData пустой!');
      useAppStore.getState().setError(
        'Приложение должно открываться через Telegram Mini App. Пожалуйста, откройте бота в Telegram и нажмите кнопку Mini App.'
      );
      useAppStore.getState().setIsLoading(false);
      return;
    }

    // Аутентификация через TanStack Query hook
    authenticate();

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
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
  }, [currentScreen, setCurrentScreen]);

  const navigateTo = (screen: 'ai-chat' | 'emergency') => {
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
      {/* Основной контент с Suspense для lazy loading */}
      <div className="flex-1 overflow-y-auto">
        <Suspense fallback={<LoadingFallback />}>
          {currentScreen === 'ai-chat' && user && <AIChat user={user} />}
          {currentScreen === 'emergency' && <EmergencyScreen />}
        </Suspense>
      </div>

      {/* Нижняя навигация - ТОЛЬКО SOS (чат открыт по умолчанию) */}
      {currentScreen === 'emergency' && (
        <nav className="bg-[var(--tg-theme-bg-color)] border-t border-[var(--tg-theme-hint-color)]/30 shadow-lg">
          <div className="flex justify-start px-2 py-1.5">
            <NavButton
              icon="🚨"
              label="SOS"
              isActive={true}
              onClick={() => navigateTo('emergency')}
            />
          </div>
        </nav>
      )}
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
      className={`flex flex-row items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg transition-all shadow-sm ${
        isActive
          ? 'bg-blue-400/90 text-white font-semibold shadow-md'
          : 'text-[var(--tg-theme-text-color)] bg-[var(--tg-theme-secondary-bg-color,var(--tg-theme-bg-color))] hover:bg-blue-100/50 dark:hover:bg-blue-900/20 font-medium'
      }`}
    >
      <span className="text-base">{icon}</span>
      <span className="text-[10px] font-semibold leading-tight opacity-90">{label}</span>
    </button>
  );
}

/**
 * Fallback компонент для Suspense
 */
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div>
        <p className="mt-2 text-sm text-[var(--tg-theme-hint-color)]">Загрузка...</p>
      </div>
    </div>
  );
}
