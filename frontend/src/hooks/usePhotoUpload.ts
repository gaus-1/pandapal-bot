/**
 * Hook для загрузки фотографий
 * Вынесен из AIChat.tsx для соответствия SOLID (SRP)
 *
 * Отвечает за:
 * - Валидацию файла изображения
 * - Конвертацию в base64
 * - Обработку ошибок
 */

import { useRef, useCallback } from 'react';
import { telegram } from '../services/telegram';

export interface UsePhotoUploadOptions {
  onPhotoUploaded: (base64Photo: string) => void;
  onError: (error: string) => void;
}

export interface UsePhotoUploadReturn {
  handlePhotoClick: () => void;
  handlePhotoUpload: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
}

export function usePhotoUpload({
  onPhotoUploaded,
  onError,
}: UsePhotoUploadOptions): UsePhotoUploadReturn {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handlePhotoClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handlePhotoUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      // Валидация типа файла
      if (!file.type.startsWith('image/')) {
        await telegram.showAlert('Пожалуйста, выбери изображение');
        onError('Неподдерживаемый тип файла');
        return;
      }

      telegram.hapticFeedback('medium');

      try {
        const reader = new FileReader();

        reader.onload = () => {
          const base64Photo = reader.result as string;
          onPhotoUploaded(base64Photo);
        };

        reader.onerror = () => {
          const errorMsg = 'Не удалось загрузить фото';
          telegram.notifyError();
          telegram.showAlert(errorMsg);
          onError(errorMsg);
        };

        reader.readAsDataURL(file);
      } catch (error) {
        console.error('Ошибка загрузки фото:', error);
        const errorMsg = 'Не удалось загрузить фото';
        telegram.notifyError();
        telegram.showAlert(errorMsg);
        onError(errorMsg);
      } finally {
        // Очищаем input для возможности повторной загрузки того же файла
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    },
    [onPhotoUploaded, onError]
  );

  return {
    handlePhotoClick,
    handlePhotoUpload,
    fileInputRef,
  };
}
