/**
 * Секция с табами для информации о PandaPal
 * Заменяет старые отдельные секции на единый таб-интерфейс
 */

import React from 'react';
import { Tabs } from './Tabs';
import type { Tab } from './Tabs';

/**
 * Контент для родителей
 */
const ParentsContent: React.FC = React.memo(() => (
  <div className="rounded-2xl bg-white/80 backdrop-blur p-8 md:p-12 shadow-lg">
    <h3 className="font-display text-3xl md:text-4xl font-bold mb-6 text-gray-900">
      Для родителей
    </h3>

    <div className="space-y-6 text-lg text-gray-700">
      <p className="leading-relaxed">
        Прозрачная аналитика прогресса ребенка, гибкие настройки безопасности
        и контроль времени обучения. Вы всегда будете в курсе успехов и интересов
        вашего ребенка.
      </p>

      <div className="grid md:grid-cols-2 gap-6 mt-8">
        <div className="bg-sky/10 rounded-xl p-6">
          <div className="text-3xl mb-3">📊</div>
          <h4 className="font-bold text-xl mb-2">Дашборд родителя</h4>
          <p className="text-gray-600">
            Отслеживайте активность, темы изучения и время использования в реальном времени
          </p>
        </div>

        <div className="bg-pink/10 rounded-xl p-6">
          <div className="text-3xl mb-3">🔒</div>
          <h4 className="font-bold text-xl mb-2">Гибкие настройки</h4>
          <p className="text-gray-600">
            Настройте ограничения по контенту, времени и темам в один клик
          </p>
        </div>

        <div className="bg-purple-100/50 rounded-xl p-6">
          <div className="text-3xl mb-3">📈</div>
          <h4 className="font-bold text-xl mb-2">Прогресс обучения</h4>
          <p className="text-gray-600">
            Детальная статистика по предметам, сложности и достижениям
          </p>
        </div>

        <div className="bg-green-100/50 rounded-xl p-6">
          <div className="text-3xl mb-3">⚡</div>
          <h4 className="font-bold text-xl mb-2">Мгновенные уведомления</h4>
          <p className="text-gray-600">
            Получайте оповещения о важных событиях и достижениях
          </p>
        </div>
      </div>
    </div>
  </div>
));

ParentsContent.displayName = 'ParentsContent';

/**
 * Контент о безопасности
 */
const SecurityContent: React.FC = React.memo(() => (
  <div className="rounded-2xl bg-white/80 backdrop-blur p-8 md:p-12 shadow-lg">
    <h3 className="font-display text-3xl md:text-4xl font-bold mb-6 text-gray-900">
      Безопасность превыше всего
    </h3>

    <div className="space-y-6 text-lg text-gray-700">
      <p className="leading-relaxed font-medium text-xl">
        Мы используем многоуровневую систему защиты для обеспечения безопасности детей
      </p>

      <div className="grid md:grid-cols-3 gap-6 mt-8">
        <div className="text-center">
          <div className="text-5xl mb-4">🤖</div>
          <h4 className="font-bold text-xl mb-3">AI-модерация 24/7</h4>
          <p className="text-gray-600 text-base">
            Google Gemini анализирует каждое сообщение в режиме реального времени
          </p>
          <div className="mt-4 text-2xl font-bold text-sky">99.9%</div>
          <p className="text-sm text-gray-500">точность фильтрации</p>
        </div>

        <div className="text-center">
          <div className="text-5xl mb-4">🛡️</div>
          <h4 className="font-bold text-xl mb-3">OWASP Top 10</h4>
          <p className="text-gray-600 text-base">
            Защита от всех типов веб-атак: XSS, SQLi, clickjacking
          </p>
          <div className="mt-4 text-2xl font-bold text-pink">A+ рейтинг</div>
          <p className="text-sm text-gray-500">безопасности</p>
        </div>

        <div className="text-center">
          <div className="text-5xl mb-4">🔐</div>
          <h4 className="font-bold text-xl mb-3">Шифрование данных</h4>
          <p className="text-gray-600 text-base">
            Все данные шифруются и хранятся на защищённых серверах
          </p>
          <div className="mt-4 text-2xl font-bold text-purple-600">256-bit</div>
          <p className="text-sm text-gray-500">SSL/TLS шифрование</p>
        </div>
      </div>

      <div className="mt-10 bg-gradient-to-r from-sky/20 to-pink/20 rounded-xl p-6">
        <h4 className="font-bold text-xl mb-3 flex items-center gap-2">
          <span>✅</span>
          <span>Что мы фильтруем автоматически:</span>
        </h4>
        <ul className="grid md:grid-cols-2 gap-3 text-base">
          <li className="flex items-start gap-2">
            <span className="text-red-500 font-bold">×</span>
            <span>Нецензурная лексика</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-red-500 font-bold">×</span>
            <span>Взрослый контент</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-red-500 font-bold">×</span>
            <span>Насилие и агрессия</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-red-500 font-bold">×</span>
            <span>Опасные инструкции</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-red-500 font-bold">×</span>
            <span>Буллинг и дискриминация</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-red-500 font-bold">×</span>
            <span>Личные данные (утечка)</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
));

