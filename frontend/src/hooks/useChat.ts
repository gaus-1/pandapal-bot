/**
 * Chat Hook - использует TanStack Query для кэширования истории
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getChatHistory, sendAIMessage, clearChatHistory } from '../services/api';
import { queryKeys } from '../lib/queryClient';
import { telegram } from '../services/telegram';
import { useChatStream } from './useChatStream';

// Для логирования
const logger = {
  warn: (...args: unknown[]) => console.warn(...args),
};

interface UseChatOptions {
  telegramId: number;
  limit?: number;
  useStreaming?: boolean; // Использовать streaming ответы (по умолчанию false - старый код)
}

export type ChatMessage = {
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
  imageUrl?: string; // URL изображения визуализации (для AI сообщений)
};

/**
 * Hook для работы с AI чатом
 * Кэширует историю и оптимистично обновляет UI
 * Поддерживает streaming ответы (опционально)
 */
export function useChat({ telegramId, limit = 20, useStreaming = false }: UseChatOptions) {
  const queryClient = useQueryClient();

  // Streaming hook (используется если включен)
  const {
    sendMessageStream,
    isStreaming: isStreamingActive,
    streamStatus,
  } = useChatStream({
    telegramId,
    limit,
    onError: (error) => {
      console.error('Streaming error:', error);
      // Fallback на обычный режим при ошибке
      if (useStreaming) {
        console.warn('Streaming failed, falling back to regular mode');
      }
    },
  });

  // Получение истории чата
  const {
    data: messages = [],
    isLoading: isLoadingHistory,
    error: historyError,
  } = useQuery({
    queryKey: queryKeys.chatHistory(telegramId, limit),
    queryFn: () => getChatHistory(telegramId, limit),
    enabled: !!telegramId,
  });

  // Отправка сообщения AI (streaming или обычный режим)
  const sendMessageMutation = useMutation({
    mutationFn: async ({
      message,
      photoBase64,
      audioBase64,
    }: {
      message?: string;
      photoBase64?: string;
      audioBase64?: string;
    }) => {
      // Если включен streaming, используем его
      if (useStreaming) {
        try {
          await sendMessageStream({ message, photoBase64, audioBase64 });
          // Streaming обрабатывает всё сам, возвращаем заглушку
          // НЕ вызываем onSuccess, так как streaming уже обновил UI
          return { response: '', _streaming: true };
        } catch (streamError) {
          // Fallback на обычный режим при ошибке streaming
          logger.warn('Streaming failed, falling back to regular mode:', streamError);
          // Используем обычный endpoint
          return sendAIMessage(telegramId, message, photoBase64, audioBase64);
        }
      }
      // Обычный режим
      return sendAIMessage(telegramId, message, photoBase64, audioBase64);
    },

    // Оптимистичное обновление UI
    onMutate: async (variables) => {
      // Отменяем текущие запросы истории
      await queryClient.cancelQueries({
        queryKey: queryKeys.chatHistory(telegramId, limit),
      });

      // Сохраняем предыдущее состояние для rollback
      const previousMessages = queryClient.getQueryData<ChatMessage[]>(
        queryKeys.chatHistory(telegramId, limit)
      );

      // Оптимистично добавляем сообщение пользователя
      // Если отправлено фото без текста - показываем "📷 Фото"
      const userMessageContent = variables.message || (variables.photoBase64 ? '📷 Фото' : '');
      const userMessage: ChatMessage = {
        role: 'user' as const,
        content: userMessageContent,
        timestamp: new Date().toISOString(),
      };

      queryClient.setQueryData<ChatMessage[]>(
        queryKeys.chatHistory(telegramId, limit),
        (old) => [...(old || []), userMessage]
      );

      telegram.hapticFeedback('medium');

      return { previousMessages };
    },

    // Добавляем ответ AI к истории
    onSuccess: (data) => {
      // Пропускаем обработку если это streaming (он уже обработал)
      if (data && typeof data === 'object' && '_streaming' in data) {
        return;
      }

      const aiMessage = {
        role: 'ai' as const,
        content: data.response,
        timestamp: new Date().toISOString(),
      };

      queryClient.setQueryData<ChatMessage[]>(
        queryKeys.chatHistory(telegramId, limit),
        (old) => [...(old || []), aiMessage]
      );

      telegram.notifySuccess();
    },

    // Rollback при ошибке
    onError: async (_error: Error & { data?: unknown; response?: { data?: unknown; status?: number } }, _variables, context) => {
      if (context && context.previousMessages) {
        queryClient.setQueryData<ChatMessage[]>(
          queryKeys.chatHistory(telegramId, limit),
          context.previousMessages
        );
      }
      telegram.notifyError();
      console.error('❌ Ошибка отправки сообщения:', _error);

      // Проверяем, это лимит Premium?
      const errorData = (_error?.response?.data || _error?.data) as {
        premium_required?: boolean;
        error_code?: string;
        premium_message?: string;
        error?: string;
      } | undefined;
      const isPremiumRequired = errorData?.premium_required || errorData?.error_code === 'RATE_LIMIT_EXCEEDED';

      if (isPremiumRequired) {
        // Показываем дружелюбное сообщение о Premium с кнопкой
        const premiumMessage = errorData?.premium_message || errorData?.error ||
          '🐼 Ой! Ты уже использовал все бесплатные вопросы сегодня!\n\n💎 Перейди на Premium для неограниченных вопросов!';

        const buttonId = await telegram.showPopup({
          title: '💎 Premium',
          message: premiumMessage,
          buttons: [
            { id: 'premium', type: 'default', text: '✨ Узнать о Premium' },
            { id: 'later', type: 'close', text: 'Позже' },
          ],
        });

        if (buttonId === 'premium') {
          // Переходим на экран Premium
          const { useAppStore } = await import('../store/appStore');
          useAppStore.getState().setCurrentScreen('premium');
          telegram.hapticFeedback('medium');
        }
      } else {
        // Обычные ошибки
        const errorMessage = _error?.message || 'Ошибка отправки сообщения';
        if (errorMessage.includes('аудио') || errorMessage.includes('audio')) {
          telegram.showAlert(errorMessage);
        } else if (errorMessage.includes('фото') || errorMessage.includes('photo')) {
          telegram.showAlert(errorMessage);
        } else if (errorMessage.includes('больш') || errorMessage.includes('large') || errorMessage.includes('413')) {
          telegram.showAlert('Файл слишком большой. Попробуй уменьшить размер!');
        } else {
          telegram.showAlert('Не удалось отправить сообщение. Попробуй еще раз!');
        }
      }
    },
  });

  // Очистка истории чата
  const clearHistory = async () => {
    try {
      // Вызываем API для удаления истории на сервере
      await clearChatHistory(telegramId);
      // Очищаем кеш после успешного удаления
      queryClient.setQueryData<ChatMessage[]>(
        queryKeys.chatHistory(telegramId, limit),
        []
      );
      // Инвалидируем запрос для перезагрузки
      queryClient.invalidateQueries({ queryKey: queryKeys.chatHistory(telegramId, limit) });
    } catch (error) {
      console.error('Ошибка очистки истории:', error);
      throw error;
    }
  };

  return {
    messages,
    isLoadingHistory,
    historyError,
    sendMessage: sendMessageMutation.mutate,
    isSending: sendMessageMutation.isPending || isStreamingActive,
    sendError: sendMessageMutation.error,
    clearHistory,
    streamStatus: useStreaming ? streamStatus : undefined,
  };
}
