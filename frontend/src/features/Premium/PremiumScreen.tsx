/**
 * Premium Screen - Премиум функции с оплатой через ЮKassa
 * С поддержкой Telegram Login Widget для авторизации с веб-сайта
 */

import { useState, useEffect } from 'react';
import { telegram } from '../../services/telegram';
import { useAppStore } from '../../store/appStore';
import type { UserProfile } from '../../services/api';
import { removeSavedPaymentMethod } from '../../services/api';
import { logger } from '../../utils/logger';

interface PremiumScreenProps {
  user: UserProfile | null;
}

interface PremiumPlan {
  id: string;
  name: string;
  priceRub: number;
  duration: string;
  features: string[];
}

const PREMIUM_PLANS: PremiumPlan[] = [
  {
    id: 'month',
    name: 'Месяц',
    priceRub: 299,
    duration: '30 дней',
    features: [
      '📝 Текст, фото и аудио без ограничений',
      '📚 Все предметы школьной программы без ограничений',
      '📊 Визуализации и графики по школьным предметам',
      '🎨 Генерация изображений',
      '🌍 Русский, английский, немецкий, французский, испанский',
      '🗺️ Карты стран и городов',
      '🏆 Эксклюзивные достижения',
      '📈 Аналитика прогресса',
      '🎮 Игры',
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
              logger.debug('Premium: обновлены данные пользователя');
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
      logger.debug('Premium Screen:', currentUser.is_premium, (currentUser as UserProfile).active_subscription);
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
            `Если вы пытаетесь оформить подписку, ` +
            `автоплатежи еще не активированы.`
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

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="w-full h-full bg-gradient-to-br from-rose-50/40 via-purple-50/40 to-sky-50/40 dark:from-slate-900 dark:via-slate-800 dark:to-slate-800 overflow-y-auto backdrop-blur-sm">
      <div className="max-w-4xl mx-auto px-3 xs:px-4 sm:px-6 md:px-8 py-1 xs:py-1.5 sm:py-2 md:py-3 pb-16 xs:pb-20 sm:pb-24">
        {/* Информация о пользователе (для веб-сайта) */}
        {!inTelegram && isAuthenticated && webUser && (
          <div className="mb-4 p-4 bg-gradient-to-br from-stone-50/90 to-amber-50/90 dark:from-slate-800/90 dark:to-slate-800/90 rounded-[1.5rem] border border-stone-200/25 dark:border-slate-700/40 shadow-[0_2px_8px_rgba(0,0,0,0.04)] dark:shadow-[0_2px_8px_rgba(0,0,0,0.2)] flex items-center justify-between">
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
        <div className="mb-2 xs:mb-3 sm:mb-4 text-center">
          <div className="text-4xl xs:text-5xl sm:text-6xl md:text-7xl mb-1.5 xs:mb-2 sm:mb-3">👑</div>
          <h1 className="text-base xs:text-lg sm:text-xl md:text-2xl lg:text-3xl font-display font-bold text-gray-900 dark:text-slate-100 mb-1 xs:mb-1.5 sm:mb-2">
            PandaPal Premium
          </h1>
          <p className="text-xs xs:text-sm sm:text-base md:text-base text-gray-600 dark:text-slate-400">
            Получи максимум от обучения
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-slate-500">
            В бесплатной версии PandaPal — 30 запросов в месяц. Premium: 299 ₽/мес, безлимитные запросы и все возможности.
          </p>
          {currentUser?.is_premium && (
            <div className="mt-1.5 xs:mt-2 px-2.5 xs:px-3 py-1 xs:py-1.5 bg-green-500/20 rounded-lg border border-green-500/50">
              <p className="text-xs xs:text-sm sm:text-sm text-green-600 dark:text-green-400 font-medium">
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
          <div className="mb-4 sm:mb-5 p-4 sm:p-5 bg-gradient-to-br from-blue-50/85 via-indigo-50/85 to-purple-50/85 dark:from-blue-950/30 dark:via-indigo-950/30 dark:to-purple-950/30 rounded-[1.5rem] sm:rounded-[2rem] border border-blue-200/25 dark:border-blue-800/20 shadow-[0_2px_10px_rgba(0,0,0,0.05)] dark:shadow-[0_2px_10px_rgba(0,0,0,0.25)]">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xl sm:text-2xl">💳</span>
                <div>
                  <h3 className="text-sm sm:text-base font-display font-semibold text-gray-900 dark:text-slate-100">
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
            <div className="bg-gradient-to-br from-white/95 to-stone-50/95 dark:from-slate-800/95 dark:to-slate-800/95 rounded-[2rem] sm:rounded-[2.5rem] p-4 sm:p-6 max-w-sm w-full border border-stone-200/30 dark:border-slate-700/40 shadow-[0_4px_20px_rgba(0,0,0,0.1)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.4)]">
              <h3 className="text-base sm:text-lg font-display font-bold text-gray-900 dark:text-slate-100 mb-2">
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

        {/* Тарифные планы */}
        <div className="space-y-2 xs:space-y-2.5 sm:space-y-3 mb-3 xs:mb-4 sm:mb-5">
          {PREMIUM_PLANS.map((plan) => {
            return (
              <div
                key={plan.id}
                className="relative p-3 xs:p-4 sm:p-5 md:p-6 rounded-[1.25rem] xs:rounded-[1.5rem] sm:rounded-[1.75rem] md:rounded-[2rem] transition-all bg-gradient-to-br from-purple-50/85 via-pink-50/85 to-rose-50/85 dark:from-purple-950/35 dark:via-pink-950/35 dark:to-rose-950/35 border border-purple-200/30 dark:border-purple-800/25 shadow-[0_4px_16px_rgba(139,92,246,0.1)] dark:shadow-[0_4px_16px_rgba(139,92,246,0.2)]"
              >
                <div className="flex items-center justify-between mb-1.5 xs:mb-2 sm:mb-3">
                  <div>
                    <h3 className="text-sm xs:text-base sm:text-lg md:text-xl font-display font-bold text-gray-900 dark:text-slate-100">
                      {plan.name}
                    </h3>
                    <p className="text-[10px] xs:text-xs sm:text-sm md:text-base text-gray-600 dark:text-slate-400">
                      {plan.duration}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-base xs:text-lg sm:text-xl md:text-2xl font-bold text-gray-900 dark:text-slate-100">
                      {plan.priceRub} ₽
                    </div>
                    <div className="text-[10px] xs:text-xs sm:text-sm text-gray-600 dark:text-slate-400">
                      {(plan.priceRub / 30).toFixed(0)} ₽/день
                    </div>
                  </div>
                </div>

                <div className="columns-2 gap-x-1 xs:gap-x-1 sm:gap-x-1.5 mb-3 xs:mb-3.5 sm:mb-4 md:mb-5">
                  {plan.features.map((feature, index) => (
                    <div
                      key={index}
                      className="text-[10px] xs:text-xs sm:text-sm md:text-base text-gray-900 dark:text-slate-100 leading-tight mb-0.5 break-inside-avoid-column"
                    >
                      {feature.trim()}
                    </div>
                  ))}
                </div>

                {inTelegram ? (
                  <button
                    onClick={() => handlePurchase(plan)}
                    disabled={isProcessing && selectedPlan === plan.id}
                    className="w-full mt-2 xs:mt-2.5 sm:mt-3 py-2 xs:py-2.5 sm:py-3 md:py-4 rounded-lg xs:rounded-xl sm:rounded-2xl text-xs xs:text-sm sm:text-base font-medium transition-all bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5 xs:gap-2 min-h-[44px] sm:min-h-[48px] touch-manipulation"
                  >
                    {isProcessing && selectedPlan === plan.id
                      ? 'Обработка...'
                      : `Premium за ${plan.priceRub} ₽`}
                  </button>
                ) : (
                  <a
                    href={`https://t.me/PandaPalBot?start=premium_${plan.id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full mt-2 xs:mt-2.5 sm:mt-3 py-2 xs:py-2.5 sm:py-3 md:py-4 rounded-lg xs:rounded-xl sm:rounded-2xl text-xs xs:text-sm sm:text-base font-medium transition-all bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg active:scale-95 hover:shadow-xl flex items-center justify-center gap-1.5 xs:gap-2 min-h-[40px] xs:min-h-[44px]"
                  >
                    {/* Иконка замка только на сайте (в Mini App без замка) */}
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
                    Premium за {plan.priceRub} ₽
                  </a>
                )}
              </div>
            );
          })}
        </div>

        {/* Информация о способах оплаты */}
        <div className="p-4 sm:p-5 md:p-6 bg-gradient-to-br from-slate-50/90 via-gray-50/90 to-zinc-50/90 dark:from-slate-800/90 dark:to-slate-800/90 rounded-[1.5rem] sm:rounded-[2rem] border border-slate-200/25 dark:border-slate-700/40 shadow-[0_2px_10px_rgba(0,0,0,0.05)] dark:shadow-[0_2px_10px_rgba(0,0,0,0.25)]">
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
            <h3 className="text-xs sm:text-sm md:text-base font-display font-semibold text-gray-900 dark:text-slate-100">
              Оплата только через Telegram
            </h3>
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs sm:text-sm text-gray-600 dark:text-slate-400 mb-2 sm:mb-3">
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
