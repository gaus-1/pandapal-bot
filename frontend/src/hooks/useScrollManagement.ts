/**
 * Hook для управления скроллом в чате
 * Вынесен из AIChat.tsx для соответствия SOLID (SRP)
 *
 * Отвечает за:
 * - Автоскролл к последнему сообщению
 * - Определение необходимости кнопок скролла
 * - Управление скроллом вручную
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { telegram } from '../services/telegram';

export interface UseScrollManagementReturn {
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  messagesContainerRef: React.RefObject<HTMLDivElement | null>;
  showScrollButtons: boolean;
  scrollToTop: () => void;
  scrollToBottom: () => void;
}

export function useScrollManagement(
  messagesCount: number
): UseScrollManagementReturn {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollButtons, setShowScrollButtons] = useState(false);

  // Автоскролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messagesCount]);

  // Показываем кнопки скролла если контент больше экрана
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      const hasScroll = container.scrollHeight > container.clientHeight;
      setShowScrollButtons(hasScroll);
    }
  }, [messagesCount]);

  const scrollToTop = useCallback(() => {
    messagesContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
    telegram.hapticFeedback('light');
  }, []);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    telegram.hapticFeedback('light');
  }, []);

  return {
    messagesEndRef,
    messagesContainerRef,
    showScrollButtons,
    scrollToTop,
    scrollToBottom,
  };
}
