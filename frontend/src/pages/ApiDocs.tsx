/**
 * Страница документации API PandaPal Bot
 *
 * Отображает OpenAPI/Swagger документацию для всех API endpoints
 * бота PandaPal, включая AI чат, игру, аналитику и безопасность.
 */

import React from 'react';

const ApiDocs: React.FC = () => {

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Заголовок */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            📋 PandaPal Bot API Documentation
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Полная документация API для образовательного Telegram-бота PandaPal.
            Включает AI чат, игру PandaPal Go, родительский контроль и аналитику.
          </p>
        </div>

        {/* Информация о безопасности */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-blue-800">
                🔒 Безопасность API
              </h3>
              <p className="mt-2 text-blue-700">
                Все API endpoints защищены JWT аутентификацией и соответствуют стандартам OWASP Top 10.
                Для доступа к API требуется валидный токен, полученный через Telegram OAuth.
              </p>
            </div>
          </div>
        </div>

        {/* API Endpoints */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden p-8">
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">📋 API Endpoints</h2>
              <p className="text-gray-600 mb-6">
                Основные API endpoints для взаимодействия с PandaPal Bot.
                Полная документация доступна в файле <code className="bg-gray-100 px-2 py-1 rounded">docs/api/openapi.yaml</code>
              </p>
            </div>

            <div className="space-y-4">
              <div className="border-l-4 border-blue-500 bg-blue-50 p-4 rounded">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">🤖 AI Chat API</h3>
                <ul className="space-y-2">
                  <li className="text-gray-700"><strong>POST /api/v1/ai/chat</strong> - Отправка сообщения AI ассистенту</li>
                </ul>
              </div>

              <div className="border-l-4 border-green-500 bg-green-50 p-4 rounded">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">🎮 Game API</h3>
                <ul className="space-y-2">
                  <li className="text-gray-700"><strong>POST /api/v1/game/start</strong> - Запуск игры PandaPal Go</li>
                  <li className="text-gray-700"><strong>GET /api/v1/game/progress</strong> - Получение прогресса в игре</li>
                </ul>
              </div>

              <div className="border-l-4 border-purple-500 bg-purple-50 p-4 rounded">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">👤 User Management API</h3>
                <ul className="space-y-2">
                  <li className="text-gray-700"><strong>GET /api/v1/users/profile</strong> - Получение профиля пользователя</li>
                </ul>
              </div>

              <div className="border-l-4 border-orange-500 bg-orange-50 p-4 rounded">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">👨‍👩‍👧‍👦 Parental Control API</h3>
                <ul className="space-y-2">
                  <li className="text-gray-700"><strong>GET /api/v1/parental/activity</strong> - Получение активности ребенка</li>
                </ul>
              </div>

              <div className="border-l-4 border-indigo-500 bg-indigo-50 p-4 rounded">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">📊 Analytics API</h3>
                <ul className="space-y-2">
                  <li className="text-gray-700"><strong>GET /api/v1/analytics/metrics</strong> - Получение метрик системы</li>
                </ul>
              </div>

              <div className="border-l-4 border-red-500 bg-red-50 p-4 rounded">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">🛡️ Security API</h3>
                <ul className="space-y-2">
                  <li className="text-gray-700"><strong>GET /api/v1/health</strong> - Проверка состояния системы</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Дополнительная информация */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              🤖 AI Chat API
            </h3>
            <p className="text-gray-600">
              Интеграция с Google Gemini для образовательных диалогов.
              Поддерживает текст, изображения и голосовые сообщения.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              🎮 Game API
            </h3>
            <p className="text-gray-600">
              Управление образовательной игрой PandaPal Go.
              Отслеживание прогресса и достижений пользователей.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              📊 Analytics API
            </h3>
            <p className="text-gray-600">
              Метрики системы, пользовательская аналитика
              и мониторинг производительности.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
};

export default ApiDocs;
