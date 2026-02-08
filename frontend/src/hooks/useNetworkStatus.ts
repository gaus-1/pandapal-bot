/**
 * Хук для отслеживания состояния сети.
 * Показывает уведомление при потере/восстановлении соединения.
 */

import { useEffect, useState, useCallback } from 'react';
import { queryClient } from '../lib/queryClient';

interface NetworkStatus {
  /** Есть ли подключение к сети */
  isOnline: boolean;
  /** Было ли восстановление после offline */
  wasOffline: boolean;
}

export function useNetworkStatus(): NetworkStatus {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  const [wasOffline, setWasOffline] = useState(false);

  const handleOnline = useCallback(() => {
    setIsOnline(true);
    setWasOffline(true);
    // При восстановлении сети — инвалидируем все queries для актуальных данных
    queryClient.invalidateQueries();
    // Сбрасываем wasOffline через 5 секунд
    setTimeout(() => setWasOffline(false), 5000);
  }, []);

  const handleOffline = useCallback(() => {
    setIsOnline(false);
  }, []);

  useEffect(() => {
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleOnline, handleOffline]);

  return { isOnline, wasOffline };
}
