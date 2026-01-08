/**
 * AI Chat Screen - Общение с AI (фикс UI блокировки)
 *
 * ⚠️ КРИТИЧЕСКИ ВАЖНО: ЭТОТ ФАЙЛ ЗАБЛОКИРОВАН ДЛЯ ИЗМЕНЕНИЙ
 *
 * Этот файл работает корректно и протестирован.
 * НЕ ВНОСИТЬ ИЗМЕНЕНИЯ без явного разрешения пользователя.
 * Если пользователь просит изменить - спросить подтверждение.
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
  const mimeTypeRef = useRef<string>('');
  const isGettingAccessRef = useRef(false);

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

  // Cleanup
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, []);

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
        sendMessage({
          message: inputText.trim() || 'Помоги мне с этой задачей',
          photoBase64: reader.result as string,
        });
        setInputText('');
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Ошибка загрузки фото:', error);
      telegram.notifyError();
      telegram.showAlert('Не удалось загрузить фото');
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const stopRecordingCleanup = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
    setIsRecording(false);
    setIsGettingAccess(false);
    isGettingAccessRef.current = false;
  };

  const handleVoiceStart = async () => {
    if (isRecording || isGettingAccessRef.current) return;

    isGettingAccessRef.current = true;
    setIsGettingAccess(true);
    setIsRecording(true); // Блокируем UI

    try {
      console.log('🎤 Запрос микрофона...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Пробуем стандартный webm
      let mimeType = '';
      if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
      }

      const options = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      mimeTypeRef.current = mimeType;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const recordingDuration = Date.now() - recordingStartTimeRef.current;
        const totalSize = audioChunksRef.current.reduce((acc, chunk) => acc + chunk.size, 0);

        const MIN_DURATION = 500; // 0.5 сек
        const MIN_SIZE = 1000;

        // 1. Ошибка формата (упал мгновенно)
        if (recordingDuration < 200 && totalSize === 0) {
          console.error('❌ Мгновенный сбой рекордера');
          telegram.notifyError();
          telegram.showAlert('Ошибка записи на этом устройстве. Попробуйте обновить Telegram.');
          stopRecordingCleanup(); // РАЗБЛОКИРОВКА UI
          return;
        }

        // 2. Слишком короткая запись
        if (recordingDuration < MIN_DURATION || totalSize < MIN_SIZE) {
          console.warn('⚠️ Запись слишком короткая');
          telegram.hapticFeedback('light');
          telegram.showAlert('Запись слишком короткая. Удерживай кнопку дольше.');
          stopRecordingCleanup(); // РАЗБЛОКИРОВКА UI
          return;
        }

        // 3. Успешная запись
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/webm' });
        telegram.hapticFeedback('medium');

        const reader = new FileReader();
        reader.onload = () => {
          const base64Audio = reader.result as string;
          sendMessage({
            audioBase64: base64Audio,
            ...(inputText.trim() ? { message: inputText.trim() } : {}),
          });
          setInputText('');
          stopRecordingCleanup(); // КРИТИЧЕСКИ: Разблокируем UI ПОСЛЕ отправки
        };

        reader.onerror = () => {
          telegram.showAlert('Ошибка обработки аудио');
          stopRecordingCleanup(); // Разблокировка при ошибке чтения
        };

        reader.readAsDataURL(audioBlob);
      };

      mediaRecorder.onerror = (event: Event) => {
        console.error('❌ MediaRecorder Error:', event);
        telegram.notifyError();
        stopRecordingCleanup();
        telegram.showAlert('Произошла ошибка записи аудио.');
      };

      recordingStartTimeRef.current = Date.now();
      mediaRecorder.start();
      console.log('✅ Запись начата');

    } catch (error) {
      console.error('❌ Ошибка handleVoiceStart:', error);
      telegram.notifyError();
      stopRecordingCleanup();
      if (error instanceof DOMException && error.name === 'NotAllowedError') {
        telegram.showAlert('Доступ к микрофону запрещен. Разрешите доступ в настройках.');
      } else {
        telegram.showAlert('Не удалось начать запись. Проверьте микрофон.');
      }
    }
  };

  const handleVoiceStop = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-blue-50 via-white to-purple-50 dark:from-slate-900 dark:to-slate-800">
      {/* Заголовок */}
      <div className="flex-shrink-0 bg-gradient-to-r from-blue-400/90 to-indigo-400/90 shadow-sm p-1.5 sm:p-2 border-b border-blue-300/50">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <img src="/logo.png" alt="PandaPal" width={32} height={32} loading="lazy" className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-white/90 p-0.5 shadow-sm" />
          <div className="flex-1 min-w-0">
            <h1 className="text-xs sm:text-sm md:text-base font-bold text-white drop-shadow-sm truncate">PandaPal AI</h1>
            <p className="text-[10px] sm:text-xs md:text-sm text-blue-100 font-medium truncate">Привет, {user.first_name}! 🎓</p>
          </div>
          <div className="flex items-center gap-1.5">
            <button onClick={handleClearChat} className="flex-shrink-0 w-9 h-9 rounded-lg bg-gray-400/60 hover:bg-gray-500/70 active:scale-95 transition-all flex items-center justify-center border border-gray-400/40 shadow-sm">
              <span className="text-base text-gray-700 dark:text-gray-200">🗑️</span>
            </button>
            <button onClick={() => { useAppStore.getState().setCurrentScreen('emergency'); telegram.hapticFeedback('medium'); }} className="flex-shrink-0 w-10 h-10 sm:w-11 sm:h-11 rounded-lg bg-red-500/90 hover:bg-red-600/90 active:scale-95 transition-all flex items-center justify-center shadow-sm">
              <span className="text-lg sm:text-xl">🚨</span>
            </button>
          </div>
        </div>
      </div>

      {/* Сообщения */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4" role="log">
        {isLoadingHistory ? (
          <div className="text-center py-8"><div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--tg-theme-button-color)]"></div></div>
        ) : messages.length === 0 ? (
          <div className="text-center py-8">
            <img src="/logo.png" alt="PandaPal" width={96} height={96} loading="lazy" className="w-24 h-24 mx-auto mb-4 rounded-full shadow-xl" />
            <h2 className="text-base sm:text-lg md:text-xl font-bold text-[var(--tg-theme-text-color)] mb-2">Начни общение!</h2>
            <p className="text-xs sm:text-sm md:text-base text-[var(--tg-theme-hint-color)]">Задай любой вопрос, и я помогу тебе с учебой! 📚</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in group`} role="article">
              <div className="relative max-w-[85%] sm:max-w-[80%]">
                <div className={`rounded-xl sm:rounded-2xl px-3 py-2 sm:px-4 sm:py-3 shadow-md ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-blue-400/95 to-indigo-400/95 text-white border border-blue-300/50'
                    : 'bg-white/95 dark:bg-slate-800/95 text-gray-800 dark:text-gray-100 border border-gray-200/80 dark:border-slate-600/80'
                }`}>
                  <p className="whitespace-pre-wrap break-words font-medium text-xs sm:text-sm leading-relaxed">{msg.content}</p>
                  <time className={`text-[10px] sm:text-xs mt-1.5 sm:mt-2 font-medium block ${
                    msg.role === 'user' ? 'text-blue-100/90' : 'text-gray-500 dark:text-gray-400'
                  }`}>
                    {new Date(msg.timestamp).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                  </time>
                </div>
                {/* Кнопки действий */}
                <div className="absolute -bottom-7 left-0 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => handleCopyMessage(msg.content)} className="px-2 py-1 text-xs bg-gray-200 dark:bg-slate-700 rounded hover:bg-gray-300 dark:hover:bg-slate-600">📋</button>
                  {msg.role === 'ai' && (
                    <button onClick={() => handleReplyToMessage(index)} className="px-2 py-1 text-xs bg-gray-200 dark:bg-slate-700 rounded hover:bg-gray-300 dark:hover:bg-slate-600">↩️</button>
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
                <div className="flex gap-1"><span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></span><span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce delay-100"></span><span className="w-2 h-2 bg-pink-500 rounded-full animate-bounce delay-200"></span></div>
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
          <button onClick={scrollToTop} className="w-10 h-10 rounded-full bg-blue-500 text-white shadow-lg hover:bg-blue-600 active:scale-95 transition-all flex items-center justify-center">⬆️</button>
          <button onClick={scrollToBottom} className="w-10 h-10 rounded-full bg-blue-500 text-white shadow-lg hover:bg-blue-600 active:scale-95 transition-all flex items-center justify-center">⬇️</button>
        </div>
      )}

      {/* Индикатор ответа */}
      {replyToMessage !== null && messages[replyToMessage] && (
        <div className="flex-shrink-0 bg-blue-50 dark:bg-slate-800 border-t border-blue-200 dark:border-slate-700 px-4 py-2 flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-blue-600 dark:text-blue-400 font-semibold">Ответ на:</p>
            <p className="text-sm text-gray-700 dark:text-gray-300 truncate">{messages[replyToMessage].content.slice(0, 50)}...</p>
          </div>
          <button onClick={() => setReplyToMessage(null)} className="ml-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">✖️</button>
        </div>
      )}

      {/* Поле ввода */}
      <div className="flex-shrink-0 bg-white dark:bg-slate-900 border-t border-gray-200 dark:border-slate-700 p-1.5 sm:p-2 shadow-md">
        <input ref={fileInputRef} type="file" accept="image/*" onChange={handlePhotoUpload} className="hidden" />
        <div className="flex items-center gap-1 sm:gap-1.5">
          <button onClick={handlePhotoClick} disabled={isSending || isRecording} className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-blue-400/90 to-indigo-400/90 text-white flex items-center justify-center disabled:opacity-50 hover:shadow-md transition-all active:scale-95 shadow-sm self-center">
            <span className="text-base sm:text-lg">📷</span>
          </button>

          <textarea value={inputText} onChange={(e) => setInputText(e.target.value)} onKeyPress={handleKeyPress} placeholder="Задай вопрос..." disabled={isSending || isRecording} className="flex-1 resize-none rounded-lg sm:rounded-xl px-2.5 sm:px-3 py-2 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white placeholder:text-gray-400 text-sm sm:text-base border border-gray-200 dark:border-slate-700 outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-200 disabled:opacity-50 transition-all h-[44px] sm:h-[48px] leading-tight" rows={1} style={{ maxHeight: '120px', minHeight: '44px' }} />

          {isRecording ? (
            <button onClick={handleVoiceStop} className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-red-400/90 to-pink-400/90 text-white flex items-center justify-center animate-pulse shadow-md self-center">
              <span className="text-base sm:text-lg">⏹️</span>
            </button>
          ) : inputText.trim() ? (
            <button onClick={handleSend} disabled={isSending} className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-green-400/90 to-emerald-400/90 text-white flex items-center justify-center disabled:opacity-50 transition-all active:scale-95 hover:shadow-md shadow-sm self-center">
              {isSending ? <div className="animate-spin text-base sm:text-lg">⏳</div> : <span className="text-base sm:text-lg">▶️</span>}
            </button>
          ) : (
            <button onClick={handleVoiceStart} disabled={isSending || isRecording || isGettingAccess} className="flex-shrink-0 h-[44px] sm:h-[48px] w-[44px] sm:w-[48px] rounded-lg bg-gradient-to-br from-blue-400/90 to-indigo-400/90 text-white flex items-center justify-center disabled:opacity-50 transition-all active:scale-95 hover:shadow-md shadow-sm self-center">
              <span className="text-base sm:text-lg">🎤</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
