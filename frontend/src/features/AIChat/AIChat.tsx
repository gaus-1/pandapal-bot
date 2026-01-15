/**
 * AI Chat Screen - Общение с AI (фикс UI блокировки)
 *
 * Рефакторинг: логика разделена на модули (SOLID принципы)
 * - useVoiceRecorder - запись голоса
 * - usePhotoUpload - загрузка фото
 * - useScrollManagement - управление скроллом
 */

import { useState, useEffect, useRef } from 'react';
import { telegram } from '../../services/telegram';
import { useChat } from '../../hooks/useChat';
import { useAppStore } from '../../store/appStore';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { usePhotoUpload } from '../../hooks/usePhotoUpload';
import { useScrollManagement } from '../../hooks/useScrollManagement';
import { haptic } from '../../utils/hapticFeedback';
import { MiniAppThemeToggle } from '../../components/MiniAppThemeToggle';
import { addGreetingMessage } from '../../services/api';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../../lib/queryClient';
import type { UserProfile } from '../../services/api';

interface AIChatProps {
  user: UserProfile;
}

export function AIChat({ user }: AIChatProps) {
  // Используем streaming по умолчанию для более быстрых ответов
  // При ошибке автоматически fallback на обычный режим
  const {
    messages,
    isLoadingHistory,
    sendMessage,
    isSending,
    clearHistory,
    streamStatus,
  } = useChat({ telegramId: user.telegram_id, limit: 20, useStreaming: true });

  const [inputText, setInputText] = useState('');
  const [replyToMessage, setReplyToMessage] = useState<number | null>(null);
  const [showWelcome, setShowWelcome] = useState(false);
  const [hasShownWelcomeMessage, setHasShownWelcomeMessage] = useState(false);
  const queryClient = useQueryClient();
  const logoRef = useRef<HTMLImageElement | null>(null);

  // Сохраняем выбранное случайное сообщение для генерации
  const randomMessageRef = useRef<string | null>(null);
  const shouldShowRandomRef = useRef<boolean>(false);
  const lastStatusKeyRef = useRef<string>('');

  // Определяем, показывать ли случайное сообщение (20% случаев)
  useEffect(() => {
    const status = streamStatus?.status;
    const messageType = streamStatus?.messageType;
    const statusKey = `${status}-${messageType}`;

    // Если статус изменился, решаем показывать ли случайное сообщение
    if (statusKey !== lastStatusKeyRef.current && status === 'generating') {
      lastStatusKeyRef.current = statusKey;
      shouldShowRandomRef.current = Math.random() < 0.2; // 20% случаев
      if (shouldShowRandomRef.current) {
        randomMessageRef.current = Math.random() > 0.5 ? 'Panda думает...' : 'Я думаю...';
      } else {
        randomMessageRef.current = null;
      }
    }
  }, [streamStatus?.status, streamStatus?.messageType]);

  // Выбираем сообщение статуса на основе типа сообщения и случайности
  const getStatusMessage = (): string => {
    const status = streamStatus?.status;
    const messageType = streamStatus?.messageType;

    // Если показываем случайное сообщение
    if (shouldShowRandomRef.current && randomMessageRef.current && status === 'generating') {
      return randomMessageRef.current;
    }

    // Основные статусы по типу сообщения
    if (status === 'transcribing' || (status === 'generating' && messageType === 'audio')) {
      return 'Слушаю твое сообщение...';
    }

    if (status === 'analyzing_photo' || (status === 'generating' && messageType === 'photo')) {
      return 'Смотрю, что на фото...';
    }

    if (status === 'generating' && messageType === 'text') {
      return 'Читаю твое сообщение...';
    }

    if (status === 'generating') {
      return randomMessageRef.current || 'Panda думает...';
    }

    return 'Panda думает...';
  };

  // Управление скроллом
  const {
    messagesEndRef,
    messagesContainerRef,
    showScrollButtons,
    scrollToTop,
    scrollToBottom,
  } = useScrollManagement(messages.length);

  // Загрузка фото
  const {
    handlePhotoClick,
    handlePhotoUpload,
    fileInputRef,
  } = usePhotoUpload({
    onPhotoUploaded: (base64Photo) => {
      sendMessage({
        photoBase64: base64Photo,
        message: inputText.trim() || undefined, // Не отправляем DEFAULT_PHOTO_MESSAGE, только если пользователь сам написал текст
      });
      setInputText('');
    },
    onError: (error) => {
      console.error('Ошибка загрузки фото:', error);
    },
  });

  // Запись голоса
  const {
    startRecording,
    stopRecording,
    isRecording,
    isGettingAccess,
    cleanup: cleanupVoice,
  } = useVoiceRecorder({
    onRecordingComplete: (base64Audio) => {
      sendMessage({
        audioBase64: base64Audio,
        ...(inputText.trim() ? { message: inputText.trim() } : {}),
      });
      setInputText('');
    },
    onError: (error) => {
      console.error('Ошибка записи голоса:', error);
    },
  });

  // Cleanup при размонтировании
  useEffect(() => {
    return () => {
      cleanupVoice();
    };
  }, [cleanupVoice]);

  // Показываем приветствие при первом открытии или очистке чата
  useEffect(() => {
    // Управляем состоянием приветствия на основе истории сообщений
    if (!isLoadingHistory) {
      if (messages.length === 0) {
        // История пустая - показываем приветствие и сбрасываем флаг отправки
        // Это происходит при первом открытии или после очистки истории
        console.log('📋 [Welcome] История пустая, показываем welcome screen');
        setShowWelcome(true);
        setHasShownWelcomeMessage(false);
      } else {
        // Есть сообщения - скрываем приветствие
        console.log('📋 [Welcome] Есть сообщения, скрываем welcome screen');
        setShowWelcome(false);
        setHasShownWelcomeMessage(true);
      }
    } else {
      // Пока история загружается, показываем welcome screen если еще не установлено
      if (!showWelcome && messages.length === 0) {
        console.log('📋 [Welcome] История загружается, но показываем welcome screen');
        setShowWelcome(true);
        setHasShownWelcomeMessage(false);
      }
    }
  }, [messages.length, isLoadingHistory, showWelcome]);

  // Принудительно перезапускаем анимацию логотипа при очистке чата или изменении messages.length
  useEffect(() => {
    if (showWelcome && messages.length === 0 && logoRef.current) {
      const img = logoRef.current;

      // КРИТИЧЕСКИ ВАЖНО для мобильных: используем тройной requestAnimationFrame
      // и принудительно применяем все стили через CSS класс, а не inline
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            // Удаляем все inline стили анимации, чтобы CSS класс работал
            img.style.animation = '';
            img.style.webkitAnimation = '';
            img.style.animationName = '';
            img.style.webkitAnimationName = '';
            img.style.animationDuration = '';
            img.style.webkitAnimationDuration = '';
            img.style.animationTimingFunction = '';
            img.style.webkitAnimationTimingFunction = '';
            img.style.animationIterationCount = '';
            img.style.webkitAnimationIterationCount = '';
            img.style.animationFillMode = '';
            img.style.webkitAnimationFillMode = '';
            img.style.animationPlayState = '';
            img.style.webkitAnimationPlayState = '';

            // Принудительный reflow
            void img.offsetWidth;

            // Применяем только необходимые inline стили для аппаратного ускорения
            img.style.willChange = 'transform';
            img.style.transform = 'translateZ(0)';
            img.style.webkitTransform = 'translateZ(0)';
            img.style.backfaceVisibility = 'hidden';
            img.style.webkitBackfaceVisibility = 'hidden';

            // Принудительно включаем CSS класс (если его нет)
            if (!img.classList.contains('animate-logo-bounce')) {
              img.classList.add('animate-logo-bounce');
            }

            // Еще один reflow для применения CSS класса
            void img.offsetWidth;

            // Принудительно перезапускаем через CSS
            img.style.animation = 'none';
            img.style.webkitAnimation = 'none';
            void img.offsetWidth;
            img.style.animation = '';
            img.style.webkitAnimation = '';
          });
        });
      });
    }
  }, [showWelcome, messages.length]);

  // Автоматическое приветствие от панды через 5 секунд после показа приветствия
  useEffect(() => {
    // Проверяем, что все условия выполнены для отправки приветствия
    const shouldSendWelcome =
      showWelcome &&
      !hasShownWelcomeMessage &&
      !isLoadingHistory &&
      messages.length === 0;

    if (shouldSendWelcome) {
      console.log('⏰ [Welcome] Запускаем таймер для приветствия через 5 секунд...', {
        showWelcome,
        hasShownWelcomeMessage,
        isLoadingHistory,
        messagesLength: messages.length,
      });

      const timer = setTimeout(async () => {
        console.log('⏰ [Welcome] Таймер сработал! Проверяем условия...', {
          messagesLength: messages.length,
          hasShownWelcomeMessage,
          showWelcome,
        });

        // Проверяем еще раз перед отправкой (на случай, если состояние изменилось)
        if (messages.length === 0 && !hasShownWelcomeMessage && showWelcome) {
          try {
            console.log('✅ [Welcome] Условия выполнены, добавляем приветствие...');
            // Добавляем приветственное сообщение от бота напрямую в историю (без отправки через AI)
            const greetings = ['Привет, начнем?', 'Привет! Чем могу помочь?'];
            const randomGreeting = greetings[Math.floor(Math.random() * greetings.length)];
            console.log('🐼 [Welcome] Отправляем запрос:', randomGreeting, 'to', `/api/miniapp/chat/greeting/${user.telegram_id}`);

            const result = await addGreetingMessage(user.telegram_id, randomGreeting);
            console.log('✅ [Welcome] Приветствие добавлено:', result);

            // Обновляем историю чата после добавления приветствия
            await queryClient.invalidateQueries({
              queryKey: queryKeys.chatHistory(user.telegram_id, 20),
            });
            console.log('✅ [Welcome] История чата обновлена');

            setHasShownWelcomeMessage(true);
            setShowWelcome(false);
          } catch (error) {
            console.error('❌ [Welcome] Ошибка добавления приветствия:', error);
            // Если не удалось добавить приветствие, просто скрываем welcome screen
            setHasShownWelcomeMessage(true);
            setShowWelcome(false);
          }
        } else {
          console.log('⚠️ [Welcome] Условия не выполнены, приветствие не отправлено');
        }
      }, 5000); // 5 секунд задержка

      return () => {
        console.log('🧹 [Welcome] Очистка таймера приветствия');
        clearTimeout(timer);
      };
    }
  }, [showWelcome, hasShownWelcomeMessage, isLoadingHistory, messages.length, user.telegram_id, queryClient]);

  const handleSend = () => {
    if (!inputText.trim() || isSending) return;
    let fullMessage = inputText;
    if (replyToMessage !== null && messages[replyToMessage]) {
      const replied = messages[replyToMessage];
      fullMessage = `[Ответ на: "${replied.content.slice(0, 50)}..."]\n\n${inputText}`;
    }
    sendMessage({ message: fullMessage });
    setInputText('');
    setReplyToMessage(null);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearChat = async () => {
    const confirmed = await telegram.showConfirm('Очистить историю чата?');
    if (confirmed) {
      try {
        haptic.medium();
        await clearHistory();
        // Обновляем историю чата после очистки и ждем обновления
        await queryClient.invalidateQueries({
          queryKey: queryKeys.chatHistory(user.telegram_id, 20),
        });
        // Ждем, чтобы история обновилась в компоненте
        await queryClient.refetchQueries({
          queryKey: queryKeys.chatHistory(user.telegram_id, 20),
        });
        // Сбрасываем состояние приветствия ПОСЛЕ очистки истории
        // useEffect сам покажет welcome screen когда messages.length === 0
        setHasShownWelcomeMessage(false);
        setShowWelcome(true);
      } catch (error) {
        console.error('Ошибка очистки истории:', error);
        telegram.showAlert('Ошибка при очистке истории');
      }
    }
  };

  const handleCopyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      haptic.light();
      // Используем только telegram.showPopup, без дополнительных уведомлений
      // Убираем браузерные уведомления - используем только Telegram popup
      telegram.showPopup({
        message: 'Скопировано!',
        buttons: [{ type: 'ok', text: 'OK' }],
      });
    } catch (error) {
      console.error('Ошибка копирования:', error);
      // При ошибке показываем только Telegram popup, без браузерных уведомлений
      telegram.showPopup({
        message: 'Не удалось скопировать',
        buttons: [{ type: 'ok', text: 'OK' }],
      });
    }
  };

  const handleReplyToMessage = (index: number) => {
    setReplyToMessage(index);
    haptic.light();
  };

  // Dark theme: full implementation v2
  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-blue-50 via-white to-pink-50 dark:from-slate-900 dark:to-slate-800">
      {/* Заголовок */}
      <div className="flex-shrink-0 bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-slate-800 dark:to-slate-900 shadow-sm p-1.5 sm:p-2 border-b border-blue-500/30 dark:border-slate-700">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <img src="/logo.png" alt="PandaPal" width={32} height={32} loading="lazy" className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-white/90 dark:bg-slate-800/90 p-0.5 shadow-sm" />
          <div className="flex-1 min-w-0">
            <h1 className="text-xs sm:text-sm md:text-base font-display font-bold text-white dark:text-slate-100 drop-shadow-sm truncate">PandaPal AI</h1>
            <p className="text-[10px] sm:text-xs md:text-sm text-blue-50 dark:text-slate-300 font-medium truncate">Привет, {user.first_name}! 🎓</p>
          </div>
          <div className="flex items-center gap-1.5">
            <MiniAppThemeToggle />
            <button
              onClick={handleClearChat}
              className="flex-shrink-0 w-9 h-9 rounded-lg bg-white/20 dark:bg-slate-700/80 hover:bg-white/30 dark:hover:bg-slate-600 active:bg-white/40 dark:active:bg-slate-500 active:scale-95 transition-all flex items-center justify-center border border-white/30 dark:border-slate-600 shadow-sm"
              aria-label="Очистить чат"
            >
              <span className="text-base text-white dark:text-slate-200">🗑️</span>
            </button>
            <button onClick={() => { useAppStore.getState().setCurrentScreen('emergency'); haptic.medium(); }} className="flex-shrink-0 w-10 h-10 sm:w-11 sm:h-11 rounded-lg bg-red-500/90 dark:bg-red-600/90 hover:bg-red-600/90 dark:hover:bg-red-700/90 active:scale-95 transition-all flex items-center justify-center shadow-sm">
              <span className="text-lg sm:text-xl">🚨</span>
            </button>
          </div>
        </div>
      </div>

      {/* Сообщения */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-3 sm:p-4 md:p-5 space-y-4" role="log">
        {isLoadingHistory ? (
          <div className="text-center py-8"><div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div></div>
        ) : showWelcome && messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-full py-8 animate-fade-in">
            <img
              ref={logoRef}
              src="/logo.png"
              alt="PandaPal"
              width={120}
              height={120}
              loading="eager"
              className="w-28 h-28 sm:w-32 sm:h-32 md:w-36 md:h-36 mx-auto mb-6 rounded-full shadow-2xl bg-white/50 dark:bg-slate-800/50 p-2 animate-logo-bounce"
              key={`logo-${messages.length}-${showWelcome ? 'welcome' : 'chat'}`}
              style={{
                animation: 'logoBounce 2s ease-in-out infinite',
                WebkitAnimation: 'logoBounce 2s ease-in-out infinite',
                willChange: 'transform',
                transform: 'translateZ(0)',
                WebkitTransform: 'translateZ(0)',
                backfaceVisibility: 'hidden',
                WebkitBackfaceVisibility: 'hidden',
                animationName: 'logoBounce',
                WebkitAnimationName: 'logoBounce',
                animationDuration: '2s',
                WebkitAnimationDuration: '2s',
                animationTimingFunction: 'ease-in-out',
                WebkitAnimationTimingFunction: 'ease-in-out',
                animationIterationCount: 'infinite',
                WebkitAnimationIterationCount: 'infinite',
                animationFillMode: 'both',
                WebkitAnimationFillMode: 'both',
                animationPlayState: 'running',
                WebkitAnimationPlayState: 'running',
              }}
            />
            <h2 className="text-xl sm:text-2xl md:text-3xl font-display font-bold text-gray-900 dark:text-slate-100 mb-3 animate-fade-in delay-200">Начни общение!</h2>
            <p className="text-sm sm:text-base md:text-lg text-gray-600 dark:text-slate-400 text-center max-w-md mx-auto px-4 animate-fade-in delay-300">
              Задай любой вопрос, и я помогу тебе с учебой! 📚✨
            </p>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in group`}
              role="article"
            >
              <div
                className={`relative ${
                  msg.role === 'ai' ? 'max-w-[85%] sm:max-w-[80%] md:max-w-[75%]' : 'max-w[85%] sm:max-w-[80%]'
                }`}
              >
                <div
                  className={`rounded-xl sm:rounded-2xl px-3 py-2 sm:px-4 sm:py-3 shadow-md ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-br from-blue-300/90 to-cyan-300/90 dark:from-blue-600/80 dark:to-cyan-600/80 text-gray-800 dark:text-white border border-blue-200/50 dark:border-blue-500/40'
                      : 'bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-100 border border-gray-200 dark:border-slate-600'
                  }`}
                >
                  {msg.imageUrl && msg.role === 'ai' && (
                    <img
                      src={msg.imageUrl}
                      alt="Визуализация"
                      className="w-full rounded-lg mb-2 shadow-sm"
                    />
                  )}
                  <MessageContent content={msg.content} role={msg.role} />
                  <time
                    className={`text-[10px] sm:text-xs mt-1.5 sm:mt-2 font-medium block ${
                      msg.role === 'user' ? 'text-gray-600 dark:text-gray-700' : 'text-gray-500 dark:text-gray-400'
                    }`}
                  >
                    {new Date(msg.timestamp).toLocaleTimeString('ru-RU', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </time>
                </div>
                {/* Кнопки действий */}
                <div className="absolute -bottom-6 left-0 flex gap-0.5 sm:gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => handleCopyMessage(msg.content)}
                    className="px-1.5 sm:px-2 py-0.5 text-[10px] sm:text-xs bg-gray-200/90 dark:bg-slate-700/90 rounded-md hover:bg-gray-300 dark:hover:bg-slate-600 active:bg-gray-400 dark:active:bg-slate-500 transition-colors shadow-sm"
                    title="Копировать сообщение"
                  >
                    📋
                  </button>
                  {msg.role === 'ai' && (
                    <button
                      onClick={() => handleReplyToMessage(index)}
                      className="px-1.5 sm:px-2 py-0.5 text-[10px] sm:text-xs bg-gray-200/90 dark:bg-slate-700/90 rounded-md hover:bg-gray-300 dark:hover:bg-slate-600 active:bg-gray-400 dark:active:bg-slate-500 transition-colors shadow-sm"
                      title="Ответить"
                    >
                      ↩️
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        {isSending && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-slate-800 rounded-3xl px-5 py-3 shadow-lg border border-gray-200 dark:border-slate-700">
              <div className="flex items-center gap-2">
                <div className="flex gap-1"><span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></span><span className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce delay-100"></span><span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-200"></span></div>
                <span className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                  {getStatusMessage()}
                </span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Кнопки скролла */}
      {showScrollButtons && (
        <div className="absolute right-1 sm:right-1.5 bottom-24 flex flex-col gap-1.5 sm:gap-2">
          <button onClick={scrollToTop} className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-blue-300/80 dark:bg-blue-600/80 text-gray-700 dark:text-white shadow-lg hover:bg-blue-400/80 dark:hover:bg-blue-500/80 active:scale-95 transition-all flex items-center justify-center backdrop-blur-sm text-sm sm:text-base">⬆️</button>
          <button onClick={scrollToBottom} className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-blue-300/80 dark:bg-blue-600/80 text-gray-700 dark:text-white shadow-lg hover:bg-blue-400/80 dark:hover:bg-blue-500/80 active:scale-95 transition-all flex items-center justify-center backdrop-blur-sm text-sm sm:text-base">⬇️</button>
        </div>
      )}

      {/* Индикатор ответа */}
      {replyToMessage !== null && messages[replyToMessage] && (
        <div className="flex-shrink-0 bg-blue-50 dark:bg-slate-800 border-t border-blue-500/30 dark:border-slate-700 px-4 py-2 flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-blue-500 dark:text-blue-400 font-semibold">Ответ на:</p>
            <p className="text-sm text-gray-700 dark:text-gray-300 truncate">{messages[replyToMessage].content.slice(0, 50)}...</p>
          </div>
          <button onClick={() => setReplyToMessage(null)} className="ml-2 text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 active:text-gray-800 dark:active:text-slate-100 transition-colors">✖️</button>
        </div>
      )}

      {/* Поле ввода */}
      <div className="flex-shrink-0 bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-700 p-1.5 sm:p-2 shadow-md">
        <input ref={fileInputRef} type="file" accept="image/*" onChange={handlePhotoUpload} className="hidden" />
        <div className="flex items-center gap-1 sm:gap-1.5">
          <button onClick={handlePhotoClick} disabled={isSending || isRecording} className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 text-white flex items-center justify-center disabled:opacity-50 hover:shadow-md transition-all active:scale-95 shadow-sm self-center">
            <span className="text-base sm:text-lg">📷</span>
          </button>

          <textarea value={inputText} onChange={(e) => setInputText(e.target.value)} onKeyPress={handleKeyPress} placeholder="Задай вопрос..." disabled={isSending || isRecording} className="flex-1 resize-none rounded-lg sm:rounded-xl px-2.5 sm:px-3 py-2 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-400 text-sm sm:text-base border border-gray-200 dark:border-slate-700 outline-none focus:border-blue-500 dark:focus:border-blue-400 focus:ring-1 focus:ring-blue-400 dark:focus:ring-blue-500 disabled:opacity-50 transition-all h-[44px] sm:h-[48px] leading-tight" rows={1} style={{ maxHeight: '120px', minHeight: '44px' }} />

          {isRecording ? (
            <button onClick={stopRecording} className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-red-400/90 to-pink-400/90 text-white flex items-center justify-center animate-pulse shadow-md self-center">
              <span className="text-base sm:text-lg">⏹️</span>
            </button>
          ) : inputText.trim() ? (
            <button onClick={handleSend} disabled={isSending} className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-cyan-500 to-blue-500 text-white flex items-center justify-center disabled:opacity-50 transition-all active:scale-95 hover:shadow-md shadow-sm self-center">
              {isSending ? <div className="animate-spin text-base sm:text-lg">⏳</div> : <span className="text-base sm:text-lg">▶️</span>}
            </button>
          ) : (
            <button onClick={startRecording} disabled={isSending || isRecording || isGettingAccess} className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 text-white flex items-center justify-center disabled:opacity-50 transition-all active:scale-95 hover:shadow-md shadow-sm self-center">
              <span className="text-base sm:text-lg">🎤</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface MessageContentProps {
  content: string;
  role: string;
}

function MessageContent({ content, role }: MessageContentProps) {
  if (role !== 'ai') {
    return (
      <p className="whitespace-pre-wrap break-words font-medium text-xs sm:text-sm leading-relaxed">
        {content}
      </p>
    );
  }

  // Исправляем форматирование таблицы умножения перед парсингом
  const cleanedContent = content
    // Исправляем "3 3 = 9" на "3 × 3 = 9"
    .replace(/(\d+)\s+(\d+)\s*=\s*(\d+)/g, '$1 × $2 = $3')
    // Исправляем "3*3=9" на "3 × 3 = 9"
    .replace(/(\d+)\*(\d+)\s*=\s*(\d+)/g, '$1 × $2 = $3');

  const { summary, steps, rest } = parseAiMessage(cleanedContent);

  return (
    <div className="space-y-2 sm:space-y-3">
      {summary && (
        <p className="whitespace-pre-wrap break-words font-semibold text-xs sm:text-sm leading-relaxed">
          {summary}
        </p>
      )}
      {steps.length > 0 && (
        <ol className="list-decimal list-inside space-y-1 text-xs sm:text-sm leading-relaxed pl-2">
          {steps.map((step, index) => (
            <li key={index} className="whitespace-pre-wrap break-words mb-1">
              {stripLeadingNumber(step)}
            </li>
          ))}
        </ol>
      )}
      {rest.map(
        (paragraph, index) =>
          paragraph.trim() && (
            <div
              key={index}
              className="whitespace-pre-wrap break-words text-[11px] sm:text-xs leading-relaxed"
            >
              {/* Обработка задач с структурированным форматированием */}
              {paragraph.includes('**Задача') || paragraph.includes('**Условие:') || paragraph.includes('**Решение:') || paragraph.includes('**Ответ:') || paragraph.includes('**Проверка:') ? (
                <div className="space-y-3 border-l-2 border-blue-300 dark:border-blue-600 pl-3 py-2">
                  {paragraph.split(/\n\n+/).map((section, sectionIndex) => {
                    if (!section.trim()) return null;

                    // Заголовок задачи
                    if (section.includes('**Задача')) {
                      const title = section.replace(/\*\*/g, '').trim();
                      return (
                        <h3 key={sectionIndex} className="font-display font-bold text-sm sm:text-base text-blue-600 dark:text-blue-400 mb-2">
                          {title}
                        </h3>
                      );
                    }

                    // Секции с заголовками
                    if (section.match(/^\*\*[^*]+\*\*/)) {
                      const parts = section.split(/(\*\*[^*]+\*\*)/);
                      return (
                        <div key={sectionIndex} className="space-y-1">
                          {parts.map((part, partIndex) => {
                            if (part.startsWith('**') && part.endsWith('**')) {
                              const header = part.replace(/\*\*/g, '');
                              return (
                                <p key={partIndex} className="font-semibold text-xs sm:text-sm text-gray-800 dark:text-gray-200 mt-2 first:mt-0">
                                  {header}
                                </p>
                              );
                            } else if (part.trim()) {
                              // Проверяем, есть ли нумерованные шаги
                              if (/^\d+\./.test(part.trim())) {
                                const steps = part.split(/(\d+\.\s+[^\n]+)/g).filter(s => s.trim());
                                return (
                                  <ol key={partIndex} className="list-decimal list-inside space-y-1 ml-2">
                                    {steps.map((step, stepIndex) => {
                                      const stepMatch = step.match(/^(\d+\.)\s+(.+)/);
                                      if (stepMatch) {
                                        return (
                                          <li key={stepIndex} className="text-[11px] sm:text-xs leading-relaxed">
                                            {stepMatch[2]}
                                          </li>
                                        );
                                      }
                                      return null;
                                    })}
                                  </ol>
                                );
                              }
                              return (
                                <p key={partIndex} className="text-[11px] sm:text-xs leading-relaxed text-gray-700 dark:text-gray-300">
                                  {part.trim()}
                                </p>
                              );
                            }
                            return null;
                          })}
                        </div>
                      );
                    }

                    // Обычный текст
                    return (
                      <p key={sectionIndex} className="text-[11px] sm:text-xs leading-relaxed text-gray-700 dark:text-gray-300">
                        {section.trim()}
                      </p>
                    );
                  })}
                </div>
              ) : (
                <p className="text-[11px] sm:text-xs leading-relaxed opacity-90">
                  {paragraph.trim()}
                </p>
              )}
            </div>
          ),
      )}
    </div>
  );
}

function parseAiMessage(content: string): {
  summary: string | null;
  steps: string[];
  rest: string[];
} {
  // Сначала удаляем явные дубликаты (повторяющиеся блоки текста)
  content = removeDuplicateBlocks(content);

  // Проверяем наличие задач
  const taskRegex = /###Задача\s+\d+:/i;
  const hasTasks = taskRegex.test(content);

  if (hasTasks) {
    // Разбиваем на задачи
    const tasks = content.split(/(?=###Задача\s+\d+:)/i).filter(t => t.trim());
    const parsedBlocks: string[] = [];

    for (const task of tasks) {
      if (!task.trim()) continue;

      // Разбиваем задачу на секции
      const sections: string[] = [];
      let currentSection = '';
      let currentSectionType = '';

      const lines = task.split(/\r?\n/);
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        if (!line) {
          if (currentSection) {
            sections.push(currentSection.trim());
            currentSection = '';
            currentSectionType = '';
          }
          continue;
        }

        // Определяем тип секции
        if (/^###Задача\s+\d+:/.test(line)) {
          if (currentSection) sections.push(currentSection.trim());
          currentSection = line.replace(/###/g, '**').replace(/:/g, ':**');
          currentSectionType = 'title';
        } else if (line.includes('**Условие:**')) {
          // Обрабатываем случай, когда Условие на той же строке
          const parts = line.split(/(\*\*Условие:\*\*)/);
          if (currentSection) sections.push(currentSection.trim());
          currentSection = parts.join('');
          currentSectionType = 'condition';
        } else if (line.includes('**Решение:**')) {
          const parts = line.split(/(\*\*Решение:\*\*)/);
          if (currentSection) sections.push(currentSection.trim());
          currentSection = parts.join('');
          currentSectionType = 'solution';
        } else if (line.includes('**Ответ:**')) {
          const parts = line.split(/(\*\*Ответ:\*\*)/);
          if (currentSection) sections.push(currentSection.trim());
          currentSection = parts.join('');
          currentSectionType = 'answer';
        } else if (line.includes('**Проверка:**')) {
          const parts = line.split(/(\*\*Проверка:\*\*)/);
          if (currentSection) sections.push(currentSection.trim());
          currentSection = parts.join('');
          currentSectionType = 'check';
        } else if (/^Понятно\?/.test(line)) {
          if (currentSection) sections.push(currentSection.trim());
          currentSection = line;
          currentSectionType = 'question';
        } else {
          // Продолжение текущей секции
          if (currentSectionType === 'solution' && /^\d+\./.test(line)) {
            // Шаг решения
            currentSection += '\n' + line;
          } else {
            currentSection += (currentSection ? (currentSection.endsWith(':') ? ' ' : '\n') : '') + line;
          }
        }
      }

      if (currentSection) {
        sections.push(currentSection.trim());
      }

      // Объединяем секции задачи
      if (sections.length > 0) {
        parsedBlocks.push(sections.join('\n\n'));
      }
    }

    if (parsedBlocks.length > 0) {
      return {
        summary: null,
        steps: [],
        rest: parsedBlocks,
      };
    }
  }

  // Обычный парсинг для не-задач
  const lines = content.split(/\r?\n/);
  const summaryLines: string[] = [];
  const stepLines: string[] = [];
  const otherLines: string[] = [];

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (!line.trim()) {
      otherLines.push(line);
      continue;
    }

    if (/^\s*\d+[.)]\s+/.test(line)) {
      stepLines.push(line.trim());
    } else if (summaryLines.length === 0 && !line.startsWith('**') && !line.startsWith('###')) {
      summaryLines.push(line.trim());
    } else {
      otherLines.push(line);
    }
  }

  const summary = summaryLines.length > 0 ? summaryLines.join(' ') : null;

  // Склеиваем остальные строки обратно в абзацы по пустым строкам
  const rest: string[] = [];
  let buffer: string[] = [];
  for (const line of otherLines) {
    if (!line.trim()) {
      if (buffer.length) {
        rest.push(buffer.join(' ').trim());
        buffer = [];
      }
    } else {
      buffer.push(line.trim());
    }
  }
  if (buffer.length) {
    rest.push(buffer.join(' ').trim());
  }

  return {
    summary,
    steps: stepLines,
    rest,
  };
}

function stripLeadingNumber(line: string): string {
  return line.replace(/^\s*\d+[.)]\s+/, '').trim();
}

/**
 * Удаляет повторяющиеся блоки текста из ответа AI.
 * Агрессивная версия для полного удаления всех повторений.
 */
function removeDuplicateBlocks(text: string): string {
  if (!text || text.length < 50) return text;

  // Шаг 1: Разбиваем на строки
  const lines = text.split('\n').filter(l => l.trim().length > 0);

  if (lines.length < 2) return text;

  // Шаг 2: Удаляем дубликаты строк
  const seenLines = new Set<string>();
  const uniqueLines: string[] = [];

  for (const line of lines) {
    const normalized = line.trim().toLowerCase().replace(/\s+/g, ' ');
    if (normalized.length >= 20) {
      if (!seenLines.has(normalized)) {
        seenLines.add(normalized);
        uniqueLines.push(line.trim());
      }
    } else {
      // Короткие строки проверяем на точное совпадение
      if (!uniqueLines.includes(line.trim())) {
        uniqueLines.push(line.trim());
      }
    }
  }

  let result = uniqueLines.join('\n');

  // Шаг 3: Удаляем повторяющиеся блоки (несколько строк подряд)
  if (uniqueLines.length >= 4) {
    const seenBlocks = new Set<string>();
    const finalLines: string[] = [];
    let i = 0;

    while (i < uniqueLines.length) {
      let foundDuplicate = false;
      // Проверяем блоки разной длины (от 5 до 2 строк)
      for (let blockLen = 5; blockLen >= 2; blockLen--) {
        if (i + blockLen > uniqueLines.length) continue;

        const block = uniqueLines.slice(i, i + blockLen).join('\n');
        const normalizedBlock = block.toLowerCase().replace(/\s+/g, ' ');

        if (normalizedBlock.length >= 40) {
          if (seenBlocks.has(normalizedBlock)) {
            // Пропускаем весь блок
            i += blockLen;
            foundDuplicate = true;
            break;
          } else {
            seenBlocks.add(normalizedBlock);
          }
        }
      }

      if (!foundDuplicate) {
        finalLines.push(uniqueLines[i]);
        i++;
      }
    }

    result = finalLines.join('\n');
  }

  return result;
}
