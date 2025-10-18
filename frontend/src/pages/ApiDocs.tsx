/**
 * Страница документации API PandaPal Bot
 *
 * Отображает OpenAPI/Swagger документацию для всех API endpoints
 * бота PandaPal, включая AI чат, игру, аналитику и безопасность.
 */

import React, { useEffect, useRef } from 'react';

const ApiDocs: React.FC = () => {
  const swaggerContainer = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Загружаем Swagger UI асинхронно
    const loadSwaggerUI = async () => {
      try {
        // Динамический импорт Swagger UI
        const { SwaggerUIBundle } = await import('swagger-ui-dist/swagger-ui-bundle.js');

        if (swaggerContainer.current) {
          SwaggerUIBundle({
            url: '/api/openapi.yaml', // Путь к OpenAPI спецификации
            dom_id: '#swagger-ui',
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIBundle.presets.standalone
            ],
            layout: 'StandaloneLayout',
            deepLinking: true,
            showExtensions: true,
            showCommonExtensions: true,
            docExpansion: 'list',
            defaultModelsExpandDepth: 2,
            defaultModelExpandDepth: 2,
            tryItOutEnabled: true,
            supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
            onComplete: () => {
              console.log('Swagger UI загружен успешно');
            },
            onFailure: (error: any) => {
              console.error('Ошибка загрузки Swagger UI:', error);
            }
          });
        }
      } catch (error) {
        console.error('Ошибка импорта Swagger UI:', error);
        // Fallback - показываем простое описание API
        if (swaggerContainer.current) {
          swaggerContainer.current.innerHTML = `
            <div class="api-docs-fallback">
              <h2>📋 PandaPal Bot API Documentation</h2>
              <p>Swagger UI временно недоступен. Вот основные API endpoints:</p>
              <div class="api-endpoints">
                <h3>🤖 AI Chat API</h3>
                <ul>
                  <li><strong>POST /api/v1/ai/chat</strong> - Отправка сообщения AI ассистенту</li>
                </ul>

                <h3>🎮 Game API</h3>
                <ul>
                  <li><strong>POST /api/v1/game/start</strong> - Запуск игры PandaPal Go</li>
                  <li><strong>GET /api/v1/game/progress</strong> - Получение прогресса в игре</li>
                </ul>

                <h3>👤 User Management API</h3>
                <ul>
                  <li><strong>GET /api/v1/users/profile</strong> - Получение профиля пользователя</li>
                </ul>

                <h3>👨‍👩‍👧‍👦 Parental Control API</h3>
                <ul>
                  <li><strong>GET /api/v1/parental/activity</strong> - Получение активности ребенка</li>
                </ul>

                <h3>📊 Analytics API</h3>
                <ul>
                  <li><strong>GET /api/v1/analytics/metrics</strong> - Получение метрик системы</li>
                </ul>

                <h3>🛡️ Security API</h3>
                <ul>
                  <li><strong>GET /api/v1/health</strong> - Проверка состояния системы</li>
                </ul>
              </div>
              <p>Полная документация доступна в файле <code>docs/api/openapi.yaml</code></p>
            </div>
          `;
        }
      }
    };

    loadSwaggerUI();
  }, []);

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

        {/* Swagger UI контейнер */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div id="swagger-ui" ref={swaggerContainer}></div>
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

        {/* Стили для fallback */}
        <style jsx>{`
          .api-docs-fallback {
            padding: 2rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          }

          .api-docs-fallback h2 {
            color: #1f2937;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 1rem;
          }

          .api-docs-fallback h3 {
            color: #374151;
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 2rem;
            margin-bottom: 1rem;
          }

          .api-endpoints ul {
            list-style: none;
            padding: 0;
          }

          .api-endpoints li {
            background: #f9fafb;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 0.375rem;
            border-left: 4px solid #3b82f6;
          }

          .api-endpoints code {
            background: #1f2937;
            color: #f9fafb;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-family: 'Courier New', monospace;
          }
        `}</style>
      </div>
    </div>
  );
};

export default ApiDocs;
