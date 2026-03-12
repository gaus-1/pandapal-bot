/**
 * Карта с кнопкой открытия в Яндекс.Картах.
 *
 * Telegram Mini App блокирует iframe через CSP,
 * поэтому показываем статичную карту + кнопку для интерактивного просмотра.
 */

import type { MapData } from '../hooks/useChat';

interface InteractiveMapProps {
  mapData: MapData;
  /** Статичная картинка (base64 data URL) */
  fallbackImageUrl?: string;
}

export function InteractiveMap({ mapData, fallbackImageUrl }: InteractiveMapProps) {
  const { lat, lon, zoom, label } = mapData;

  // Ссылка на Яндекс.Карты с координатами и маркером
  const yandexMapsUrl =
    `https://yandex.ru/maps/?ll=${lon},${lat}&z=${zoom}` +
    `&pt=${lon},${lat},pm2rdm`;

  const handleOpenMap = () => {
    window.open(yandexMapsUrl, '_blank');
  };

  return (
    <div className="relative w-full rounded-xl overflow-hidden mb-fib-2 shadow-md group">
      {/* Статичная карта */}
      {fallbackImageUrl && (
        <img
          src={fallbackImageUrl}
          alt={`Карта: ${label}`}
          className="w-full block rounded-xl"
        />
      )}

      {/* Кнопка "Открыть карту" поверх изображения */}
      <button
        onClick={handleOpenMap}
        className="absolute bottom-fib-2 right-fib-2 flex items-center gap-fib-1 px-fib-2 py-fib-1
          bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm
          text-xs font-medium text-blue-600 dark:text-blue-400
          rounded-lg shadow-md border border-gray-200/50 dark:border-slate-600/50
          hover:bg-white dark:hover:bg-slate-700 active:scale-95
          transition-all"
      >
        <span>🗺️</span>
        <span>Открыть карту</span>
      </button>
    </div>
  );
}
