/**
 * Хук для управления доступностью (a11y)
 * Соответствует WCAG 2.1 AA и стандартам 2025
 *
 * @module hooks/useAccessibility
 */

import { useEffect, useState, useCallback } from 'react';

interface AccessibilitySettings {
  /** Увеличенный текст */
  largeText: boolean;
  /** Высокая контрастность */
  highContrast: boolean;
  /** Уменьшенная анимация */
  reducedMotion: boolean;
  /** Фокус-индикаторы */
  keyboardFocus: boolean;
}

/**
 * Хук для управления настройками доступности
 */
export const useAccessibility = () => {
  const [settings, setSettings] = useState<AccessibilitySettings>({
    largeText: false,
    highContrast: false,
    reducedMotion: false,
    keyboardFocus: true,
  });

  // Определение системных предпочтений
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Проверка prefers-reduced-motion
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setSettings(prev => ({ ...prev, reducedMotion: reducedMotionQuery.matches }));

    const handleReducedMotionChange = (e: MediaQueryListEvent) => {
      setSettings(prev => ({ ...prev, reducedMotion: e.matches }));
    };

    reducedMotionQuery.addEventListener('change', handleReducedMotionChange);

    // Проверка prefers-contrast
    const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
    setSettings(prev => ({ ...prev, highContrast: highContrastQuery.matches }));

    const handleHighContrastChange = (e: MediaQueryListEvent) => {
      setSettings(prev => ({ ...prev, highContrast: e.matches }));
    };

    highContrastQuery.addEventListener('change', handleHighContrastChange);

    // Загрузка сохраненных настроек
    const savedSettings = localStorage.getItem('a11y-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(prev => ({ ...prev, ...parsed }));
      } catch (e) {
        console.error('Failed to parse a11y settings:', e);
      }
    }

    return () => {
      reducedMotionQuery.removeEventListener('change', handleReducedMotionChange);
      highContrastQuery.removeEventListener('change', handleHighContrastChange);
    };
  }, []);

  // Сохранение настроек
  useEffect(() => {
    localStorage.setItem('a11y-settings', JSON.stringify(settings));

    // Применение настроек к body
    const body = document.body;
    body.classList.toggle('large-text', settings.largeText);
    body.classList.toggle('high-contrast', settings.highContrast);
    body.classList.toggle('reduced-motion', settings.reducedMotion);
    body.classList.toggle('keyboard-focus', settings.keyboardFocus);
  }, [settings]);

  const toggleLargeText = useCallback(() => {
    setSettings(prev => ({ ...prev, largeText: !prev.largeText }));
  }, []);

  const toggleHighContrast = useCallback(() => {
    setSettings(prev => ({ ...prev, highContrast: !prev.highContrast }));
  }, []);

  const toggleReducedMotion = useCallback(() => {
    setSettings(prev => ({ ...prev, reducedMotion: !prev.reducedMotion }));
  }, []);

  const toggleKeyboardFocus = useCallback(() => {
    setSettings(prev => ({ ...prev, keyboardFocus: !prev.keyboardFocus }));
  }, []);

  return {
    settings,
    toggleLargeText,
    toggleHighContrast,
    toggleReducedMotion,
    toggleKeyboardFocus,
  };
};

/**
 * Хук для trap focus (для модальных окон)
 */
export const useFocusTrap = (isActive: boolean) => {
  useEffect(() => {
    if (!isActive) return;

    const focusableElements = document.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    document.addEventListener('keydown', handleTab);
    firstElement.focus();

    return () => {
      document.removeEventListener('keydown', handleTab);
    };
  }, [isActive]);
};

/**
 * Хук для анонсов для скрин-ридеров
 */
export const useAnnouncer = () => {
  const [announcer, setAnnouncer] = useState<HTMLDivElement | null>(null);

  useEffect(() => {
    // Создаем невидимый элемент для анонсов
    const div = document.createElement('div');
    div.setAttribute('role', 'status');
    div.setAttribute('aria-live', 'polite');
    div.setAttribute('aria-atomic', 'true');
    div.style.position = 'absolute';
    div.style.left = '-10000px';
    div.style.width = '1px';
    div.style.height = '1px';
    div.style.overflow = 'hidden';

    document.body.appendChild(div);
    setAnnouncer(div);

    return () => {
      document.body.removeChild(div);
    };
  }, []);

  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!announcer) return;

    announcer.setAttribute('aria-live', priority);
    announcer.textContent = message;

    // Очищаем после анонса
    setTimeout(() => {
      if (announcer) announcer.textContent = '';
    }, 1000);
  }, [announcer]);

  return { announce };
};

/**
 * Проверка цветового контраста
 */
export const checkColorContrast = (foreground: string, background: string): {
  ratio: number;
  wcagAA: boolean;
  wcagAAA: boolean;
} => {
  const getLuminance = (hex: string): number => {
    const rgb = parseInt(hex.slice(1), 16);
    const r = ((rgb >> 16) & 0xff) / 255;
    const g = ((rgb >> 8) & 0xff) / 255;
    const b = ((rgb >> 0) & 0xff) / 255;

    const [rs, gs, bs] = [r, g, b].map(c => {
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };

  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);
  const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);

  return {
    ratio: Math.round(ratio * 100) / 100,
    wcagAA: ratio >= 4.5, // Стандарт для обычного текста
    wcagAAA: ratio >= 7, // Усиленный стандарт
  };
};
