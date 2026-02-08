/**
 * Компонент уведомления о состоянии сети.
 * Показывает баннер при потере соединения и при восстановлении.
 */

import { useNetworkStatus } from '../hooks/useNetworkStatus';

export function NetworkStatusBar() {
  const { isOnline, wasOffline } = useNetworkStatus();

  if (isOnline && !wasOffline) {
    return null;
  }

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-50 px-4 py-2 text-center text-sm font-medium transition-all duration-300 ${
        isOnline
          ? 'bg-green-500 text-white'
          : 'bg-red-500 text-white'
      }`}
      role="alert"
    >
      {isOnline
        ? 'Соединение восстановлено'
        : 'Нет подключения к интернету'}
    </div>
  );
}
