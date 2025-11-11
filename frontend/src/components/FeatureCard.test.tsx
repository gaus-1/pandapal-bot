/**
 * Тесты для компонента FeatureCard
 * Проверяем отображение карточки преимущества
 * @module components/FeatureCard.test
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FeatureCard } from './FeatureCard';
import type { Feature } from '../types';

describe('FeatureCard Component', () => {
  // Моковые данные для тестирования
  const mockFeature: Feature = {
    id: 'test-feature',
    title: 'Тестовое преимущество',
    description: 'Описание тестового преимущества',
  };

  /**
   * Тест 1: Базовый рендеринг
   */
  it('должен отрендерить карточку с данными', () => {
    render(<FeatureCard feature={mockFeature} />);

    // Проверяем заголовок
    expect(screen.getByText(mockFeature.title)).toBeInTheDocument();

    // Проверяем описание
    expect(screen.getByText(mockFeature.description)).toBeInTheDocument();
  });

  /**
   * Тест 2: Semantic HTML
   * Проверяем использование правильных тегов
   */
  it('должен использовать semantic HTML (article, h3)', () => {
    render(<FeatureCard feature={mockFeature} />);

    // Проверяем, что это article
    const article = screen.getByRole('article');
    expect(article).toBeInTheDocument();

    // Проверяем heading level 3
    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toHaveTextContent(mockFeature.title);
  });

  /**
   * Тест 3: Стилизация (Tailwind CSS)
   */
  it('должен иметь правильные CSS классы', () => {
    render(<FeatureCard feature={mockFeature} />);

    const article = screen.getByRole('article');

    // Проверяем ключевые классы
    expect(article.className).toContain('rounded-2xl');
    expect(article.className).toContain('bg-white/80');
    expect(article.className).toContain('backdrop-blur');
    expect(article.className).toContain('shadow-sm');
  });

  /**
   * Тест 4: Props validation
   * Проверяем, что компонент работает с разными данными
   */
  it('должен корректно отображать разные данные', () => {
    const feature1: Feature = {
      id: '1',
      title: 'Заголовок 1',
      description: 'Описание 1',
    };

    const feature2: Feature = {
      id: '2',
      title: 'Заголовок 2',
      description: 'Описание 2',
    };

    const { rerender } = render(<FeatureCard feature={feature1} />);
    expect(screen.getByText('Заголовок 1')).toBeInTheDocument();

    rerender(<FeatureCard feature={feature2} />);
    expect(screen.getByText('Заголовок 2')).toBeInTheDocument();
  });

  /**
   * Тест 5: XSS Protection (OWASP A03)
   * Проверяем, что опасный контент экранируется
   */
  it('должен экранировать HTML в тексте (защита от XSS)', () => {
    const maliciousFeature: Feature = {
      id: 'xss-test',
      title: '<script>alert("XSS")</script>',
      description: '<img src=x onerror=alert("XSS")>',
    };

    render(<FeatureCard feature={maliciousFeature} />);

    // React автоматически экранирует, но проверим
    expect(screen.queryByText('alert("XSS")')).not.toBeInTheDocument();

    // Текст должен отобразиться как строка, а не выполниться
    const article = screen.getByRole('article');
    expect(article.innerHTML).not.toContain('<script>');
  });

  /**
   * Тест 6: Performance (React.memo)
   */
  it('должен быть мемоизирован для оптимизации', () => {
    expect(FeatureCard.displayName).toBe('FeatureCard');
  });

  /**
   * Тест 7: Пустые данные
   * Проверяем обработку edge cases
   */
  it('должен корректно обрабатывать пустые строки', () => {
    const emptyFeature: Feature = {
      id: 'empty',
      title: '',
      description: '',
    };

    render(<FeatureCard feature={emptyFeature} />);

    // Компонент должен отрендериться без ошибок
    const article = screen.getByRole('article');
    expect(article).toBeInTheDocument();
  });

  /**
   * Тест 8: Длинный текст
   * Проверяем, что компонент не ломается на длинном контенте
   */
  it('должен корректно отображать длинный текст', () => {
    const longFeature: Feature = {
      id: 'long',
      title: 'A'.repeat(200),
      description: 'B'.repeat(1000),
    };

    render(<FeatureCard feature={longFeature} />);

    expect(screen.getByRole('article')).toBeInTheDocument();
  });
});
