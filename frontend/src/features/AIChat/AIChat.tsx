/**
 * AI Chat Screen - Общение с AI
 * Использует TanStack Query для оптимизированного кэширования
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
  // Используем оптимизированный хук с TanStack Query
  const {
    messages,
    isLoadingHistory,
    sendMessage,
    isSending,
  } = useChat({ telegramId: user.telegram_id, limit: 20 });

  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingStartTimeRef = useRef<number>(0);

  // Автоскролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cleanup: останавливаем запись при размонтировании
  useEffect(() => {
    return () => {
      // Останавливаем запись если она активна
      if (mediaRecorderRef.current && isRecording) {
        try {
          mediaRecorderRef.current.stop();
        } catch (e) {
          console.warn('⚠️ Ошибка при остановке записи в cleanup:', e);
        }
      }

      // Останавливаем все треки потока
      if (mediaRecorderRef.current?.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach((track) => {
          track.stop();
        });
      }

      mediaRecorderRef.current = null;
      setIsRecording(false);
    };
  }, [isRecording]);

  const handleSend = () => {
    if (!inputText.trim() || isSending) return;

    sendMessage({ message: inputText });
    setInputText('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
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
      // Конвертируем в base64
      const reader = new FileReader();
      reader.onload = () => {
        const base64Data = reader.result as string;

        // Отправляем через TanStack Query хук
        sendMessage({
          message: inputText.trim() || 'Помоги мне с этой задачей',
          photoBase64: base64Data,
        });

        setInputText('');
      };

      reader.readAsDataURL(file);
    } catch (error: any) {
      console.error('Ошибка загрузки фото:', error);
      telegram.notifyError();
      await telegram.showAlert(error.message || 'Не удалось загрузить фото. Попробуй еще раз!');
    } finally {
      // Очищаем input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Обработка записи аудио
  const handleVoiceStart = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: Blob[] = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = () => {
        // Проверяем что аудио записалось
        if (audioChunks.length === 0) {
          console.error('❌ Аудио не записалось - chunks пустой');
          telegram.notifyError();
          telegram.showAlert('Не удалось записать аудио. Попробуй еще раз!');
          stream.getTracks().forEach((track) => track.stop());
          setIsRecording(false);
          return;
        }

        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

        // Проверяем размер аудио (максимум 10MB)
        const MAX_AUDIO_SIZE = 10 * 1024 * 1024; // 10MB
        if (audioBlob.size > MAX_AUDIO_SIZE) {
          console.error(`❌ Аудио слишком большое: ${audioBlob.size} байт`);
          telegram.notifyError();
          telegram.showAlert('Аудио слишком длинное. Максимум 10MB. Попробуй записать короче!');
          stream.getTracks().forEach((track) => track.stop());
          setIsRecording(false);
          return;
        }

        if (audioBlob.size === 0) {
          console.error('❌ Аудио пустое (0 байт)');
          telegram.notifyError();
          telegram.showAlert('Аудио пустое. Попробуй записать заново!');
          stream.getTracks().forEach((track) => track.stop());
          setIsRecording(false);
          return;
        }

        telegram.hapticFeedback('medium');

        try {
          // Конвертируем аудио в base64
          const reader = new FileReader();

          reader.onload = () => {
            const base64Audio = reader.result as string;

            if (!base64Audio || base64Audio.length === 0) {
              console.error('❌ Base64 аудио пустое');
              telegram.notifyError();
              telegram.showAlert('Ошибка конвертации аудио. Попробуй еще раз!');
              stream.getTracks().forEach((track) => track.stop());
              setIsRecording(false);
              return;
            }

            // Отправляем через TanStack Query хук
            sendMessage({
              audioBase64: base64Audio,
            });

            // Останавливаем поток после успешной отправки
            stream.getTracks().forEach((track) => track.stop());
            setIsRecording(false);
          };

          reader.onerror = (error) => {
            console.error('❌ Ошибка FileReader:', error);
            telegram.notifyError();
            telegram.showAlert('Ошибка чтения аудио. Попробуй записать заново!');
            stream.getTracks().forEach((track) => track.stop());
            setIsRecording(false);
          };

          reader.readAsDataURL(audioBlob);
        } catch (error: any) {
          console.error('❌ Ошибка отправки аудио:', error);
          telegram.notifyError();
          telegram.showAlert(error.message || 'Не удалось отправить голосовое сообщение!');
          stream.getTracks().forEach((track) => track.stop());
          setIsRecording(false);
        }
      };

      // Обработка ошибок MediaRecorder
      mediaRecorder.onerror = (event: any) => {
        console.error('❌ Ошибка MediaRecorder:', event);
        telegram.notifyError();
        telegram.showAlert('Ошибка записи аудио. Попробуй еще раз!');
        stream.getTracks().forEach((track) => track.stop());
        setIsRecording(false);
        mediaRecorderRef.current = null;
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      recordingStartTimeRef.current = Date.now();
      setIsRecording(true);
      telegram.hapticFeedback('heavy');
    } catch (error) {
      console.error('❌ Ошибка доступа к микрофону:', error);
      telegram.notifyError();
      await telegram.showAlert('Не удалось получить доступ к микрофону. Разреши доступ в настройках браузера.');
      setIsRecording(false);
    }
  };

  const handleVoiceStop = () => {
    if (mediaRecorderRef.current && isRecording) {
      // Проверяем минимальную длину записи (0.5 секунды)
      const recordingDuration = Date.now() - recordingStartTimeRef.current;
      const MIN_RECORDING_DURATION = 500; // 0.5 секунды

      if (recordingDuration < MIN_RECORDING_DURATION) {
        console.warn('⚠️ Запись слишком короткая, отменяем');
        mediaRecorderRef.current.stop();
        // Очищаем chunks и останавливаем поток
        if (mediaRecorderRef.current.stream) {
          mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
        }
        mediaRecorderRef.current = null;
        setIsRecording(false);
        telegram.hapticFeedback('light');
        return;
      }

      mediaRecorderRef.current.stop();
      telegram.hapticFeedback('medium');
      // setIsRecording(false) будет вызван в onstop
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:to-slate-800">
      {/* КОМПАКТНЫЙ пастельный заголовок */}
      <div className="flex-shrink-0 bg-gradient-to-r from-blue-400/90 to-indigo-400/90 shadow-sm p-1.5 sm:p-2 border-b border-blue-300/50">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <img src="/logo.png" alt="PandaPal" className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-white/90 p-0.5 shadow-sm" />
          <div className="flex-1 min-w-0">
            <h1 className="text-sm sm:text-base font-bold text-white drop-shadow-sm truncate">
              PandaPal AI
            </h1>
            <p className="text-[10px] sm:text-xs text-blue-100 font-medium truncate">
              Привет, {user.first_name}! 🎓
            </p>
          </div>
          {/* Кнопка достижений */}
          <button
            onClick={() => {
              useAppStore.getState().setCurrentScreen('achievements');
              telegram.hapticFeedback('light');
            }}
            className="flex-shrink-0 w-8 h-8 sm:w-9 sm:h-9 rounded-lg bg-white/20 hover:bg-white/30 active:scale-95 transition-all flex items-center justify-center shadow-sm"
            aria-label="Достижения"
            title="Достижения"
          >
            <span className="text-lg sm:text-xl">🏆</span>
          </button>
        </div>
      </div>

      {/* Список сообщений */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" role="log" aria-label="История сообщений чата" aria-live="polite" aria-atomic="false">
        {isLoadingHistory ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-8">
            <img src="/logo.png" alt="PandaPal" className="w-24 h-24 mx-auto mb-4 rounded-full shadow-xl" />
            <h2 className="text-xl font-bold text-[var(--tg-theme-text-color)] mb-2">
              Начни общение!
            </h2>
            <p className="text-[var(--tg-theme-hint-color)]">
              Задай любой вопрос, и я помогу тебе с учебой! 📚
            </p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
              role="article"
              aria-label={msg.role === 'user' ? 'Ваше сообщение' : 'Сообщение от PandaPal'}
            >
              <div
                className={`max-w-[85%] sm:max-w-[80%] rounded-xl sm:rounded-2xl px-3 py-2 sm:px-4 sm:py-3 shadow-md ${
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
                  dateTime={new Date(msg.timestamp).toISOString()}
                  aria-label={`Время отправки: ${new Date(msg.timestamp).toLocaleTimeString('ru-RU', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}`}
                >
                  {new Date(msg.timestamp).toLocaleTimeString('ru-RU', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </time>
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

      {/* Поле ввода - КОМПАКТНОЕ, адаптивное */}
      <div className="flex-shrink-0 bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-700 p-1.5 sm:p-2 shadow-md">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handlePhotoUpload}
          className="hidden"
        />

        <div className="flex items-center gap-1 sm:gap-1.5">
          {/* Кнопка фото - выровнена по центру с textarea */}
          <button
            onClick={handlePhotoClick}
            disabled={isSending || isRecording}
            className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-blue-400/90 to-indigo-400/90 text-white flex items-center justify-center disabled:opacity-50 hover:shadow-md transition-all active:scale-95 shadow-sm self-center"
            title="Отправить фото"
            aria-label="Отправить фото"
          >
            <span className="text-base sm:text-lg" aria-hidden="true">📷</span>
          </button>

          {/* Поле ввода текста */}
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Задай вопрос..."
            disabled={isSending || isRecording}
            className="flex-1 resize-none rounded-lg sm:rounded-xl px-2.5 sm:px-3 py-2 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white placeholder:text-gray-400 text-sm sm:text-base border border-gray-200 dark:border-slate-700 outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-200 disabled:opacity-50 transition-all h-[44px] sm:h-[48px] leading-tight"
            rows={1}
            style={{ maxHeight: '120px', minHeight: '44px' }}
            aria-label="Поле ввода сообщения"
          />

          {/* Кнопка аудио / отправки - выровнена по центру с textarea */}
          {isRecording ? (
            <button
              onClick={handleVoiceStop}
              className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-red-400/90 to-pink-400/90 text-white flex items-center justify-center animate-pulse shadow-md self-center"
              title="Остановить запись"
              aria-label="Остановить запись голосового сообщения"
            >
              <span className="text-base sm:text-lg" aria-hidden="true">⏹️</span>
            </button>
          ) : inputText.trim() ? (
            <button
              onClick={handleSend}
              disabled={isSending}
              className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-green-400/90 to-emerald-400/90 text-white flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95 hover:shadow-md shadow-sm self-center"
              title="Отправить сообщение"
              aria-label="Отправить текстовое сообщение"
            >
              {isSending ? (
                <div className="animate-spin text-base sm:text-lg" aria-hidden="true">⏳</div>
              ) : (
                <span className="text-base sm:text-lg" aria-hidden="true">▶️</span>
              )}
            </button>
          ) : (
            <button
              onClick={handleVoiceStart}
              disabled={isSending}
              className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-blue-400/90 to-indigo-400/90 text-white flex items-center justify-center disabled:opacity-50 transition-all active:scale-95 hover:shadow-md shadow-sm self-center"
              title="Записать голосовое сообщение"
              aria-label="Записать голосовое сообщение"
            >
              <span className="text-base sm:text-lg" aria-hidden="true">🎤</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
