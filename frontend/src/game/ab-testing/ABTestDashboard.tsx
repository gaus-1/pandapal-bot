/**
 * Dashboard для отображения статистики A/B тестов PandaPal Go.
 *
 * Позволяет разработчикам и аналитикам просматривать результаты
 * A/B тестирования игровых механик в реальном времени.
 */

import React, { useState, useEffect } from 'react';
import { gameABIntegration } from './GameABIntegration';
import { abTestManager } from './ABTestManager';
import './ab-test-styles.css';

interface ABTestDashboardProps {
  isVisible: boolean;
  onClose: () => void;
}

const ABTestDashboard: React.FC<ABTestDashboardProps> = ({ isVisible, onClose }) => {
  const [stats, setStats] = useState<Record<string, any>>({});
  const [activeTests, setActiveTests] = useState<Array<{ testId: string; variantId: string }>>([]);
  const [isABTestingEnabled, setIsABTestingEnabled] = useState(false);

  useEffect(() => {
    if (isVisible) {
      updateStats();
      const interval = setInterval(updateStats, 5000); // Обновляем каждые 5 секунд
      return () => clearInterval(interval);
    }
  }, [isVisible]);

  const updateStats = () => {
    setStats(gameABIntegration.getTestStatistics());
    setActiveTests(gameABIntegration.getActiveTests());
    setIsABTestingEnabled(gameABIntegration.isABTestingActive());
  };

  const handleExportResults = () => {
    const results = gameABIntegration.exportTestResults();
    const blob = new Blob([results], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pandapal_ab_test_results_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleToggleABTesting = () => {
    const newEnabled = !isABTestingEnabled;
    gameABIntegration.setABTestingEnabled(newEnabled);
    setIsABTestingEnabled(newEnabled);
    updateStats();
  };

  if (!isVisible) return null;

  return (
    <div className="ab-test-dashboard-overlay">
      <div className="ab-test-dashboard">
        <div className="ab-test-dashboard-header">
          <h2>🧪 A/B Test Dashboard - PandaPal Go</h2>
          <button
            className="ab-test-close-btn"
            onClick={onClose}
            title="Закрыть dashboard"
          >
            ✕
          </button>
        </div>

        <div className="ab-test-dashboard-content">
          {/* Общая информация */}
          <div className="ab-test-section">
            <h3>📊 Общая информация</h3>
            <div className="ab-test-info-grid">
              <div className="ab-test-info-item">
                <span className="info-label">A/B тестирование:</span>
                <span className={`info-value ${isABTestingEnabled ? 'enabled' : 'disabled'}`}>
                  {isABTestingEnabled ? 'Включено' : 'Отключено'}
                </span>
              </div>
              <div className="ab-test-info-item">
                <span className="info-label">Активных тестов:</span>
                <span className="info-value">{activeTests.length}</span>
              </div>
              <div className="ab-test-info-item">
                <span className="info-label">Пользователь ID:</span>
                <span className="info-value">{abTestManager['userId']}</span>
              </div>
            </div>

            <div className="ab-test-controls">
              <button
                className={`ab-test-toggle-btn ${isABTestingEnabled ? 'enabled' : 'disabled'}`}
                onClick={handleToggleABTesting}
              >
                {isABTestingEnabled ? 'Отключить A/B тесты' : 'Включить A/B тесты'}
              </button>
              <button
                className="ab-test-export-btn"
                onClick={handleExportResults}
              >
                📥 Экспорт результатов
              </button>
            </div>
          </div>

          {/* Активные тесты */}
          {activeTests.length > 0 && (
            <div className="ab-test-section">
              <h3>🎯 Активные тесты</h3>
              <div className="ab-test-active-list">
                {activeTests.map((test, index) => (
                  <div key={index} className="ab-test-active-item">
                    <span className="test-id">{test.testId}</span>
                    <span className="test-variant">Вариант: {test.variantId}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Статистика по тестам */}
          {Object.keys(stats).length > 0 && (
            <div className="ab-test-section">
              <h3>📈 Статистика тестов</h3>
              {Object.entries(stats).map(([testId, testStats]) => (
                <div key={testId} className="ab-test-stats-card">
                  <h4>{testStats.name}</h4>
                  <div className="ab-test-stats-grid">
                    <div className="stats-item">
                      <span className="stats-label">Участников:</span>
                      <span className="stats-value">{testStats.totalParticipants}</span>
                    </div>

                    {Object.entries(testStats.variants || {}).map(([variantId, variantStats]: [string, any]) => (
                      <div key={variantId} className="variant-stats">
                        <h5>Вариант: {variantId}</h5>
                        <div className="variant-metrics">
                          <div className="metric">
                            <span className="metric-label">Участников:</span>
                            <span className="metric-value">{variantStats.participants}</span>
                          </div>
                          <div className="metric">
                            <span className="metric-label">Среднее время игры:</span>
                            <span className="metric-value">{variantStats.avgPlayTime?.toFixed(1)}с</span>
                          </div>
                          <div className="metric">
                            <span className="metric-label">Средний счет:</span>
                            <span className="metric-value">{variantStats.avgScore?.toFixed(0)}</span>
                          </div>
                          <div className="metric">
                            <span className="metric-label">Пройденных уровней:</span>
                            <span className="metric-value">{variantStats.avgLevelsCompleted?.toFixed(1)}</span>
                          </div>
                          <div className="metric">
                            <span className="metric-label">Ошибок:</span>
                            <span className="metric-value">{variantStats.totalErrors}</span>
                          </div>
                          <div className="metric">
                            <span className="metric-label">Процент ошибок:</span>
                            <span className="metric-value">{(variantStats.errorRate * 100)?.toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Конфигурация игры */}
          <div className="ab-test-section">
            <h3>⚙️ Текущая конфигурация игры</h3>
            <div className="ab-test-config">
              <pre className="config-json">
                {JSON.stringify(gameABIntegration.getGameConfig(), null, 2)}
              </pre>
            </div>
          </div>

          {/* Инструкции */}
          <div className="ab-test-section">
            <h3>📖 Инструкции</h3>
            <div className="ab-test-instructions">
              <p><strong>Как использовать A/B тестирование:</strong></p>
              <ul>
                <li>Включите A/B тестирование для участия в тестах</li>
                <li>Играйте в игру - ваши действия автоматически логируются</li>
                <li>Просматривайте статистику в реальном времени</li>
                <li>Экспортируйте результаты для анализа</li>
              </ul>

              <p><strong>Активные тесты:</strong></p>
              <ul>
                <li><strong>difficulty_test</strong> - тестирование сложности математических задач</li>
                <li><strong>ui_test</strong> - тестирование пользовательского интерфейса</li>
                <li><strong>mechanics_test</strong> - тестирование игровых механик</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .ab-test-dashboard-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 10000;
          padding: 20px;
        }

        .ab-test-dashboard {
          background: white;
          border-radius: 12px;
          max-width: 800px;
          width: 100%;
          max-height: 90vh;
          overflow-y: auto;
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }

        .ab-test-dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #eee;
          background: #f8fafc;
          border-radius: 12px 12px 0 0;
        }

        .ab-test-dashboard-header h2 {
          margin: 0;
          color: #1e293b;
          font-size: 24px;
        }

        .ab-test-close-btn {
          background: #ef4444;
          color: white;
          border: none;
          border-radius: 6px;
          width: 32px;
          height: 32px;
          cursor: pointer;
          font-size: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .ab-test-close-btn:hover {
          background: #dc2626;
        }

        .ab-test-dashboard-content {
          padding: 20px;
        }

        .ab-test-section {
          margin-bottom: 30px;
        }

        .ab-test-section h3 {
          color: #374151;
          margin-bottom: 15px;
          font-size: 18px;
          border-bottom: 2px solid #e5e7eb;
          padding-bottom: 5px;
        }

        .ab-test-info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .ab-test-info-item {
          display: flex;
          justify-content: space-between;
          padding: 10px;
          background: #f9fafb;
          border-radius: 6px;
        }

        .info-label {
          font-weight: 600;
          color: #374151;
        }

        .info-value {
          font-weight: 700;
        }

        .info-value.enabled {
          color: #059669;
        }

        .info-value.disabled {
          color: #dc2626;
        }

        .ab-test-controls {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }

        .ab-test-toggle-btn,
        .ab-test-export-btn {
          padding: 10px 20px;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s ease;
        }

        .ab-test-toggle-btn.enabled {
          background: #dc2626;
          color: white;
        }

        .ab-test-toggle-btn.disabled {
          background: #059669;
          color: white;
        }

        .ab-test-export-btn {
          background: #3b82f6;
          color: white;
        }

        .ab-test-toggle-btn:hover,
        .ab-test-export-btn:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }

        .ab-test-active-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .ab-test-active-item {
          display: flex;
          justify-content: space-between;
          padding: 10px;
          background: #eff6ff;
          border-radius: 6px;
          border-left: 4px solid #3b82f6;
        }

        .test-id {
          font-weight: 600;
          color: #1e40af;
        }

        .test-variant {
          color: #374151;
        }

        .ab-test-stats-card {
          background: #f9fafb;
          border-radius: 8px;
          padding: 15px;
          margin-bottom: 15px;
        }

        .ab-test-stats-card h4 {
          margin: 0 0 15px 0;
          color: #1f2937;
        }

        .ab-test-stats-grid {
          display: grid;
          gap: 15px;
        }

        .stats-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #e5e7eb;
        }

        .stats-label {
          font-weight: 600;
          color: #374151;
        }

        .stats-value {
          font-weight: 700;
          color: #1f2937;
        }

        .variant-stats {
          background: white;
          border-radius: 6px;
          padding: 15px;
          border: 1px solid #e5e7eb;
        }

        .variant-stats h5 {
          margin: 0 0 10px 0;
          color: #374151;
          font-size: 14px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .variant-metrics {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 8px;
        }

        .metric {
          display: flex;
          justify-content: space-between;
          padding: 5px 0;
          font-size: 14px;
        }

        .metric-label {
          color: #6b7280;
        }

        .metric-value {
          font-weight: 600;
          color: #1f2937;
        }

        .ab-test-config {
          background: #f3f4f6;
          border-radius: 6px;
          padding: 15px;
          overflow-x: auto;
        }

        .config-json {
          margin: 0;
          font-family: 'Courier New', monospace;
          font-size: 12px;
          color: #374151;
          white-space: pre-wrap;
        }

        .ab-test-instructions {
          background: #fef3c7;
          border-radius: 6px;
          padding: 15px;
          border-left: 4px solid #f59e0b;
        }

        .ab-test-instructions p {
          margin: 0 0 10px 0;
          color: #92400e;
        }

        .ab-test-instructions ul {
          margin: 0;
          padding-left: 20px;
          color: #92400e;
        }

        .ab-test-instructions li {
          margin-bottom: 5px;
        }

        @media (max-width: 768px) {
          .ab-test-dashboard {
            margin: 10px;
            max-height: 95vh;
          }

          .ab-test-info-grid {
            grid-template-columns: 1fr;
          }

          .ab-test-controls {
            flex-direction: column;
          }

          .variant-metrics {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default ABTestDashboard;
