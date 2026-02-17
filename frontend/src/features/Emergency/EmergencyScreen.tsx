/**
 * Emergency Screen - Экстренные номера для детей
 * РЕАЛЬНЫЕ номера служб спасения России
 */

import { useEffect, useRef } from 'react';
import { telegram } from '../../services/telegram';

interface EmergencyNumber {
  number: string;
  title: string;
  icon: string;
  description: string;
  when: string[];
  color: string;
}

const EMERGENCY_NUMBERS: EmergencyNumber[] = [
  {
    number: '112',
    title: 'Единая служба спасения',
    icon: '🚨',
    description: 'Работает круглосуточно, бесплатно по всей России, даже без SIM-карты',
    when: [
      'Пожар, авария, преступление',
      'Нужна медицинская помощь',
      'Любая экстренная ситуация',
    ],
    color: 'bg-red-500',
  },
  {
    number: '101',
    title: 'Пожарная служба МЧС',
    icon: '🚒',
    description: 'Круглосуточно, бесплатно',
    when: ['Пожар (дым, огонь, запах гари)', 'Люди в опасности', 'Нужна эвакуация'],
    color: 'bg-orange-500',
  },
  {
    number: '102',
    title: 'Полиция',
    icon: '👮',
    description: 'Круглосуточно, бесплатно',
    when: [
      'Преступление (кража, драка, угроза)',
      'Подозрительные люди',
      'Ты в опасности',
      'Потерялся',
    ],
    color: 'bg-blue-500',
  },
  {
    number: '103',
    title: 'Скорая помощь',
    icon: '🚑',
    description: 'Круглосуточно, бесплатно',
    when: [
      'Кто-то без сознания',
      'Сильная боль, травма, кровь',
      'Отравление',
      'Высокая температура',
    ],
    color: 'bg-green-500',
  },
  {
    number: '8-800-2000-122',
    title: 'Детский телефон доверия',
    icon: '💙',
    description: 'Круглосуточно, бесплатно, анонимно',
    when: [
      'Тебя обижают (дома, в школе, в интернете)',
      'Грустно, страшно, одиноко',
      'Проблемы с учебой или друзьями',
      'Нужен совет взрослого',
    ],
    color: 'bg-blue-500',
  },
];

export function EmergencyScreen() {
  const containerRef = useRef<HTMLDivElement>(null);

  // Автоскролл при открытии экрана - показываем начало контента
  useEffect(() => {
    // Задержка для рендеринга контента
    const scrollTimeout = setTimeout(() => {
      if (containerRef.current && typeof containerRef.current.scrollTo === 'function') {
        // Скроллим контейнер в начало (он сам скроллится)
        containerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }, 200);

    return () => clearTimeout(scrollTimeout);
  }, []);

  const handleCall = (number: string, title: string) => {
    telegram.hapticFeedback('heavy');

    // Подтверждение перед звонком
    telegram.showConfirm(`Позвонить: ${number} (${title})?`).then((confirmed) => {
      if (confirmed) {
        // Открываем телефон для звонка
        window.location.href = `tel:${number}`;
        telegram.notifySuccess();
      }
    });
  };

  return (
    <div ref={containerRef} data-emergency-screen className="h-full overflow-y-auto bg-white dark:bg-slate-800 p-4 sm:p-6 md:p-8 max-w-4xl mx-auto pb-24">
      {/* Заголовок */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-display font-bold text-gray-900 dark:text-slate-100 mb-2 sm:mb-3">
          🚨 Экстренные номера
        </h1>
        <p className="font-sans text-xs sm:text-sm md:text-base text-gray-600 dark:text-slate-400">
          В опасности? Звони сразу! Все звонки бесплатные 24/7
        </p>
      </div>

      {/* Список номеров */}
      <div className="space-y-4 sm:space-y-5 md:space-y-6">
        {EMERGENCY_NUMBERS.map((emergency) => (
          <div
            key={emergency.number}
            className="bg-gray-50 dark:bg-slate-800 rounded-2xl sm:rounded-3xl p-4 sm:p-5 md:p-6 shadow-lg border border-gray-200 dark:border-slate-700"
          >
            {/* Заголовок карточки */}
            <div className="flex items-center justify-between mb-3 sm:mb-4">
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="text-3xl sm:text-4xl md:text-5xl">{emergency.icon}</div>
                <div>
                  <h3 className="text-sm sm:text-base md:text-lg font-display font-bold text-gray-900 dark:text-slate-100">
                    {emergency.title}
                  </h3>
                  <p className="font-sans text-xs sm:text-sm md:text-base text-gray-600 dark:text-slate-400">
                    {emergency.description}
                  </p>
                </div>
              </div>
            </div>

            {/* Когда звонить */}
            <div className="mb-3 sm:mb-4">
              <p className="font-display text-sm sm:text-base md:text-lg font-semibold text-gray-900 dark:text-slate-100 mb-2 sm:mb-3">
                Звони, если:
              </p>
              <ul className="space-y-2.5 xs:space-y-3 sm:space-y-3.5 md:space-y-4">
                {emergency.when.map((reason, idx) => (
                  <li
                    key={idx}
                    className="font-sans text-sm sm:text-base md:text-lg text-gray-600 dark:text-slate-400 flex items-baseline gap-2.5 xs:gap-3 sm:gap-3.5 md:gap-4"
                  >
                    <span
                      className="text-blue-500 dark:text-blue-400 font-bold flex-shrink-0 leading-none"
                      style={{
                        fontSize: '0.75em',
                        lineHeight: '1.6',
                        verticalAlign: 'baseline'
                      }}
                    >
                      •
                    </span>
                    <span className="flex-1 leading-relaxed break-words">{reason}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Кнопка звонка */}
            <button
              onClick={() => handleCall(emergency.number, emergency.title)}
              className={`w-full py-3 sm:py-4 md:py-5 rounded-xl sm:rounded-2xl text-sm sm:text-base md:text-lg font-bold text-white transition-all ${emergency.color} hover:opacity-90 active:scale-95 min-h-[44px] sm:min-h-[48px] touch-manipulation`}
              aria-label={`Позвонить в ${emergency.title}: ${emergency.number}`}
            >
              <span aria-hidden="true">📞</span> Позвонить: {emergency.number}
            </button>
          </div>
        ))}
      </div>

      {/* Предупреждение */}
      <div className="mt-6 sm:mt-8 bg-yellow-500/10 dark:bg-yellow-500/20 border-2 border-yellow-500/30 dark:border-yellow-500/50 rounded-2xl sm:rounded-3xl p-4 sm:p-5 md:p-6">
        <p className="font-sans text-sm sm:text-base md:text-lg text-gray-900 dark:text-slate-100 text-center">
          <span className="font-bold">⚠️ Важно:</span> Не паникуй! Говори четко и спокойно. Назови
          свой адрес и опиши ситуацию.
        </p>
      </div>
    </div>
  );
}
