/**
 * AI Chat Screen - Общение с AI (улучшенная версия)
 * Добавлено: очистка чата, копирование, ответ на сообщение, скролл
 */

import { useState, useEffect, useRef } from 'react';
import { telegram } from '../../services/telegram';
import { useChat } from '../../hooks/useChat';
import { useAppStore } from '../../store/appStore';
import type { UserProfile } from '../../services/api';

interface AIChatProps {
  user: UserProfile;
}

export function AIChat({ user }: AIChatProps) {
  const {
    messages,
    isLoadingHistory,
    sendMessage,
    isSending,
    clearHistory,
  } = useChat({ telegramId: user.telegram_id, limit: 20 });

  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [replyToMessage, setReplyToMessage] = useState<number | null>(null);
  const [showScrollButtons, setShowScrollButtons] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingStartTimeRef = useRef<number>(0);
  const audioChunksRef = useRef<Blob[]>([]);
  const mimeTypeRef = useRef<string>('audio/webm');
  const recordingStartedRef = useRef(false);
  const startErrorRef = useRef<Error | null>(null);

  // Автоскролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Показываем кнопки скролла если контент больше экрана
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      const hasScroll = container.scrollHeight > container.clientHeight;
      setShowScrollButtons(hasScroll);
    }
  }, [messages]);

  // Cleanup: останавливаем запись при размонтировании
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && isRecording) {
        try {
          if (mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
          }
        } catch (e) {
          console.warn('⚠️ Ошибка при остановке записи в cleanup:', e);
        }
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => {
          track.stop();
        });
        streamRef.current = null;
      }
      mediaRecorderRef.current = null;
      setIsRecording(false);
    };
  }, [isRecording]);

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
        await clearHistory();
        telegram.hapticFeedback('medium');
        await telegram.showAlert('История чата очищена');
      } catch (error) {
        console.error('Ошибка очистки истории:', error);
        telegram.showAlert('Ошибка при очистке истории');
      }
    }
  };

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
    telegram.hapticFeedback('light');
    telegram.showPopup({
      message: 'Скопировано!',
      buttons: [{ type: 'ok', text: 'OK' }],
    });
  };

  const handleReplyToMessage = (index: number) => {
    setReplyToMessage(index);
    telegram.hapticFeedback('light');
  };

  const scrollToTop = () => {
    messagesContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
    telegram.hapticFeedback('light');
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    telegram.hapticFeedback('light');
  };

  // Обработка загрузки фото
  const handlePhotoClick = () => {
    fileInputRef.current?.click();
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      await telegram.showAlert('Пожалуйста, выбери изображение');
      return;
    }

    telegram.hapticFeedback('medium');

    try {
      const reader = new FileReader();
      reader.onload = () => {
        const base64Data = reader.result as string;
        sendMessage({
          message: inputText.trim() || 'Помоги мне с этой задачей',
          photoBase64: base64Data,
        });
        setInputText('');
      };
      reader.readAsDataURL(file);
    } catch (error: unknown) {
      console.error('Ошибка загрузки фото:', error);
      telegram.notifyError();
      const errorMessage = error instanceof Error ? error.message : 'Не удалось загрузить фото. Попробуй еще раз!';
      await telegram.showAlert(errorMessage);
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Обработка записи аудио
  const handleVoiceStart = async () => {
    if (isRecording || mediaRecorderRef.current) {
      console.warn('⚠️ Запись уже идет');
      return;
    }

    try {
      console.log('🎤 Запрос доступа к микрофону...');
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });

      streamRef.current = stream;
      console.log('✅ Доступ к микрофону получен');

      // Проверяем что stream активен
      if (!stream || stream.getTracks().length === 0) {
        throw new Error('Stream не содержит аудио треков');
      }

      const audioTrack = stream.getAudioTracks()[0];
      if (!audioTrack || audioTrack.readyState !== 'live') {
        throw new Error('Аудио трек не активен');
      }

      console.log('✅ Аудио трек активен:', audioTrack.label);

      // Определяем поддерживаемый формат (приоритет для мобильных устройств)
      let mimeType = '';
      const supportedTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4',
        'audio/aac',
      ];

      for (const type of supportedTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          mimeType = type;
          break;
        }
      }

      // Если ничего не поддерживается, используем формат по умолчанию
      if (!mimeType) {
        console.warn('⚠️ Ни один формат не поддерживается, используем по умолчанию');
      }

      mimeTypeRef.current = mimeType; // Сохраняем в ref для доступа в обработчиках
      console.log('📝 Используемый формат:', mimeType || 'по умолчанию');

      // Создаем MediaRecorder с обработкой ошибок
      let mediaRecorder: MediaRecorder;
      try {
        if (mimeType) {
          try {
            mediaRecorder = new MediaRecorder(stream, { mimeType });
            console.log('✅ MediaRecorder создан с mimeType:', mimeType);
          } catch (mimeError) {
            console.warn('⚠️ Ошибка создания с mimeType, пробуем без него:', mimeError);
            mediaRecorder = new MediaRecorder(stream);
            mimeTypeRef.current = ''; // Обновляем ref
            console.log('✅ MediaRecorder создан без mimeType (fallback)');
          }
        } else {
          mediaRecorder = new MediaRecorder(stream);
          console.log('✅ MediaRecorder создан без mimeType');
        }
        console.log('✅ MediaRecorder создан, состояние:', mediaRecorder.state);
      } catch (recorderError) {
        console.error('❌ Критическая ошибка создания MediaRecorder:', recorderError);
        // Очищаем stream перед выбросом ошибки
        stream.getTracks().forEach((track) => track.stop());
        throw new Error('Не удалось создать запись аудио. Попробуй обновить страницу.');
      }

      // Очищаем массив чанков для новой записи
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          console.log('📦 Получен аудио чанк:', event.data.size, 'байт');
          audioChunksRef.current.push(event.data);
        }
      };

      // Сбрасываем флаги для новой записи
      recordingStartedRef.current = false;
      startErrorRef.current = null;

      mediaRecorder.onstart = () => {
        recordingStartedRef.current = true;
        console.log('✅ MediaRecorder начал запись, состояние:', mediaRecorder.state);
      };

      mediaRecorder.onpause = () => {
        console.warn('⚠️ MediaRecorder приостановлен');
      };

      mediaRecorder.onresume = () => {
        console.log('▶️ MediaRecorder возобновлен');
      };

      mediaRecorder.onstop = () => {
        console.log('🛑 Запись остановлена, чанков:', audioChunksRef.current.length);

        if (audioChunksRef.current.length === 0) {
          console.error('❌ Аудио не записалось');
          telegram.notifyError();
          telegram.showAlert('Не удалось записать аудио. Попробуй еще раз!');
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          setIsRecording(false);
          mediaRecorderRef.current = null;
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, { type: mimeTypeRef.current || 'audio/webm' });
        const MAX_AUDIO_SIZE = 10 * 1024 * 1024;

        console.log('📊 Размер аудио:', audioBlob.size, 'байт');

        if (audioBlob.size > MAX_AUDIO_SIZE) {
          console.error(`❌ Аудио слишком большое: ${audioBlob.size} байт`);
          telegram.notifyError();
          telegram.showAlert('Аудио слишком длинное. Максимум 10MB.');
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          setIsRecording(false);
          mediaRecorderRef.current = null;
          return;
        }

        if (audioBlob.size === 0) {
          console.error('❌ Аудио пустое');
          telegram.notifyError();
          telegram.showAlert('Аудио пустое. Попробуй заново!');
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          setIsRecording(false);
          mediaRecorderRef.current = null;
          return;
        }

        telegram.hapticFeedback('medium');

        try {
          const reader = new FileReader();
          reader.onload = () => {
            const base64Audio = reader.result as string;
            if (!base64Audio || base64Audio.length === 0) {
              console.error('❌ Base64 аудио пустое');
              telegram.notifyError();
              telegram.showAlert('Ошибка конвертации. Попробуй еще раз!');
              if (streamRef.current) {
                streamRef.current.getTracks().forEach((track) => track.stop());
                streamRef.current = null;
              }
              setIsRecording(false);
              mediaRecorderRef.current = null;
              return;
            }
            console.log('✅ Аудио готово к отправке, размер base64:', base64Audio.length);
            sendMessage({ audioBase64: base64Audio });
            if (streamRef.current) {
              streamRef.current.getTracks().forEach((track) => track.stop());
              streamRef.current = null;
            }
            setIsRecording(false);
            mediaRecorderRef.current = null;
          };
          reader.onerror = (error) => {
            console.error('❌ Ошибка FileReader:', error);
            telegram.notifyError();
            telegram.showAlert('Ошибка чтения аудио!');
            if (streamRef.current) {
              streamRef.current.getTracks().forEach((track) => track.stop());
              streamRef.current = null;
            }
            setIsRecording(false);
            mediaRecorderRef.current = null;
          };
          reader.readAsDataURL(audioBlob);
        } catch (error: unknown) {
          console.error('❌ Ошибка отправки аудио:', error);
          telegram.notifyError();
          const errorMessage = error instanceof Error ? error.message : 'Не удалось отправить!';
          telegram.showAlert(errorMessage);
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          setIsRecording(false);
          mediaRecorderRef.current = null;
        }
      };

      mediaRecorder.onerror = (event: Event) => {
        console.error('❌ Ошибка MediaRecorder:', event);
        const errorEvent = event as ErrorEvent;
        console.error('❌ Детали ошибки:', errorEvent.error || errorEvent.message);

        // Сохраняем ошибку для проверки после start()
        if (errorEvent.error instanceof Error) {
          startErrorRef.current = errorEvent.error;
        } else {
          startErrorRef.current = new Error(errorEvent.message || 'Неизвестная ошибка MediaRecorder');
        }

        telegram.notifyError();

        let errorMsg = 'Ошибка записи аудио!';
        if (errorEvent.error) {
          errorMsg = `Ошибка записи: ${errorEvent.error.message || errorEvent.error}`;
        }

        telegram.showAlert(errorMsg).catch((alertError) => {
          console.error('❌ Ошибка показа alert:', alertError);
        });

        // Безопасная очистка ресурсов
        try {
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => {
              try {
                track.stop();
              } catch (e) {
                console.warn('⚠️ Ошибка остановки трека:', e);
              }
            });
            streamRef.current = null;
          }
        } catch (cleanupError) {
          console.error('❌ Ошибка очистки stream:', cleanupError);
        }

        setIsRecording(false);
        mediaRecorderRef.current = null;
      };

      // Проверяем что stream все еще активен перед началом записи
      const currentAudioTrack = stream.getAudioTracks()[0];
      if (!currentAudioTrack || currentAudioTrack.readyState !== 'live') {
        throw new Error('Аудио трек потерян перед началом записи');
      }

      // Запускаем запись с интервалом для получения данных
      try {
        if (mediaRecorder.state !== 'inactive') {
          console.warn('⚠️ MediaRecorder уже активен, состояние:', mediaRecorder.state);
          throw new Error('MediaRecorder уже активен');
        }

        // Проверяем stream еще раз перед start
        const trackBeforeStart = stream.getAudioTracks()[0];
        if (!trackBeforeStart || trackBeforeStart.readyState !== 'live') {
          throw new Error('Аудио трек потерян перед start()');
        }

        // Сохраняем ссылку на recorder ДО start(), чтобы обработчики могли его использовать
        mediaRecorderRef.current = mediaRecorder;

        // Упрощенная логика: сразу запускаем запись без сложных проверок
        try {
          const timeslice = 250; // 250мс для стабильной работы на мобильных
          console.log('🎙️ Запуск записи с timeslice:', timeslice);
          mediaRecorder.start(timeslice);
          console.log('✅ start() вызван, состояние:', mediaRecorder.state);

          // Устанавливаем состояние сразу, не ждем события onstart
          // Это важно для мобильных устройств, где события могут задерживаться
          recordingStartTimeRef.current = Date.now();
          setIsRecording(true);
          telegram.hapticFeedback('heavy');
          console.log('✅ Состояние записи установлено');

          // Небольшая задержка для проверки, но не блокируем основной поток
          setTimeout(() => {
            const state = mediaRecorderRef.current?.state;
            const started = recordingStartedRef.current;
            const error = startErrorRef.current;

            console.log('🔍 Проверка через 200мс:', { state, started, error: error?.message });

            if (error) {
              console.error('❌ Ошибка обнаружена:', error);
              setIsRecording(false);
              if (streamRef.current) {
                streamRef.current.getTracks().forEach((track) => track.stop());
                streamRef.current = null;
              }
              mediaRecorderRef.current = null;
              telegram.notifyError();
              telegram.showAlert(`Ошибка записи: ${error.message}`).catch(console.error);
            } else if (state === 'inactive' && !started) {
              console.warn('⚠️ Запись не началась, но ошибки нет. Возможно, это нормально для некоторых устройств.');
            }
          }, 200);

        } catch (startSyncError) {
          console.error('❌ Синхронная ошибка при start():', startSyncError);
          setIsRecording(false);
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          mediaRecorderRef.current = null;
          throw new Error(`Не удалось начать запись: ${startSyncError instanceof Error ? startSyncError.message : String(startSyncError)}`);
        }

        recordingStartTimeRef.current = Date.now();
        setIsRecording(true);
        telegram.hapticFeedback('heavy');
        console.log('✅ Запись успешно начата и подтверждена');
      } catch (startError) {
        console.error('❌ Ошибка запуска записи:', startError);
        telegram.notifyError();
        // Очищаем ресурсы
        try {
          if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
          }
        } catch (e) {
          console.warn('⚠️ Ошибка при остановке recorder после ошибки:', e);
        }
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
        mediaRecorderRef.current = null;
        setIsRecording(false);
        const errorMsg = startError instanceof Error ? startError.message : 'Не удалось начать запись. Попробуй еще раз.';
        await telegram.showAlert(errorMsg);
        return;
      }
    } catch (error) {
      console.error('❌ Ошибка доступа к микрофону:', error);
      telegram.notifyError();

      let errorMessage = 'Не удалось получить доступ к микрофону.';

      if (error instanceof DOMException) {
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
          // Более детальное сообщение для системных ошибок
          if (error.message.includes('system') || error.message.includes('Permission denied by system')) {
            errorMessage = (
              'Доступ к микрофону заблокирован системой.\n\n' +
              '1. Проверь настройки разрешений Telegram\n' +
              '2. Разреши доступ к микрофону в настройках устройства\n' +
              '3. Перезапусти Telegram и попробуй снова\n' +
              '4. Если проблема сохраняется, используй текстовый ввод'
            );
          } else {
            errorMessage = (
              'Доступ к микрофону запрещен.\n\n' +
              '1. Нажми на иконку замка в адресной строке\n' +
              '2. Разреши доступ к микрофону\n' +
              '3. Обнови страницу и попробуй снова'
            );
          }
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
          errorMessage = 'Микрофон не найден.\n\nУбедись, что микрофон подключен и доступен.';
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
          errorMessage = 'Микрофон занят другим приложением.\n\nЗакрой другие приложения, использующие микрофон, и попробуй снова.';
        } else {
          errorMessage = `Ошибка доступа к микрофону: ${error.message}`;
        }
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      await telegram.showAlert(errorMessage);
      setIsRecording(false);
      mediaRecorderRef.current = null;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    }
  };

  const handleVoiceStop = () => {
    if (mediaRecorderRef.current && isRecording) {
      const recordingDuration = Date.now() - recordingStartTimeRef.current;
      const MIN_RECORDING_DURATION = 500;

      console.log('🛑 Остановка записи, длительность:', recordingDuration, 'мс');

      if (recordingDuration < MIN_RECORDING_DURATION) {
        console.warn('⚠️ Запись слишком короткая');
        try {
          if (mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
          }
        } catch (e) {
          console.warn('⚠️ Ошибка при остановке короткой записи:', e);
        }
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
        mediaRecorderRef.current = null;
        setIsRecording(false);
        telegram.hapticFeedback('light');
        return;
      }

      try {
        if (mediaRecorderRef.current.state !== 'inactive') {
          mediaRecorderRef.current.stop();
        }
        telegram.hapticFeedback('medium');
      } catch (e) {
        console.error('❌ Ошибка при остановке записи:', e);
        telegram.notifyError();
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
        mediaRecorderRef.current = null;
        setIsRecording(false);
      }
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:to-slate-800">
      {/* КОМПАКТНЫЙ заголовок */}
      <div className="flex-shrink-0 bg-gradient-to-r from-blue-400/90 to-indigo-400/90 shadow-sm p-1.5 sm:p-2 border-b border-blue-300/50">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <img src="/logo.png" alt="PandaPal" width={32} height={32} loading="lazy" className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-white/90 p-0.5 shadow-sm" />
          <div className="flex-1 min-w-0">
            <h1 className="text-xs sm:text-sm md:text-base font-bold text-white drop-shadow-sm truncate">
              PandaPal AI
            </h1>
            <p className="text-[10px] sm:text-xs md:text-sm text-blue-100 font-medium truncate">
              Привет, {user.first_name}! 🎓
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            {/* Кнопка очистки чата */}
            <button
              onClick={handleClearChat}
              className="flex-shrink-0 w-9 h-9 rounded-lg bg-gray-400/60 hover:bg-gray-500/70 active:scale-95 transition-all flex items-center justify-center border border-gray-400/40 shadow-sm"
              aria-label="Очистить чат"
              title="Очистить историю"
            >
              <span className="text-base text-gray-700 dark:text-gray-200">🗑️</span>
            </button>
            {/* Кнопка SOS */}
            <button
              onClick={() => {
                useAppStore.getState().setCurrentScreen('emergency');
                telegram.hapticFeedback('medium');
                // Скроллим к началу экрана SOS после переключения
                setTimeout(() => {
                  const emergencyContainer = document.querySelector('[data-emergency-screen]') as HTMLElement;
                  if (emergencyContainer) {
                    // Скроллим сам контейнер (он имеет overflow-y-auto)
                    emergencyContainer.scrollTo({ top: 0, behavior: 'smooth' });
                  }
                }, 300);
              }}
              className="flex-shrink-0 w-10 h-10 sm:w-11 sm:h-11 rounded-lg bg-red-500/90 hover:bg-red-600/90 active:scale-95 transition-all flex items-center justify-center shadow-sm"
              aria-label="Экстренные номера"
              title="Экстренные номера"
            >
              <span className="text-lg sm:text-xl">🚨</span>
            </button>
          </div>
        </div>
      </div>

      {/* Список сообщений */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
        role="log"
        aria-label="История сообщений"
      >
        {isLoadingHistory ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-8">
            <img src="/logo.png" alt="PandaPal" width={96} height={96} loading="lazy" className="w-24 h-24 mx-auto mb-4 rounded-full shadow-xl" />
            <h2 className="text-base sm:text-lg md:text-xl font-bold text-[var(--tg-theme-text-color)] mb-2">
              Начни общение!
            </h2>
            <p className="text-xs sm:text-sm md:text-base text-[var(--tg-theme-hint-color)]">
              Задай любой вопрос, и я помогу тебе с учебой! 📚
            </p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in group`}
              role="article"
            >
              <div className="relative max-w-[85%] sm:max-w-[80%]">
                <div
                  className={`rounded-xl sm:rounded-2xl px-3 py-2 sm:px-4 sm:py-3 shadow-md ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-br from-blue-400/95 to-indigo-400/95 text-white border border-blue-300/50'
                      : 'bg-white/95 dark:bg-slate-800/95 text-gray-800 dark:text-gray-100 border border-gray-200/80 dark:border-slate-600/80'
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words font-medium text-xs sm:text-sm leading-relaxed">{msg.content}</p>
                  <time
                    className={`text-[10px] sm:text-xs mt-1.5 sm:mt-2 font-medium block ${
                      msg.role === 'user' ? 'text-blue-100/90' : 'text-gray-500 dark:text-gray-400'
                    }`}
                  >
                    {new Date(msg.timestamp).toLocaleTimeString('ru-RU', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </time>
                </div>
                {/* Кнопки действий (копировать, ответить) */}
                <div className="absolute -bottom-7 left-0 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => handleCopyMessage(msg.content)}
                    className="px-2 py-1 text-xs bg-gray-200 dark:bg-slate-700 rounded hover:bg-gray-300 dark:hover:bg-slate-600"
                    title="Копировать"
                  >
                    📋
                  </button>
                  {msg.role === 'ai' && (
                    <button
                      onClick={() => handleReplyToMessage(index)}
                      className="px-2 py-1 text-xs bg-gray-200 dark:bg-slate-700 rounded hover:bg-gray-300 dark:hover:bg-slate-600"
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
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce delay-100"></span>
                  <span className="w-2 h-2 bg-pink-500 rounded-full animate-bounce delay-200"></span>
                </div>
                <span className="text-sm text-gray-600 dark:text-gray-400 font-medium">PandaPal думает...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Кнопки скролла */}
      {showScrollButtons && (
        <div className="absolute right-4 bottom-24 flex flex-col gap-2">
          <button
            onClick={scrollToTop}
            className="w-10 h-10 rounded-full bg-blue-500 text-white shadow-lg hover:bg-blue-600 active:scale-95 transition-all flex items-center justify-center"
            aria-label="Вверх"
          >
            ⬆️
          </button>
          <button
            onClick={scrollToBottom}
            className="w-10 h-10 rounded-full bg-blue-500 text-white shadow-lg hover:bg-blue-600 active:scale-95 transition-all flex items-center justify-center"
            aria-label="Вниз"
          >
            ⬇️
          </button>
        </div>
      )}

      {/* Индикатор ответа на сообщение */}
      {replyToMessage !== null && messages[replyToMessage] && (
        <div className="flex-shrink-0 bg-blue-50 dark:bg-slate-800 border-t border-blue-200 dark:border-slate-700 px-4 py-2 flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-blue-600 dark:text-blue-400 font-semibold">Ответ на:</p>
            <p className="text-sm text-gray-700 dark:text-gray-300 truncate">
              {messages[replyToMessage].content.slice(0, 50)}...
            </p>
          </div>
          <button
            onClick={() => setReplyToMessage(null)}
            className="ml-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            ✖️
          </button>
        </div>
      )}

      {/* Поле ввода */}
      <div className="flex-shrink-0 bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-700 p-1.5 sm:p-2 shadow-md">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handlePhotoUpload}
          className="hidden"
        />

        <div className="flex items-center gap-1 sm:gap-1.5">
          <button
            onClick={handlePhotoClick}
            disabled={isSending || isRecording}
            className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-blue-400/90 to-indigo-400/90 text-white flex items-center justify-center disabled:opacity-50 hover:shadow-md transition-all active:scale-95 shadow-sm self-center"
            title="Отправить фото"
          >
            <span className="text-base sm:text-lg">📷</span>
          </button>

          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Задай вопрос..."
            disabled={isSending || isRecording}
            className="flex-1 resize-none rounded-lg sm:rounded-xl px-2.5 sm:px-3 py-2 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white placeholder:text-gray-400 text-sm sm:text-base border border-gray-200 dark:border-slate-700 outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-200 disabled:opacity-50 transition-all h-[44px] sm:h-[48px] leading-tight"
            rows={1}
            style={{ maxHeight: '120px', minHeight: '44px' }}
          />

          {isRecording ? (
            <button
              onClick={handleVoiceStop}
              className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-red-400/90 to-pink-400/90 text-white flex items-center justify-center animate-pulse shadow-md self-center"
              title="Остановить"
            >
              <span className="text-base sm:text-lg">⏹️</span>
            </button>
          ) : inputText.trim() ? (
            <button
              onClick={handleSend}
              disabled={isSending}
              className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-green-400/90 to-emerald-400/90 text-white flex items-center justify-center disabled:opacity-50 transition-all active:scale-95 hover:shadow-md shadow-sm self-center"
              title="Отправить"
            >
              {isSending ? (
                <div className="animate-spin text-base sm:text-lg">⏳</div>
              ) : (
                <span className="text-base sm:text-lg">▶️</span>
              )}
            </button>
          ) : (
            <button
              onClick={handleVoiceStart}
              disabled={isSending}
              className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-blue-400/90 to-indigo-400/90 text-white flex items-center justify-center disabled:opacity-50 transition-all active:scale-95 hover:shadow-md shadow-sm self-center"
              title="Голосовое"
            >
              <span className="text-base sm:text-lg">🎤</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
