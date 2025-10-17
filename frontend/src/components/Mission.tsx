/**
 * Секция "Наша миссия" в стиле Montfort ESG
 * Рассказывает о ценностях и целях проекта
 */

import React from 'react';

export const Mission: React.FC = React.memo(() => {
  return (
    <section
      id="mission"
      className="py-20 md:py-32 bg-gradient-to-br from-sky/5 via-purple-50/30 to-pink/5"
      aria-label="Наша миссия"
    >
      <div className="max-w-6xl mx-auto px-4">
        {/* Заголовок секции */}
        <div className="text-center mb-16">
          <h2 className="font-display text-4xl md:text-5xl font-bold mb-6 text-gray-900">
            Наша миссия
          </h2>
          <p className="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto">
            Создать безопасное образовательное пространство, где дети
            учатся с удовольствием, а родители спокойны за их будущее
          </p>
        </div>

        {/* Основной контент */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Левая колонка - текст */}
          <div className="bg-white/80 backdrop-blur rounded-2xl p-8 md:p-10 shadow-lg">
            <h3 className="font-bold text-2xl md:text-3xl mb-6 text-gray-900">
              Почему мы создали PandaPal?
            </h3>

            <div className="space-y-4 text-gray-700 text-lg leading-relaxed">
              <p>
                В эпоху цифровых технологий дети всё больше времени проводят онлайн.
                Мы верим, что это время должно быть не только безопасным, но и полезным.
              </p>

              <p>
                <strong className="text-sky font-semibold">PandaPal</strong> —  это не просто AI-бот.
                Это персональный образовательный помощник, который адаптируется под уникальные
                потребности каждого ребенка.
              </p>

              <p>
                Мы используем передовые технологии искусственного интеллекта, чтобы сделать
                обучение увлекательным, а контроль безопасности — максимально надёжным.
              </p>
            </div>
          </div>

          {/* Правая колонка - ценности */}
          <div className="space-y-6">
            <div className="bg-sky/10 backdrop-blur rounded-xl p-6 border-l-4 border-sky">
              <div className="flex items-start gap-4">
                <div className="text-4xl">🎯</div>
                <div>
                  <h4 className="font-bold text-xl mb-2 text-gray-900">Персонализация</h4>
                  <p className="text-gray-700">
                    Каждый ребенок уникален. AI адаптирует контент под возраст,
                    уровень и темп обучения.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-pink/10 backdrop-blur rounded-xl p-6 border-l-4 border-pink">
              <div className="flex items-start gap-4">
                <div className="text-4xl">🛡️</div>
                <div>
                  <h4 className="font-bold text-xl mb-2 text-gray-900">Безопасность</h4>
                  <p className="text-gray-700">
                    Многоуровневая AI-модерация 24/7 защищает детей от
                    неподходящего контента.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-purple-100/50 backdrop-blur rounded-xl p-6 border-l-4 border-purple-500">
              <div className="flex items-start gap-4">
                <div className="text-4xl">🌟</div>
                <div>
                  <h4 className="font-bold text-xl mb-2 text-gray-900">Мотивация</h4>
                  <p className="text-gray-700">
                    Геймификация превращает учёбу в игру. Награды, уровни,
                    достижения — обучение становится интересным!
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-green-100/50 backdrop-blur rounded-xl p-6 border-l-4 border-green-500">
              <div className="flex items-start gap-4">
                <div className="text-4xl">🤝</div>
                <div>
                  <h4 className="font-bold text-xl mb-2 text-gray-900">Прозрачность</h4>
                  <p className="text-gray-700">
                    Родители видят всю активность ребенка и могут настраивать
                    параметры безопасности.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Цифры и факты */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16">
          <div className="text-center bg-white/60 backdrop-blur rounded-xl p-6 shadow-md">
            <div className="text-4xl md:text-5xl font-bold text-sky mb-2">24/7</div>
            <p className="text-gray-600 font-medium">AI-модерация</p>
          </div>

          <div className="text-center bg-white/60 backdrop-blur rounded-xl p-6 shadow-md">
            <div className="text-4xl md:text-5xl font-bold text-pink mb-2">6-18</div>
            <p className="text-gray-600 font-medium">Возраст детей</p>
          </div>

          <div className="text-center bg-white/60 backdrop-blur rounded-xl p-6 shadow-md">
            <div className="text-4xl md:text-5xl font-bold text-purple-600 mb-2">99.9%</div>
            <p className="text-gray-600 font-medium">Точность фильтрации</p>
          </div>

          <div className="text-center bg-white/60 backdrop-blur rounded-xl p-6 shadow-md">
            <div className="text-4xl md:text-5xl font-bold text-green-600 mb-2">∞</div>
            <p className="text-gray-600 font-medium">Бесплатно навсегда</p>
          </div>
        </div>
      </div>
    </section>
  );
});

Mission.displayName = 'Mission';
