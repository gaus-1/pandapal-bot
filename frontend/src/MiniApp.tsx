/**
 * Telegram Mini App - главный компонент
 * Использует Zustand для состояния и TanStack Query для данных
 */

import { useEffect, lazy, Suspense } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './lib/queryClient';
import { useAppStore, selectUser, selectCurrentScreen, selectIsLoading, selectError, type Screen } from './store/appStore';
import { useAuth } from './hooks/useAuth';
import { telegram } from './services/telegram';
import { logger } from './utils/logger';
import { ErrorBoundary } from './components/ErrorBoundary';
import { NetworkStatusBar } from './components/NetworkStatusBar';

// Lazy loading экранов для оптимизации
const AIChat = lazy(() => import('./features/AIChat/AIChat').then(m => ({ default: m.AIChat })));
const EmergencyScreen = lazy(() => import('./features/Emergency/EmergencyScreen').then(m => ({ default: m.EmergencyScreen })));
const AchievementsScreen = lazy(() => import('./features/Achievements/AchievementsScreen').then(m => ({ default: m.AchievementsScreen })));
const PremiumScreen = lazy(() => import('./features/Premium/PremiumScreen').then(m => ({ default: m.PremiumScreen })));
const DonationScreen = lazy(() => import('./features/Donation/DonationScreen').then(m => ({ default: m.DonationScreen })));
const GamesScreen = lazy(() => import('./features/Games/GamesScreen').then(m => ({ default: m.GamesScreen })));
const MyPandaScreen = lazy(() => import('./features/MyPanda/MyPandaScreen').then(m => ({ default: m.MyPandaScreen })));

