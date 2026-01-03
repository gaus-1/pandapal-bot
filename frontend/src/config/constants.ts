/**
 * Константы и конфигурация приложения
 * Здесь хранятся все тексты, URL и настройки для удобства редактирования
 * @module config/constants
 */

import type { Feature, Section, SiteConfig } from '../types';

/**
 * Основная конфигурация сайта
 * При изменении домена или бота — меняйте здесь
 */
export const SITE_CONFIG: SiteConfig = {
  name: 'PandaPal',
  description: 'Безопасный ИИ-друг для твоего ребенка',
  url: 'https://pandapal.ru',
  botUrl: 'https://t.me/PandaPalBot', // Ссылка на Telegram-бота
  logo: {
    src: '/logo.png', // Путь к логотипу (панда с книгой)
    alt: 'PandaPal', // Описание для screen readers
  },
} as const;

/**
 * Список преимуществ продукта
 * Отображаются в виде карточек на главной странице
 */
export const FEATURES: readonly Feature[] = [
  {
    id: 'adaptivity',
    title: 'Адаптивность',
    description: 'Контент подстраивается под возраст и уровень ребенка.',
  },
  {
    id: 'security',
    title: 'Безопасность',
    description: 'Фильтрация контента и защита персональных данных.',
  },
  {
    id: 'gamification',
    title: 'Игра',
    description: 'Геймификация и система достижений для мотивации.',
  },
] as const;

/**
 * Контентные секции
 */
export const SECTIONS: readonly Section[] = [
  {
    id: 'benefits',
    title: 'Для чего это тебе?',
    description:
      'PandaPal — это твой личный помощник в учебе, который всегда готов ответить на вопросы, помочь с домашкой и объяснить сложные темы простыми словами. Задавай вопросы голосом или текстом, отправляй фото задач, и получай понятные объяснения, которые помогут тебе разобраться и запомнить материал. Все ответы адаптированы под твой возраст и класс, чтобы было интересно и понятно.',
  },
] as const;

/**
 * Ссылки в навигации (Header)
 */
export const NAVIGATION_LINKS = [
  { href: '#benefits', label: 'Для чего это тебе?' },
] as const;
