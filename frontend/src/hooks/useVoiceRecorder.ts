/**
 * Hook для записи голосовых сообщений
 * Вынесен из AIChat.tsx для соответствия SOLID (SRP)
 *
 * Отвечает за:
 * - Запрос доступа к микрофону
 * - Управление MediaRecorder
 * - Валидацию записи
 * - Конвертацию в base64
 */

import { useRef, useCallback, useState } from 'react';
import { telegram } from '../services/telegram';
import {
  MIN_RECORDING_DURATION,
  MIN_AUDIO_SIZE,
  INSTANT_FAILURE_THRESHOLD,
  AUDIO_MIME_TYPE,
} from '../features/AIChat/constants';

export interface UseVoiceRecorderOptions {
  onRecordingComplete: (base64Audio: string) => void;
  onError: (error: string) => void;
}

export interface UseVoiceRecorderReturn {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  isRecording: boolean;
  isGettingAccess: boolean;
  cleanup: () => void;
}

export function useVoiceRecorder({
  onRecordingComplete,
  onError,
}: UseVoiceRecorderOptions): UseVoiceRecorderReturn {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingStartTimeRef = useRef<number>(0);
  const audioChunksRef = useRef<Blob[]>([]);
  const mimeTypeRef = useRef<string>('');
  const [isRecording, setIsRecording] = useState(false);
  const [isGettingAccess, setIsGettingAccess] = useState(false);
  const isGettingAccessRef = useRef(false);

  const cleanup = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
    isGettingAccessRef.current = false;
  }, []);

  const stopRecordingCleanup = useCallback(() => {
    setIsRecording(false);
    setIsGettingAccess(false);
    isGettingAccessRef.current = false;
    cleanup();
  }, [cleanup]);

  const validateRecording = useCallback(
    (duration: number, totalSize: number): { valid: boolean; error?: string } => {
      // Ошибка формата (упал мгновенно)
      if (duration < INSTANT_FAILURE_THRESHOLD && totalSize === 0) {
        return {
          valid: false,
          error: 'Ошибка записи на этом устройстве. Попробуйте обновить Telegram.',
        };
      }

      // Слишком короткая запись
      if (duration < MIN_RECORDING_DURATION || totalSize < MIN_AUDIO_SIZE) {
        return {
          valid: false,
          error: 'Запись слишком короткая. Удерживай кнопку дольше.',
        };
      }

      return { valid: true };
    },
    []
  );

  const startRecording = useCallback(async () => {
    if (isRecording || isGettingAccessRef.current) return;

    isGettingAccessRef.current = true;
    setIsGettingAccess(true);
    setIsRecording(true);

    try {
      // Запрос доступа к микрофону
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Определяем поддерживаемый MIME тип
      let mimeType = '';
      if (MediaRecorder.isTypeSupported(AUDIO_MIME_TYPE)) {
        mimeType = AUDIO_MIME_TYPE;
      }

      const options = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      mimeTypeRef.current = mimeType;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const recordingDuration = Date.now() - recordingStartTimeRef.current;
        const totalSize = audioChunksRef.current.reduce(
          (acc, chunk) => acc + chunk.size,
          0
        );

        const validation = validateRecording(recordingDuration, totalSize);

        if (!validation.valid) {
          console.warn('⚠️ Запись не прошла валидацию:', validation.error);
          telegram.notifyError();
          telegram.showAlert(validation.error || 'Ошибка записи');
          stopRecordingCleanup();
          return;
        }

        // Успешная запись
        const audioBlob = new Blob(audioChunksRef.current, {
          type: mimeType || AUDIO_MIME_TYPE,
        });
        telegram.hapticFeedback('medium');

        const reader = new FileReader();
        reader.onload = () => {
          const base64Audio = reader.result as string;
          onRecordingComplete(base64Audio);
          stopRecordingCleanup();
        };

        reader.onerror = () => {
          telegram.showAlert('Ошибка обработки аудио');
          stopRecordingCleanup();
          onError('Ошибка обработки аудио');
        };

        reader.readAsDataURL(audioBlob);
      };

      mediaRecorder.onerror = (event: Event) => {
        console.error('❌ MediaRecorder Error:', event);
        telegram.notifyError();
        stopRecordingCleanup();
        telegram.showAlert('Произошла ошибка записи аудио.');
        onError('Произошла ошибка записи аудио.');
      };

      recordingStartTimeRef.current = Date.now();
      mediaRecorder.start();
      // Запись начата
    } catch (error) {
      console.error('❌ Ошибка handleVoiceStart:', error);
      telegram.notifyError();
      stopRecordingCleanup();

      let errorMessage = 'Не удалось начать запись. Проверьте микрофон.';
      if (error instanceof DOMException && error.name === 'NotAllowedError') {
        errorMessage = 'Доступ к микрофону запрещен. Разрешите доступ в настройках.';
      }

      telegram.showAlert(errorMessage);
      onError(errorMessage);
    }
  }, [validateRecording, onRecordingComplete, onError, stopRecordingCleanup, isRecording]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  return {
    startRecording,
    stopRecording,
    isRecording,
    isGettingAccess,
    cleanup,
  };
}
