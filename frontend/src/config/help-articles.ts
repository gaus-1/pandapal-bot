/**
 * Конфиг раздела «Помощь»: категории и статьи.
 * Единый источник для /help и /help/<slug>.
 */

export interface HelpCategory {
  id: string;
  titleRu: string;
  titleEn?: string;
  order: number;
}

export type HelpBodyBlock = { type: 'p'; text: string } | { type: 'ul'; items: string[] };

export interface HelpArticle {
  id: string;
  slug: string;
  categoryId: string;
  titleRu: string;
  titleEn?: string;
  descriptionRu: string;
  descriptionEn?: string;
  bodyRu: HelpBodyBlock[];
  bodyEn?: HelpBodyBlock[];
  relatedSlugs?: string[];
  relatedIntentPaths?: { path: string; labelRu: string; labelEn?: string }[];
}

export const HELP_CATEGORIES: HelpCategory[] = [
  { id: 'start', titleRu: 'Начало работы', order: 1 },
  { id: 'homework', titleRu: 'Учёба и домашние задания', order: 2 },
  { id: 'games', titleRu: 'Игры и Моя панда', order: 3 },
  { id: 'premium', titleRu: 'Premium и оплата', order: 4 },
  { id: 'safety', titleRu: 'Безопасность', order: 5 },
];

export const HELP_ARTICLES: HelpArticle[] = [
  {
    id: 'how-to-start',
    slug: 'kak-nachat',
    categoryId: 'start',
    titleRu: 'Как начать пользоваться PandaPal',
    descriptionRu: 'Пошаговая инструкция: как открыть бота, войти в Mini App и задать первый вопрос.',
    bodyRu: [
      { type: 'p', text: 'Откройте Telegram и найдите бота @PandaPalBot или перейдите по ссылке https://t.me/PandaPalBot.' },
      { type: 'p', text: 'Нажмите «Открыть PandaPal». Вам откроется Mini App — веб-приложение внутри Telegram.' },
      { type: 'p', text: 'В Mini App можно сразу задавать вопросы текстом, отправлять фото задания или голосовые сообщения. PandaPal отвечает по школьным предметам для 1–9 класса.' },
      { type: 'ul', items: ['Официальный бот: @PandaPalBot', 'Сайт: pandapal.ru', 'Ничего устанавливать не нужно — всё работает в Telegram.'] },
    ],
    relatedSlugs: ['proverka-dz-po-foto'],
    relatedIntentPaths: [
      { path: '/pomoshch-s-domashkoy-v-telegram', labelRu: 'Помощь с домашкой в Telegram' },
    ],
  },
  {
    id: 'homework-by-photo',
    slug: 'proverka-dz-po-foto',
    categoryId: 'homework',
    titleRu: 'Как отправить фото задания на проверку',
    descriptionRu: 'Можно ли отправить фото домашнего задания и как получить объяснение решения.',
    bodyRu: [
      { type: 'p', text: 'Да, PandaPal принимает фото заданий. В чате Mini App нажмите на иконку скрепки или камеры и выберите изображение с телефона или сделайте снимок.' },
      { type: 'p', text: 'После отправки бот распознает текст и задание и даст пошаговое объяснение или подсказку. Можно уточнять ответы следующими сообщениями.' },
      { type: 'p', text: 'Фото удобно для задач по математике, русскому языку и другим предметам — не нужно перепечатывать условие.' },
    ],
    relatedSlugs: ['kak-nachat'],
    relatedIntentPaths: [
      { path: '/pomoshch-s-domashkoy-v-telegram', labelRu: 'Помощь с домашним заданием в Telegram' },
    ],
  },
  {
    id: 'my-panda',
    slug: 'igra-moya-panda',
    categoryId: 'games',
    titleRu: 'Игра «Моя панда»: как кормить и играть',
    descriptionRu: 'Виртуальный питомец в PandaPal: кормление, игры, сон и достижения.',
    bodyRu: [
      { type: 'p', text: '«Моя панда» — это виртуальный питомец (тамагочи) внутри Mini App. Ребёнок может кормить панду, играть с ней и укладывать спать.' },
      { type: 'p', text: 'Действия ограничены по времени: кормить — раз в 30 минут, играть и «на дерево» — раз в час, уложить спать — раз в 2 часа. Так панда приучает к режиму.' },
      { type: 'p', text: 'Чтобы открыть игру сразу, используйте ссылку: https://t.me/PandaPalBot?startapp=my_panda' },
    ],
    relatedIntentPaths: [
      { path: '/igra-moya-panda', labelRu: 'Подробнее об игре Моя панда' },
    ],
  },
  {
    id: 'premium-and-limits',
    slug: 'premium-i-limity',
    categoryId: 'premium',
    titleRu: 'Premium и лимиты запросов',
    descriptionRu: 'Чем отличается бесплатный режим от Premium и как увеличить лимит запросов.',
    bodyRu: [
      { type: 'p', text: 'В бесплатном режиме действует лимит на количество запросов к AI в день. Подробности и актуальные условия — на странице Premium.' },
      { type: 'p', text: 'Premium-подписка снимает ограничения и даёт расширенные возможности. Оплата только через официальный раздел в Mini App и сервис ЮKassa.' },
      { type: 'p', text: 'Premium активируется только после подтверждения оплаты (webhook). До этого дополнительные запросы сверх лимита недоступны.' },
    ],
    relatedIntentPaths: [
      { path: '/premium', labelRu: 'Страница Premium' },
    ],
  },
  {
    id: 'safety-and-moderation',
    slug: 'bezopasnost-i-moderaciya',
    categoryId: 'safety',
    titleRu: 'Безопасность и модерация в PandaPal',
    descriptionRu: 'Как PandaPal обеспечивает безопасность детей: модерация контента и образовательный фокус.',
    bodyRu: [
      { type: 'p', text: 'PandaPal рассчитан на школьников 1–9 класса. Все ответы проходят модерацию: блокируются нежелательные темы и формулировки.' },
      { type: 'p', text: 'Сервис ориентирован на учёбу и объяснения по школьным предметам. Родители могут контролировать использование через настройки и ограничения в Telegram.' },
      { type: 'p', text: 'Мы не храним голосовые сообщения после обработки запроса и соблюдаем политику конфиденциальности.' },
    ],
    relatedSlugs: ['kak-nachat'],
    relatedIntentPaths: [
      { path: '/bezopasnyy-ai-dlya-detey', labelRu: 'Безопасный ИИ для детей' },
      { path: '/privacy', labelRu: 'Политика конфиденциальности' },
    ],
  },
];

const slugToArticle = new Map<string, HelpArticle>();
HELP_ARTICLES.forEach((a) => slugToArticle.set(a.slug, a));

export function getHelpArticleBySlug(slug: string): HelpArticle | undefined {
  return slugToArticle.get(slug);
}

export function getHelpArticlesByCategory(categoryId: string): HelpArticle[] {
  return HELP_ARTICLES.filter((a) => a.categoryId === categoryId).sort(
    (a, b) => HELP_ARTICLES.indexOf(a) - HELP_ARTICLES.indexOf(b)
  );
}

export function getAllHelpSlugs(): string[] {
  return HELP_ARTICLES.map((a) => a.slug);
}
