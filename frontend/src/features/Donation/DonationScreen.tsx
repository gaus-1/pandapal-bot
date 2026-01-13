/**
 * Donation Screen - Поддержка проекта через Telegram Stars
 */

import { useState } from 'react';
import { telegram } from '../../services/telegram';
import { useAppStore } from '../../store/appStore';
import type { UserProfile } from '../../services/api';

interface DonationScreenProps {
  user?: UserProfile | null;
}

const DONATION_AMOUNTS = [50, 100, 200, 500, 1000];

export function DonationScreen({ user }: DonationScreenProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedAmount, setSelectedAmount] = useState<number>(100);
  const [customAmount, setCustomAmount] = useState<string>('');
  const inTelegram = telegram.isInTelegram();
  const { isAuthenticated } = useAppStore();

  const handleDonate = async (amount: number) => {
    // Telegram Stars работают ТОЛЬКО в Telegram
    if (!inTelegram) {
      // Для обычного сайта - сразу открываем бота
      window.open('https://t.me/PandaPalBot', '_blank');
      return;
    }

    if (amount < 50) {
      await telegram.showAlert('Минимальная сумма поддержки: 50 ⭐');
      return;
    }

    telegram.hapticFeedback('medium');

    setIsProcessing(true);

    try {
      const telegramId = user?.telegram_id || 0;

      // Если пользователь не авторизован
      if (!telegramId) {
        await telegram.showAlert('Пожалуйста, авторизуйтесь в боте для поддержки проекта');
        return;
      }

      const response = await fetch('/api/miniapp/donation/create-invoice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          telegram_id: telegramId,
          amount: amount,
        }),
      });

      const data = await response.json();

      if (data.success && data.invoice_link) {
        telegram.openInvoice(data.invoice_link, (status) => {
          if (status === 'paid') {
            telegram.notifySuccess();
            telegram.showAlert('🎉 Спасибо за поддержку проекта! Вы помогаете развитию PandaPal!');
          } else if (status === 'cancelled') {
            telegram.showAlert('❌ Оплата отменена');
          } else if (status === 'failed') {
            telegram.notifyError();
            telegram.showAlert('❌ Ошибка оплаты. Попробуй еще раз!');
          }
        });
      } else {
        telegram.notifyError();
        await telegram.showAlert('Ошибка создания счета. Попробуй еще раз!');
      }
    } catch (error) {
      console.error('Ошибка поддержки проекта:', error);
      telegram.notifyError();
      await telegram.showAlert('Произошла ошибка. Попробуй позже!');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCustomDonate = () => {
    const amount = parseInt(customAmount);
    if (isNaN(amount) || amount < 50) {
      if (inTelegram) {
        telegram.showAlert('Введите сумму от 50 ⭐');
      } else {
        // Для обычного сайта - сразу открываем бота
        window.open('https://t.me/PandaPalBot', '_blank');
      }
      return;
    }
    handleDonate(amount);
  };

  return (
    <div className="w-full h-full bg-gradient-to-br from-amber-50/40 via-orange-50/40 to-yellow-50/40 dark:from-slate-900 dark:via-slate-800 dark:to-slate-800 overflow-y-auto backdrop-blur-sm">
      <div className="max-w-2xl mx-auto px-3 sm:px-4 md:px-6 py-3 sm:py-4 md:py-6 pb-16 sm:pb-20 md:pb-24">
        {/* Заголовок */}
        <div className="mb-3 sm:mb-4 md:mb-6 text-center">
          <h1 className="text-xl sm:text-2xl md:text-3xl font-display font-bold text-gray-900 dark:text-slate-100 mb-1.5 sm:mb-2">
            PandaPal
          </h1>
          <p className="text-xs sm:text-sm md:text-base text-gray-600 dark:text-slate-400">
            Ваша поддержка помогает развитию проекта
          </p>
        </div>

        {/* Информация о поддержке */}
        <div className="mb-3 sm:mb-4 md:mb-6 p-4 sm:p-5 md:p-6 bg-gradient-to-br from-amber-50/80 via-orange-50/80 to-yellow-50/80 dark:from-amber-950/30 dark:via-orange-950/30 dark:to-yellow-950/30 rounded-[1.5rem] sm:rounded-[2rem] border border-amber-200/25 dark:border-amber-800/20 shadow-[0_2px_10px_rgba(0,0,0,0.05)] dark:shadow-[0_2px_10px_rgba(0,0,0,0.25)]">
          <h2 className="text-xs sm:text-sm md:text-base font-display font-semibold text-gray-900 dark:text-slate-100 mb-2 sm:mb-2.5">
            Зачем поддерживать проект?
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 sm:gap-2 md:gap-3 text-xs sm:text-sm text-gray-900 dark:text-slate-100">
            <div className="flex items-center gap-1.5">
              <span className="text-sm sm:text-base md:text-lg flex-shrink-0">✨</span>
              <span className="break-words"><strong>Развитие функций</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm sm:text-base md:text-lg flex-shrink-0">📚</span>
              <span className="break-words"><strong>Улучшение качества</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm sm:text-base md:text-lg flex-shrink-0">🎯</span>
              <span className="break-words"><strong>Доступность</strong></span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm sm:text-base md:text-lg flex-shrink-0">💬</span>
              <span className="break-words"><strong>Поддержка</strong></span>
            </div>
          </div>
        </div>

        {/* Выбор суммы */}
        <div className="mb-3 sm:mb-4 md:mb-6">
          <h3 className="text-xs sm:text-sm md:text-base font-display font-semibold text-gray-900 dark:text-slate-100 mb-2 sm:mb-3 md:mb-4">
            Выберите сумму поддержки:
          </h3>
          <div className="grid grid-cols-3 sm:grid-cols-5 gap-1.5 sm:gap-2 md:gap-3 mb-3 sm:mb-4 md:mb-5">
            {DONATION_AMOUNTS.map((amount) => (
              <button
                key={amount}
                onClick={() => {
                  setSelectedAmount(amount);
                  setCustomAmount(amount.toString());
                }}
                className={`w-full py-2 sm:py-2.5 md:py-3 rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium transition-all touch-manipulation ${
                  selectedAmount === amount
                    ? 'bg-blue-500 dark:bg-blue-600 text-white shadow-md'
                    : 'bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-slate-100 border border-gray-200 dark:border-slate-700 hover:bg-gray-100 dark:hover:bg-slate-700 active:bg-gray-200 dark:active:bg-slate-600'
                }`}
              >
                <span className="text-yellow-400">⭐</span> {amount}
              </button>
            ))}
          </div>

          {/* Произвольная сумма */}
          <div className="mb-3 sm:mb-4 md:mb-5">
            <label className="block text-xs sm:text-sm font-medium text-gray-900 dark:text-slate-100 mb-1.5 sm:mb-2 md:mb-2.5">
              Или введите свою сумму (от 50 ⭐):
            </label>
            <div className="flex gap-1.5 sm:gap-2 md:gap-3">
              <input
                type="number"
                min="50"
                value={customAmount}
                onChange={(e) => setCustomAmount(e.target.value)}
                placeholder="50"
                className="flex-1 px-2.5 sm:px-3 md:px-4 py-2 sm:py-2.5 md:py-3 rounded-lg sm:rounded-xl text-xs sm:text-sm md:text-base bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white border border-gray-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 dark:focus:ring-blue-400/50"
              />
              <button
                onClick={handleCustomDonate}
                disabled={isProcessing || !customAmount}
                className="px-3 sm:px-4 md:px-6 py-2 sm:py-2.5 md:py-3 rounded-lg sm:rounded-xl text-xs sm:text-sm md:text-base bg-blue-500 dark:bg-blue-600 text-white font-semibold disabled:opacity-50 active:opacity-80 transition-opacity touch-manipulation min-h-[44px] whitespace-nowrap flex items-center justify-center gap-2"
              >
                {/* Иконка замка (вне мини-аппа или когда не авторизован) */}
                {(!inTelegram || !isAuthenticated) && (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                )}
                Поддержать
              </button>
            </div>
          </div>
        </div>

        {/* Информация о способе оплаты */}
        <div className="p-4 sm:p-5 md:p-6 bg-gradient-to-br from-sky-50/80 via-blue-50/80 to-indigo-50/80 dark:from-sky-950/30 dark:via-blue-950/30 dark:to-indigo-950/30 rounded-[1.5rem] sm:rounded-[2rem] border border-sky-200/25 dark:border-sky-800/20 shadow-[0_2px_10px_rgba(0,0,0,0.05)] dark:shadow-[0_2px_10px_rgba(0,0,0,0.25)]">
          <div className="flex items-center gap-1.5 sm:gap-2 mb-1.5 sm:mb-2">
            <span className="text-base sm:text-lg md:text-xl">⭐</span>
            <h3 className="text-xs sm:text-sm md:text-base font-display font-semibold text-gray-900 dark:text-slate-100">
              Telegram Stars
            </h3>
          </div>
          <div className="space-y-0.5 sm:space-y-1 text-xs sm:text-sm text-gray-600 dark:text-slate-400">
            <div>• Оплата из баланса Telegram</div>
            <div>• Безопасная оплата</div>
          </div>
        </div>
      </div>
    </div>
  );
}
