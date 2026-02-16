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
  messagesCount: number,
  isSending?: boolean
): UseScrollManagementReturn {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollButtons, setShowScrollButtons] = useState(false);
  const prevSendingRef = useRef(false);

  // Автоскролл к последнему сообщению при новом сообщении или по завершении ответа
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messagesCount]);

  // После завершения отправки (ответ пришёл) — скролл вниз (фикс «увеличивается чат»)
  // Два таймаута: после мержа финального сообщения и после отрисовки
  useEffect(() => {
    if (prevSendingRef.current && !isSending) {
      const t1 = setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
      const t2 = setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 350);
      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
      };
    }
    prevSendingRef.current = !!isSending;
  }, [isSending]);

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
