/**
 * Система мониторинга производительности
 * Отслеживание Core Web Vitals и отправка в аналитику
 *
 * @module monitoring/performanceMonitoring
 */

interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
  navigationType: string;
}

/**
 * Пороговые значения для Core Web Vitals (стандарты 2025)
 */
const THRESHOLDS = {
  LCP: { good: 2500, poor: 4000 },
  INP: { good: 200, poor: 500 },
  CLS: { good: 0.1, poor: 0.25 },
  FCP: { good: 1800, poor: 3000 },
  TTFB: { good: 800, poor: 1800 },
};

/**
 * Определение рейтинга метрики
 */
const getRating = (name: string, value: number): 'good' | 'needs-improvement' | 'poor' => {
  const threshold = THRESHOLDS[name as keyof typeof THRESHOLDS];
  if (!threshold) return 'good';

  if (value <= threshold.good) return 'good';
  if (value <= threshold.poor) return 'needs-improvement';
  return 'poor';
};

/**
 * Отправка метрик в аналитику
 */
const sendToAnalytics = (metric: PerformanceMetric) => {
  // Google Analytics 4
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', metric.name, {
      value: Math.round(metric.value),
      metric_rating: metric.rating,
      metric_delta: Math.round(metric.delta),
      metric_id: metric.id,
    });
  }

  // Консольное логирование для разработки
  if (process.env.NODE_ENV === 'development') {
    const emoji = metric.rating === 'good' ? '✅' : metric.rating === 'needs-improvement' ? '⚠️' : '❌';
    console.log(`${emoji} ${metric.name}:`, {
      value: `${Math.round(metric.value)}ms`,
      rating: metric.rating,
      threshold: THRESHOLDS[metric.name as keyof typeof THRESHOLDS],
    });
  }

  // Sentry (если настроен)
  if (metric.rating === 'poor' && typeof window !== 'undefined' && (window as any).Sentry) {
    (window as any).Sentry.captureMessage(`Poor ${metric.name}: ${metric.value}ms`, {
      level: 'warning',
      tags: {
        metric: metric.name,
        rating: metric.rating,
      },
      contexts: {
        performance: {
          value: metric.value,
          threshold: THRESHOLDS[metric.name as keyof typeof THRESHOLDS],
        },
      },
    });
  }
};

/**
 * Инициализация мониторинга Web Vitals
 */
export const initPerformanceMonitoring = () => {
  if (typeof window === 'undefined') return;

  // Динамический импорт web-vitals для оптимизации бандла
  import('web-vitals').then(({ onCLS, onFCP, onINP, onLCP, onTTFB }) => {
    // Largest Contentful Paint
    onLCP((metric: any) => {
      sendToAnalytics({
        ...metric,
        rating: getRating('LCP', metric.value),
      });
    });

    // Interaction to Next Paint
    onINP((metric: any) => {
      sendToAnalytics({
        ...metric,
        rating: getRating('INP', metric.value),
      });
    });

    // Cumulative Layout Shift
    onCLS((metric: any) => {
      sendToAnalytics({
        ...metric,
        rating: getRating('CLS', metric.value),
      });
    });

    // First Contentful Paint
    onFCP((metric: any) => {
      sendToAnalytics({
        ...metric,
        rating: getRating('FCP', metric.value),
      });
    });

    // Time to First Byte
    onTTFB((metric: any) => {
      sendToAnalytics({
        ...metric,
        rating: getRating('TTFB', metric.value),
      });
    });
  }).catch(err => {
    console.error('Failed to load web-vitals:', err);
  });

  // Дополнительный мониторинг производительности
  monitorLongTasks();
  monitorResourceLoading();
};

/**
 * Мониторинг долгих задач (Long Tasks)
 */
const monitorLongTasks = () => {
  if ('PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.duration > 50) {
            console.warn('⚠️ Long Task detected:', {
              duration: `${entry.duration.toFixed(2)}ms`,
              startTime: entry.startTime,
            });

            // Отправляем в аналитику только очень долгие задачи
            if (entry.duration > 100 && (window as any).gtag) {
              (window as any).gtag('event', 'long_task', {
                value: Math.round(entry.duration),
                start_time: Math.round(entry.startTime),
              });
            }
          }
        });
      });

      observer.observe({ entryTypes: ['longtask'] });
    } catch (e) {
      // PerformanceObserver может не поддерживаться
      console.warn('Long Tasks monitoring not supported');
    }
  }
};

/**
 * Мониторинг загрузки ресурсов
 */
const monitorResourceLoading = () => {
  if ('PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry: any) => {
          // Отслеживаем медленно загружающиеся ресурсы
          if (entry.duration > 3000) {
            console.warn('⚠️ Slow resource:', {
              name: entry.name,
              duration: `${entry.duration.toFixed(2)}ms`,
              type: entry.initiatorType,
              size: entry.transferSize ? `${(entry.transferSize / 1024).toFixed(2)}KB` : 'N/A',
            });
          }

          // Отслеживаем большие ресурсы
          if (entry.transferSize && entry.transferSize > 500 * 1024) { // > 500KB
            console.warn('⚠️ Large resource:', {
              name: entry.name,
              size: `${(entry.transferSize / 1024).toFixed(2)}KB`,
              type: entry.initiatorType,
            });
          }
        });
      });

      observer.observe({ entryTypes: ['resource'] });
    } catch (e) {
      console.warn('Resource monitoring not supported');
    }
  }
};

/**
 * Отчет о текущих метриках производительности
 */
export const getPerformanceReport = () => {
  if (typeof window === 'undefined' || !window.performance) return null;

  const perfData = window.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

  if (!perfData) return null;

  return {
    // Время загрузки
    domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
    loadComplete: perfData.loadEventEnd - perfData.loadEventStart,

    // Этапы загрузки
    dns: perfData.domainLookupEnd - perfData.domainLookupStart,
    tcp: perfData.connectEnd - perfData.connectStart,
    request: perfData.responseStart - perfData.requestStart,
    response: perfData.responseEnd - perfData.responseStart,

    // Общее время
    totalTime: perfData.loadEventEnd - perfData.fetchStart,

    // Ресурсы
    resources: performance.getEntriesByType('resource').length,

    // Память (если доступно)
    memory: (performance as any).memory ? {
      used: ((performance as any).memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
      total: ((performance as any).memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB',
      limit: ((performance as any).memory.jsHeapSizeLimit / 1048576).toFixed(2) + ' MB',
    } : null,
  };
};
