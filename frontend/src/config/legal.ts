/**
 * Данные оператора персональных данных (по уведомлению РКН).
 * Используются в текстах политик и оферты.
 */

export const OPERATOR = {
  /** Краткое указание для публичных документов: ФИО и почта */
  display: 'Савин В.Е. 79516625803@ya.ru',
} as const;

export const LEGAL_ROUTES = {
  privacy: '/privacy',
  personalData: '/personal-data',
  offer: '/offer',
} as const;

export const FEEDBACK_FORM_URL =
  'https://forms.yandex.ru/cloud/695ba5a6068ff07700f0029a';
