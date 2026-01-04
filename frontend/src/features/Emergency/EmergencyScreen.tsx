/**
 * Emergency Screen - Экстренные номера для детей
 * РЕАЛЬНЫЕ номера служб спасения России
 */

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
    color: 'bg-purple-500',
  },
];

export function EmergencyScreen() {
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
    <div className="min-h-screen bg-[var(--tg-theme-bg-color)] p-4 sm:p-6 md:p-8 max-w-4xl mx-auto">
      {/* Заголовок */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-[var(--tg-theme-text-color)] mb-2 sm:mb-3">
          🚨 Экстренные номера
        </h1>
        <p className="text-sm sm:text-base md:text-lg text-[var(--tg-theme-hint-color)]">
          В опасности? Звони сразу! Все звонки бесплатные 24/7
        </p>
      </div>

      {/* Список номеров */}
      <div className="space-y-4 sm:space-y-5 md:space-y-6">
        {EMERGENCY_NUMBERS.map((emergency) => (
          <div
            key={emergency.number}
            className="bg-[var(--tg-theme-secondary-bg-color)] rounded-2xl sm:rounded-3xl p-4 sm:p-5 md:p-6 shadow-lg"
          >
            {/* Заголовок карточки */}
            <div className="flex items-center justify-between mb-3 sm:mb-4">
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="text-3xl sm:text-4xl md:text-5xl">{emergency.icon}</div>
                <div>
                  <h3 className="text-base sm:text-lg md:text-xl font-bold text-[var(--tg-theme-text-color)]">
                    {emergency.title}
                  </h3>
                  <p className="text-sm sm:text-base md:text-lg text-[var(--tg-theme-hint-color)]">
                    {emergency.description}
                  </p>
                </div>
              </div>
            </div>

            {/* Когда звонить */}
            <div className="mb-3 sm:mb-4">
              <p className="text-sm sm:text-base md:text-lg font-semibold text-[var(--tg-theme-text-color)] mb-2 sm:mb-3">
                Звони, если:
              </p>
              <ul className="space-y-1 sm:space-y-2">
                {emergency.when.map((reason, idx) => (
                  <li
                    key={idx}
                    className="text-sm sm:text-base md:text-lg text-[var(--tg-theme-hint-color)] flex items-start gap-2"
                  >
                    <span className="text-[var(--tg-theme-link-color)] font-bold">•</span>
                    {reason}
                  </li>
                ))}
              </ul>
            </div>

            {/* Кнопка звонка */}
            <button
              onClick={() => handleCall(emergency.number, emergency.title)}
              className={`w-full py-3 sm:py-4 md:py-5 rounded-xl sm:rounded-2xl text-sm sm:text-base md:text-lg font-bold text-white transition-all ${emergency.color} hover:opacity-90 active:scale-95`}
              aria-label={`Позвонить в ${emergency.title}: ${emergency.number}`}
            >
              <span aria-hidden="true">📞</span> Позвонить: {emergency.number}
            </button>
          </div>
        ))}
      </div>

      {/* Предупреждение */}
      <div className="mt-6 sm:mt-8 bg-yellow-500/10 border-2 border-yellow-500/30 rounded-2xl sm:rounded-3xl p-4 sm:p-5 md:p-6">
        <p className="text-sm sm:text-base md:text-lg text-[var(--tg-theme-text-color)] text-center">
          <span className="font-bold">⚠️ Важно:</span> Не паникуй! Говори четко и спокойно. Назови
          свой адрес и опиши ситуацию.
        </p>
      </div>
    </div>
  );
}
