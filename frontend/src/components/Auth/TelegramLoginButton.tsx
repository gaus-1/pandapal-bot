import { useEffect, useState } from 'react';
import { useAppStore } from '../../store/appStore';

interface TelegramLoginButtonProps {
  onAuth: (user: TelegramUser) => void;
  buttonSize?: 'small' | 'medium' | 'large';
  requestWriteAccess?: boolean;
}

interface TelegramUser {
  telegram_id: number;
  full_name: string;
  username?: string;
  is_premium: boolean;
}

interface TelegramAuthData {
  id: string;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: string;
  hash: string;
  [key: string]: string | undefined;
}

/**
 * Telegram Login Widget - Кнопка входа через Telegram
 *
 * Использует официальный Telegram Login Widget для безопасной авторизации.
 * После успешной авторизации создаёт сессию на backend и сохраняет данные пользователя.
 *
 * @param onAuth - Callback функция, вызываемая после успешной авторизации
 * @param buttonSize - Размер кнопки: 'small', 'medium', 'large'
 * @param requestWriteAccess - Запросить ли разрешение на отправку сообщений
 */
export const TelegramLoginButton: React.FC<TelegramLoginButtonProps> = ({
  onAuth,
  buttonSize = 'large',
  requestWriteAccess = false,
}) => {
  const { setWebUser, setSessionToken } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Создаём глобальный callback для Telegram Widget
    window.TelegramLoginWidget = {
      dataOnauth: async (telegramData: TelegramAuthData) => {
        setIsLoading(true);
        setError(null);

        try {
          // Отправляем данные на backend для валидации и создания сессии
          const response = await fetch('/api/auth/telegram/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams(telegramData as Record<string, string>).toString(),
          });

          if (!response.ok) {
            throw new Error('Ошибка авторизации');
          }

          const data = await response.json();

          if (data.success) {
            // Сохраняем session token в localStorage
            localStorage.setItem('telegram_session', data.session_token);
            setSessionToken(data.session_token);

            // Сохраняем данные пользователя в store
            setWebUser(data.user);

            // Вызываем callback
            onAuth(data.user);

            // Авторизация через Telegram успешна
          } else {
            throw new Error(data.error || 'Неизвестная ошибка');
          }
        } catch (err) {
          console.error('❌ Ошибка авторизации:', err);
          setError('Не удалось войти через Telegram. Попробуйте ещё раз.');
        } finally {
          setIsLoading(false);
        }
      },
    };

    // Загружаем скрипт Telegram Widget
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.async = true;
    script.setAttribute('data-telegram-login', 'PandaPalBot');
    script.setAttribute('data-size', buttonSize);
    script.setAttribute('data-onauth', 'TelegramLoginWidget.dataOnauth(user)');
    script.setAttribute('data-request-access', requestWriteAccess ? 'write' : '');

    const container = document.getElementById('telegram-login-container');
    if (container) {
      container.appendChild(script);
    }

    // Cleanup
    return () => {
      if (container && container.contains(script)) {
        container.removeChild(script);
      }
    };
  }, [buttonSize, requestWriteAccess, onAuth, setWebUser, setSessionToken]);

  return (
    <div className="telegram-login-wrapper">
      {isLoading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Авторизация...</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      <div id="telegram-login-container"></div>

      <style>{`
        .telegram-login-wrapper {
          position: relative;
          display: inline-block;
        }

        .loading-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(255, 255, 255, 0.95);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
          z-index: 10;
        }

        .spinner {
          width: 32px;
          height: 32px;
          border: 3px solid #e5e7eb;
          border-top-color: #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .loading-overlay p {
          margin-top: 12px;
          color: #6b7280;
          font-size: 14px;
        }

        .error-message {
          margin-bottom: 12px;
          padding: 12px 16px;
          background: #fee2e2;
          border: 1px solid #fca5a5;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          color: #991b1b;
          font-size: 14px;
        }

        .error-message button {
          background: none;
          border: none;
          color: #991b1b;
          cursor: pointer;
          font-size: 18px;
          padding: 0 4px;
        }

        .error-message button:hover {
          opacity: 0.7;
        }
      `}</style>
    </div>
  );
};

// Расширяем глобальный объект Window
declare global {
  interface Window {
    TelegramLoginWidget?: {
      dataOnauth: (user: TelegramAuthData) => void;
    };
  }
}
