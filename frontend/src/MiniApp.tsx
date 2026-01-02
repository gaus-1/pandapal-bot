/**
 * Telegram Mini App - главный компонент
 * Навигация и экраны для всех функций бота
 */

import { useEffect, useState } from 'react';
import { telegram } from './services/telegram';
import { authenticateUser, type UserProfile } from './services/api';

// Импорт экранов
import { AIChat } from './features/AIChat/AIChat';

export function MiniApp() {
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
  }, []);

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
    <div className="h-screen overflow-hidden bg-[var(--tg-theme-bg-color)]">
      {/* Показываем ТОЛЬКО AI Chat - полноэкранно */}
      <AIChat user={user} />
    </div>
  );
}
