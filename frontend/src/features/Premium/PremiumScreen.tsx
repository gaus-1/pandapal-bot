/**
 * Premium Screen - Премиум функции с оплатой через ЮKassa
 * С поддержкой Telegram Login Widget для авторизации с веб-сайта
 */

import { useState, useEffect } from 'react';
import { telegram } from '../../services/telegram';
import { TelegramLoginButton } from '../../components/Auth/TelegramLoginButton';
import { useAppStore, type WebUser } from '../../store/appStore';
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
      '📊 Детальная аналитика',
      '🏆 Эксклюзивные достижения',
      '💬 Приоритетная поддержка',
      '🎁 Бонусные уроки',
      '🌟 VIP статус',
    ],
  },
];

export function PremiumScreen({ user: miniAppUser }: PremiumScreenProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  // App store для веб-сайта (Telegram Login Widget)
  const { webUser, isAuthenticated, verifySession, logout, sessionToken } = useAppStore();

  const inTelegram = telegram.isInTelegram();

  // Определяем текущего пользователя (Mini App или Web)
  const currentUser = inTelegram ? miniAppUser : webUser;

  // Проверяем сессию при загрузке (только для веб-сайта)
  useEffect(() => {
    if (!inTelegram) {
      verifySession();
    }
  }, [inTelegram, verifySession]);

  const handlePurchase = async (plan: PremiumPlan) => {
    // Проверка авторизации
    if (!currentUser) {
      if (inTelegram) {
        await telegram.showAlert('Ошибка: пользователь не авторизован');
      } else {
        alert('Пожалуйста, войдите через Telegram для оплаты');
      }
      return;
    }

    // Сразу переходим к оплате без confirm (убрано по требованию)
    telegram.hapticFeedback('medium');

    setIsProcessing(true);
    setSelectedPlan(plan.id);

    try {
      // Оплата через ЮKassa (карта/СБП)
      const telegramId = currentUser.telegram_id;

      const response = await fetch('/api/miniapp/premium/create-payment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(webUser && sessionToken
            ? { 'Authorization': `Bearer ${sessionToken}` }
            : {}
          ),
        },
        body: JSON.stringify({
          telegram_id: telegramId,
          plan_id: plan.id,
          user_email: currentUser.username ? `${currentUser.username}@telegram.local` : undefined,
        }),
      });

      const data = await response.json();

      if (data.success && data.confirmation_url) {
        // Открываем страницу оплаты ЮKassa
        if (inTelegram) {
          // В Telegram используем openLink
          telegram.openLink(data.confirmation_url);
        } else {
          // На сайте - прямой переход (не блокируется браузером)
          window.location.href = data.confirmation_url;
        }
      } else {
        if (inTelegram) {
          telegram.notifyError();
        } else {
          alert('Ошибка создания платежа. Попробуй еще раз!');
        }
      }
    } catch (error) {
      console.error('Ошибка покупки:', error);
      if (inTelegram) {
        telegram.notifyError();
      } else {
        alert('Произошла ошибка. Попробуй позже!');
      }
    } finally {
      setIsProcessing(false);
      setSelectedPlan(null);
    }
  };

  const handleAuthSuccess = (user: WebUser) => {
    console.log('✅ Авторизация успешна:', user);
  };

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="w-full h-full bg-white dark:bg-slate-900 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8 py-4 sm:py-6 md:py-8 pb-20 sm:pb-24">

        {/* Telegram Login Widget (только для веб-сайта) */}
        {!inTelegram && !isAuthenticated && (
          <div className="mb-6 p-6 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 dark:from-blue-500/20 dark:to-cyan-500/20 rounded-2xl border-2 border-blue-500/30 dark:border-blue-500/50">
            <h2 className="text-xl font-bold text-gray-900 dark:text-slate-100 mb-3 text-center">
              🔐 Войдите через Telegram
            </h2>
            <p className="text-sm text-gray-600 dark:text-slate-400 mb-4 text-center">
              Для оплаты Premium необходимо авторизоваться через Telegram
            </p>
            <div className="flex justify-center">
              <TelegramLoginButton
                onAuth={handleAuthSuccess}
                buttonSize="large"
              />
            </div>
          </div>
        )}

        {/* Информация о пользователе (для веб-сайта) */}
        {!inTelegram && isAuthenticated && webUser && (
          <div className="mb-4 p-4 bg-gray-50 dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-slate-400">Вы вошли как:</p>
              <p className="text-base font-semibold text-gray-900 dark:text-slate-100">
                👤 {webUser.full_name}
                {webUser.username && (
                  <span className="text-sm text-gray-600 dark:text-slate-400 ml-2">
                    @{webUser.username}
                  </span>
                )}
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100 transition-colors"
            >
              Выйти
            </button>
          </div>
        )}

        {/* Заголовок */}
        <div className="mb-4 sm:mb-5 text-center">
          <div className="text-5xl sm:text-6xl md:text-7xl mb-2 sm:mb-3">👑</div>
          <h1 className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold text-gray-900 dark:text-slate-100 mb-1.5 sm:mb-2">
            PandaPal Premium
          </h1>
          <p className="text-xs sm:text-sm md:text-base text-gray-600 dark:text-slate-400">
            Получи максимум от обучения
          </p>
          {currentUser?.is_premium && (
            <div className="mt-2 px-3 py-1.5 bg-green-500/20 rounded-lg border border-green-500/50">
              <p className="text-xs sm:text-sm text-green-600 dark:text-green-400 font-medium">
                ✅ Premium активен
              </p>
            </div>
          )}
        </div>

        {/* Преимущества */}
        <div className="mb-4 sm:mb-5 p-3 sm:p-4 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-xl sm:rounded-2xl border-2 border-blue-500/30">
            <h2 className="text-sm sm:text-base md:text-lg font-semibold text-gray-900 dark:text-slate-100 mb-2">
              🌟 Что дает Premium?
            </h2>
            <ul className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 sm:gap-2 text-xs sm:text-sm text-gray-900 dark:text-slate-100">
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
                  ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 dark:from-blue-500/30 dark:to-cyan-500/30 border-2 border-blue-500/50 dark:border-blue-500/70'
                  : 'bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700'
              }`}
            >
              {plan.popular && (
                <div className="inline-block px-2 sm:px-3 py-0.5 sm:py-1 bg-blue-500 text-white text-xs font-bold rounded-full mb-1.5 sm:mb-2">
                  🔥 ПОПУЛЯРНЫЙ
                </div>
              )}

              <div className="flex items-center justify-between mb-2 sm:mb-3">
                <div>
                  <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900 dark:text-slate-100">
                    {plan.name}
                  </h3>
                  <p className="text-xs sm:text-sm md:text-base text-gray-600 dark:text-slate-400">
                    {plan.duration}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-100">
                    {plan.priceRub} ₽
                  </div>
                  <div className="text-xs sm:text-sm text-gray-600 dark:text-slate-400">
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
                    className="text-xs sm:text-sm md:text-base text-gray-900 dark:text-slate-100"
                  >
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handlePurchase(plan)}
                disabled={isProcessing && selectedPlan === plan.id || (!inTelegram && !isAuthenticated)}
                className="w-full py-2.5 sm:py-3 md:py-4 rounded-xl sm:rounded-2xl text-sm sm:text-base font-medium transition-all bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isProcessing && selectedPlan === plan.id
                  ? 'Обработка...'
                  : !inTelegram && !isAuthenticated
                  ? '🔐 Войдите для оплаты'
                  : `Купить Premium за ${plan.priceRub} ₽`}
              </button>
            </div>
          ))}
        </div>

        {/* Информация о способах оплаты */}
        <div className="p-3 sm:p-4 bg-gray-50 dark:bg-slate-800 rounded-xl sm:rounded-2xl border border-gray-200 dark:border-slate-700">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-base sm:text-lg">💳</span>
            <h3 className="text-xs sm:text-sm md:text-base font-semibold text-gray-900 dark:text-slate-100">
              Безопасная оплата через ЮKassa
            </h3>
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs sm:text-sm text-gray-600 dark:text-slate-400">
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
