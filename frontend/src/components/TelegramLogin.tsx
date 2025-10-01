/**
 * Компонент авторизации через Telegram
 * Использует официальный Telegram Login Widget
 * @module components/TelegramLogin
 */

import React, { useEffect, useCallback } from 'react';

/**
 * Данные пользователя от Telegram
 * Приходят после успешной авторизации
 */
interface TelegramUser {
  id: number;           // Telegram ID
  first_name: string;   // Имя
  last_name?: string;   // Фамилия
  username?: string;    // Username (без @)
  photo_url?: string;   // URL фото профиля
  auth_date: number;    // Unix timestamp авторизации
  hash: string;         // HMAC-SHA256 подпись для верификации
}

/**
 * Props для TelegramLogin
 */
interface TelegramLoginProps {
  /** Callback при успешной авторизации */
  onAuth: (user: TelegramUser) => void;
  /** Размер кнопки: small, medium, large */
  size?: 'small' | 'medium' | 'large';
  /** Показывать фото пользователя */
  showAvatar?: boolean;
}

/**
 * Глобальный callback для Telegram Widget
 * Telegram вызывает эту функцию после авторизации
 */
declare global {
  interface Window {
    onTelegramAuth: (user: TelegramUser) => void;
  }
}

/**
 * Компонент кнопки "Войти через Telegram"
 * 
 * Использует официальный виджет Telegram для безопасной авторизации:
 * 1. Пользователь кликает кнопку
 * 2. Открывается окно Telegram (web или app)
 * 3. Пользователь подтверждает авторизацию
 * 4. Telegram передаёт данные + hash для верификации
 * 5. Frontend отправляет данные на backend для проверки подписи
 * 
 * Безопасность:
 * - Hash проверяется на backend (HMAC-SHA256 с bot_token)
 * - Защита от подделки данных
 * - Timeout: данные действительны 1 час
 */
export const TelegramLogin: React.FC<TelegramLoginProps> = React.memo(({
  onAuth,
  size = 'large',
  showAvatar = true,
}) => {
  const botName = 'PandaPalBot'; // Имя бота без @
  
  /**
   * Обработчик успешной авторизации
   * Вызывается Telegram Widget после подтверждения
   */
  const handleTelegramAuth = useCallback((user: TelegramUser) => {
    console.log('✅ Telegram авторизация:', user);
    
    // Передаём данные родительскому компоненту
    onAuth(user);
  }, [onAuth]);
  
  useEffect(() => {
    // Регистрируем глобальный callback для Telegram
    window.onTelegramAuth = handleTelegramAuth;
    
    // Загружаем скрипт Telegram Widget
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.async = true;
    script.setAttribute('data-telegram-login', botName);
    script.setAttribute('data-size', size);
    script.setAttribute('data-userpic', showAvatar.toString());
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    
    // Добавляем скрипт в контейнер
    const container = document.getElementById('telegram-login-container');
    if (container) {
      container.appendChild(script);
    }
    
    // Cleanup при unmount
    return () => {
      if (container && script.parentNode) {
        container.removeChild(script);
      }
      window.onTelegramAuth = undefined as any;
    };
  }, [botName, size, showAvatar, handleTelegramAuth]);
  
  return (
    <div className="flex flex-col items-center gap-4">
      {/* Контейнер для Telegram Widget */}
      <div id="telegram-login-container" className="flex justify-center" />
      
      {/* Описание для пользователя */}
      <p className="text-sm text-gray-600 text-center max-w-md">
        Войдите через Telegram, чтобы начать общение с PandaPal AI 🐼
      </p>
      
      {/* Информация о безопасности */}
      <p className="text-xs text-gray-500 text-center max-w-md">
        🔒 Безопасная авторизация через Telegram.
        Мы не храним ваш пароль и не имеем доступа к личным сообщениям.
      </p>
    </div>
  );
});

TelegramLogin.displayName = 'TelegramLogin';

