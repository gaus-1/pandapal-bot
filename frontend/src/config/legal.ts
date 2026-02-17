/**
 * Данные оператора персональных данных (по уведомлению РКН).
 * Используются в текстах политик и оферты.
 */

export const OPERATOR = {
  fullName: 'Савин Вячеслав Евгеньевич',
  address: '198334, г. Санкт-Петербург, ул. Добровольцев, д. 62, корп. 2, кв. 69',
  email: '79516625803@ya.ru',
  phone: '89516625803',
  inn: '371104743407',
} as const;

export const LEGAL_ROUTES = {
  privacy: '/privacy',
  personalData: '/personal-data',
  offer: '/offer',
} as const;

export const FEEDBACK_FORM_URL =
  'https://forms.yandex.ru/cloud/695ba5a6068ff07700f0029a';
