/**
 * AI Chat Screen - Общение с AI (улучшенная версия)
 * Добавлено: очистка чата, копирование, ответ на сообщение, скролл
 */

import { useState, useEffect, useRef } from 'react';
import { telegram } from '../../services/telegram';
import { useChat } from '../../hooks/useChat';
import { useAppStore } from '../../store/appStore';
import { sendLogToServer } from '../../services/api';
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
  const [isGettingAccess, setIsGettingAccess] = useState(false);
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
  const isGettingAccessRef = useRef(false); // Защита от повторных вызовов

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
    console.log('📤 handleSend вызван', {
      hasText: !!inputText.trim(),
      textLength: inputText.length,
      isSending,
      hasReply: replyToMessage !== null,
    });

    if (!inputText.trim() || isSending) {
      console.warn('⚠️ handleSend: пропущен (нет текста или уже отправляется)');
      return;
    }

    let fullMessage = inputText;
    if (replyToMessage !== null && messages[replyToMessage]) {
      const replied = messages[replyToMessage];
      fullMessage = `[Ответ на: "${replied.content.slice(0, 50)}..."]\n\n${inputText}`;
    }

    console.log('📤 Отправляю текстовое сообщение, длина:', fullMessage.length);
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
    console.log('📷 handlePhotoClick вызван');
    fileInputRef.current?.click();
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('📷 handlePhotoUpload вызван');
    const file = e.target.files?.[0];
    if (!file) {
      console.warn('⚠️ handlePhotoUpload: файл не выбран');
      return;
    }
    console.log('📷 Файл выбран:', {
      name: file.name,
      size: file.size,
      type: file.type,
    });

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
  // Вспомогательная функция для очистки interval requestData()
  const clearDataInterval = (recorder: MediaRecorder | null) => {
    if (recorder) {
      const recorderWithInterval = recorder as MediaRecorder & { __dataInterval?: number };
      if (recorderWithInterval.__dataInterval) {
        clearInterval(recorderWithInterval.__dataInterval);
        delete recorderWithInterval.__dataInterval;
      }
    }
  };

  const handleVoiceStart = async () => {
    const logData = {
      isRecording,
      hasRecorder: !!mediaRecorderRef.current,
      isGettingAccess: isGettingAccessRef.current,
      userAgent: navigator.userAgent,
      platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
      hasMediaDevices: !!navigator.mediaDevices,
      hasGetUserMedia: !!navigator.mediaDevices?.getUserMedia,
    };
    console.log('🎤 handleVoiceStart вызван', logData);
    sendLogToServer('info', 'handleVoiceStart вызван', logData, user.telegram_id).catch(() => {});

    // Защита от повторных вызовов
    // Разрешаем перезапуск, если ресурсы очищены (для автоматического перезапуска)
    if ((mediaRecorderRef.current || isGettingAccess) && !(mediaRecorderRef.current === null && streamRef.current === null)) {
      console.warn('⚠️ Запись уже идет или доступ уже запрашивается');
      sendLogToServer('warn', 'Попытка повторного вызова handleVoiceStart', {
        isRecording,
        hasRecorder: !!mediaRecorderRef.current,
        isGettingAccess,
        platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
      }, user.telegram_id).catch(() => {});
      return;
    }

    // Устанавливаем флаг сразу, чтобы блокировать повторные вызовы
    isGettingAccessRef.current = true;
    setIsGettingAccess(true);
    setIsRecording(true); // Блокируем кнопку сразу

    try {
      console.log('🎤 Запрос доступа к микрофону...');

      // Проверяем разрешения через Permissions API (если доступно)
      let permissionStatus: PermissionStatus | null = null;
      if (navigator.permissions && navigator.permissions.query) {
        try {
          permissionStatus = await navigator.permissions.query({ name: 'microphone' as PermissionName });
          console.log('📋 Статус разрешения микрофона:', permissionStatus.state);
          sendLogToServer('info', 'Проверка разрешения микрофона', {
            state: permissionStatus.state,
            platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
          }, user.telegram_id).catch(() => {});

          // Отслеживаем изменение статуса разрешения
          permissionStatus.onchange = () => {
            console.log('📋 Статус разрешения изменился:', permissionStatus?.state);
            sendLogToServer('info', 'Изменение статуса разрешения микрофона', {
              state: permissionStatus?.state,
              platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
            }, user.telegram_id).catch(() => {});
          };
        } catch (permError) {
          console.warn('⚠️ Permissions API недоступна:', permError);
        }
      }

      // Для Android в Telegram используем упрощенный запрос без дополнительных параметров
      // Это может помочь избежать проблем с разрешениями
      const isAndroid = /Android/i.test(navigator.userAgent);
      const isTelegram = navigator.userAgent.includes('Telegram');

      const audioConstraints = isAndroid && isTelegram
        ? { audio: true } // Упрощенный запрос для Android/Telegram
        : {
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
            }
          };

      console.log('🎤 Параметры запроса:', JSON.stringify(audioConstraints));
      sendLogToServer('info', 'Запрос getUserMedia', {
        constraints: audioConstraints,
        isAndroid,
        isTelegram,
        permissionState: permissionStatus?.state,
      }, user.telegram_id).catch(() => {});

      // Добавляем таймаут для диагностики зависаний
      const getUserMediaPromise = navigator.mediaDevices.getUserMedia(audioConstraints);

      // Логируем начало выполнения промиса
      getUserMediaPromise
        .then(() => {
          console.log('✅ getUserMediaPromise resolved');
        })
        .catch((err) => {
          console.error('❌ getUserMediaPromise rejected:', err);
          sendLogToServer('error', 'getUserMediaPromise rejected', {
            error: err instanceof Error ? err.message : String(err),
            errorName: err instanceof DOMException ? err.name : 'Unknown',
            platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
          }, user.telegram_id).catch(() => {});
        });

      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => {
          console.error('⏰ getUserMedia timeout after 10 seconds');
          sendLogToServer('error', 'getUserMedia timeout', {
            timeout: 10000,
            platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
          }, user.telegram_id).catch(() => {});
          reject(new DOMException('getUserMedia timeout after 10 seconds', 'TimeoutError'));
        }, 10000);
      });

      console.log('⏳ Ожидание ответа getUserMedia...');
      sendLogToServer('info', 'Ожидание ответа getUserMedia', {
        timeout: 10000,
        platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
      }, user.telegram_id).catch(() => {});

      let stream: MediaStream;
      try {
        stream = await Promise.race([getUserMediaPromise, timeoutPromise]);
      } catch (raceError) {
        console.error('❌ Ошибка в Promise.race:', raceError);
        sendLogToServer('error', 'Ошибка Promise.race getUserMedia', {
          error: raceError instanceof Error ? raceError.message : String(raceError),
          errorName: raceError instanceof DOMException ? raceError.name : 'Unknown',
          isTimeout: raceError instanceof DOMException && raceError.name === 'TimeoutError',
          platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
        }, user.telegram_id).catch(() => {});
        throw raceError;
      }

      try {
        streamRef.current = stream;
        console.log('✅ Доступ к микрофону получен');

        // Добавляем обработчики событий на треки, чтобы отследить, когда stream закрывается
        stream.getAudioTracks().forEach((track) => {
          track.onended = () => {
            console.error('❌ Трек завершился (ended):', track.id);
            sendLogToServer('error', 'Аудио трек завершился (ended)', {
              trackId: track.id,
              readyState: track.readyState,
              enabled: track.enabled,
              muted: track.muted,
              platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
            }, user.telegram_id).catch(() => {});
          };

          track.onmute = () => {
            console.warn('⚠️ Трек заглушен:', track.id);
            sendLogToServer('warn', 'Аудио трек заглушен', {
              trackId: track.id,
              platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
            }, user.telegram_id).catch(() => {});
          };

          track.onunmute = () => {
            console.log('✅ Трек разглушен:', track.id);
          };
        });

        await sendLogToServer('info', 'Доступ к микрофону получен', {
          tracksCount: stream.getAudioTracks().length,
          tracks: stream.getAudioTracks().map(t => ({
            id: t.id,
            label: t.label,
            enabled: t.enabled,
            muted: t.muted,
            readyState: t.readyState,
          })),
          platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
        }, user.telegram_id).catch(() => {});

        console.log('📝 Начинаю определение формата...');
        await sendLogToServer('info', 'Начинаю определение формата', {
          platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
        }, user.telegram_id).catch(() => {});
      } catch (streamError) {
        console.error('❌ Ошибка после получения stream:', streamError);
        sendLogToServer('error', 'Ошибка после получения stream', {
          error: streamError instanceof Error ? streamError.message : String(streamError),
          platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
        }, user.telegram_id).catch(() => {});
        throw streamError;
      }

      // Определяем поддерживаемый формат (как в рабочей версии от 1-2 января)
      const supportedTypes = [
        'audio/webm',
        'audio/webm;codecs=opus',
        'audio/ogg;codecs=opus',
        'audio/mp4',
        'audio/aac',
      ];

      let mimeType = '';
      for (const type of supportedTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          mimeType = type;
          break;
        }
      }

      mimeTypeRef.current = mimeType;
      console.log('📝 Используемый формат:', mimeType || 'по умолчанию');
      sendLogToServer('info', 'Формат определен', {
        mimeType: mimeType || 'default',
        platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
      }, user.telegram_id).catch(() => {});

      console.log('🎬 Начинаю создание MediaRecorder...');
      sendLogToServer('info', 'Начинаю создание MediaRecorder', {
        mimeType: mimeType || 'default',
        platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
      }, user.telegram_id).catch(() => {});

      // Создаем MediaRecorder с обработкой ошибок
      // ВАЖНО: Используем streamRef.current вместо локальной переменной stream
      // чтобы гарантировать, что мы используем актуальный stream
      if (!streamRef.current || !streamRef.current.active) {
        console.error('❌ Stream неактивен перед созданием MediaRecorder!');
        sendLogToServer('error', 'Stream неактивен перед созданием MediaRecorder', {
          streamExists: !!streamRef.current,
          streamActive: streamRef.current?.active ?? false,
          platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
        }, user.telegram_id).catch(() => {});
        throw new Error('Stream неактивен перед созданием MediaRecorder');
      }

      let mediaRecorder: MediaRecorder;
      try {
        // Используем streamRef.current вместо локальной переменной stream
        const currentStream = streamRef.current;
        if (mimeType) {
          try {
            mediaRecorder = new MediaRecorder(currentStream, { mimeType });
            console.log('✅ MediaRecorder создан с mimeType:', mimeType);
          } catch (mimeError) {
            console.warn('⚠️ Ошибка создания с mimeType, пробуем без него:', mimeError);
            mediaRecorder = new MediaRecorder(currentStream);
            mimeTypeRef.current = '';
            console.log('✅ MediaRecorder создан без mimeType (fallback)');
          }
        } else {
          mediaRecorder = new MediaRecorder(currentStream);
          console.log('✅ MediaRecorder создан без mimeType');
        }
        console.log('✅ MediaRecorder создан, состояние:', mediaRecorder.state);
        sendLogToServer('info', 'MediaRecorder создан успешно', {
          state: mediaRecorder.state,
          mimeType: mimeType || 'default',
          platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
        }, user.telegram_id).catch(() => {});
      } catch (recorderError) {
        console.error('❌ Критическая ошибка создания MediaRecorder:', recorderError);
        sendLogToServer('error', 'Ошибка создания MediaRecorder', {
          error: recorderError instanceof Error ? recorderError.message : String(recorderError),
          errorName: recorderError instanceof Error ? recorderError.name : 'Unknown',
          platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
        }, user.telegram_id).catch(() => {});
        stream.getTracks().forEach((track) => track.stop());
        throw new Error('Не удалось создать запись аудио. Попробуй обновить страницу.');
      }

      console.log('🧹 Очищаю массив чанков...');
      // Очищаем массив чанков для новой записи
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          console.log('📦 Получен аудио чанк:', event.data.size, 'байт');
          audioChunksRef.current.push(event.data);
          sendLogToServer('info', 'Получен аудио чанк', {
            chunkSize: event.data.size,
            totalChunks: audioChunksRef.current.length,
            totalSize: audioChunksRef.current.reduce((sum, chunk) => sum + chunk.size, 0),
            platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
          }, user.telegram_id).catch(() => {});
        } else {
          console.warn('⚠️ Получен пустой чанк или без данных');
          sendLogToServer('warn', 'Получен пустой аудио чанк', {
            hasData: !!event.data,
            dataSize: event.data?.size ?? 0,
            platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
          }, user.telegram_id).catch(() => {});
        }
      };

      // Сбрасываем флаги для новой записи
      recordingStartedRef.current = false;
      startErrorRef.current = null;

      mediaRecorder.onstart = () => {
        recordingStartedRef.current = true;
        isGettingAccessRef.current = false; // Сбрасываем флаг после успешного начала
        setIsGettingAccess(false);
        console.log('✅ MediaRecorder начал запись, состояние:', mediaRecorder.state);

        // Используем capturedStream из замыкания вместо streamRef.current
        const streamState = {
          streamExists: !!capturedStream,
          streamActive: capturedStream?.active ?? false,
          tracksCount: capturedStream?.getAudioTracks().length ?? 0,
          tracks: capturedStream?.getAudioTracks().map(t => ({
            id: t.id,
            enabled: t.enabled,
            muted: t.muted,
            readyState: t.readyState,
          })) ?? [],
        };

        console.log('📊 Состояние stream в onstart:', streamState);

        if (!capturedStream || !capturedStream.active) {
          console.error('❌ Stream неактивен в onstart! Это может быть причиной проблемы.');
          sendLogToServer('error', 'Stream неактивен в onstart', {
            state: mediaRecorder.state,
            ...streamState,
            platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
          }, user.telegram_id).catch(() => {});
        } else {
          sendLogToServer('info', 'MediaRecorder.onstart вызван', {
            state: mediaRecorder.state,
            ...streamState,
            platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
          }, user.telegram_id).catch(() => {});
        }
      };

      mediaRecorder.onpause = () => {
        console.warn('⚠️ MediaRecorder приостановлен');
      };

      mediaRecorder.onresume = () => {
        console.log('▶️ MediaRecorder возобновлен');
      };

      mediaRecorder.onstop = () => {
        // Очищаем interval для requestData() если он был установлен
        clearDataInterval(mediaRecorderRef.current);

        const recordingDuration = recordingStartTimeRef.current > 0
          ? Date.now() - recordingStartTimeRef.current
          : 0;
        const totalSize = audioChunksRef.current.reduce((sum, chunk) => sum + chunk.size, 0);
        const MIN_RECORDING_DURATION = 500; // Минимальная длительность записи (500мс)
        const wasManuallyStopped = recordingDuration > 100; // Если больше 100мс, скорее всего остановлено вручную

        console.log('🛑 Запись остановлена, чанков:', audioChunksRef.current.length, 'размер:', totalSize, 'байт', 'длительность:', recordingDuration, 'мс', 'вручную:', wasManuallyStopped);
        sendLogToServer('info', 'MediaRecorder.onstop вызван', {
          chunksCount: audioChunksRef.current.length,
          totalSize,
          duration: recordingDuration,
          state: mediaRecorderRef.current?.state ?? 'unknown',
          streamActive: streamRef.current?.active ?? false,
          wasManuallyStopped,
          platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
        }, user.telegram_id).catch(() => {});

        // Если запись остановилась автоматически (не вручную) и пользователь все еще хочет записывать,
        // попробуем перезапустить запись с новым stream
        if (!wasManuallyStopped && isRecording) {
          console.warn('⚠️ Запись остановилась автоматически, пытаюсь перезапустить с новым stream...');
          sendLogToServer('warn', 'Автоматический перезапуск записи с новым stream', {
            duration: recordingDuration,
            streamActive: streamRef.current?.active,
            platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
          }, user.telegram_id).catch(() => {});

          // Очищаем старые ресурсы
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          mediaRecorderRef.current = null;
          audioChunksRef.current = [];
          recordingStartTimeRef.current = 0;
          recordingStartedRef.current = false;

          // Пытаемся получить новый stream и перезапустить запись
          // Вызываем handleVoiceStart асинхронно, чтобы не блокировать текущий обработчик
          setTimeout(() => {
            if (isRecording) {
              console.log('🔄 Перезапускаю запись с новым stream...');
              handleVoiceStart().catch((restartError) => {
                console.error('❌ Ошибка перезапуска записи:', restartError);
                sendLogToServer('error', 'Ошибка перезапуска записи с новым stream', {
                  error: restartError instanceof Error ? restartError.message : String(restartError),
                  platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
                }, user.telegram_id).catch(() => {});
                setIsRecording(false);
                telegram.notifyError();
                telegram.showAlert('Не удалось перезапустить запись. Попробуй еще раз!').catch(() => {});
              });
            }
          }, 100);
          return; // Не обрабатываем остановку, пытаемся перезапустить
        }

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
        const MIN_AUDIO_SIZE = 1000; // Минимальный размер для валидного WebM файла (1KB)
        // recordingDuration уже вычислена выше в onstop

        console.log('📊 Размер аудио:', audioBlob.size, 'байт');
        console.log('📊 Длительность записи:', recordingDuration, 'мс');

        // Проверяем минимальную длительность записи ТОЛЬКО если остановлено вручную
        // Если остановлено автоматически, запись уже перезапущена выше
        if (wasManuallyStopped && recordingDuration < MIN_RECORDING_DURATION) {
          console.error(`❌ Запись слишком короткая: ${recordingDuration}мс (минимум ${MIN_RECORDING_DURATION}мс)`);
          sendLogToServer('error', 'Запись слишком короткая (остановлено вручную)', {
            duration: recordingDuration,
            minDuration: MIN_RECORDING_DURATION,
            audioSize: audioBlob.size,
            wasManuallyStopped,
            platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
          }, user.telegram_id).catch(() => {});
          telegram.notifyError();
          telegram.showAlert('Запись слишком короткая. Говори дольше и нажми кнопку еще раз для отправки!');
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          setIsRecording(false);
          mediaRecorderRef.current = null;
          return;
        }

        // Проверяем минимальный размер аудио ТОЛЬКО если остановлено вручную
        // Если остановлено автоматически, запись уже перезапущена выше
        if (wasManuallyStopped && audioBlob.size < MIN_AUDIO_SIZE) {
          console.error(`❌ Аудио слишком маленькое: ${audioBlob.size} байт (минимум ${MIN_AUDIO_SIZE} байт)`);
          sendLogToServer('error', 'Аудио слишком маленькое (остановлено вручную)', {
            audioSize: audioBlob.size,
            minSize: MIN_AUDIO_SIZE,
            duration: recordingDuration,
            chunksCount: audioChunksRef.current.length,
            wasManuallyStopped,
            platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
          }, user.telegram_id).catch(() => {});
          telegram.notifyError();
          telegram.showAlert('Запись слишком короткая. Говори дольше и нажми кнопку еще раз для отправки!');
          if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
          }
          setIsRecording(false);
          mediaRecorderRef.current = null;
          return;
        }

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
            console.log('📤 Вызываю sendMessage с audioBase64, длина:', base64Audio.length);
            const hasText = inputText.trim().length > 0;
            sendLogToServer('info', 'Аудио готово к отправке', {
              base64Length: base64Audio.length,
              audioBlobSize: audioBlob.size,
              hasText,
              textLength: inputText.trim().length,
            }, user.telegram_id).catch(() => {});
            try {
              // Отправляем аудио вместе с текстом, если он есть
              sendMessage({
                audioBase64: base64Audio,
                ...(hasText ? { message: inputText.trim() } : {}),
              });
              console.log('✅ sendMessage вызван успешно', { hasText, textLength: inputText.trim().length });
              sendLogToServer('info', 'sendMessage вызван с audioBase64', {
                base64Length: base64Audio.length,
                hasText,
                textLength: inputText.trim().length,
              }, user.telegram_id).catch(() => {});
              // Очищаем поле ввода после отправки
              if (hasText) {
                setInputText('');
              }
            } catch (sendError) {
              console.error('❌ Ошибка вызова sendMessage:', sendError);
              sendLogToServer('error', 'Ошибка вызова sendMessage', {
                error: sendError instanceof Error ? sendError.message : String(sendError),
              }, user.telegram_id).catch(() => {});
              telegram.notifyError();
              telegram.showAlert('Ошибка отправки аудио. Попробуй еще раз!');
            }
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

        const errorDetails = {
          error: errorEvent.error instanceof Error ? errorEvent.error.message : String(errorEvent.error),
          errorName: errorEvent.error instanceof Error ? errorEvent.error.name : 'Unknown',
          message: errorEvent.message || 'Unknown error',
          state: mediaRecorderRef.current?.state ?? 'unknown',
          streamActive: streamRef.current?.active ?? false,
          platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
        };
        sendLogToServer('error', 'MediaRecorder.onerror вызван', errorDetails, user.telegram_id).catch(() => {});

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

      // Сохраняем ссылку на recorder ДО start(), чтобы обработчики могли его использовать
      mediaRecorderRef.current = mediaRecorder;
      console.log('💾 mediaRecorderRef установлен');
      sendLogToServer('info', 'MediaRecorder создан и сохранен в ref', {
        state: mediaRecorder.state,
        mimeType: mimeTypeRef.current || 'default',
        streamActive: streamRef.current?.active ?? false,
        tracksCount: streamRef.current?.getAudioTracks().length ?? 0,
        platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
      }, user.telegram_id).catch(() => {});

      // Сохраняем stream в замыкании для использования в обработчиках
      const capturedStream = stream;

      // Упрощенная логика: сразу запускаем запись без сложных проверок
      // Убрали проверки трека - они могут срабатывать преждевременно на мобильных
      try {
        // Для Android/Telegram не используем timeslice - может вызывать закрытие stream
        // Вместо этого используем requestData() вручную через интервалы
        const isAndroid = /Android/i.test(navigator.userAgent);
        const isTelegram = navigator.userAgent.includes('Telegram');
        const useTimeslice = !(isAndroid && isTelegram);
        const timeslice = useTimeslice ? 250 : undefined;

        console.log('🎙️ Запуск записи', timeslice ? `с timeslice: ${timeslice}` : 'без timeslice (Android/Telegram)');

        // Проверяем состояние stream перед start() используя capturedStream
        const streamStateBeforeStart = {
          streamExists: !!capturedStream,
          streamActive: capturedStream?.active ?? false,
          tracksCount: capturedStream?.getAudioTracks().length ?? 0,
          tracks: capturedStream?.getAudioTracks().map(t => ({
            id: t.id,
            enabled: t.enabled,
            muted: t.muted,
            readyState: t.readyState,
          })) ?? [],
        };

        console.log('📊 Состояние stream перед start():', streamStateBeforeStart);

        if (!capturedStream || !capturedStream.active) {
          console.error('❌ Stream неактивен перед start()! Останавливаем запись.');
          sendLogToServer('error', 'Stream неактивен перед start()', {
            stateBeforeStart: mediaRecorder.state,
            ...streamStateBeforeStart,
            platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
          }, user.telegram_id).catch(() => {});
          throw new Error('Stream неактивен перед началом записи');
        }

        sendLogToServer('info', 'Запуск записи', {
          timeslice: timeslice ?? 'none',
          useTimeslice,
          stateBeforeStart: mediaRecorder.state,
          ...streamStateBeforeStart,
          platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
        }, user.telegram_id).catch(() => {});

        // Для Android/Telegram запускаем без timeslice
        if (timeslice !== undefined) {
          mediaRecorder.start(timeslice);
        } else {
          mediaRecorder.start();
          // Для Android/Telegram вызываем requestData() вручную каждые 250мс
          const dataInterval = setInterval(() => {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
              try {
                mediaRecorderRef.current.requestData();
              } catch (e) {
                console.warn('⚠️ Ошибка requestData():', e);
                clearInterval(dataInterval);
              }
            } else {
              clearInterval(dataInterval);
            }
          }, 250);
          // Сохраняем interval для очистки при остановке
          (mediaRecorderRef.current as MediaRecorder & { __dataInterval?: number }).__dataInterval = dataInterval;
        }
        console.log('✅ start() вызван, состояние:', mediaRecorder.state);
        sendLogToServer('info', 'mediaRecorder.start() вызван', {
          stateAfterStart: mediaRecorder.state,
          platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
        }, user.telegram_id).catch(() => {});

        // Устанавливаем состояние сразу, не ждем события onstart
        // Это важно для мобильных устройств, где события могут задерживаться
        recordingStartTimeRef.current = Date.now();
        setIsRecording(true);
        isGettingAccessRef.current = false; // Сбрасываем флаг после успешного начала
        setIsGettingAccess(false);

        // Простая проверка состояния через небольшие интервалы
        let checkCount = 0;
        const checkInterval = setInterval(() => {
          checkCount++;
          const state = mediaRecorderRef.current?.state;
          const started = recordingStartedRef.current;
          const error = startErrorRef.current;

          if (error) {
            console.error('❌ Ошибка обнаружена:', error);
            clearInterval(checkInterval);
            setIsRecording(false);
            if (streamRef.current) {
              streamRef.current.getTracks().forEach((track) => track.stop());
              streamRef.current = null;
            }
            mediaRecorderRef.current = null;
            telegram.notifyError();
            telegram.showAlert(`Ошибка записи: ${error.message}`).catch(console.error);
          } else if (state === 'recording' || started) {
            console.log('✅ Запись успешно начата!');
            sendLogToServer('info', 'Запись успешно начата (проверка)', {
              state,
              started,
              checkCount,
              streamActive: streamRef.current?.active ?? false,
              platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
            }, user.telegram_id).catch(() => {});
            clearInterval(checkInterval);
          } else if (checkCount >= 10) {
            // После 1 секунды останавливаем проверку
            console.warn('⚠️ Проверка завершена, запись может быть активна');
            sendLogToServer('warn', 'Проверка записи завершена без подтверждения', {
              state,
              started,
              checkCount,
              streamActive: streamRef.current?.active ?? false,
              platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
            }, user.telegram_id).catch(() => {});
            clearInterval(checkInterval);
          }
        }, 100);
      } catch (startSyncError) {
        console.error('❌ Ошибка синхронного запуска:', startSyncError);
        setIsRecording(false);
        isGettingAccessRef.current = false; // Сбрасываем флаг при ошибке
        setIsGettingAccess(false);
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
        mediaRecorderRef.current = null;
        throw new Error(`Не удалось начать запись: ${startSyncError instanceof Error ? startSyncError.message : String(startSyncError)}`);
      }

      telegram.hapticFeedback('heavy');
    } catch (error) {
      // Сбрасываем флаги при любой ошибке
      isGettingAccessRef.current = false;
      setIsGettingAccess(false);
      setIsRecording(false);

      const errorDetails = {
        name: error instanceof DOMException ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : String(error),
        code: error instanceof DOMException ? error.code : undefined,
        stack: error instanceof Error ? error.stack : undefined,
        userAgent: navigator.userAgent,
        platform: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
      };
      console.error('❌ Ошибка доступа к микрофону:', error);
      console.error('❌ Детали ошибки:', errorDetails);
      // Отправляем лог асинхронно, чтобы не блокировать UI
      sendLogToServer('error', 'Ошибка доступа к микрофону', errorDetails, user.telegram_id).catch(() => {});
      telegram.notifyError();

      let errorMessage = 'Не удалось получить доступ к микрофону.';

      if (error instanceof DOMException) {
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
          // Укороченное сообщение для Telegram popup (максимум 200 символов)
          if (error.message.includes('system') || error.message.includes('Permission denied by system')) {
            errorMessage = 'Доступ к микрофону заблокирован системой.\n\nПроверь:\n1. Настройки Telegram → Конфиденциальность → Микрофон\n2. Настройки устройства → Разрешения → Микрофон\n3. Попробуй перезапустить Telegram';
          } else {
            errorMessage = 'Доступ к микрофону запрещен.\n\nРазреши доступ в настройках браузера или Telegram.';
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

      console.error('❌ Показываю пользователю ошибку:', errorMessage);
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
    const logData = {
      hasRecorder: !!mediaRecorderRef.current,
      isRecording,
      recorderState: mediaRecorderRef.current?.state,
    };
    console.log('🛑 handleVoiceStop вызван', logData);
    sendLogToServer('info', 'handleVoiceStop вызван', logData, user.telegram_id).catch(() => {});

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
        // Очищаем interval для requestData() если он был установлен
        clearDataInterval(mediaRecorderRef.current);

        console.log('🛑 Вызываю mediaRecorder.stop(), состояние:', mediaRecorderRef.current.state);
        if (mediaRecorderRef.current.state !== 'inactive') {
          mediaRecorderRef.current.stop();
          console.log('✅ mediaRecorder.stop() вызван, состояние после:', mediaRecorderRef.current.state);
        } else {
          console.warn('⚠️ MediaRecorder уже inactive, stop() не нужен');
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
              disabled={isSending || isRecording || isGettingAccess}
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
