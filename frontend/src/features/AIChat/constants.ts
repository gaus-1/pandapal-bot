/**
 * Константы для AI Chat компонента
 * Вынесены для соответствия SOLID принципам (SRP, DIP)
 */

/** Минимальная длительность записи голоса (мс) */
export const MIN_RECORDING_DURATION = 500;

/** Минимальный размер аудио файла (байты) */
export const MIN_AUDIO_SIZE = 1000;

/** Порог для определения мгновенного сбоя рекордера (мс) */
export const INSTANT_FAILURE_THRESHOLD = 200;

/** Поддерживаемый MIME тип для аудио */
export const AUDIO_MIME_TYPE = 'audio/webm';

/** Дефолтный текст для фото без описания */
export const DEFAULT_PHOTO_MESSAGE = 'Помоги мне с этой задачей';

/** Лимит сообщений в истории чата */
export const DEFAULT_CHAT_LIMIT = 20;
