/**
 * Premium Screen - Премиум функции с оплатой через ЮKassa
 * С поддержкой Telegram Login Widget для авторизации с веб-сайта
 */

import { useState, useEffect } from 'react';
import { telegram } from '../../services/telegram';
import { TelegramLoginButton } from '../../components/Auth/TelegramLoginButton';
import { useAppStore, type WebUser } from '../../store/appStore';
import type { UserProfile } from '../../services/api';
import { removeSavedPaymentMethod } from '../../services/api';
import { SITE_CONFIG } from '../../config/constants';

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
  const [isRemovingCard, setIsRemovingCard] = useState(false);
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);

  // App store для веб-сайта (Telegram Login Widget)
  const { webUser, isAuthenticated, verifySession, logout, sessionToken } = useAppStore();

  const inTelegram = telegram.isInTelegram();

  // Определяем текущего пользователя (Mini App или Web)
  const currentUser = inTelegram ? miniAppUser : webUser;

  const { setUser } = useAppStore();

  // Проверяем сессию при загрузке (только для веб-сайта)
  useEffect(() => {
    if (!inTelegram) {
      verifySession();
    }
  }, [inTelegram, verifySession]);

  // Автообновление статуса подписки после возврата с оплаты
  useEffect(() => {
    const checkPaymentStatus = async () => {
      // Проверяем наличие параметра payment_id в URL (возврат с ЮKassa)
      const urlParams = new URLSearchParams(window.location.search);
      const paymentId = urlParams.get('payment_id');

      if (paymentId && currentUser) {
        // Обновляем данные пользователя для получения актуального статуса подписки
        try {
          const response = await fetch(`/api/miniapp/user/${currentUser.telegram_id}`);
          if (response.ok) {
            const data = await response.json();
            if (data.success && data.user) {
              console.log('🔍 Обновленные данные пользователя:', data.user);
              console.log('🔍 Active subscription:', data.user.active_subscription);
              console.log('🔍 has_saved_payment_method:', data.user.active_subscription?.has_saved_payment_method);
              setUser(data.user);
              // Убираем payment_id из URL
              window.history.replaceState({}, '', window.location.pathname);
            }
          }
        } catch (error) {
          console.error('Ошибка обновления статуса подписки:', error);
        }
      }
    };

    checkPaymentStatus();
  }, [currentUser, setUser]);

  // Логирование для отладки
  useEffect(() => {
    if (currentUser) {
      console.log('🔍 Premium Screen - currentUser:', currentUser);
      console.log('🔍 is_premium:', currentUser.is_premium);
      console.log('🔍 active_subscription:', (currentUser as UserProfile).active_subscription);
      console.log('🔍 has_saved_payment_method:', (currentUser as UserProfile).active_subscription?.has_saved_payment_method);
      console.log('🔍 auto_renew:', (currentUser as UserProfile).active_subscription?.auto_renew);
    }
  }, [currentUser]);

  // Обработчик отвязки карты
  const handleRemoveCard = async () => {
    if (!currentUser) return;

    setIsRemovingCard(true);
    try {
      await removeSavedPaymentMethod(currentUser.telegram_id);

      // Обновляем данные пользователя через API
      const response = await fetch(`/api/miniapp/user/${currentUser.telegram_id}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.user) {
          setUser(data.user);
        }
      }

      setShowRemoveConfirm(false);

      if (inTelegram) {
        await telegram.showAlert('✅ Карта успешно отвязана. Автоплатежи отключены.');
      } else {
        alert('✅ Карта успешно отвязана. Автоплатежи отключены.');
      }
    } catch (error) {
      console.error('Ошибка отвязки карты:', error);
      if (inTelegram) {
        await telegram.showAlert('❌ Ошибка отвязки карты. Попробуйте позже.');
      } else {
        alert('❌ Ошибка отвязки карты. Попробуйте позже.');
      }
    } finally {
      setIsRemovingCard(false);
    }
  };

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

      if (!response.ok) {
        // Ошибка от сервера
        const errorMessage = data.error || data.message || 'Ошибка создания платежа';
        console.error('Ошибка создания платежа:', errorMessage, data);

        // Специальная обработка ошибки аутентификации
        if (response.status === 401 || errorMessage.includes('аутентификации') || errorMessage.includes('401')) {
          await telegram.showAlert(
            'Ошибка настройки платежей: проверь переменные окружения YOOKASSA_TEST_SECRET_KEY в Railway'
          );
          return;
        }

        if (inTelegram) {
          await telegram.showAlert(
            `❌ Ошибка: ${errorMessage}\n\n` +
            `Если вы пытаетесь купить подписку на месяц или год, ` +
            `автоплатежи еще не активированы. Попробуйте план на неделю.`
          );
        } else {
          alert(`Ошибка: ${errorMessage}`);
        }
        return;
      }

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
        const errorMessage = data.error || 'Не удалось создать платеж';
        console.error('Ошибка создания платежа:', errorMessage, data);

        if (inTelegram) {
          await telegram.showAlert(`❌ ${errorMessage}`);
        } else {
          alert(`Ошибка: ${errorMessage}`);
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
              className="px-4 py-2 text-sm text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-100 active:text-gray-950 dark:active:text-slate-50 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 active:bg-gray-200 dark:active:bg-slate-600"
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

        {/* Сохраненная карта (если есть активная подписка с автоплатежом) */}
        {/* В тестовом режиме ЮKassa карта может не сохраняться (saved=False), но auto_renew=True */}
        {/* Показываем блок если есть активная подписка И (есть saved_payment_method ИЛИ auto_renew включен) */}
        {currentUser?.is_premium &&
         (currentUser as UserProfile)?.active_subscription &&
         ((currentUser as UserProfile).active_subscription?.has_saved_payment_method ||
          (currentUser as UserProfile).active_subscription?.auto_renew) && (
          <div className="mb-4 sm:mb-5 p-3 sm:p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl sm:rounded-2xl border border-blue-200 dark:border-blue-800">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xl sm:text-2xl">💳</span>
                <div>
                  <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-slate-100">
                    Сохраненная карта
                  </h3>
                  <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-400">
                    {(currentUser as UserProfile).active_subscription?.has_saved_payment_method
                      ? 'Автоплатеж включен'
                      : 'Автоплатеж активен'}
                  </p>
                </div>
              </div>
              {/* Показываем кнопку отвязки если есть активная подписка с автоплатежом */}
              {/* В тестовом режиме карта может не сохраняться, но автоплатеж активен, поэтому показываем кнопку */}
              {((currentUser as UserProfile).active_subscription?.has_saved_payment_method ||
                (currentUser as UserProfile).active_subscription?.auto_renew) && (
                <button
                  onClick={() => setShowRemoveConfirm(true)}
                  disabled={isRemovingCard}
                  className="px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 active:text-red-800 dark:active:text-red-200 transition-colors rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 active:bg-red-100 dark:active:bg-red-900/30 disabled:opacity-50 disabled:cursor-not-allowed border border-red-200 dark:border-red-800"
                >
                  {isRemovingCard ? 'Отвязка...' : 'Отвязать'}
                </button>
              )}
            </div>
            <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-400">
              {(currentUser as UserProfile).active_subscription?.has_saved_payment_method
                ? 'Подписка будет автоматически продлеваться. Вы можете отвязать карту в любой момент.'
                : 'Подписка будет автоматически продлеваться. В тестовом режиме карта не сохраняется, но автоплатеж активен.'}
            </p>
          </div>
        )}

        {/* Диалог подтверждения отвязки */}
        {showRemoveConfirm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-slate-800 rounded-xl sm:rounded-2xl p-4 sm:p-6 max-w-sm w-full border border-gray-200 dark:border-slate-700">
              <h3 className="text-base sm:text-lg font-bold text-gray-900 dark:text-slate-100 mb-2">
                Отвязать карту?
              </h3>
              <p className="text-sm sm:text-base text-gray-600 dark:text-slate-400 mb-4">
                После отвязки карты автоплатежи будут отключены. Подписка не будет продлеваться автоматически.
              </p>
              <div className="flex gap-2 sm:gap-3">
                <button
                  onClick={() => setShowRemoveConfirm(false)}
                  disabled={isRemovingCard}
                  className="flex-1 px-4 py-2 text-sm sm:text-base text-gray-700 dark:text-slate-300 hover:text-gray-900 dark:hover:text-slate-100 active:text-gray-950 dark:active:text-slate-50 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 active:bg-gray-200 dark:active:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-300 dark:border-slate-600"
                >
                  Отмена
                </button>
                <button
                  onClick={handleRemoveCard}
                  disabled={isRemovingCard}
                  className="flex-1 px-4 py-2 text-sm sm:text-base text-white bg-red-600 hover:bg-red-700 active:bg-red-800 transition-colors rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isRemovingCard ? 'Отвязка...' : 'Отвязать'}
                </button>
              </div>
            </div>
          </div>
        )}

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
          {PREMIUM_PLANS.map((plan) => {
            return (
              <div
                key={plan.id}
                className={`relative p-3 sm:p-4 md:p-5 rounded-xl sm:rounded-2xl transition-all ${
                  plan.popular
                    ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 dark:from-blue-500/30 dark:to-cyan-500/30 border-2 border-blue-500/50 dark:border-blue-500/70'
                    : 'bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700'
                }`}
              >
                {/* Замочек (всегда вне мини-аппа) */}
                {!inTelegram && (
                  <div className="absolute top-3 right-3 sm:top-4 sm:right-4 text-gray-600 dark:text-slate-400">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="w-6 h-6 sm:w-7 sm:h-7"
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
                  </div>
                )}

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
                  onClick={() => {
                    if (!inTelegram) {
                      window.open(SITE_CONFIG.botUrl, '_blank', 'noopener,noreferrer');
                      return;
                    }
                    handlePurchase(plan);
                  }}
                  disabled={isProcessing && selectedPlan === plan.id}
                  className="w-full py-2.5 sm:py-3 md:py-4 rounded-xl sm:rounded-2xl text-sm sm:text-base font-medium transition-all bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {/* Иконка замка (всегда вне мини-аппа) */}
                  {!inTelegram && (
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
                  {isProcessing && selectedPlan === plan.id
                    ? 'Обработка...'
                    : !inTelegram
                    ? 'Открыть в мини-апп для оплаты'
                    : `Купить Premium за ${plan.priceRub} ₽`}
                </button>
              </div>
            );
          })}
        </div>

        {/* Информация о способах оплаты */}
        <div className="p-3 sm:p-4 bg-gray-50 dark:bg-slate-800 rounded-xl sm:rounded-2xl border border-gray-200 dark:border-slate-700">
          <div className="flex items-center gap-2 mb-1.5">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="w-5 h-5 text-gray-900 dark:text-slate-100"
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
            <h3 className="text-xs sm:text-sm md:text-base font-semibold text-gray-900 dark:text-slate-100">
              Оплата только через Telegram
            </h3>
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs sm:text-sm text-gray-600 dark:text-slate-400 mb-2 sm:mb-3">
            <span>• Visa, Mastercard, МИР</span>
            <span>• СБП</span>
            <span>• Автоматический чек</span>
            <span>• Мгновенная активация</span>
          </div>
          {!inTelegram && !isAuthenticated && (
            <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-gray-200 dark:border-slate-700">
              <p className="text-xs sm:text-sm text-gray-700 dark:text-slate-300 font-medium mb-1 flex items-center gap-1.5">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="w-4 h-4 text-gray-700 dark:text-slate-300"
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
                Для оплаты Premium необходимо войти:
              </p>
              <ul className="text-xs sm:text-sm text-gray-600 dark:text-slate-400 space-y-0.5 sm:space-y-1 ml-4 list-disc">
                <li>Через Telegram мини-приложение (откройте PandaPal в Telegram)</li>
                <li>Или через Telegram бота @pandapal_bot</li>
                <li>Или войдите на сайте через Telegram Login Widget выше</li>
              </ul>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-slate-400 mt-1.5 sm:mt-2 italic">
                💡 Оплата доступна только через Telegram
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
