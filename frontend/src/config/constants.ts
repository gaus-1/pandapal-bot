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
    id: 'interactive',
    title: 'Интерактивность',
    description: 'Интерактивные задания и система достижений для мотивации.',
  },
] as const;

/**
 * Контентные секции (Для родителей)
 * Легко добавить новые секции — просто расширьте этот массив
 */
export const SECTIONS: readonly Section[] = [
  {
    id: 'parents', // Используется как якорь (#parents)
    title: 'Для родителей',
    description:
      'Прозрачная аналитика прогресса ребенка, гибкие настройки безопасности и контроль времени обучения. Вы всегда будете в курсе успехов и интересов вашего ребенка.',
  },
] as const;

/**
 * Ссылки в навигации (Header)
 * Автоматически генерируются из SECTIONS, но можно переопределить
 */
export const NAVIGATION_LINKS = [
  { href: '#parents', label: 'Для родителей' },
  { href: '/docs', label: 'Документация' },
  { href: '/api-docs', label: 'API Docs' },
] as const;
