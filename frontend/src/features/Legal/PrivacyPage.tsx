/**
 * Политика конфиденциальности.
 * Соответствует уведомлению РКН: цели — оказание услуг, обратная связь.
 */

import React from 'react';
import { LegalPageLayout } from './LegalPageLayout';
import { OPERATOR } from '../../config/legal';
import { SITE_CONFIG } from '../../config/constants';

export const PrivacyPage: React.FC = React.memo(() => {
  return (
    <LegalPageLayout
      title="Политика конфиденциальности"
      subtitle="Как мы защищаем твои данные"
    >
      <p>
        Настоящая политика конфиденциальности определяет порядок обработки и защиты персональных данных пользователей сервиса {SITE_CONFIG.name} (далее — Сервис). Использование Сервиса означает согласие с настоящей политикой.
      </p>

      <h2 className="font-display font-bold text-lg text-gray-900 dark:text-slate-50 mt-6">
        1. Оператор персональных данных
      </h2>
      <p>
        Оператор: {OPERATOR.fullName}. Адрес: {OPERATOR.address}. Электронная почта: {OPERATOR.email}. Телефон: {OPERATOR.phone}.
      </p>

      <h2 className="font-display font-bold text-lg text-gray-900 dark:text-slate-50 mt-6">
        2. Цели обработки данных
      </h2>
      <p>
        Оказание услуг клиентам; установление обратной связи с клиентами; обеспечение работы сайта, Telegram-бота и Mini App; обработка платежей и поддержка пользователей.
      </p>

      <h2 className="font-display font-bold text-lg text-gray-900 dark:text-slate-50 mt-6">
        3. Какие данные мы обрабатываем
      </h2>
      <p>
        Идентификатор Telegram, имя и имя пользователя (username), данные обратной связи (если указаны), технические данные (IP, тип устройства), данные, необходимые для приёма оплаты (в соответствии с политикой платёжного провайдера). На сайте могут использоваться cookie и метрика для анализа посещаемости.
      </p>

      <h2 className="font-display font-bold text-lg text-gray-900 dark:text-slate-50 mt-6">
        4. Хранение и передача данных
      </h2>
      <p>
        Персональные данные граждан РФ хранятся на территории Российской Федерации. Трансграничная передача персональных данных не осуществляется.
      </p>

      <h2 className="font-display font-bold text-lg text-gray-900 dark:text-slate-50 mt-6">
        5. Права пользователя
      </h2>
      <p>
        Вы вправе запросить доступ к своим данным, их уточнение, блокирование или удаление, а также отозвать согласие на обработку, направив запрос оператору по указанным контактам.
      </p>

      <h2 className="font-display font-bold text-lg text-gray-900 dark:text-slate-50 mt-6">
        6. Изменения
      </h2>
      <p>
        Актуальная версия политики публикуется на данной странице. Дата последнего обновления: 03.01.2026.
      </p>
    </LegalPageLayout>
  );
});
PrivacyPage.displayName = 'PrivacyPage';
