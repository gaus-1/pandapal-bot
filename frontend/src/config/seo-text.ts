/**
 * Канонические тексты для AEO/SEO: единый источник формулировок о PandaPal.
 * Использовать в index.html (meta, JSON-LD, answer-first), Hero, README.
 */

/** Каноническое определение PandaPal (RU), 1–2 предложения */
export const CANONICAL_DESCRIPTION_RU =
  'PandaPal — безопасный AI-помощник и робот-репетитор для школьников 1–9 класса в формате Telegram Mini App. Обработка текста фото и аудио. Помогает с уроками по всем предметам, работает 24/7. Модерация контента и родительский контроль.';

/** Каноническое определение PandaPal (EN) */
export const CANONICAL_DESCRIPTION_EN =
  'PandaPal is a safe AI assistant and tutor bot for students in grades 1–9 as a Telegram Mini App. Text, photo and voice processing. Homework help in all subjects, 24/7. Content moderation and parental controls.';

/** Короткий слоган для Hero (RU) */
export const HERO_TAGLINE_RU = 'Адаптивное, игровое, безопасное обучение и общение для детей 1–9 классов';

/** Короткий слоган для Hero (EN) */
export const HERO_TAGLINE_EN = 'Adaptive, playful, safe learning and interaction for children in grades 1–9';

/** Лендинг «Моя панда»: заголовок (RU) */
export const PANDA_PET_PAGE_TITLE_RU = 'Моя панда — виртуальный питомец в PandaPal';

/** Лендинг «Моя панда»: описание (RU), answer-first до ~50 слов */
export const PANDA_PET_DESCRIPTION_RU =
  '«Моя панда» — виртуальный питомец (тамагочи) в PandaPal: кормите, играйте, укладывайте спать. Реакции панды и достижения. Доступ в Mini App по боту @PandaPalBot.';

/** Прямая ссылка на игру «Моя панда» в Mini App (deep link) */
export const PANDA_PET_DIRECT_LINK = 'https://t.me/PandaPalBot?startapp=my_panda';

/** FAQ для страницы «Моя панда» */
export const PANDA_PET_FAQ_RU: { question: string; answer: string }[] = [
  {
    question: 'Что такое «Моя панда» в PandaPal?',
    answer:
      'Виртуальный питомец в формате тамагочи: ребёнок кормит панду, играет с ней и укладывает спать. Реакции панды зависят от голода, настроения и энергии. Доступ в Mini App по боту @PandaPalBot.',
  },
  {
    question: 'Как кормить и играть с пандой?',
    answer:
      'В Mini App откройте раздел «Моя панда»: «Покормить» — каждые 30 мин, «Играть» и «На дерево»/«Упасть» — раз в час, «Уложить спать» — раз в 2 часа, «В туалет» — раз в 20 мин. Панда показывает разные эмоции в зависимости от голода, настроения и энергии.',
  },
  {
    question: 'Для какого возраста подходит «Моя панда»?',
    answer:
      'Виртуальный питомец рассчитан на детей младшего и среднего школьного возраста. Игра бесплатна и доступна всем пользователям бота PandaPal.',
  },
  {
    question: 'Как открыть игру Моя панда сразу?',
    answer:
      'Прямая ссылка на тамагочи в Telegram: https://t.me/PandaPalBot?startapp=my_panda — откроет бота и сразу экран с виртуальной пандой.',
  },
];
