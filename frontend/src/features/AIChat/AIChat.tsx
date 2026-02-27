/**
 * AI Chat Screen - Общение с AI (фикс UI блокировки)
 *
 * Рефакторинг: логика разделена на модули (SOLID принципы)
 * - useVoiceRecorder - запись голоса
 * - usePhotoUpload - загрузка фото
 * - useScrollManagement - управление скроллом
 */

import { useState, useEffect, useRef, useMemo } from 'react';
import { telegram } from '../../services/telegram';
import { useChat, type ChatMessage } from '../../hooks/useChat';
import { useAppStore } from '../../store/appStore';
import { logger } from '../../utils/logger';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { usePhotoUpload } from '../../hooks/usePhotoUpload';
import { useScrollManagement } from '../../hooks/useScrollManagement';
import { haptic } from '../../utils/hapticFeedback';
import { MiniAppThemeToggle } from '../../components/MiniAppThemeToggle';
import { ChatBackground } from '../../components/ChatBackground';
import { DateSeparator } from '../../components/DateSeparator';
import { InteractiveMap } from '../../components/InteractiveMap';
import { PandaChatReaction } from '../../components/PandaChatReaction';
import { addGreetingMessage } from '../../services/api';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../../lib/queryClient';
import type { UserProfile } from '../../services/api';

interface AIChatProps {
  user: UserProfile;
}

/** Медиа для приветственного экрана: два видео + картинка спящей панды (рандом при пустой истории) */
const WELCOME_MEDIA = [
  { type: 'video' as const, src: '/video/panda_eats.mp4', alt: 'Панда ест' },
  { type: 'video' as const, src: '/video/panda_talk.mp4', alt: 'Панда говорит' },
  { type: 'image' as const, src: '/panda-sleeping.png', alt: 'Панда спит' },
];