export function MiniApp() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <NetworkStatusBar />
        <MiniAppContent />
      </ErrorBoundary>
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

  // Тема управляется через MiniAppThemeToggle и index.html
  // Здесь не дублируем логику, чтобы избежать конфликтов

  useEffect(() => {
    // Локальная разработка: localhost + miniapp — сразу mock-пользователь, без запросов к API
    const isLocalMiniappDev = import.meta.env.DEV && typeof window !== 'undefined' && (() => {
      const host = window.location.hostname;
      const path = window.location.pathname;
      const q = new URLSearchParams(window.location.search);
      const isLocal = host === 'localhost' || host === '127.0.0.1' || host === '';
      const pathOk = path === '/miniapp' || path.startsWith('/miniapp/');
      const queryOk = q.get('miniapp') === '1' || q.get('miniapp') === 'true';
      return isLocal && (pathOk || queryOk);
    })();
    if (isLocalMiniappDev) {
      try {
        telegram.init();
      } catch (e) {
        logger.debug('Telegram init in local dev:', e);
      }
      const { setUser, setIsLoading, setError } = useAppStore.getState();
      setUser({
        telegram_id: 0,
        first_name: 'Локальный',
        user_type: 'child',
        is_premium: false,
      });
      setError(null);
      setIsLoading(false);
      return;
    }

    // Инициализация Telegram Mini App
    telegram.init();

    logger.debug('Telegram init:', telegram.getPlatform(), telegram.isTelegramWebApp());

    // Проверяем что initData доступен
    const initData = telegram.getInitData();
    if (!initData) {
      // Для web.telegram.org initData может появиться позже
      // Ждем немного и проверяем снова
      console.warn('⚠️ initData недоступен, ожидаем...');

      const checkInitData = () => {
        const currentInitData = telegram.getInitData();
        if (currentInitData) {
          logger.debug('initData появился, продолжаем инициализацию');
          authenticate();

          // Проверяем startParam из initData (теперь доступен)
          const startParamFromInit = telegram.getStartParam();
          if (startParamFromInit === 'games') {
            useAppStore.getState().setCurrentScreen('games');
          } else if (startParamFromInit === 'my_panda') {
            useAppStore.getState().setCurrentScreen('my-panda');
          }
        } else {
          // Если через 2 секунды все еще нет - показываем ошибку только если точно в Telegram
          const isTelegramUA = typeof window !== 'undefined' &&
            (window.navigator.userAgent.includes('Telegram') ||
             window.location.hostname.includes('telegram.org'));

          if (isTelegramUA) {
            // В Telegram, но нет initData - возможно проблема с ботом
            console.error('❌ initData не появился в Telegram');
            useAppStore.getState().setError(
              'Не удалось загрузить данные. Попробуйте перезапустить Mini App через кнопку в боте.'
            );
          } else if (import.meta.env.DEV && typeof window !== 'undefined' &&
            (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
            // Локальная разработка без Telegram — mock-пользователь для просмотра Mini App
            const { setUser, setIsLoading, setError } = useAppStore.getState();
            setUser({
              telegram_id: 0,
              first_name: 'Локальный',
              user_type: 'child',
              is_premium: false,
            });
            setError(null);
            setIsLoading(false);
          }
          useAppStore.getState().setIsLoading(false);
        }
      };

      // Проверяем сразу и через 1 секунду
      setTimeout(checkInitData, 1000);
      return;
    }

    // Аутентификация через TanStack Query hook
    authenticate();

    // Проверяем deep linking (startapp=games)
    // Сначала из initData (если доступен)
    let startParam = telegram.getStartParam();

    // Если нет в initData, проверяем URL напрямую (для web.telegram.org)
    if (!startParam && typeof window !== 'undefined') {
      try {
        // Проверяем search параметры
        const urlParams = new URLSearchParams(window.location.search);
        let tgaddr = urlParams.get('tgaddr');

        // Если нет в search, проверяем hash (для web.telegram.org/k/#?tgaddr=...)
        if (!tgaddr && window.location.hash) {
          const hashParams = new URLSearchParams(window.location.hash.slice(1));
          tgaddr = hashParams.get('tgaddr');
        }

        if (tgaddr) {
          // Парсим tgaddr: tg://resolve?domain=PandaPalBot&startapp=games
          const tgaddrParams = new URLSearchParams(tgaddr.split('?')[1] || '');
          startParam = tgaddrParams.get('startapp');
        }

        // Также проверяем прямой параметр startapp в URL (search и hash)
        if (!startParam) {
          startParam = urlParams.get('startapp');
        }
        if (!startParam && window.location.hash) {
          const hashParams = new URLSearchParams(window.location.hash.slice(1));
          startParam = hashParams.get('startapp');
        }
      } catch (e) {
        console.warn('Ошибка парсинга URL параметров:', e);
      }
    }

    if (startParam === 'games') {
      setCurrentScreen('games');
    } else if (startParam === 'my_panda') {
      setCurrentScreen('my-panda');
    }

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

  const navigateTo = (screen: Screen) => {
    setCurrentScreen(screen);
    telegram.hapticFeedback('medium');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen min-h-dvh bg-[var(--tg-theme-bg-color)] safe-area-inset">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div>
          <p className="mt-4 text-[var(--tg-theme-text-color)]">Загрузка...</p>
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen min-h-dvh bg-[var(--tg-theme-bg-color)] p-4 safe-area-inset">
        <div className="text-center">
          <div className="text-6xl mb-4">😔</div>
          <h2 className="text-xl font-display font-bold text-[var(--tg-theme-text-color)] mb-2">
            Ошибка загрузки
          </h2>
          <p className="text-[var(--tg-theme-hint-color)]">
            {error || 'Не удалось загрузить данные'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-6 py-2 bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] rounded-lg"
            aria-label="Перезагрузить страницу"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen min-h-dvh flex flex-col bg-white dark:bg-slate-800 overflow-hidden">
      {/* Основной контент с Suspense для lazy loading */}
      <div className="flex-1 overflow-hidden">
        <Suspense fallback={<LoadingFallback />}>
          {currentScreen === 'ai-chat' && user && <AIChat user={user} />}
          {currentScreen === 'emergency' && <EmergencyScreen />}
          {currentScreen === 'achievements' && user && <AchievementsScreen user={user} />}
          {currentScreen === 'premium' && user && <PremiumScreen user={user} />}
          {currentScreen === 'donation' && <DonationScreen user={user} />}
          {currentScreen === 'games' && user && <GamesScreen user={user} />}
          {currentScreen === 'my-panda' && user && <MyPandaScreen user={user} />}
        </Suspense>
      </div>

      {/* Нижняя навигация - фиксированная */}
      {currentScreen === 'ai-chat' ? (
        <nav className="flex-shrink-0 bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 shadow-lg safe-area-inset-bottom" aria-label="Основная навигация">
          <div className="flex gap-1.5 sm:gap-2 md:gap-3 px-1.5 sm:px-2 md:px-3 py-2 sm:py-2.5 md:py-3 max-w-full overflow-x-auto">
            <NavButton
              icon="🏆"
              label="Достижения"
              isActive={false}
              onClick={() => navigateTo('achievements')}
            />
            <NavButton
              icon="🎮"
              label="PandaPalGo"
              isActive={false}
              onClick={() => navigateTo('games')}
            />
            <NavButton
              icon="👑"
              label="Premium"
              isActive={false}
              onClick={() => navigateTo('premium')}
            />
          </div>
        </nav>
      ) : currentScreen === 'games' ? null : currentScreen === 'my-panda' ? (
        <nav className="flex-shrink-0 bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 shadow-lg safe-area-inset-bottom" aria-label="Основная навигация">
          <div className="flex gap-1.5 sm:gap-2 md:gap-3 px-1.5 sm:px-2 md:px-3 py-2 sm:py-2.5 md:py-3 max-w-full overflow-x-auto">
            <NavButton icon="💬" label="Чат" isActive={false} onClick={() => navigateTo('ai-chat')} />
            <NavButton icon="🏆" label="Достижения" isActive={false} onClick={() => navigateTo('achievements')} />
            <NavButton icon="🎮" label="PandaPalGo" isActive={false} onClick={() => navigateTo('games')} />
            <NavButton icon="👑" label="Premium" isActive={false} onClick={() => navigateTo('premium')} />
          </div>
        </nav>
      ) : (
        <nav className="flex-shrink-0 bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 shadow-lg safe-area-inset-bottom" aria-label="Основная навигация">
          <div className="flex gap-1.5 sm:gap-2 md:gap-3 px-1.5 sm:px-2 md:px-3 py-2 sm:py-2.5 md:py-3 max-w-full overflow-x-auto">
            <NavButton
              icon="💬"
              label="Чат"
              isActive={false}
              onClick={() => navigateTo('ai-chat')}
            />
            {currentScreen === 'achievements' && (
              <NavButton
                icon="🏆"
                label="Достижения"
                isActive={true}
                onClick={() => navigateTo('achievements')}
              />
            )}
            {currentScreen === 'premium' && (
              <NavButton
                icon="💝"
                label="Поддержать"
                isActive={false}
                onClick={() => navigateTo('donation')}
              />
            )}
            {currentScreen === 'donation' && (
              <NavButton
                icon="👑"
                label="Premium"
                isActive={false}
                onClick={() => navigateTo('premium')}
              />
            )}
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
      className={`flex-1 flex flex-col items-center justify-center gap-0.5 sm:gap-1 py-2 sm:py-2.5 px-1.5 sm:px-2 rounded-lg sm:rounded-xl transition-all min-w-0 min-h-[60px] sm:min-h-[70px] touch-manipulation ${
        isActive
          ? 'bg-blue-500 dark:bg-blue-600 text-white font-semibold shadow-md'
          : 'text-gray-900 dark:text-slate-100 bg-white dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 active:bg-gray-200 dark:active:bg-slate-600 active:scale-95 font-medium border border-gray-200 dark:border-slate-700'
      }`}
      aria-label={label}
      aria-current={isActive ? 'page' : undefined}
    >
      <span className="text-xl sm:text-2xl md:text-3xl flex-shrink-0 leading-none" aria-hidden="true">{icon}</span>
      <span className="text-xs sm:text-sm md:text-base font-medium leading-tight text-center break-words line-clamp-2 w-full px-0.5">{label}</span>
    </button>
  );
}

/**
 * Fallback компонент для Suspense
 */
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-full min-h-screen min-h-dvh">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">Загрузка...</p>
      </div>
    </div>
  );
}
