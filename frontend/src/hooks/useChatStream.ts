/**
 * Hook для streaming AI чата через SSE (Server-Sent Events)
 * Вынесен из useChat для соответствия SOLID (SRP)
 *
 * Отвечает за:
 * - Установку SSE соединения
 * - Обработку chunks ответа AI
 * - Обновление UI в реальном времени
 */

import { useState, useCallback, useRef } from 'react';
import { queryKeys } from '../lib/queryClient';
import { useQueryClient } from '@tanstack/react-query';
import { telegram } from '../services/telegram';
import type { ChatMessage } from './useChat';

interface UseChatStreamOptions {
  telegramId: number;
  limit?: number;
  onError?: (error: string) => void;
}

interface StreamStatus {
  status: 'idle' | 'connecting' | 'transcribing' | 'analyzing_photo' | 'generating' | 'completed' | 'error';
  message?: string;
  messageType?: 'text' | 'photo' | 'audio'; // Тип отправленного сообщения
}

export function useChatStream({ telegramId, limit = 20, onError }: UseChatStreamOptions) {
  const queryClient = useQueryClient();
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState<StreamStatus>({ status: 'idle' });
  const eventSourceRef = useRef<EventSource | null>(null);
  const currentResponseRef = useRef<string>('');

  const sendMessageStream = useCallback(
    async ({
      message,
      photoBase64,
      audioBase64,
    }: {
      message?: string;
      photoBase64?: string;
      audioBase64?: string;
    }) => {
      if (isStreaming) return;

      // Определяем тип сообщения
      const messageType = audioBase64 ? 'audio' : photoBase64 ? 'photo' : 'text';

      setIsStreaming(true);
      setStreamStatus({ status: 'connecting', messageType });
      currentResponseRef.current = '';

      // Отменяем текущие запросы истории
      await queryClient.cancelQueries({
        queryKey: queryKeys.chatHistory(telegramId, limit),
      });

      // Сохраняем предыдущее состояние для rollback
      const previousMessages = queryClient.getQueryData<ChatMessage[]>(
        queryKeys.chatHistory(telegramId, limit)
      );

      // НЕ добавляем сообщение пользователя здесь - оно уже добавлено в onMutate в useChat
      // Просто вызываем haptic feedback
      telegram.hapticFeedback('medium');

      try {
        // Получаем API_BASE_URL
        const API_BASE_URL = import.meta.env.PROD
          ? 'https://pandapal.ru/api'
          : 'http://localhost:10000/api';

        // Отправляем запрос на streaming endpoint через POST
        const response = await fetch(`${API_BASE_URL}/miniapp/ai/chat-stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            telegram_id: telegramId,
            message,
            photo_base64: photoBase64,
            audio_base64: audioBase64,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
          throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        // Читаем SSE stream
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('Stream reader not available');
        }

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Парсим SSE события (формат: event: <type>\ndata: <json>\n\n)
          const events = buffer.split('\n\n');
          buffer = events.pop() || ''; // Последнее неполное событие остается в буфере

          for (const eventBlock of events) {
            if (!eventBlock.trim()) continue;

            let eventType = 'message';
            let eventData = '';

            const lines = eventBlock.split('\n');
            for (const line of lines) {
              if (line.startsWith('event: ')) {
                eventType = line.substring(7).trim();
              } else if (line.startsWith('data: ')) {
                eventData = line.substring(6).trim();
              }
            }

            if (!eventData) continue;

            try {
              const data = JSON.parse(eventData);

                // Обработка разных типов событий
                if (data.status === 'transcribing') {
                  setStreamStatus((prev) => ({ ...prev, status: 'transcribing' }));
                } else if (data.status === 'analyzing_photo') {
                  setStreamStatus((prev) => ({ ...prev, status: 'analyzing_photo' }));
                } else if (data.status === 'generating') {
                  setStreamStatus((prev) => ({ ...prev, status: 'generating' }));
                } else if (eventType === 'chunk' && data.chunk) {
                  // Получен chunk текста
                  // YandexGPT может возвращать либо инкрементальные chunks (только новый текст),
                  // либо накопленный текст в каждом chunk
                  // Проверяем, является ли chunk инкрементальным или накопленным
                  const chunkText = data.chunk;

                  // Если текущий накопленный текст уже содержит начало chunk, значит это накопленный формат
                  if (currentResponseRef.current && chunkText.startsWith(currentResponseRef.current)) {
                    // Это накопленный текст - используем его напрямую
                    currentResponseRef.current = chunkText;
                  } else {
                    // Это инкрементальный chunk - добавляем к накопленному
                    currentResponseRef.current += chunkText;
                  }

                  // Обновляем сообщение AI в кэше
                  queryClient.setQueryData<ChatMessage[]>(
                    queryKeys.chatHistory(telegramId, limit),
                    (old) => {
                      if (!old) return old;
                      const updated = [...old];
                      const lastMessage = updated[updated.length - 1];

                      if (lastMessage && lastMessage.role === 'user') {
                        // Добавляем новое сообщение AI с накопленным текстом
                        updated.push({
                          role: 'ai',
                          content: currentResponseRef.current,
                          timestamp: new Date().toISOString(),
                        });
                      } else if (lastMessage && lastMessage.role === 'ai') {
                        // Обновляем существующее сообщение AI
                        updated[updated.length - 1] = {
                          ...lastMessage,
                          content: currentResponseRef.current,
                        };
                      }

                      return updated;
                    }
                  );
                } else if (eventType === 'message' && data.content) {
                  // Получено полное сообщение (например, секретное сообщение)
                  const messageContent = data.content;

                  // Обновляем или добавляем сообщение AI
                  queryClient.setQueryData<ChatMessage[]>(
                    queryKeys.chatHistory(telegramId, limit),
                    (old) => {
                      if (!old) return old;
                      const updated = [...old];
                      const lastMessage = updated[updated.length - 1];

                      if (lastMessage && lastMessage.role === 'user') {
                        // Добавляем новое сообщение AI
                        updated.push({
                          role: 'ai',
                          content: messageContent,
                          timestamp: new Date().toISOString(),
                        });
                      } else if (lastMessage && lastMessage.role === 'ai') {
                        // Обновляем существующее сообщение AI
                        updated[updated.length - 1] = {
                          ...lastMessage,
                          content: messageContent,
                        };
                      }

                      return updated;
                    }
                  );
                  currentResponseRef.current = messageContent;
                } else if (eventType === 'image' && data.image) {
                  // Получено изображение (визуализация или сгенерированное)
                  const imageBase64 = data.image;
                  // Определяем тип изображения: generated_image = JPEG, иначе PNG
                  const imageType = data.type === 'generated_image' ? 'jpeg' : 'png';
                  const imageUrl = `data:image/${imageType};base64,${imageBase64}`;

                  // Обновляем последнее сообщение AI, добавляя изображение
                  queryClient.setQueryData<ChatMessage[]>(
                    queryKeys.chatHistory(telegramId, limit),
                    (old) => {
                      if (!old) return old;
                      const updated = [...old];
                      const lastMessage = updated[updated.length - 1];

                      if (lastMessage && lastMessage.role === 'ai') {
                        // Добавляем изображение к сообщению AI
                        updated[updated.length - 1] = {
                          ...lastMessage,
                          imageUrl: imageUrl,
                        };
                      } else {
                        // Если нет сообщения AI, создаем новое
                        updated.push({
                          role: 'ai',
                          content: data.type === 'generated_image' ? '🎨 Изображение сгенерировано' : '',
                          imageUrl: imageUrl,
                          timestamp: new Date().toISOString(),
                        });
                      }

                      return updated;
                    }
                  );
                } else if (eventType === 'achievements' && data.achievements) {
                  // Достижения получены, но не показываем popup в чате
                  // (достижения можно посмотреть в разделе "Достижения")
                } else if (eventType === 'error' && data.error) {
                  throw new Error(data.error);
                } else if (eventType === 'done') {
                  // Streaming завершен
                  setStreamStatus({ status: 'completed' });
                }
            } catch (parseError) {
              // Игнорируем ошибки парсинга отдельных событий
              console.debug('Ошибка парсинга SSE event:', parseError);
            }
          }
        }

        // Сообщение уже обновлено через chunks, ничего дополнительного делать не нужно
        telegram.notifySuccess();
        setStreamStatus((prev) => ({ ...prev, status: 'completed' }));

        // НЕ инвалидируем запрос - история уже обновлена через chunks
        // Инвалидация приведет к дублированию сообщения пользователя

      } catch (error) {
        console.error('❌ Ошибка streaming:', error);

        // Rollback оптимистичного обновления
        if (previousMessages) {
          queryClient.setQueryData<ChatMessage[]>(
            queryKeys.chatHistory(telegramId, limit),
            previousMessages
          );
        }

        const errorMessage = error instanceof Error ? error.message : 'Ошибка отправки сообщения';
        setStreamStatus((prev) => ({ ...prev, status: 'error', message: errorMessage }));
        telegram.notifyError();

        if (onError) {
          onError(errorMessage);
        } else {
          telegram.showAlert('Не удалось отправить сообщение. Попробуй еще раз!');
        }
      } finally {
        setIsStreaming(false);
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      }
    },
    [telegramId, limit, isStreaming, queryClient, onError]
  );

  return {
    sendMessageStream,
    isStreaming,
    streamStatus,
  };
}
