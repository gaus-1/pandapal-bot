/**
 * Типы данных приложения PandaPal
 * Определяет структуру для компонентов и конфигурации
 * @module types
 */

/**
 * Преимущество продукта (карточка в блоке Features)
 */
export interface Feature {
  /** Уникальный идентификатор (для React key) */
  id: string;
  /** Заголовок преимущества */
  title: string;
  /** Описание преимущества */
  description: string;
}

/**
 * Секция контента (Для родителей, Для учителей и т.д.)
 */
export interface Section {
  /** ID секции (используется как якорь #id) */
  id: string;
  /** Заголовок секции */
  title: string;
  /** Описание секции (строка или массив строк для структурированного отображения) */
  description: string | string[];
}

/**
 * Ссылка в навигации
 */
export interface NavigationLink {
  /** URL или якорь (#section) */
  href: string;
  /** Текст ссылки */
  label: string;
  /** Внешняя ссылка (откроется в новой вкладке) */
  external?: boolean;
}

/**
 * Конфигурация сайта (общие настройки)
 */
export interface SiteConfig {
  /** Название продукта */
  name: string;
  /** Краткое описание */
  description: string;
  /** Основной URL сайта */
  url: string;
  /** Ссылка на Telegram-бота */
  botUrl: string;
  /** Настройки логотипа */
  logo: {
    /** Путь к файлу логотипа */
    src: string;
    /** Alt-текст для доступности */
    alt: string;
  };
}
