/**
 * Authentication Hook - использует TanStack Query для кэширования
 */

import { useMutation } from '@tanstack/react-query';
import { authenticateUser } from '../services/api';
import { useAppStore } from '../store/appStore';
import { telegram } from '../services/telegram';
import { logger } from '../utils/logger';

/**
 * Hook для аутентификации пользователя через Telegram Mini App
 * Автоматически обновляет глобальное состояние через Zustand
 */
export function useAuth() {
  const { setUser, setError, setIsLoading } = useAppStore();

  const mutation = useMutation({
    mutationFn: authenticateUser,
    onSuccess: (userProfile) => {
      logger.debug('Auth success:', userProfile.telegram_id);
      setUser(userProfile);
      setIsLoading(false);
      setError(null);
      telegram.notifySuccess();
    },
    onError: (error: Error) => {
      console.error('❌ Ошибка аутентификации:', error);

      let errorMessage = 'Не удалось загрузить приложение.';

      // Расшифровываем ошибки
      if (error.message.includes('Invalid Telegram signature')) {
        errorMessage = 'Ошибка проверки подписи Telegram. Перезапустите бота.';
      } else if (error.message.includes('initData недоступен')) {
        errorMessage = 'Приложение должно запускаться через Telegram Mini App.';
      } else if (error.message.includes('fetch')) {
        errorMessage = 'Не удалось подключиться к серверу. Проверьте интернет-соединение.';
      } else {
        errorMessage = `Ошибка: ${error.message}`;
      }

      setError(errorMessage);
      setIsLoading(false);
      telegram.notifyError();
    },
  });

  return {
    authenticate: mutation.mutate,
    isAuthenticating: mutation.isPending,
    error: mutation.error,
  };
}
