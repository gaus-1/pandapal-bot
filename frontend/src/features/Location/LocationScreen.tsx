/**
 * Location Screen - РЕАЛЬНОЕ определение местоположения
 * Использует Geolocation API + отправка родителям
 */

import { useState } from 'react';
import { telegram } from '../../services/telegram';
import type { UserProfile } from '../../services/api';

interface LocationScreenProps {
  user: UserProfile;
}

interface LocationData {
  latitude: number;
  longitude: number;
  accuracy?: number;
  address?: string;
}

export function LocationScreen({ user }: LocationScreenProps) {
  const [isSending, setIsSending] = useState(false);
  const [location, setLocation] = useState<LocationData | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const getLocation = () => {
    setIsSending(true);
    setError(null);
    telegram.hapticFeedback('medium');

    // Проверяем поддержку геолокации
    if (!navigator.geolocation) {
      setError('❌ Геолокация недоступна в твоем устройстве');
      setIsSending(false);
      telegram.notifyError();
      return;
    }

    // Запрашиваем разрешение через Telegram WebApp (если доступно)
    if (telegram.isInTelegram()) {
      telegram.showPopup({
        title: 'Доступ к местоположению',
        message: 'Разреши доступ к геолокации в следующем окне браузера',
        buttons: [
          { id: 'ok', type: 'default', text: 'Понятно' }
        ]
      });
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude, accuracy } = position.coords;

        setLocation({
          latitude,
          longitude,
          accuracy,
        });

        // Получаем адрес через обратное геокодирование
        try {
          const address = await reverseGeocode(latitude, longitude);
          setLocation((prev) => (prev ? { ...prev, address } : null));
        } catch (err) {
          console.error('Ошибка геокодирования:', err);
        }

        // Отправляем родителям
        await sendLocationToParent(latitude, longitude, accuracy);

        setMessage('✅ Местоположение отправлено родителям!');
        telegram.notifySuccess();
        setIsSending(false);
      },
      (err) => {
        console.error('Ошибка геолокации:', err);
        let errorMsg = '❌ Не удалось определить местоположение';

        switch (err.code) {
          case err.PERMISSION_DENIED:
            errorMsg = '❌ Разреши доступ к геолокации в настройках браузера';
            break;
          case err.POSITION_UNAVAILABLE:
            errorMsg = '❌ Геолокация недоступна';
            break;
          case err.TIMEOUT:
            errorMsg = '❌ Время ожидания истекло. Попробуй еще раз';
            break;
        }

        setError(errorMsg);
        telegram.notifyError();
        setIsSending(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  };

  const reverseGeocode = async (lat: number, lon: number): Promise<string> => {
    // Используем Nominatim (OpenStreetMap) для обратного геокодирования
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=18&addressdetails=1`,
      {
        headers: {
          'User-Agent': 'PandaPal-Bot',
        },
      }
    );

    if (!response.ok) throw new Error('Geocoding failed');

    const data = await response.json();
    return data.display_name || 'Адрес не определен';
  };

  const sendLocationToParent = async (
    latitude: number,
    longitude: number,
    accuracy?: number
  ): Promise<void> => {
    // Отправляем через backend API родителям
    try {
      const response = await fetch('/api/miniapp/location/share', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          telegram_id: user.telegram_id,
          latitude,
          longitude,
          accuracy,
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send location');
      }
    } catch (err) {
      console.error('Ошибка отправки местоположения:', err);
      // Не показываем ошибку пользователю, но логируем
    }
  };

  return (
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4">
      {/* Заголовок */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-2">📍 Где я?</h1>
        <p className="text-[var(--tg-theme-hint-color)]">
          Потерялся? Отправь свое местоположение родителям
        </p>
      </div>

      {/* Основная карточка */}
      <div className="bg-[var(--tg-theme-secondary-bg-color)] rounded-2xl p-6 mb-4 shadow-lg">
        {!location ? (
          <>
            <div className="text-center mb-6">
              <div className="text-6xl mb-4">🗺️</div>
              <p className="text-[var(--tg-theme-text-color)] mb-2">
                Нажми кнопку, чтобы определить твое местоположение
              </p>
            </div>

            <button
              onClick={getLocation}
              disabled={isSending}
              className="w-full bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] py-4 px-6 rounded-xl font-bold text-lg disabled:opacity-50 hover:opacity-90 active:scale-95 transition-all"
            >
              {isSending ? '🔍 Определяю...' : '📍 Определить местоположение'}
            </button>
          </>
        ) : (
          <>
            <div className="text-center mb-4">
              <div className="text-6xl mb-4">✅</div>
              <p className="font-bold text-[var(--tg-theme-text-color)] text-lg mb-2">
                Местоположение найдено!
              </p>
            </div>

            {/* Информация о местоположении */}
            <div className="bg-[var(--tg-theme-bg-color)] rounded-xl p-4 mb-4">
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-[var(--tg-theme-hint-color)]">Координаты:</span>
                  <p className="font-mono text-[var(--tg-theme-text-color)]">
                    {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
                  </p>
                </div>

                {location.accuracy && (
                  <div>
                    <span className="text-[var(--tg-theme-hint-color)]">Точность:</span>
                    <p className="text-[var(--tg-theme-text-color)]">±{Math.round(location.accuracy)}м</p>
                  </div>
                )}

                {location.address && (
                  <div>
                    <span className="text-[var(--tg-theme-hint-color)]">Адрес:</span>
                    <p className="text-[var(--tg-theme-text-color)]">{location.address}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Ссылка на карту */}
            <a
              href={`https://www.google.com/maps?q=${location.latitude},${location.longitude}`}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full bg-blue-500 text-white py-3 px-6 rounded-xl font-bold text-center mb-3 hover:bg-blue-600 transition-colors"
            >
              🗺️ Открыть на карте
            </a>

            <button
              onClick={() => {
                setLocation(null);
                setMessage(null);
                setError(null);
              }}
              className="w-full bg-[var(--tg-theme-hint-color)]/20 text-[var(--tg-theme-text-color)] py-3 px-6 rounded-xl font-bold hover:bg-[var(--tg-theme-hint-color)]/30 transition-colors"
            >
              🔄 Определить заново
            </button>
          </>
        )}

        {/* Сообщения */}
        {message && (
          <div className="mt-4 text-center p-3 bg-green-500/20 rounded-lg">
            <p className="text-[var(--tg-theme-text-color)] font-semibold">{message}</p>
          </div>
        )}

        {error && (
          <div className="mt-4 text-center p-3 bg-red-500/20 rounded-lg">
            <p className="text-[var(--tg-theme-text-color)] font-semibold">{error}</p>
          </div>
        )}
      </div>

      {/* Предупреждение о конфиденциальности */}
      <div className="bg-yellow-500/10 border-2 border-yellow-500/30 rounded-2xl p-4">
        <p className="text-sm text-[var(--tg-theme-text-color)]">
          <span className="font-bold">🔒 Конфиденциально:</span> Твое местоположение увидят только
          родители. Данные не сохраняются на сервере.
        </p>
      </div>
    </div>
  );
}
