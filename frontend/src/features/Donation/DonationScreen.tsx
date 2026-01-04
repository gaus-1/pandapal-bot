/**
 * Donation Screen - Поддержка проекта через Telegram Stars
 */

import { useState } from 'react';
import { telegram } from '../../services/telegram';
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

  const handleDonate = async (amount: number) => {
    // Telegram Stars работают ТОЛЬКО в Telegram
    if (!inTelegram) {
      alert('⭐ Поддержка звездами доступна только через Telegram Bot.\n\nОткройте @PandaPalBot в Telegram для поддержки проекта.');
      return;
    }

    if (amount < 50) {
      await telegram.showAlert('Минимальная сумма поддержки: 50 ⭐');
      return;
    }

    telegram.hapticFeedback('medium');

    const confirmed = await telegram.showConfirm(
      `Поддержать проект на ${amount} ⭐ Telegram Stars?`
    );

    if (!confirmed) return;

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
        alert('⭐ Поддержка звездами доступна только через Telegram Bot.\n\nОткройте @PandaPalBot в Telegram для поддержки проекта.');
      }
      return;
    }
    handleDonate(amount);
  };

  return (
    <div className="w-full h-full bg-[var(--tg-theme-bg-color)] overflow-y-auto">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8 py-4 sm:py-6 md:py-8 pb-20 sm:pb-24">
      {/* Заголовок */}
      <div className="mb-4 sm:mb-5 text-center">
        <div className="text-5xl sm:text-6xl md:text-7xl mb-2 sm:mb-3">💝</div>
        <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-[var(--tg-theme-text-color)] mb-1.5 sm:mb-2">
          Поддержать проект PandaPal
        </h1>
        <p className="text-xs sm:text-sm md:text-base text-[var(--tg-theme-hint-color)]">
          Ваша поддержка помогает развитию проекта
        </p>
      </div>

      {/* Информация о поддержке */}
      <div className="mb-4 sm:mb-5 p-3 sm:p-4 bg-gradient-to-r from-pink-500/20 to-purple-500/20 rounded-xl sm:rounded-2xl border-2 border-pink-500/30">
        <h2 className="text-base sm:text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2">
          🌟 Зачем поддерживать проект?
        </h2>
        <ul className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 sm:gap-2 text-xs sm:text-sm text-[var(--tg-theme-text-color)]">
          <li>✨ <strong>Развитие функций</strong></li>
          <li>📚 <strong>Улучшение качества</strong></li>
          <li>🎯 <strong>Доступность</strong></li>
          <li>💬 <strong>Поддержка</strong></li>
        </ul>
      </div>

      {/* Выбор суммы */}
      <div className="mb-4 sm:mb-5">
        <h3 className="text-base sm:text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2 sm:mb-3">
          Выберите сумму поддержки:
        </h3>
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 sm:gap-3 mb-3 sm:mb-4">
          {DONATION_AMOUNTS.map((amount) => (
            <button
              key={amount}
              onClick={() => {
                setSelectedAmount(amount);
                setCustomAmount(amount.toString());
              }}
              className={`py-2.5 sm:py-3 md:py-4 rounded-xl sm:rounded-2xl text-xs sm:text-sm md:text-base font-medium transition-all ${
                selectedAmount === amount
                  ? 'bg-gradient-to-r from-pink-500 to-purple-500 text-white shadow-lg'
                  : 'bg-[var(--tg-theme-hint-color)]/20 text-[var(--tg-theme-text-color)]'
              }`}
            >
              {amount} ⭐
            </button>
          ))}
        </div>

        {/* Произвольная сумма */}
        <div className="mb-3 sm:mb-4">
          <label className="block text-xs sm:text-sm md:text-base font-medium text-[var(--tg-theme-text-color)] mb-1.5 sm:mb-2">
            Или введите свою сумму (от 50 ⭐):
          </label>
          <div className="flex gap-2 sm:gap-3">
            <input
              type="number"
              min="50"
              value={customAmount}
              onChange={(e) => setCustomAmount(e.target.value)}
              placeholder="50"
              className="flex-1 px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl sm:rounded-2xl text-sm sm:text-base bg-[var(--tg-theme-hint-color)]/20 text-[var(--tg-theme-text-color)] border border-[var(--tg-theme-hint-color)]/30"
            />
            <button
              onClick={handleCustomDonate}
              disabled={isProcessing || !customAmount}
              className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl sm:rounded-2xl text-sm sm:text-base bg-blue-500 text-white font-medium disabled:opacity-50 active:scale-95"
            >
              Поддержать
            </button>
          </div>
        </div>
      </div>

      {/* Информация о способе оплаты */}
      <div className="p-3 sm:p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-xl sm:rounded-2xl border border-[var(--tg-theme-hint-color)]/20">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-base sm:text-lg">⭐</span>
          <h3 className="text-sm sm:text-base font-semibold text-[var(--tg-theme-text-color)]">
            Telegram Stars
          </h3>
        </div>
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs sm:text-sm text-[var(--tg-theme-hint-color)]">
          <span>• Оплата из баланса Telegram</span>
          <span>• Безопасная оплата</span>
        </div>
      </div>
      </div>
    </div>
  );
}
