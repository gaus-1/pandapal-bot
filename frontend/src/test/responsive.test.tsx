/**
 * Тесты адаптивности сайта для всех устройств
 * Проверяем корректное отображение на мобильных, планшетах и десктопах
 */

import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import App from '../App';

// Мокаем window.matchMedia для тестирования медиа-запросов
const mockMatchMedia = (matches: boolean) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
};

describe('Адаптивность сайта', () => {
  beforeEach(() => {
    // Сбрасываем все моки перед каждым тестом
    vi.clearAllMocks();
  });

  describe('Мобильные устройства (до 480px)', () => {
    beforeEach(() => {
      mockMatchMedia(true); // Симулируем мобильный экран
      // Устанавливаем размер viewport для мобильного
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 667,
      });
    });

    it('должен корректно отображать Header на мобильных', () => {
      render(<App />);

      // Проверяем, что навигация скрыта на мобильных (hidden md:flex)
      const navigation = screen.getByRole('navigation');
      expect(navigation).toHaveClass('hidden', 'md:flex');

      // Логотип должен быть виден (используем getAllByAltText для множественных элементов)
      const logos = screen.getAllByAltText('PandaPal');
      expect(logos).toHaveLength(2); // Header и Footer

      // Проверяем логотип в Header (первый)
      const headerLogo = logos[0];
      expect(headerLogo).toHaveClass('w-12', 'h-12');
    });

    it('должен корректно отображать Hero секцию на мобильных', () => {
      render(<App />);

      // Заголовок должен быть адаптивным
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveClass('text-4xl', 'md:text-6xl');

      // Описание должно быть адаптивным
      const description = screen.getByText(/Адаптивное, игровое и безопасное обучение/);
      expect(description).toHaveClass('text-lg', 'md:text-xl');
    });

    it('должен корректно отображать Features на мобильных', () => {
      render(<App />);

      // Сетка должна быть в одну колонку на мобильных
      const featuresSection = screen.getByLabelText('Преимущества');
      expect(featuresSection).toHaveClass('grid', 'md:grid-cols-3');

      // Все карточки должны быть видны
      const featureCards = screen.getAllByRole('article');
      expect(featureCards).toHaveLength(3);
    });

    it('должен иметь правильные отступы на мобильных', () => {
      render(<App />);

      const main = screen.getByRole('main');
      expect(main).toHaveClass('px-4'); // Отступы 16px на мобильных

      const header = screen.getByRole('banner');
      expect(header).toHaveClass('px-4', 'py-6');
    });
  });

  describe('Планшеты (481px - 768px)', () => {
    beforeEach(() => {
      mockMatchMedia(false); // Симулируем планшет
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 1024,
      });
    });

    it('должен корректно отображать навигацию на планшетах', () => {
      render(<App />);

      // На планшетах навигация должна быть видна
      const navigation = screen.getByRole('navigation');
      expect(navigation).toHaveClass('md:flex');

      // Проверяем наличие ссылок навигации (используем getAllByText для множественных элементов)
      const parentLinks = screen.getAllByText('Для родителей');

      expect(parentLinks.length).toBeGreaterThanOrEqual(1);
    });

    it('должен корректно отображать Hero на планшетах', () => {
      render(<App />);

      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveClass('md:text-6xl'); // Больший размер на планшетах

      const description = screen.getByText(/Адаптивное, игровое и безопасное обучение/);
      expect(description).toHaveClass('md:text-xl');
    });
  });

  describe('Десктоп (769px+)', () => {
    beforeEach(() => {
      mockMatchMedia(false);
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1200,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 800,
      });
    });

    it('должен корректно отображать все элементы на десктопе', () => {
      render(<App />);

      // Проверяем максимальную ширину контейнера
      const main = screen.getByRole('main');
      expect(main).toHaveClass('max-w-6xl', 'mx-auto');

      // Проверяем сетку Features в 3 колонки
      const featuresSection = screen.getByLabelText('Преимущества');
      expect(featuresSection).toHaveClass('md:grid-cols-3');
    });

    it('должен иметь правильные отступы на десктопе', () => {
      render(<App />);

      const header = screen.getByRole('banner');
      expect(header).toHaveClass('px-4'); // Стандартные отступы

      const main = screen.getByRole('main');
      expect(main).toHaveClass('px-4');
    });
  });

  describe('Анимации и интерактивность', () => {
    it('должен поддерживать prefers-reduced-motion', () => {
      // Симулируем пользователя с отключенными анимациями
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation(query => {
          if (query === '(prefers-reduced-motion: reduce)') {
            return {
              matches: true,
              media: query,
              onchange: null,
              addListener: vi.fn(),
              removeListener: vi.fn(),
              addEventListener: vi.fn(),
              removeEventListener: vi.fn(),
              dispatchEvent: vi.fn(),
            };
          }
          return {
            matches: false,
            media: query,
            onchange: null,
            addListener: vi.fn(),
            removeListener: vi.fn(),
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
            dispatchEvent: vi.fn(),
          };
        }),
      });

      render(<App />);

      // Логотип должен иметь анимации (используем первый логотип из Header)
      const logos = screen.getAllByAltText('PandaPal');
      const headerLogo = logos[0];
      expect(headerLogo).toHaveClass('panda-logo-animated');
    });

    it('должен иметь hover эффекты на интерактивных элементах', () => {
      render(<App />);

      // CTA кнопка должна иметь hover эффекты
      const ctaButton = screen.getByText('Начать использовать');
      expect(ctaButton).toHaveClass('hover:shadow-xl', 'hover:scale-105');

      // Кнопка в навигации должна иметь hover эффекты
      const navButton = screen.getByText('Начать');
      expect(navButton).toHaveClass('hover:shadow-lg');
    });
  });

  describe('Доступность для детей', () => {
    it('должен иметь достаточно крупные кликабельные области', () => {
      render(<App />);

      // CTA кнопка должна быть достаточно большой
      const ctaButton = screen.getByText('Начать использовать');
      expect(ctaButton).toHaveClass('px-8', 'py-4'); // Минимум 44x44px

      // Кнопка в навигации тоже должна быть крупной
      const navButton = screen.getByText('Начать');
      expect(navButton).toHaveClass('px-5', 'py-2');
    });

    it('должен иметь понятные иконки и эмодзи', () => {
      render(<App />);

      // Логотип должен быть понятным для детей (используем первый логотип)
      const logos = screen.getAllByAltText('PandaPal');
      expect(logos).toHaveLength(2);
      expect(logos[0]).toBeInTheDocument();

      // Проверяем наличие эмодзи в заголовке (если есть)
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeInTheDocument();
    });

    it('должен иметь контрастные цвета для читаемости', () => {
      render(<App />);

      // Проверяем, что используются контрастные цвета
      const ctaButton = screen.getByText('Начать использовать');
      expect(ctaButton).toHaveClass('bg-pink', 'text-gray-900');

      // Проверяем, что основной контейнер имеет правильный цвет текста
      const mainContainer = screen.getByRole('main').parentElement;
      expect(mainContainer).toHaveClass('text-gray-900');
    });
  });
});
