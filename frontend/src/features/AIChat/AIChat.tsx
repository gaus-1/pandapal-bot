/**
 * AI Chat Screen - Общение с AI
 */

import { useState, useEffect, useRef } from 'react';
import { telegram } from '../../services/telegram';
import { sendAIMessage, getChatHistory, type UserProfile } from '../../services/api';

interface Message {
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
}

interface AIChatProps {
  user: UserProfile;
}

export function AIChat({ user }: AIChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  // Загрузка истории чата
  useEffect(() => {
    getChatHistory(user.telegram_id, 20)
      .then((history) => {
        setMessages(history);
        setIsLoadingHistory(false);
      })
      .catch((err) => {
        console.error('Ошибка загрузки истории:', err);
        setIsLoadingHistory(false);
      });
  }, [user.telegram_id]);

  // Автоскролл к последнему сообщению
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputText,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    telegram.hapticFeedback('medium');

    try {
      const response = await sendAIMessage(user.telegram_id, inputText);

      const aiMessage: Message = {
        role: 'ai',
        content: response.response,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, aiMessage]);
      telegram.notifySuccess();
    } catch (error) {
      console.error('Ошибка отправки сообщения:', error);
      telegram.notifyError();
      await telegram.showAlert('Не удалось отправить сообщение. Попробуй еще раз!');
    } finally {
      setIsLoading(false);
    }
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

    // Показываем превью
    const userMessage: Message = {
      role: 'user',
      content: `📷 Фото: ${file.name}`,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Конвертируем в base64
      const reader = new FileReader();
      reader.onload = async () => {
        // const base64 = reader.result as string; // TODO: использовать для отправки

        // Отправляем на backend (TODO: добавить endpoint для фото)
        const response = await sendAIMessage(
          user.telegram_id,
          `Пользователь отправил фото. Анализирую изображение...`
        );

        const aiMessage: Message = {
          role: 'ai',
          content: response.response,
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, aiMessage]);
        telegram.notifySuccess();
      };

      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Ошибка загрузки фото:', error);
      telegram.notifyError();
      await telegram.showAlert('Не удалось загрузить фото. Попробуй еще раз!');
    } finally {
      setIsLoading(false);
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

      mediaRecorder.onstop = async () => {
        // const audioBlob = new Blob(audioChunks, { type: 'audio/webm' }); // TODO: использовать для отправки

        telegram.hapticFeedback('medium');

        const userMessage: Message = {
          role: 'user',
          content: `🎤 Голосовое сообщение`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMessage]);
        setIsLoading(true);

        try {
          // TODO: Отправить на backend для распознавания речи
          const response = await sendAIMessage(
            user.telegram_id,
            'Пользователь отправил голосовое сообщение. Обрабатываю...'
          );

          const aiMessage: Message = {
            role: 'ai',
            content: response.response,
            timestamp: new Date().toISOString(),
          };

          setMessages((prev) => [...prev, aiMessage]);
          telegram.notifySuccess();
        } catch (error) {
          console.error('Ошибка отправки аудио:', error);
          telegram.notifyError();
          await telegram.showAlert('Не удалось отправить голосовое сообщение!');
        } finally {
          setIsLoading(false);
        }

        // Останавливаем поток
        stream.getTracks().forEach((track) => track.stop());
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
    <div className="flex flex-col h-full bg-[var(--tg-theme-bg-color)]">
      {/* Заголовок */}
      <div className="flex-shrink-0 bg-[var(--tg-theme-bg-color)] border-b border-[var(--tg-theme-hint-color)]/20 p-4">
        <div className="flex items-center gap-3">
          <div className="text-4xl">🐼</div>
          <div>
            <h1 className="text-xl font-bold text-[var(--tg-theme-text-color)]">
              PandaPal AI
            </h1>
            <p className="text-sm text-[var(--tg-theme-hint-color)]">
              Привет, {user.first_name}! Чем помочь? 🎓
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
            <div className="text-6xl mb-4">🐼</div>
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
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                  msg.role === 'user'
                    ? 'bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)]'
                    : 'bg-[var(--tg-theme-hint-color)]/10 text-[var(--tg-theme-text-color)]'
                }`}
              >
                <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                <p className="text-xs opacity-70 mt-1">
                  {new Date(msg.timestamp).toLocaleTimeString('ru-RU', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-[var(--tg-theme-hint-color)]/10 rounded-2xl px-4 py-2">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-[var(--tg-theme-hint-color)] rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-[var(--tg-theme-hint-color)] rounded-full animate-bounce delay-100"></span>
                  <span className="w-2 h-2 bg-[var(--tg-theme-hint-color)] rounded-full animate-bounce delay-200"></span>
                </div>
                <span className="text-sm text-[var(--tg-theme-hint-color)]">Думаю...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Поле ввода */}
      <div className="flex-shrink-0 bg-[var(--tg-theme-bg-color)] border-t border-[var(--tg-theme-hint-color)]/20 p-4">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handlePhotoUpload}
          className="hidden"
        />

        <div className="flex items-end gap-2">
          {/* Кнопка фото */}
          <button
            onClick={handlePhotoClick}
            disabled={isLoading || isRecording}
            className="flex-shrink-0 w-12 h-12 rounded-full bg-[var(--tg-theme-hint-color)]/20 text-[var(--tg-theme-text-color)] flex items-center justify-center disabled:opacity-50 hover:bg-[var(--tg-theme-hint-color)]/30 transition-all active:scale-95"
            title="Отправить фото"
          >
            <span className="text-xl">📷</span>
          </button>

          {/* Поле ввода текста */}
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Напиши свой вопрос..."
            disabled={isLoading || isRecording}
            className="flex-1 resize-none rounded-2xl px-4 py-3 bg-[var(--tg-theme-hint-color)]/10 text-[var(--tg-theme-text-color)] placeholder:text-[var(--tg-theme-hint-color)] border-none outline-none focus:ring-2 focus:ring-[var(--tg-theme-button-color)] disabled:opacity-50"
            rows={1}
            style={{ maxHeight: '100px' }}
          />

          {/* Кнопка аудио / отправки */}
          {isRecording ? (
            <button
              onClick={handleVoiceStop}
              className="flex-shrink-0 w-12 h-12 rounded-full bg-red-500 text-white flex items-center justify-center animate-pulse"
              title="Остановить запись"
            >
              <span className="text-xl">⏹️</span>
            </button>
          ) : inputText.trim() ? (
            <button
              onClick={handleSend}
              disabled={isLoading}
              className="flex-shrink-0 w-12 h-12 rounded-full bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
              title="Отправить сообщение"
            >
              {isLoading ? (
                <div className="animate-spin">⏳</div>
              ) : (
                <span className="text-xl">▶️</span>
              )}
            </button>
          ) : (
            <button
              onClick={handleVoiceStart}
              disabled={isLoading}
              className="flex-shrink-0 w-12 h-12 rounded-full bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] flex items-center justify-center disabled:opacity-50 transition-all active:scale-95"
              title="Записать голосовое сообщение"
            >
              <span className="text-xl">🎤</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
