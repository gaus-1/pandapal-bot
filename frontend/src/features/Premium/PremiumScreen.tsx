/**
 * Premium Screen - Премиум функции с оплатой через Telegram Stars
 */

import { useState } from 'react';
import { telegram } from '../../services/telegram';
import type { UserProfile } from '../../services/api';

interface PremiumScreenProps {
  user: UserProfile;
}

interface PremiumPlan {
  id: string;
  name: string;
  price: number;
  duration: string;
  features: string[];
  popular?: boolean;
}

const PREMIUM_PLANS: PremiumPlan[] = [
  {
    id: 'week',
    name: 'Неделя',
    price: 50,
    duration: '7 дней',
    features: [
      '✨ Неограниченные AI запросы',
      '📚 Доступ ко всем предметам',
      '🎯 Персональный репетитор',
      '📊 Детальная аналитика',
    ],
  },
  {
    id: 'month',
    name: 'Месяц',
    price: 150,
    duration: '30 дней',
    features: [
      '✨ Неограниченные AI запросы',
      '📚 Доступ ко всем предметам',
      '🎯 Персональный репетитор',
      '📊 Детальная аналитика',
      '🏆 Эксклюзивные достижения',
      '💬 Приоритетная поддержка',
    ],
    popular: true,
  },
  {
    id: 'year',
    name: 'Год',
    price: 999,
    duration: '365 дней',
    features: [
      '✨ Неограниченные AI запросы',
      '📚 Доступ ко всем предметам',
      '🎯 Персональный репетитор',
      '📊 Детальная аналитика',
      '🏆 Эксклюзивные достижения',
      '💬 Приоритетная поддержка',
      '🎁 Бонусные уроки',
      '🌟 VIP статус',
    ],
  },
];

export function PremiumScreen({ user }: PremiumScreenProps) {
  const [isProcessing, setIsProcessing] = useState(false);

  const handlePurchase = async (plan: PremiumPlan) => {
    telegram.hapticFeedback('medium');

    const confirmed = await telegram.showConfirm(
      `Купить премиум на ${plan.duration} за ${plan.price} ⭐ Telegram Stars?`
    );

    if (!confirmed) return;

    setIsProcessing(true);

    try {
      // Создаем invoice на backend
      const response = await fetch('/api/miniapp/premium/create-invoice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          telegram_id: user.telegram_id,
          plan_id: plan.id,
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Открываем форму оплаты Telegram
        telegram.openInvoice(data.invoice_link, (status) => {
          if (status === 'paid') {
            telegram.notifySuccess();
            telegram.showAlert('🎉 Спасибо за покупку! Премиум активирован!');
          } else if (status === 'cancelled') {
            telegram.showAlert('❌ Оплата отменена');
          } else if (status === 'failed') {
            telegram.notifyError();
            telegram.showAlert('❌ Ошибка оплаты. Попробуй еще раз!');
          }
        });
      } else {
        telegram.notifyError();
        await telegram.showAlert('Ошибка создания счета');
      }
    } catch (error) {
      console.error('Ошибка покупки:', error);
      telegram.notifyError();
      await telegram.showAlert('Произошла ошибка. Попробуй позже!');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4 pb-24">
      {/* Заголовок */}
      <div className="mb-6 text-center">
        <div className="text-6xl mb-3">👑</div>
        <h1 className="text-2xl font-bold text-[var(--tg-theme-text-color)] mb-2">
          PandaPal Premium
        </h1>
        <p className="text-[var(--tg-theme-hint-color)]">
          Получи максимум от обучения
        </p>
      </div>

      {/* Преимущества */}
      <div className="mb-6 p-4 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl border-2 border-purple-500/30">
        <h2 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-3">
          🌟 Что дает Premium?
        </h2>
        <ul className="space-y-2 text-sm text-[var(--tg-theme-text-color)]">
          <li>✨ <strong>Неограниченные запросы</strong> к AI без лимитов</li>
          <li>📚 <strong>Все предметы</strong> и уровни сложности</li>
          <li>🎯 <strong>Персональный план</strong> обучения</li>
          <li>📊 <strong>Детальная аналитика</strong> прогресса</li>
          <li>🏆 <strong>Эксклюзивные достижения</strong> и награды</li>
          <li>💬 <strong>Приоритетная поддержка</strong> 24/7</li>
        </ul>
      </div>

      {/* Тарифные планы */}
      <div className="space-y-3 mb-6">
        {PREMIUM_PLANS.map((plan) => (
          <div
            key={plan.id}
            className={`p-4 rounded-2xl transition-all ${
              plan.popular
                ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-2 border-purple-500/50'
                : 'bg-[var(--tg-theme-hint-color)]/10 border border-[var(--tg-theme-hint-color)]/20'
            }`}
          >
            {plan.popular && (
              <div className="inline-block px-3 py-1 bg-purple-500 text-white text-xs font-bold rounded-full mb-2">
                🔥 ПОПУЛЯРНЫЙ
              </div>
            )}

            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-xl font-bold text-[var(--tg-theme-text-color)]">
                  {plan.name}
                </h3>
                <p className="text-sm text-[var(--tg-theme-hint-color)]">
                  {plan.duration}
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-[var(--tg-theme-text-color)]">
                  {plan.price} ⭐
                </div>
                <div className="text-xs text-[var(--tg-theme-hint-color)]">
                  {(plan.price / (plan.id === 'week' ? 7 : plan.id === 'month' ? 30 : 365)).toFixed(1)} ⭐/день
                </div>
              </div>
            </div>

            <ul className="space-y-1 mb-4">
              {plan.features.map((feature, index) => (
                <li
                  key={index}
                  className="text-sm text-[var(--tg-theme-text-color)]"
                >
                  {feature}
                </li>
              ))}
            </ul>

            <button
              onClick={() => handlePurchase(plan)}
              disabled={isProcessing}
              className={`w-full py-3 rounded-xl font-medium transition-all ${
                plan.popular
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg active:scale-95'
                  : 'bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] active:scale-95'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isProcessing ? 'Обработка...' : 'Купить Premium'}
            </button>
          </div>
        ))}
      </div>

      {/* Информация о Telegram Stars */}
      <div className="p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl border border-[var(--tg-theme-hint-color)]/20">
        <h3 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2 flex items-center gap-2">
          <span>⭐</span>
          <span>Telegram Stars</span>
        </h3>
        <p className="text-sm text-[var(--tg-theme-hint-color)] mb-2">
          Безопасная оплата через Telegram. Никаких банковских карт!
        </p>
        <ul className="space-y-1 text-xs text-[var(--tg-theme-hint-color)]">
          <li>• Оплата из баланса Telegram</li>
          <li>• Мгновенная активация Premium</li>
          <li>• Возврат средств в течение 72 часов</li>
          <li>• Поддержка 24/7</li>
        </ul>
      </div>
    </div>
  );
}
