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
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4 sm:p-6 md:p-8 pb-24 sm:pb-28 max-w-4xl mx-auto">
      {/* Заголовок */}
      <div className="mb-6 sm:mb-8 text-center">
        <div className="text-6xl sm:text-7xl md:text-8xl mb-3 sm:mb-4">👑</div>
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-[var(--tg-theme-text-color)] mb-2 sm:mb-3">
          PandaPal Premium
        </h1>
        <p className="text-sm sm:text-base md:text-lg text-[var(--tg-theme-hint-color)]">
          Получи максимум от обучения
        </p>
        {user?.is_premium && user.premium_days_left !== undefined && (
          <div className="mt-3 px-4 py-2 bg-green-500/20 rounded-xl border border-green-500/50">
            <p className="text-sm text-green-600 dark:text-green-400 font-medium">
              ✅ Premium активен еще {user.premium_days_left} {user.premium_days_left === 1 ? 'день' : user.premium_days_left < 5 ? 'дня' : 'дней'}
            </p>
          </div>
        )}
      </div>

      {/* Преимущества */}
      <div className="mb-6 sm:mb-8 p-4 sm:p-5 md:p-6 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl sm:rounded-3xl border-2 border-purple-500/30">
        <h2 className="text-lg sm:text-xl md:text-2xl font-semibold text-[var(--tg-theme-text-color)] mb-3 sm:mb-4">
          🌟 Что дает Premium?
        </h2>
        <ul className="space-y-2 sm:space-y-3 text-sm sm:text-base md:text-lg text-[var(--tg-theme-text-color)]">
          <li>✨ <strong>Неограниченные запросы</strong> к AI без лимитов</li>
          <li>📚 <strong>Все предметы</strong> и уровни сложности</li>
          <li>🎯 <strong>Персональный план</strong> обучения</li>
          <li>📊 <strong>Детальная аналитика</strong> прогресса</li>
          <li>🏆 <strong>Эксклюзивные достижения</strong> и награды</li>
          <li>💬 <strong>Приоритетная поддержка</strong> 24/7</li>
        </ul>
      </div>

      {/* Тарифные планы */}
      <div className="space-y-3 sm:space-y-4 md:space-y-5 mb-6 sm:mb-8">
        {PREMIUM_PLANS.map((plan) => (
          <div
            key={plan.id}
            className={`p-4 sm:p-5 md:p-6 rounded-2xl sm:rounded-3xl transition-all ${
              plan.popular
                ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-2 border-purple-500/50'
                : 'bg-[var(--tg-theme-hint-color)]/10 border border-[var(--tg-theme-hint-color)]/20'
            }`}
          >
            {plan.popular && (
              <div className="inline-block px-3 sm:px-4 py-1 sm:py-1.5 bg-purple-500 text-white text-xs sm:text-sm font-bold rounded-full mb-2 sm:mb-3">
                🔥 ПОПУЛЯРНЫЙ
              </div>
            )}

            <div className="flex items-center justify-between mb-3 sm:mb-4">
              <div>
                <h3 className="text-xl sm:text-2xl md:text-3xl font-bold text-[var(--tg-theme-text-color)]">
                  {plan.name}
                </h3>
                <p className="text-sm sm:text-base md:text-lg text-[var(--tg-theme-hint-color)]">
                  {plan.duration}
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-[var(--tg-theme-text-color)]">
                  {plan.priceRub} ₽
                </div>
                <div className="text-xs sm:text-sm md:text-base text-[var(--tg-theme-hint-color)]">
                  {(() => {
                    const days = plan.id === 'week' ? 7 : plan.id === 'month' ? 30 : 365;
                    return `${(plan.priceRub / days).toFixed(0)} ₽/день`;
                  })()}
                </div>
              </div>
            </div>

            <ul className="space-y-1 sm:space-y-2 mb-4 sm:mb-5">
              {plan.features.map((feature, index) => (
                <li
                  key={index}
                  className="text-sm sm:text-base md:text-lg text-[var(--tg-theme-text-color)]"
                >
                  {feature}
                </li>
              ))}
            </ul>

            <button
              onClick={() => handlePurchase(plan)}
              disabled={isProcessing && selectedPlan === plan.id}
              className={`w-full py-3 sm:py-4 md:py-5 rounded-xl sm:rounded-2xl text-sm sm:text-base md:text-lg font-medium transition-all ${
                plan.popular
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg active:scale-95'
                  : 'bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] active:scale-95'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isProcessing && selectedPlan === plan.id
                ? 'Обработка...'
                : `Купить Premium за ${plan.priceRub} ₽`}
            </button>
          </div>
        ))}
      </div>

      {/* Информация о способах оплаты */}
      <div className="p-4 sm:p-5 md:p-6 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl sm:rounded-3xl border border-[var(--tg-theme-hint-color)]/20">
        <h3 className="text-lg sm:text-xl md:text-2xl font-semibold text-[var(--tg-theme-text-color)] mb-2 sm:mb-3 flex items-center gap-2">
          <span>💳</span>
          <span>Безопасная оплата через ЮKassa</span>
        </h3>
        <p className="text-sm sm:text-base md:text-lg text-[var(--tg-theme-hint-color)] mb-2 sm:mb-3">
          Поддержка всех банковских карт и СБП!
        </p>
        <ul className="space-y-1 sm:space-y-2 text-xs sm:text-sm md:text-base text-[var(--tg-theme-hint-color)]">
          <li>• Оплата картой Visa, Mastercard, МИР</li>
          <li>• Быстрая оплата через СБП</li>
          <li>• Автоматическая отправка чека</li>
          <li>• Мгновенная активация Premium</li>
        </ul>
      </div>
    </div>
  );
}
