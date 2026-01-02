/**
 * AI Chat Screen - Общение с AI
 * Использует TanStack Query для оптимизированного кэширования
 */

import { useState, useEffect, useRef } from 'react';
import { telegram } from '../../services/telegram';
import { useChat } from '../../hooks/useChat';
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

  // Автоскролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

        telegram.hapticFeedback('medium');

        try {
          // Конвертируем аудио в base64
          const reader = new FileReader();
          reader.onload = () => {
            const base64Audio = reader.result as string;

            // Отправляем через TanStack Query хук
            sendMessage({
              audioBase64: base64Audio,
            });
          };

          reader.readAsDataURL(audioBlob);
        } catch (error: any) {
          console.error('Ошибка отправки аудио:', error);
          telegram.notifyError();
          telegram.showAlert(error.message || 'Не удалось отправить голосовое сообщение!');
        } finally {
          // Останавливаем поток
          stream.getTracks().forEach((track) => track.stop());
        }
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      telegram.hapticFeedback('heavy');
    } catch (error) {
      console.error('Ошибка доступа к микрофону:', error);
      telegram.notifyError();
      await telegram.showAlert('Не удалось получить доступ к микрофону. Разреши доступ в настройках браузера.');
    }
  };

  const handleVoiceStop = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      telegram.hapticFeedback('medium');
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
        </div>
      </div>

      {/* Список сообщений */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
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
            >
              <div
                className={`max-w-[85%] sm:max-w-[80%] rounded-xl sm:rounded-2xl px-3 py-2 sm:px-4 sm:py-3 shadow-md ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-blue-400/95 to-indigo-400/95 text-white border border-blue-300/50'
                    : 'bg-white/95 dark:bg-slate-800/95 text-gray-800 dark:text-gray-100 border border-gray-200/80 dark:border-slate-600/80'
                }`}
              >
                <p className="whitespace-pre-wrap break-words font-medium text-xs sm:text-sm leading-relaxed">{msg.content}</p>
                <p className={`text-[10px] sm:text-xs mt-1.5 sm:mt-2 font-medium ${
                  msg.role === 'user' ? 'text-blue-100/90' : 'text-gray-500 dark:text-gray-400'
                }`}>
                  {new Date(msg.timestamp).toLocaleTimeString('ru-RU', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
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

        <div className="flex items-end gap-1 sm:gap-1.5">
          {/* Кнопка фото - ПАСТЕЛЬНАЯ, адаптивная */}
          <button
            onClick={handlePhotoClick}
            disabled={isSending || isRecording}
            className="flex-shrink-0 w-8 h-8 sm:w-9 sm:h-9 md:w-10 md:h-10 rounded-lg bg-gradient-to-br from-blue-400/90 to-indigo-400/90 text-white flex items-center justify-center disabled:opacity-50 hover:shadow-md transition-all active:scale-95 shadow-sm"
            title="Отправить фото"
          >
            <span className="text-base sm:text-lg">📷</span>
          </button>

          {/* Поле ввода текста - БОЛЬШЕ пространства, адаптивное */}
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Задай вопрос..."
            disabled={isSending || isRecording}
            className="flex-1 resize-none rounded-lg sm:rounded-xl px-2.5 sm:px-3 py-1.5 sm:py-2 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white placeholder:text-gray-400 text-xs sm:text-sm border border-gray-200 dark:border-slate-700 outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-200 disabled:opacity-50 transition-all"
            rows={1}
            style={{ maxHeight: '100px' }}
          />

          {/* Кнопка аудио / отправки - ПАСТЕЛЬНАЯ, адаптивная */}
          {isRecording ? (
            <button
              onClick={handleVoiceStop}
              className="flex-shrink-0 w-8 h-8 sm:w-9 sm:h-9 md:w-10 md:h-10 rounded-lg bg-gradient-to-br from-red-400/90 to-pink-400/90 text-white flex items-center justify-center animate-pulse shadow-md"
              title="Остановить запись"
            >
              <span className="text-base sm:text-lg">⏹️</span>
            </button>
          ) : inputText.trim() ? (
            <button
              onClick={handleSend}
              disabled={isSending}
              className="flex-shrink-0 w-8 h-8 sm:w-9 sm:h-9 md:w-10 md:h-10 rounded-lg bg-gradient-to-br from-green-400/90 to-emerald-400/90 text-white flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95 hover:shadow-md shadow-sm"
              title="Отправить сообщение"
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
              className="flex-shrink-0 w-8 h-8 sm:w-9 sm:h-9 md:w-10 md:h-10 rounded-lg bg-gradient-to-br from-blue-400/90 to-indigo-400/90 text-white flex items-center justify-center disabled:opacity-50 transition-all active:scale-95 hover:shadow-md shadow-sm"
              title="Записать голосовое сообщение"
            >
              <span className="text-base sm:text-lg">🎤</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
