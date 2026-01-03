/**
 * Premium Screen - Премиум функции с оплатой через Telegram Stars и ЮKassa
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
  priceStars: number;
  priceRub: number;
  duration: string;
  features: string[];
  popular?: boolean;
}

const PREMIUM_PLANS: PremiumPlan[] = [
  {
    id: 'week',
    name: 'Неделя',
    priceStars: 50,
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
    priceStars: 150,
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
    priceStars: 999,
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

type PaymentMethod = 'stars' | 'card';

export function PremiumScreen({ user }: PremiumScreenProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<PaymentMethod>('card');
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  const handlePurchase = async (plan: PremiumPlan, paymentMethod: PaymentMethod) => {
    telegram.hapticFeedback('medium');

    const price = paymentMethod === 'stars' ? plan.priceStars : plan.priceRub;
    const priceText =
      paymentMethod === 'stars' ? `${price} ⭐ Telegram Stars` : `${price} ₽`;

    const confirmed = await telegram.showConfirm(
      `Купить премиум на ${plan.duration} за ${priceText}?`
    );

    if (!confirmed) return;

    setIsProcessing(true);
    setSelectedPlan(plan.id);

    try {
      if (paymentMethod === 'stars') {
        // Оплата через Telegram Stars
        const response = await fetch('/api/miniapp/premium/create-invoice', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            telegram_id: user.telegram_id,
            plan_id: plan.id,
            payment_method: 'stars',
          }),
        });

        const data = await response.json();

        if (data.success) {
          telegram.openInvoice(data.invoice_link, (status) => {
            if (status === 'paid') {
              telegram.notifySuccess();
              telegram.showAlert('🎉 Спасибо за покупку! Премиум активирован!');
              // Обновляем страницу для отображения нового статуса
              setTimeout(() => window.location.reload(), 1000);
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
      } else {
        // Оплата через ЮKassa (карта/СБП)
        const response = await fetch('/api/miniapp/premium/create-payment', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            telegram_id: user.telegram_id,
            plan_id: plan.id,
            user_email: user.username ? `${user.username}@telegram.local` : undefined,
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
        {user.is_premium && user.premium_days_left !== undefined && (
          <div className="mt-3 px-4 py-2 bg-green-500/20 rounded-xl border border-green-500/50">
            <p className="text-sm text-green-600 dark:text-green-400 font-medium">
              ✅ Premium активен еще {user.premium_days_left} {user.premium_days_left === 1 ? 'день' : user.premium_days_left < 5 ? 'дня' : 'дней'}
            </p>
          </div>
        )}
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
                  {selectedPaymentMethod === 'stars' ? `${plan.priceStars} ⭐` : `${plan.priceRub} ₽`}
                </div>
                <div className="text-xs text-[var(--tg-theme-hint-color)]">
                  {(() => {
                    const days = plan.id === 'week' ? 7 : plan.id === 'month' ? 30 : 365;
                    if (selectedPaymentMethod === 'stars') {
                      return `${(plan.priceStars / days).toFixed(1)} ⭐/день`;
                    }
                    return `${(plan.priceRub / days).toFixed(0)} ₽/день`;
                  })()}
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

            {/* Выбор способа оплаты */}
            <div className="mb-3 flex gap-2">
              <button
                onClick={() => setSelectedPaymentMethod('card')}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedPaymentMethod === 'card'
                    ? 'bg-blue-500 text-white'
                    : 'bg-[var(--tg-theme-hint-color)]/20 text-[var(--tg-theme-text-color)]'
                }`}
              >
                💳 Карта/СБП
              </button>
              <button
                onClick={() => setSelectedPaymentMethod('stars')}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedPaymentMethod === 'stars'
                    ? 'bg-yellow-500 text-white'
                    : 'bg-[var(--tg-theme-hint-color)]/20 text-[var(--tg-theme-text-color)]'
                }`}
              >
                ⭐ Stars
              </button>
            </div>

            <button
              onClick={() => handlePurchase(plan, selectedPaymentMethod)}
              disabled={isProcessing && selectedPlan === plan.id}
              className={`w-full py-3 rounded-xl font-medium transition-all ${
                plan.popular
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg active:scale-95'
                  : 'bg-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-text-color)] active:scale-95'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isProcessing && selectedPlan === plan.id
                ? 'Обработка...'
                : `Купить Premium за ${selectedPaymentMethod === 'stars' ? `${plan.priceStars} ⭐` : `${plan.priceRub} ₽`}`}
            </button>
          </div>
        ))}
      </div>

      {/* Информация о способах оплаты */}
      <div className="space-y-3">
        <div className="p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl border border-[var(--tg-theme-hint-color)]/20">
          <h3 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2 flex items-center gap-2">
            <span>💳</span>
            <span>Карта или СБП</span>
          </h3>
          <p className="text-sm text-[var(--tg-theme-hint-color)] mb-2">
            Безопасная оплата через ЮKassa. Поддержка всех банковских карт и СБП!
          </p>
          <ul className="space-y-1 text-xs text-[var(--tg-theme-hint-color)]">
            <li>• Оплата картой Visa, Mastercard, МИР</li>
            <li>• Быстрая оплата через СБП</li>
            <li>• Автоматическая отправка чека</li>
            <li>• Мгновенная активация Premium</li>
          </ul>
        </div>

        <div className="p-4 bg-[var(--tg-theme-hint-color)]/10 rounded-2xl border border-[var(--tg-theme-hint-color)]/20">
          <h3 className="text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2 flex items-center gap-2">
            <span>⭐</span>
            <span>Telegram Stars (поддержка проекта)</span>
          </h3>
          <p className="text-sm text-[var(--tg-theme-hint-color)] mb-2">
            Поддержи проект через Telegram Stars. Это помогает развитию PandaPal!
          </p>
          <ul className="space-y-1 text-xs text-[var(--tg-theme-hint-color)]">
            <li>• Оплата из баланса Telegram</li>
            <li>• Мгновенная активация Premium</li>
            <li>• Поддержка развития проекта</li>
            <li>• Возврат средств в течение 72 часов</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