SecurityContent.displayName = 'SecurityContent';

/**
 * Контент о возможностях
 */
const FeaturesContent: React.FC = React.memo(() => (
  <div className="rounded-2xl bg-white/80 backdrop-blur p-8 md:p-12 shadow-lg">
    <h3 className="font-display text-3xl md:text-4xl font-bold mb-6 text-gray-900">
      Возможности PandaPal
    </h3>

    <div className="space-y-8 text-lg text-gray-700">
      <p className="leading-relaxed text-xl">
        Современные технологии для эффективного обучения
      </p>

      <div className="space-y-6">
        <div className="flex gap-6 items-start bg-gradient-to-r from-sky/10 to-transparent rounded-xl p-6">
          <div className="text-4xl">🎮</div>
          <div>
            <h4 className="font-bold text-2xl mb-2">Геймификация</h4>
            <p className="text-gray-600">
              Система уровней, достижений и наград. Обучение превращается в увлекательную игру!
            </p>
          </div>
        </div>

        <div className="flex gap-6 items-start bg-gradient-to-r from-pink/10 to-transparent rounded-xl p-6">
          <div className="text-4xl">🎯</div>
          <div>
            <h4 className="font-bold text-2xl mb-2">Персонализация</h4>
            <p className="text-gray-600">
              AI адаптирует сложность и стиль объяснений под возраст (6-18 лет) и уровень ребенка
            </p>
          </div>
        </div>

        <div className="flex gap-6 items-start bg-gradient-to-r from-purple-100/50 to-transparent rounded-xl p-6">
          <div className="text-4xl">🧠</div>
          <div>
            <h4 className="font-bold text-2xl mb-2">AI-помощник</h4>
            <p className="text-gray-600">
              Google Gemini 1.5 Flash отвечает на вопросы, объясняет сложные темы простым языком
            </p>
          </div>
        </div>

        <div className="flex gap-6 items-start bg-gradient-to-r from-green-100/50 to-transparent rounded-xl p-6">
          <div className="text-4xl">📚</div>
          <div>
            <h4 className="font-bold text-2xl mb-2">Веб-парсинг образовательных сайтов</h4>
            <p className="text-gray-600">
              Автоматический сбор актуальных материалов с проверенных источников (nsportal.ru и др.)
            </p>
          </div>
        </div>

        <div className="flex gap-6 items-start bg-gradient-to-r from-yellow-100/50 to-transparent rounded-xl p-6">
          <div className="text-4xl">🖼️</div>
          <div>
            <h4 className="font-bold text-2xl mb-2">Vision API</h4>
            <p className="text-gray-600">
              Отправь фото домашнего задания или конспекта - PandaPal проанализирует и поможет разобраться
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
));

FeaturesContent.displayName = 'FeaturesContent';

/**
 * Основной компонент с табами
 */
export const InfoTabs: React.FC = React.memo(() => {
  const tabs: Tab[] = [
    {
      id: 'parents',
      label: 'Для родителей',
      icon: '👨‍👩‍👧',
      content: <ParentsContent />,
    },
    {
      id: 'security',
      label: 'Безопасность',
      icon: '🛡️',
      content: <SecurityContent />,
    },
    {
      id: 'features',
      label: 'Возможности',
      icon: '⚡',
      content: <FeaturesContent />,
    },
  ];

  return (
    <section
      id="info"
      className="py-16 md:py-24"
      aria-label="Информация о PandaPal"
    >
      <Tabs tabs={tabs} defaultTab="parents" />
    </section>
  );
});

InfoTabs.displayName = 'InfoTabs';
