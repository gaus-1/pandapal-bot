/**
 * Chat Hook - использует TanStack Query для кэширования истории
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getChatHistory, sendAIMessage } from '../services/api';
import { queryKeys } from '../lib/queryClient';
import { telegram } from '../services/telegram';

interface UseChatOptions {
  telegramId: number;
  limit?: number;
}

type ChatMessage = {
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
};

/**
 * Hook для работы с AI чатом
 * Кэширует историю и оптимистично обновляет UI
 */
export function useChat({ telegramId, limit = 20 }: UseChatOptions) {
  const queryClient = useQueryClient();

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

  // Отправка сообщения AI
  const sendMessageMutation = useMutation({
    mutationFn: ({
      message,
      photoBase64,
      audioBase64,
    }: {
      message?: string;
      photoBase64?: string;
      audioBase64?: string;
    }) => sendAIMessage(telegramId, message, photoBase64, audioBase64),

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
      const userMessage: ChatMessage = {
        role: 'user' as const,
        content: variables.photoBase64
          ? '📷 Анализирую фото...'
          : variables.audioBase64
          ? '🎤 Распознаю голос...'
          : variables.message || '',
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
    onError: (_error: Error, _variables, context) => {
      if (context && context.previousMessages) {
        queryClient.setQueryData<ChatMessage[]>(
          queryKeys.chatHistory(telegramId, limit),
          context.previousMessages
        );
      }
      telegram.notifyError();
      console.error('❌ Ошибка отправки сообщения:', _error);

      // Показываем понятное сообщение об ошибке
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
    },
  });

  return {
    messages,
    isLoadingHistory,
    historyError,
    sendMessage: sendMessageMutation.mutate,
    isSending: sendMessageMutation.isPending,
    sendError: sendMessageMutation.error,
  };
}