function pickRandomWelcomeMedia(): (typeof WELCOME_MEDIA)[number] {
  return WELCOME_MEDIA[Math.floor(Math.random() * WELCOME_MEDIA.length)];
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
  const [welcomeMedia, setWelcomeMedia] = useState<typeof WELCOME_MEDIA[number]>(() => pickRandomWelcomeMedia());
  const [welcomeVideoReady, setWelcomeVideoReady] = useState(false);
  const queryClient = useQueryClient();
  const logoRef = useRef<HTMLImageElement | null>(null);
  const welcomeMediaKeyRef = useRef(0);

  // Сброс welcomeVideoReady при смене видео; фолбэк на мобильных, если onCanPlay/onPlaying не сработали
  useEffect(() => {
    if (welcomeMedia.type !== 'video') {
      setWelcomeVideoReady(false);
      return;
    }
    setWelcomeVideoReady(false);
    const t = setTimeout(() => setWelcomeVideoReady(true), 2500);
    return () => clearTimeout(t);
  }, [welcomeMedia.src, welcomeMedia.type]);

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
      return 'Слушаю...';
    }

    if (status === 'analyzing_photo' || (status === 'generating' && messageType === 'photo')) {
      return 'Смотрю...';
    }

    if (status === 'generating' && messageType === 'text') {
      return 'Читаю...';
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
  } = useScrollManagement(messages.length, isSending);

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
      logger.error('Ошибка загрузки фото:', error);
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
      logger.error('Ошибка записи голоса:', error);
    },
  });

  // Cleanup при размонтировании
  useEffect(() => {
    return () => {
      cleanupVoice();
    };
  }, [cleanupVoice]);

  // Показываем приветствие при первом открытии или очистке чата. Случайно выбираем одно из трёх медиа (2 видео + спящая панда).
  useEffect(() => {
    if (!isLoadingHistory) {
      if (messages.length === 0) {
        logger.debug('[Welcome] История пустая, показываем welcome screen');
        setShowWelcome(true);
        setHasShownWelcomeMessage(false);
        setWelcomeMedia(pickRandomWelcomeMedia());
        welcomeMediaKeyRef.current += 1;
        setWelcomeVideoReady(false);
      } else {
        logger.debug('[Welcome] Есть сообщения, скрываем welcome screen');
        setShowWelcome(false);
        setHasShownWelcomeMessage(true);
      }
    } else {
      if (!showWelcome && messages.length === 0) {
        logger.debug('[Welcome] История загружается, показываем welcome screen');
        setShowWelcome(true);
        setHasShownWelcomeMessage(false);
        setWelcomeMedia(pickRandomWelcomeMedia());
        welcomeMediaKeyRef.current += 1;
        setWelcomeVideoReady(false);
      }
    }
  }, [messages.length, isLoadingHistory, showWelcome]);

  // Автоматическое приветствие от панды через 5 секунд после показа приветствия
  useEffect(() => {
    // Проверяем, что все условия выполнены для отправки приветствия
    const shouldSendWelcome =
      showWelcome &&
      !hasShownWelcomeMessage &&
      !isLoadingHistory &&
      messages.length === 0;

    if (shouldSendWelcome) {
      logger.debug('[Welcome] Запускаем таймер для приветствия...');

      const timer = setTimeout(async () => {
        logger.debug('[Welcome] Таймер сработал, проверяем условия...');

        // Проверяем еще раз перед отправкой (на случай, если состояние изменилось)
        if (messages.length === 0 && !hasShownWelcomeMessage && showWelcome) {
          try {
            // Добавляем приветственное сообщение от бота напрямую в историю (без отправки через AI)
            const greetings = ['Привет, начнем?', 'Привет! Чем могу помочь?'];
            const randomGreeting = greetings[Math.floor(Math.random() * greetings.length)];

            const result = await addGreetingMessage(user.telegram_id, randomGreeting);
            logger.debug('[Welcome] Приветствие добавлено:', result);

            // Обновляем историю чата после добавления приветствия
            await queryClient.invalidateQueries({
              queryKey: queryKeys.chatHistory(user.telegram_id, 20),
            });

            setHasShownWelcomeMessage(true);
            setShowWelcome(false);
          } catch (error) {
            logger.error('❌ [Welcome] Ошибка добавления приветствия:', error);
            // Если не удалось добавить приветствие, просто скрываем welcome screen
            setHasShownWelcomeMessage(true);
            setShowWelcome(false);
          }
        } else {
          logger.debug('[Welcome] Условия не выполнены, приветствие не отправлено');
        }
      }, 5000); // 5 секунд задержка перед приветственным сообщением от панды

      return () => {
        logger.debug('[Welcome] Очистка таймера');
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
        // Сбрасываем состояние приветствия и сразу выбираем новый случайный логотип
        setHasShownWelcomeMessage(false);
        setShowWelcome(true);
        setWelcomeMedia(pickRandomWelcomeMedia());
        welcomeMediaKeyRef.current += 1;
        setWelcomeVideoReady(false);
      } catch (error) {
        logger.error('Ошибка очистки истории:', error);
        telegram.showAlert('Ошибка при очистке истории');
      }
    }
  };

  const handleCopyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      haptic.light();
      // Используем showAlert вместо showPopup для совместимости с версией 6.0
      await telegram.showAlert('Скопировано!');
    } catch (error) {
      logger.error('Ошибка копирования:', error);
      // При ошибке показываем alert
      await telegram.showAlert('Не удалось скопировать');
    }
  };

  const handleReplyToMessage = (index: number) => {
    setReplyToMessage(index);
    haptic.light();
  };

  // Группировка сообщений по датам для отсечек
  const groupedMessages = useMemo(() => {
    if (!messages.length) return [];

    const grouped: Array<ChatMessage | { type: 'date'; date: Date }> = [];
    let lastDate: Date | null = null;

    for (const msg of messages) {
      const msgDate = new Date(msg.timestamp);
      msgDate.setHours(0, 0, 0, 0);

      if (!lastDate || lastDate.getTime() !== msgDate.getTime()) {
        grouped.push({ type: 'date', date: msgDate });
        lastDate = msgDate;
      }

      grouped.push(msg);
    }

    return grouped;
  }, [messages]);

  // Dark theme: full implementation v2
  return (
    <div className="flex flex-col h-full relative overflow-hidden">
      {/* Фон с doodles */}
      <ChatBackground />

      {/* Основной контент */}
      <div className="flex flex-col h-full relative" style={{ zIndex: 1, position: 'relative' }}>
      {/* Заголовок */}
      <div className="flex-shrink-0 bg-gradient-to-r from-blue-500 to-cyan-500 dark:from-slate-800 dark:to-slate-800 shadow-sm p-1.5 sm:p-2 border-b border-blue-500/30 dark:border-slate-700 relative z-10">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <img src="/logo.png" alt="PandaPal" width={32} height={32} loading="lazy" className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-white/90 dark:bg-slate-800/90 p-0.5 shadow-sm" />
          <div className="flex-1 min-w-0">
            <h1 className="text-xs sm:text-sm md:text-base font-display font-bold text-white dark:text-slate-100 drop-shadow-sm truncate">PandaPal AI</h1>
            <p className="text-[10px] sm:text-xs md:text-sm text-blue-50 dark:text-slate-300 font-semibold truncate">Привет, {user.first_name}! 🎓</p>
          </div>
          <div className="flex items-center gap-1.5">
            <MiniAppThemeToggle />
            <button
              onClick={handleClearChat}
              className="flex-shrink-0 w-11 h-11 sm:w-12 sm:h-12 rounded-lg bg-white/20 dark:bg-slate-700/80 hover:bg-white/30 dark:hover:bg-slate-600 active:bg-white/40 dark:active:bg-slate-500 active:scale-95 transition-all flex items-center justify-center border border-white/30 dark:border-slate-600 shadow-sm touch-manipulation"
              aria-label="Очистить чат"
            >
              <span className="text-base text-white dark:text-slate-200">🗑️</span>
            </button>
            <button onClick={() => { useAppStore.getState().setCurrentScreen('emergency'); haptic.medium(); }} className="flex-shrink-0 w-11 h-11 sm:w-12 sm:h-12 rounded-lg bg-red-500/90 dark:bg-red-600/90 hover:bg-red-600/90 dark:hover:bg-red-700/90 active:scale-95 transition-all flex items-center justify-center shadow-sm touch-manipulation">
              <span className="text-lg sm:text-xl">🚨</span>
            </button>
          </div>
        </div>
      </div>

      {/* Сообщения */}
      <div ref={messagesContainerRef} className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-fib-3 sm:p-fib-4 md:p-fib-4 space-y-fib-3 sm:space-y-fib-4 relative z-[1] bg-transparent" role="log">
        {isLoadingHistory ? (
          <div className="text-center py-8"><div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 dark:border-blue-400"></div></div>
        ) : showWelcome && messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-full py-8 animate-fade-in relative z-10">
            <div
              className="relative w-40 h-40 sm:w-44 sm:h-44 md:w-52 md:h-52 mx-auto mb-6 rounded-full shadow-2xl bg-rose-50 dark:bg-slate-800/90 backdrop-blur-sm p-2 overflow-hidden flex items-center justify-center animate-logo-bounce shrink-0"
              style={{
                willChange: 'transform',
                transform: 'translateZ(0)',
                backfaceVisibility: 'hidden',
                WebkitBackfaceVisibility: 'hidden',
                isolation: 'isolate',
              } as React.CSSProperties}
            >
              {welcomeMedia.type === 'video' ? (
                <>
                  <video
                    key={`welcome-video-${welcomeMediaKeyRef.current}-${welcomeMedia.src}`}
                    src={welcomeMedia.src}
                    poster="/panda-sleeping.png"
                    preload="auto"
                    muted
                    loop
                    autoPlay
                    playsInline
                    onCanPlay={() => setWelcomeVideoReady(true)}
                    onPlaying={() => setWelcomeVideoReady(true)}
                    onLoadedData={() => setWelcomeVideoReady(true)}
                    className="absolute inset-0 z-10 w-full h-full min-w-0 min-h-0 object-contain object-center rounded-full bg-rose-50 dark:bg-slate-800/90 block"
                    aria-label={welcomeMedia.alt}
                  />
                  {!welcomeVideoReady && (
                    <div className="absolute inset-0 z-0 flex items-center justify-center rounded-full bg-rose-50 dark:bg-slate-700/80" aria-hidden>
                      <div className="h-8 w-8 border-2 border-slate-400 dark:border-slate-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                  )}
                </>
              ) : (
                <img
                  ref={logoRef}
                  src={welcomeMedia.src}
                  alt={welcomeMedia.alt}
                  width={120}
                  height={120}
                  loading="eager"
                  className="max-w-full max-h-full w-auto h-auto min-w-[80px] min-h-[80px] object-contain object-center rounded-full block"
                  style={{ objectFit: 'contain', objectPosition: 'center' }}
                  key={`welcome-img-${welcomeMediaKeyRef.current}-${welcomeMedia.src}`}
                  onError={() => setWelcomeMedia(WELCOME_MEDIA[0])}
                />
              )}
            </div>
            <h2 className="text-xl sm:text-2xl md:text-3xl font-display font-bold text-gray-900 dark:text-slate-100 mb-3 animate-fade-in delay-200">Начни общение!</h2>
            <p className="text-sm sm:text-base md:text-lg text-gray-600 dark:text-slate-400 text-center max-w-md mx-auto px-fib-4 animate-fade-in delay-300">
              Задай любой вопрос, и я помогу тебе с учебой! 📚✨
            </p>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 dark:border-blue-400"></div>
          </div>
        ) : (
          (() => {
            const firstAiMessageIndex = messages.findIndex((m) => m.role === 'ai');
            return groupedMessages.map((item) => {
              if ('type' in item && item.type === 'date') {
                return <DateSeparator key={`date-${item.date.getTime()}`} date={item.date} />;
              }
              const msg = item as ChatMessage;
              const msgIndex = messages.indexOf(msg);
              const isGreeting =
                msg.role === 'ai' &&
                msgIndex === firstAiMessageIndex &&
                msg.content.length < 120;

              return (
              <div
                key={`msg-${msgIndex}`}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in group`}
                role="article"
              >
                <div
                  className={`relative ${
                    msg.role === 'ai' ? 'max-w-[85%] sm:max-w-[80%] md:max-w-[75%]' : 'max-w-[85%] sm:max-w-[80%]'
                  }`}
                >
                  <div
                    className={`rounded-2xl sm:rounded-3xl px-3.5 py-2.5 sm:px-4 sm:py-3 shadow-lg backdrop-blur-sm transition-all ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-br from-blue-500/95 to-cyan-500/95 dark:from-blue-600/95 dark:to-cyan-600/95 text-white border border-blue-400/30 dark:border-blue-500/30'
                        : 'bg-white/95 dark:bg-slate-800/95 text-gray-900 dark:text-slate-100 border border-gray-200/50 dark:border-slate-700/50'
                    }`}
                  >
                    {msg.role === 'ai' && msg.mapData ? (
                      <InteractiveMap
                        mapData={msg.mapData}
                        fallbackImageUrl={msg.imageUrl}
                      />
                    ) : msg.videoUrl && msg.role === 'ai' ? (
                      (() => {
                        const videoUrl = msg.videoUrl;
                        const fullUrl =
                          videoUrl.startsWith('http')
                            ? videoUrl
                            : typeof window !== 'undefined'
                              ? `${window.location.origin}${videoUrl}`
                              : videoUrl;
                        return (
                          <video
                            key={fullUrl}
                            src={fullUrl}
                            muted
                            playsInline
                            controls
                            autoPlay
                            preload="auto"
                            className="max-w-[280px] sm:max-w-[320px] w-full aspect-video object-contain object-center rounded-xl mb-2 shadow-md"
                          />
                        );
                      })()
                    ) : msg.imageUrl && msg.role === 'ai' ? (
                      <img
                        src={msg.imageUrl}
                        alt="Визуализация"
                        className="w-full max-w-full object-contain object-center rounded-xl mb-2 shadow-md"
                      />
                    ) : null}
                    {msg.role === 'ai' && msg.pandaReaction ? (
                      <PandaChatReaction reaction={msg.pandaReaction} />
                    ) : null}
                    <MessageContent content={msg.content} role={msg.role} isGreeting={isGreeting} />
                    <div className="flex items-center justify-end mt-1.5 sm:mt-2 gap-1.5">
                      <time
                        className={`text-[10px] sm:text-xs font-medium ${
                          msg.role === 'user'
                            ? 'text-blue-100/80 dark:text-blue-200/80'
                            : 'text-gray-500 dark:text-slate-400'
                        }`}
                      >
                        {new Date(msg.timestamp).toLocaleTimeString('ru-RU', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </time>
                    </div>
                  </div>
                  {/* Кнопки действий */}
                  <div className="absolute -bottom-6 left-0 flex gap-0.5 sm:gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleCopyMessage(msg.content)}
                      className="px-1.5 sm:px-2 py-0.5 text-[10px] sm:text-xs bg-white/90 dark:bg-slate-700/90 rounded-md hover:bg-gray-100 dark:hover:bg-slate-600 active:bg-gray-200 dark:active:bg-slate-500 transition-colors shadow-sm border border-gray-200 dark:border-slate-600"
                      title="Копировать сообщение"
                    >
                      📋
                    </button>
                    {msg.role === 'ai' && (
                      <button
                        onClick={() => handleReplyToMessage(msgIndex)}
                        className="px-1.5 sm:px-2 py-0.5 text-[10px] sm:text-xs bg-white/90 dark:bg-slate-700/90 rounded-md hover:bg-gray-100 dark:hover:bg-slate-600 active:bg-gray-200 dark:active:bg-slate-500 transition-colors shadow-sm border border-gray-200 dark:border-slate-600"
                        title="Ответить"
                      >
                        ↩️
                      </button>
                    )}
                  </div>
                </div>
              </div>
              );
            });
          })()
        )}
        {isSending && (
          <div className="flex justify-start">
            <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-sm rounded-3xl px-5 py-3 shadow-lg border border-gray-200/50 dark:border-slate-700/50">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-cyan-500 dark:bg-cyan-400 rounded-full animate-bounce delay-100"></span>
                  <span className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full animate-bounce delay-200"></span>
                </div>
                <span className="text-sm text-gray-700 dark:text-slate-300 font-medium">
                  {getStatusMessage()}
                </span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Индикатор ответа */}
      {replyToMessage !== null && messages[replyToMessage] && (
        <div className="flex-shrink-0 bg-blue-50/95 dark:bg-slate-800/95 backdrop-blur-sm border-t border-blue-500/30 dark:border-slate-700 px-fib-4 py-fib-2 flex items-center justify-between relative z-10">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-blue-500 dark:text-blue-400 font-semibold">Ответ на:</p>
            <p className="text-sm text-gray-700 dark:text-slate-300 truncate">{messages[replyToMessage].content.slice(0, 50)}...</p>
          </div>
          <button onClick={() => setReplyToMessage(null)} className="ml-2 text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200 active:text-gray-800 dark:active:text-slate-100 transition-colors">✖️</button>
        </div>
      )}

      {/* Поле ввода */}
      <div className="flex-shrink-0 bg-white/95 dark:bg-slate-800/95 backdrop-blur-sm border-t border-gray-200/50 dark:border-slate-700/50 p-fib-2 sm:p-fib-2 shadow-lg relative z-10">
        <input ref={fileInputRef} type="file" accept="image/*" onChange={handlePhotoUpload} className="hidden" />
        <div className="flex items-center gap-fib-1 sm:gap-fib-2">
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

      {/* Кнопки скролла */}
      {showScrollButtons && (
        <div className="absolute right-1 sm:right-1.5 bottom-24 sm:bottom-28 flex flex-col gap-1.5 sm:gap-2 z-30 pointer-events-auto">
          <button
            onClick={scrollToTop}
            className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-blue-300/80 dark:bg-blue-600/80 text-gray-700 dark:text-white shadow-lg hover:bg-blue-400/80 dark:hover:bg-blue-500/80 active:scale-95 transition-all flex items-center justify-center backdrop-blur-sm text-sm sm:text-base pointer-events-auto touch-manipulation"
            aria-label="Вверх"
          >
            ⬆️
          </button>
          <button
            onClick={scrollToBottom}
            className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-blue-300/80 dark:bg-blue-600/80 text-gray-700 dark:text-white shadow-lg hover:bg-blue-400/80 dark:hover:bg-blue-500/80 active:scale-95 transition-all flex items-center justify-center backdrop-blur-sm text-sm sm:text-base pointer-events-auto touch-manipulation"
            aria-label="Вниз"
          >
            ⬇️
          </button>
        </div>
      )}
      </div>
    </div>
  );
}

import {
  parseStructuredSections,
  parseListItems,
  isList,
  isNumberedList,
  isMarkdownTable,
  parseMarkdownTable,
} from './parseStructuredSections';

interface MessageContentProps {
  content: string;
  role: string;
  isGreeting?: boolean;
}

/** Рендер текста с поддержкой **жирного** (markdown bold). */
function renderTextWithBold(text: string): React.ReactNode {
  const parts = text.split('**');
  return (
    <>
      {parts.map((part, i) =>
        i % 2 === 1 ? (
          <strong key={i} className="font-semibold">{part}</strong>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
}

/** Строка — только подзаголовок (заканчивается на «:», без **, не слишком длинная). */
function isSubheadingLine(line: string): boolean {
  const t = line.trim();
  if (!t.endsWith(':') || t.includes('**') || t.length > 120) return false;
  return true;
}

/** В строке вида «— Подзаголовок: текст» или «Подзаголовок: текст» выделить жирным часть до «:». */
function renderLineWithOptionalSubheadingBold(line: string): React.ReactNode {
  const t = line.trim();
  if (t.includes('**')) return renderTextWithBold(line);
  const colonIdx = t.indexOf(':');
  if (colonIdx > 0 && colonIdx <= 80) {
    const beforeColon = t.slice(0, colonIdx + 1);
    const afterColon = t.slice(colonIdx + 1).trim();
    if (afterColon.length > 0) {
      return (
        <>
          <strong className="font-semibold">{beforeColon}</strong>
          {afterColon ? ` ${afterColon}` : null}
        </>
      );
    }
  }
  return renderTextWithBold(line);
}

/** Рендер абзаца: подзаголовочные строки (оканчиваются на «:») — жирным, остальное с ** или подзаголовок в начале строки. */
function renderParagraphWithSubheadingBold(content: string): React.ReactNode {
  const lines = content.split('\n');
  return (
    <>
      {lines.map((line, i) => {
        const key = `line-${i}`;
        if (isSubheadingLine(line)) {
          return (
            <span key={key} className="block font-chat">
              <strong className="font-semibold">{line.trim()}</strong>
              {i < lines.length - 1 ? '\n' : null}
            </span>
          );
        }
        return (
          <span key={key} className="block">
            {renderLineWithOptionalSubheadingBold(line)}
            {i < lines.length - 1 ? '\n' : null}
          </span>
        );
      })}
    </>
  );
}

/** Единый класс для всего текста ответов Панды: Literata везде, размер чуть крупнее. */
const AI_MESSAGE_TEXT_CLASS =
  'text-sm sm:text-base leading-relaxed text-gray-900 dark:text-slate-100 font-chat';

/** Строка — только цифры (или цифры + точка/скобка в конце), не нумерованный пункт «1. Текст». */
function isDigitOnlyLine(line: string): boolean {
  const t = line.trim().replace(/\r/g, '');
  if (!t) return false;
  return /^\s*\d+[.)]?\s*$/.test(t);
}

/** Склеивает столбик цифр (1\\n8\\n3 → 183) для отображения. Страховка для истории и стрима. */
function mergeDigitOnlyLines(text: string): string {
  if (!text || !text.includes('\n')) return text;
  const lines = text.split('\n');
  const result: string[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (isDigitOnlyLine(line)) {
      const digitLines: string[] = [line];
      let j = i + 1;
      while (j < lines.length && isDigitOnlyLine(lines[j])) {
        digitLines.push(lines[j]);
        j += 1;
      }
      const merged = digitLines.map((ln) => ln.replace(/\D/g, '')).join('');
      if (merged) result.push(merged);
      i = j;
    } else {
      result.push(line);
      i += 1;
    }
  }
  return result.join('\n');
}

function renderSectionContent(content: string) {
  const chatTextClass = AI_MESSAGE_TEXT_CLASS;
  if (isNumberedList(content)) {
    const items = parseListItems(content);
    return (
      <ol className={`list-decimal list-inside space-y-1 ml-2 ${chatTextClass}`}>
        {items.map((item, i) => (
          <li key={i} className="whitespace-pre-wrap break-words mb-1">
            {renderLineWithOptionalSubheadingBold(item)}
          </li>
        ))}
      </ol>
    );
  }

  if (isList(content)) {
    const items = parseListItems(content);
    return (
      <ul className={`list-disc list-inside space-y-1 ml-2 ${chatTextClass}`}>
        {items.map((item, i) => (
          <li key={i} className="whitespace-pre-wrap break-words mb-1">
            {renderLineWithOptionalSubheadingBold(item)}
          </li>
        ))}
      </ul>
    );
  }

  if (isMarkdownTable(content)) {
    const table = parseMarkdownTable(content);
    if (table && (table.headers.length > 0 || table.rows.length > 0)) {
      return (
        <div className="overflow-x-auto my-2 rounded border border-gray-200 dark:border-slate-600">
          <table className={`w-full border-collapse ${chatTextClass}`}>
            {table.headers.length > 0 && (
              <thead>
                <tr>
                  {table.headers.map((h, i) => (
                    <th key={i} className="px-2 py-1.5 text-left font-semibold border-b border-gray-200 dark:border-slate-600 bg-gray-50 dark:bg-slate-700/50">
                      {renderLineWithOptionalSubheadingBold(h)}
                    </th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody>
              {table.rows.map((row, ri) => (
                <tr key={ri}>
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-2 py-1.5 border-b border-gray-100 dark:border-slate-700/50 whitespace-normal break-words">
                      {renderLineWithOptionalSubheadingBold(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }
  }

  // Обычный текст: жирный через ** и подзаголовки
  return (
    <p className={`whitespace-pre-wrap break-words ${chatTextClass}`}>
      {renderParagraphWithSubheadingBold(content)}
    </p>
  );
}

function MessageContent({ content, role, isGreeting }: MessageContentProps) {
  if (role !== 'ai') {
    return (
      <p className="whitespace-pre-wrap break-words font-medium text-xs sm:text-sm leading-relaxed text-white dark:text-white">
        {content}
      </p>
    );
  }

  const wrapperClass = isGreeting
    ? `whitespace-pre-wrap break-words ${AI_MESSAGE_TEXT_CLASS} font-semibold`
    : '';

  // Убираем «цифры в столбик» (год 1837 как 1\n8\n3\n7), затем форматирование таблицы умножения
  const cleanedContent = mergeDigitOnlyLines(content)
    // Исправляем "3 3 = 9" на "3 × 3 = 9"
    .replace(/(\d+)\s+(\d+)\s*=\s*(\d+)/g, '$1 × $2 = $3')
    // Исправляем "3*3=9" на "3 × 3 = 9"
    .replace(/(\d+)\*(\d+)\s*=\s*(\d+)/g, '$1 × $2 = $3');

  const structuredSections = parseStructuredSections(cleanedContent);
  const inner = (
    <div className="space-y-0">
      {structuredSections.map((section, index) => (
        <div
          key={index}
          className="py-2 first:pt-0 last:pb-0"
        >
          {section.title && (
            <h3 className={`font-chat font-semibold mb-1.5 text-gray-900 dark:text-slate-100 ${AI_MESSAGE_TEXT_CLASS}`}>
              {renderTextWithBold(section.title)}
            </h3>
          )}
          <div>
            {renderSectionContent(section.content)}
          </div>
        </div>
      ))}
    </div>
  );

  return isGreeting && wrapperClass ? (
    <div className={wrapperClass}>{inner}</div>
  ) : (
    inner
  );
}
