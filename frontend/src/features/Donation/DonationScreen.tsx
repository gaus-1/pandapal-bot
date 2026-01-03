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

  const handleDonate = async (amount: number) => {
    if (amount < 50) {
      if (telegram.isInTelegram()) {
        await telegram.showAlert('Минимальная сумма поддержки: 50 ⭐');
      } else {
        alert('Минимальная сумма поддержки: 50 ⭐');
      }
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

      // Если пользователь не авторизован, используем временный ID
      if (!telegramId) {
        if (telegram.isInTelegram()) {
          await telegram.showAlert('Пожалуйста, авторизуйтесь в боте для поддержки проекта');
        } else {
          alert('Пожалуйста, авторизуйтесь в боте для поддержки проекта');
        }
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
        if (telegram.isInTelegram()) {
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
          // Для сайта открываем в новой вкладке
          window.open(data.invoice_link, '_blank');
          if (telegram.isInTelegram()) {
            telegram.showAlert('💳 Откройте страницу оплаты. Спасибо за поддержку!');
          } else {
            alert('💳 Откройте страницу оплаты в новой вкладке. Спасибо за поддержку!');
          }
        }
      } else {
        telegram.notifyError();
        if (telegram.isInTelegram()) {
          await telegram.showAlert('Ошибка создания счета. Попробуй еще раз!');
        } else {
          alert('Ошибка создания счета. Попробуй еще раз!');
        }
      }
    } catch (error) {
      console.error('Ошибка поддержки проекта:', error);
      telegram.notifyError();
      if (telegram.isInTelegram()) {
        await telegram.showAlert('Произошла ошибка. Попробуй позже!');
      } else {
        alert('Произошла ошибка. Попробуй позже!');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCustomDonate = () => {
    const amount = parseInt(customAmount);
    if (isNaN(amount) || amount < 50) {
      if (telegram.isInTelegram()) {
        telegram.showAlert('Введите сумму от 50 ⭐');
      } else {
        alert('Введите сумму от 50 ⭐');
      }
      return;
    }
    handleDonate(amount);
  };

  return (
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4 pb-24">
      {/* Заголовок */}
      <div className="mb-6 text-center">
        <div className="text-6xl mb-3">💝</div>
        <h1 className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-2">
          Поддержать проект PandaPal
        </h1>
        <p className="text-[var(--tg-theme-hint-color)]">
          Ваша поддержка помогает развитию проекта
        </p>
      </div>

      {/* Информация о поддержке */}
      <div className="mb-6 p-4 bg-gradient-to-r from-pink-500/20 to-purple-500/20 rounded-2xl border-2 border-pink-500/30">
        <h2 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-3">
          🌟 Зачем поддерживать проект?
        </h2>
        <ul className="space-y-2 text-sm text-[var(--tg-theme-text-color)]">
          <li>✨ <strong>Развитие функций</strong> — новые возможности для детей</li>
          <li>📚 <strong>Улучшение качества</strong> — лучшие ответы и материалы</li>
          <li>🎯 <strong>Доступность</strong> — бесплатные функции для всех</li>
          <li>💬 <strong>Поддержка</strong> — быстрая помощь пользователям</li>
        </ul>
      </div>

      {/* Выбор суммы */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-3">
          Выберите сумму поддержки:
        </h3>
        <div className="grid grid-cols-3 gap-3 mb-4">
          {DONATION_AMOUNTS.map((amount) => (
            <button
              key={amount}
              onClick={() => setSelectedAmount(amount)}
              className={`py-3 rounded-xl font-medium transition-all ${
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
        <div className="mb-4">
          <label className="block text-sm font-medium text-[var(--tg-theme-text-color)] mb-2">
            Или введите свою сумму (от 50 ⭐):
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              min="50"
              value={customAmount}
              onChange={(e) => setCustomAmount(e.target.value)}
              placeholder="50"
              className="flex-1 px-4 py-2 rounded-xl bg-[var(--tg-theme-hint-color)]/20 text-[var(--tg-theme-text-color)] border border-[var(--tg-theme-hint-color)]/30"
            />
            <button
              onClick={handleCustomDonate}
              disabled={isProcessing || !customAmount}
              className="px-4 py-2 rounded-xl bg-blue-500 text-white font-medium disabled:opacity-50"
            >
              Поддержать
            </button>
          </div>
        </div>

        {/* Кнопка поддержки */}
        <button
          onClick={() => handleDonate(selectedAmount)}
          disabled={isProcessing}
          className="w-full py-3 rounded-xl font-medium bg-gradient-to-r from-pink-500 to-purple-500 text-white shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? 'Обработка...' : `Поддержать проект на ${selectedAmount} ⭐`}
        </button>
      </div>

      {/* Информация о способе оплаты */}
      <div className="p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl border border-[var(--tg-theme-hint-color)]/20">
        <h3 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2 flex items-center gap-2">
          <span>⭐</span>
          <span>Telegram Stars</span>
        </h3>
        <p className="text-sm text-[var(--tg-theme-hint-color)] mb-2">
          Поддержка проекта через Telegram Stars. Это помогает развитию PandaPal!
        </p>
        <ul className="space-y-1 text-xs text-[var(--tg-theme-hint-color)]">
          <li>• Оплата из баланса Telegram</li>
          <li>• Безопасная оплата через Telegram</li>
          <li>• Поддержка развития проекта</li>
          <li>• Возврат средств в течение 72 часов</li>
        </ul>
      </div>
    </div>
  );
}
