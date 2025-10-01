/**
 * Кастомный хук для обработки ошибок загрузки изображений
 * Автоматически подставляет fallback-изображение при ошибке
 * @module hooks/useImageFallback
 */

import { useState, useCallback } from 'react';

/**
 * Хук для fallback изображений
 * 
 * @param fallbackSrc - Путь к запасному изображению (показывается при ошибке)
 * @returns Объект с текущим src и обработчиком ошибки
 * 
 * @example
 * const { handleError } = useImageFallback('/placeholder.png');
 * <img src="/logo.png" onError={handleError} />
 */
export const useImageFallback = (fallbackSrc: string = '/vite.svg') => {
  // Храним текущий src изображения
  const [imgSrc, setImgSrc] = useState<string | null>(null);

  /**
   * Обработчик ошибки загрузки изображения
   * Подставляет fallback-изображение вместо сломанного
   */
  const handleError = useCallback(
    (e: React.SyntheticEvent<HTMLImageElement>) => {
      // Меняем src на fallback
      e.currentTarget.src = fallbackSrc;
      setImgSrc(fallbackSrc);
    },
    [fallbackSrc] // Пересоздаём callback только при смене fallback
  );

  return { imgSrc, handleError };
};

