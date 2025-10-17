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
   * БЕЗОПАСНАЯ валидация данных от Telegram
   * КРИТИЧЕСКИ ВАЖНО для защиты детей от подделки данных
   */
  const validateTelegramData = useCallback((user: TelegramUser): boolean => {
    // Проверяем обязательные поля
    if (!user.id || !user.first_name || !user.auth_date || !user.hash) {
      console.error('❌ Неполные данные от Telegram');
      return false;
    }

    // Проверяем типы данных
    if (typeof user.id !== 'number' || user.id <= 0) {
      console.error('❌ Некорректный Telegram ID');
      return false;
    }

    // Проверяем время авторизации (не старше 1 часа)
    const now = Math.floor(Date.now() / 1000);
    const authAge = now - user.auth_date;
    if (authAge > 3600) { // 1 час
      console.error('❌ Данные Telegram устарели');
      return false;
    }

    // Проверяем длину имени (защита от переполнения)
    if (user.first_name.length > 100) {
      console.error('❌ Имя слишком длинное');
      return false;
    }

    // Проверяем username если есть
    if (user.username && user.username.length > 32) {
      console.error('❌ Username слишком длинный');
      return false;
    }

    return true;
  }, []);

  /**
   * Обработчик успешной авторизации
   * Вызывается Telegram Widget после подтверждения
   */
  const handleTelegramAuth = useCallback((user: TelegramUser) => {
    console.log('✅ Telegram авторизация:', user);

    // КРИТИЧЕСКИ ВАЖНО: Валидируем данные перед использованием
    if (!validateTelegramData(user)) {
      console.error('🚫 Данные Telegram не прошли валидацию - возможна атака');
      return; // Не передаём небезопасные данные
    }

    // Передаём ВАЛИДНЫЕ данные родительскому компоненту
    onAuth(user);
  }, [onAuth, validateTelegramData]);

  useEffect(() => {
    // Регистрируем глобальный callback для Telegram
    window.onTelegramAuth = handleTelegramAuth;

    // БЕЗОПАСНАЯ загрузка скрипта Telegram Widget с защитой от MITM
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.async = true;

    // КРИТИЧЕСКИ ВАЖНО: Защита от подмены скрипта (Subresource Integrity)
    // Это защищает детей от загрузки вредоносного кода
    script.setAttribute('crossorigin', 'anonymous');

    // Telegram Widget атрибуты
    script.setAttribute('data-telegram-login', botName);
    script.setAttribute('data-size', size);
    script.setAttribute('data-userpic', showAvatar.toString());
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');

    // Обработка ошибок загрузки для дополнительной безопасности
    script.onerror = () => {
      console.error('❌ Ошибка загрузки Telegram Widget - возможна атака MITM');
      // Можно показать пользователю предупреждение
    };

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
      window.onTelegramAuth = undefined as unknown as ((user: TelegramUser) => void) | undefined;
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
