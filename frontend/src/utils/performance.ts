/**
 * Утилиты для оптимизации производительности
 * Соответствует стандартам Core Web Vitals 2025
 *
 * @module utils/performance
 */

/**
 * Метрики Web Vitals
 */
export interface WebVitalsMetrics {
  /** Largest Contentful Paint (должен быть < 2.5s) */
  lcp: number | null;
  /** Interaction to Next Paint (должен быть < 200ms) */
  inp: number | null;
  /** Cumulative Layout Shift (должен быть < 0.1) */
  cls: number | null;
  /** First Contentful Paint */
  fcp: number | null;
  /** Time to First Byte */
  ttfb: number | null;
}

/**
 * Отслеживание Core Web Vitals
 */
export const trackWebVitals = (onMetric: (metric: { name: string; value: number }) => void) => {
  if (typeof window === 'undefined') return;

  // Динамический импорт web-vitals для уменьшения размера бандла
  import('web-vitals').then(({ onCLS, onFCP, onLCP, onTTFB, onINP }) => {
    onCLS(onMetric);
    onFCP(onMetric);
    onLCP(onMetric);
    onTTFB(onMetric);
    onINP(onMetric);
  });
};

/**
 * Предзагрузка критических ресурсов
 */
export const preloadCriticalAssets = () => {
  // Предзагрузка шрифтов
  const fonts = [
    '/fonts/montserrat-bold.woff2',
    '/fonts/open-sans-regular.woff2',
  ];

  fonts.forEach(font => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'font';
    link.type = 'font/woff2';
    link.href = font;
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  });
};

/**
 * Ленивая загрузка изображений с Intersection Observer
 */
export const lazyLoadImages = () => {
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target as HTMLImageElement;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
            observer.unobserve(img);
          }
        }
      });
    });

    document.querySelectorAll('img.lazy').forEach(img => {
      imageObserver.observe(img);
    });
  }
};

/**
 * Оптимизация анимаций с помощью will-change
 */
export const optimizeAnimation = (element: HTMLElement, properties: string[]) => {
  element.style.willChange = properties.join(', ');

  // Удаляем will-change после завершения анимации
  const removeWillChange = () => {
    element.style.willChange = 'auto';
    element.removeEventListener('animationend', removeWillChange);
    element.removeEventListener('transitionend', removeWillChange);
  };

  element.addEventListener('animationend', removeWillChange);
  element.addEventListener('transitionend', removeWillChange);
};

/**
 * Дебаунс для оптимизации частых событий
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Троттлинг для ограничения частоты вызовов
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

/**
 * Проверка поддержки WebP/AVIF
 */
export const checkImageFormatSupport = async (): Promise<{
  webp: boolean;
  avif: boolean;
}> => {
  const webp = await checkFormat('image/webp', 'UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEADsD+JaQAA3AAAAAA');
  const avif = await checkFormat('image/avif', 'AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAABcAAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAEAAAABAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQAMAAAAABNjb2xybmNseAACAAIABoAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAAB9tZGF0EgAKCBgABogQEDQgMgkQAAAAB8dSLfI=');

  return { webp, avif };
};

const checkFormat = (mimeType: string, base64: string): Promise<boolean> => {
  return new Promise(resolve => {
    const img = new Image();
    img.onload = () => resolve(true);
    img.onerror = () => resolve(false);
    img.src = `data:${mimeType};base64,${base64}`;
  });
};

/**
 * Получение оптимального формата изображения
 */
export const getOptimalImageUrl = (
  formats: { webp?: string; avif?: string; jpg: string }
): string => {
  // Проверяем поддержку форматов (должно быть закэшировано)
  if (formats.avif && document.createElement('canvas').toDataURL('image/avif').indexOf('data:image/avif') === 0) {
    return formats.avif;
  }

  if (formats.webp && document.createElement('canvas').toDataURL('image/webp').indexOf('data:image/webp') === 0) {
    return formats.webp;
  }

  return formats.jpg;
};

/**
 * Отчет о производительности
 */
export const reportPerformance = () => {
  if (typeof window === 'undefined' || !window.performance) return;

  const perfData = window.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

  if (perfData) {
    const metrics = {
      dns: perfData.domainLookupEnd - perfData.domainLookupStart,
      tcp: perfData.connectEnd - perfData.connectStart,
      request: perfData.responseStart - perfData.requestStart,
      response: perfData.responseEnd - perfData.responseStart,
      dom: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
      load: perfData.loadEventEnd - perfData.loadEventStart,
      total: perfData.loadEventEnd - perfData.fetchStart,
    };

    console.log('📊 Performance Metrics:', metrics);
    return metrics;
  }
};
