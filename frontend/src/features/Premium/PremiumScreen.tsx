/**
 * Premium Screen - Премиум функции с оплатой через ЮKassa
 */

import { useState } from 'react';
import { telegram } from '../../services/telegram';
import type { UserProfile } from '../../services/api';

interface PremiumScreenProps {
  user: UserProfile | null;
}

interface PremiumPlan {
  id: string;
  name: string;
  priceRub: number;
  duration: string;
  features: string[];
  popular?: boolean;
}

const PREMIUM_PLANS: PremiumPlan[] = [
  {
    id: 'week',
    name: 'Неделя',
    priceRub: 99,
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
    priceRub: 399,
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
    priceRub: 2990,
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
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  const handlePurchase = async (plan: PremiumPlan) => {
    telegram.hapticFeedback('medium');

    const confirmed = await telegram.showConfirm(
      `Купить премиум на ${plan.duration} за ${plan.priceRub} ₽?`
    );

    if (!confirmed) return;

    setIsProcessing(true);
    setSelectedPlan(plan.id);

    try {
      // Оплата через ЮKassa (карта/СБП)
      const telegramId = user?.telegram_id;
      if (!telegramId) {
        if (telegram.isInTelegram()) {
          await telegram.showAlert('Пожалуйста, авторизуйтесь в боте для покупки Premium');
        } else {
          alert('Пожалуйста, авторизуйтесь в боте для покупки Premium');
        }
        return;
      }

      const response = await fetch('/api/miniapp/premium/create-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          telegram_id: telegramId,
          plan_id: plan.id,
          user_email: user?.username ? `${user.username}@telegram.local` : undefined,
        }),
      });

      const data = await response.json();

      if (data.success && data.confirmation_url) {
        // Открываем страницу оплаты ЮKassa
        // В Telegram Mini App используем openLink, в браузере - window.open
        if (telegram.isInTelegram()) {
          telegram.openLink(data.confirmation_url);
          telegram.showAlert(
            '💳 Откройте страницу оплаты. После успешной оплаты Premium активируется автоматически!'
          );
        } else {
          window.open(data.confirmation_url, '_blank');
          telegram.showAlert(
            '💳 Откройте страницу оплаты в новой вкладке. После успешной оплаты Premium активируется автоматически!'
          );
        }
      } else {
        telegram.notifyError();
        await telegram.showAlert('Ошибка создания платежа. Попробуй еще раз!');
      }
    } catch (error) {
      console.error('Ошибка покупки:', error);
      telegram.notifyError();
      await telegram.showAlert('Произошла ошибка. Попробуй позже!');
    } finally {
      setIsProcessing(false);
      setSelectedPlan(null);
    }
  };

  return (
    <div className="w-full h-full bg-[var(--tg-theme-bg-color)] overflow-y-auto">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8 py-4 sm:py-6 md:py-8 pb-20 sm:pb-24">
      {/* Заголовок */}
      <div className="mb-4 sm:mb-5 text-center">
        <div className="text-5xl sm:text-6xl md:text-7xl mb-2 sm:mb-3">👑</div>
        <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-[var(--tg-theme-text-color)] mb-1.5 sm:mb-2">
          PandaPal Premium
        </h1>
        <p className="text-xs sm:text-sm md:text-base text-[var(--tg-theme-hint-color)]">
          Получи максимум от обучения
        </p>
        {user?.is_premium && user.premium_days_left !== undefined && (
          <div className="mt-2 px-3 py-1.5 bg-green-500/20 rounded-lg border border-green-500/50">
            <p className="text-xs sm:text-sm text-green-600 dark:text-green-400 font-medium">
              ✅ Premium активен еще {user.premium_days_left} {user.premium_days_left === 1 ? 'день' : user.premium_days_left < 5 ? 'дня' : 'дней'}
            </p>
          </div>
        )}
      </div>

      {/* Преимущества */}
      <div className="mb-4 sm:mb-5 p-3 sm:p-4 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl sm:rounded-2xl border-2 border-purple-500/30">
        <h2 className="text-base sm:text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2">
          🌟 Что дает Premium?
        </h2>
        <ul className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 sm:gap-2 text-xs sm:text-sm text-[var(--tg-theme-text-color)]">
          <li>✨ <strong>Неограниченные запросы</strong></li>
          <li>📚 <strong>Все предметы</strong></li>
          <li>🎯 <strong>Персональный план</strong></li>
          <li>📊 <strong>Детальная аналитика</strong></li>
          <li>🏆 <strong>Эксклюзивные достижения</strong></li>
          <li>💬 <strong>Приоритетная поддержка</strong></li>
        </ul>
      </div>

      {/* Тарифные планы */}
      <div className="space-y-2.5 sm:space-y-3 mb-4 sm:mb-5">
        {PREMIUM_PLANS.map((plan) => (
          <div
            key={plan.id}
            className={`p-3 sm:p-4 md:p-5 rounded-xl sm:rounded-2xl transition-all ${
              plan.popular
                ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-2 border-purple-500/50'
                : 'bg-[var(--tg-theme-hint-color)]/10 border border-[var(--tg-theme-hint-color)]/20'
            }`}
          >
            {plan.popular && (
              <div className="inline-block px-2 sm:px-3 py-0.5 sm:py-1 bg-purple-500 text-white text-xs font-bold rounded-full mb-1.5 sm:mb-2">
                🔥 ПОПУЛЯРНЫЙ
              </div>
            )}

            <div className="flex items-center justify-between mb-2 sm:mb-3">
              <div>
                <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-[var(--tg-theme-text-color)]">
                  {plan.name}
                </h3>
                <p className="text-xs sm:text-sm md:text-base text-[var(--tg-theme-hint-color)]">
                  {plan.duration}
                </p>
              </div>
              <div className="text-right">
                <div className="text-xl sm:text-2xl md:text-3xl font-bold text-[var(--tg-theme-text-color)]">
                  {plan.priceRub} ₽
                </div>
                <div className="text-xs sm:text-sm text-[var(--tg-theme-hint-color)]">
                  {(() => {
                    const days = plan.id === 'week' ? 7 : plan.id === 'month' ? 30 : 365;
                    return `${(plan.priceRub / days).toFixed(0)} ₽/день`;
                  })()}
                </div>
              </div>
            </div>

            <ul className="grid grid-cols-2 gap-1 sm:gap-1.5 mb-3 sm:mb-4">
              {plan.features.map((feature, index) => (
                <li
                  key={index}
                  className="text-xs sm:text-sm md:text-base text-[var(--tg-theme-text-color)]"
                >
                  {feature}
                </li>
              ))}
            </ul>

            <button
              onClick={() => handlePurchase(plan)}
              disabled={isProcessing && selectedPlan === plan.id}
              className="w-full py-2.5 sm:py-3 md:py-4 rounded-xl sm:rounded-2xl text-sm sm:text-base font-medium transition-all bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing && selectedPlan === plan.id
                ? 'Обработка...'
                : `Купить Premium за ${plan.priceRub} ₽`}
            </button>
          </div>
        ))}
      </div>

      {/* Информация о способах оплаты */}
      <div className="p-3 sm:p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-xl sm:rounded-2xl border border-[var(--tg-theme-hint-color)]/20">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-base sm:text-lg">💳</span>
          <h3 className="text-sm sm:text-base font-semibold text-[var(--tg-theme-text-color)]">
            Безопасная оплата через ЮKassa
          </h3>
        </div>
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs sm:text-sm text-[var(--tg-theme-hint-color)]">
          <span>• Visa, Mastercard, МИР</span>
          <span>• СБП</span>
          <span>• Автоматический чек</span>
          <span>• Мгновенная активация</span>
        </div>
      </div>
      </div>
    </div>
  );
}
