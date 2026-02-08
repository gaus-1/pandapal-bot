/**
 * Интерактивная карта Yandex Maps (iframe widget).
 *
 * Показывает карту с маркером — можно двигать, зумить.
 * Не требует npm-зависимостей и API-ключа на фронтенде.
 */

import { useState, useCallback } from 'react';
import type { MapData } from '../hooks/useChat';

interface InteractiveMapProps {
  mapData: MapData;
  /** Статичная картинка как fallback (base64 data URL) */
  fallbackImageUrl?: string;
}

export function InteractiveMap({ mapData, fallbackImageUrl }: InteractiveMapProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  const handleLoad = useCallback(() => setIsLoaded(true), []);
  const handleError = useCallback(() => setHasError(true), []);

  // Yandex Maps embed widget — интерактивная карта без API ключа
  const { lat, lon, zoom, label } = mapData;
  const mapUrl =
    `https://yandex.ru/map-widget/v1/?ll=${lon},${lat}&z=${zoom}` +
    `&pt=${lon},${lat},pm2rdm` +
    `&l=map`;

  // Если iframe не загрузился — показываем статичную картинку
  if (hasError && fallbackImageUrl) {
    return (
      <img
        src={fallbackImageUrl}
        alt={`Карта: ${label}`}
        className="w-full rounded-xl mb-2 shadow-md"
      />
    );
  }

  return (
    <div className="relative w-full rounded-xl overflow-hidden mb-2 shadow-md">
      {/* Skeleton / loading state */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800 animate-pulse">
          <div className="text-center text-gray-400 dark:text-gray-500">
            <span className="text-2xl">🗺️</span>
            <p className="text-xs mt-1">Загрузка карты...</p>
          </div>
        </div>
      )}

      <iframe
        src={mapUrl}
        title={`Карта: ${label}`}
        width="100%"
        height="300"
        frameBorder="0"
        allowFullScreen
        onLoad={handleLoad}
        onError={handleError}
        className="w-full block"
        style={{ minHeight: '280px', border: 'none' }}
      />
    </div>
  );
}
