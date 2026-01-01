/**
 * Тесты для компонента Features
 * Проверяем отображение списка преимуществ
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Features } from '../Features';

describe('Features Component', () => {
  it('рендерится без ошибок', () => {
    const { container } = render(<Features />);
    expect(container).toBeInTheDocument();
  });

  it('имеет правильную семантическую структуру section', () => {
    const { container } = render(<Features />);
    const section = container.querySelector('section');
    expect(section).toBeInTheDocument();
    expect(section).toHaveAttribute('id', 'features');
  });

  it('имеет aria-label для доступности', () => {
    const { container } = render(<Features />);
    const section = container.querySelector('section');
    expect(section).toHaveAttribute('aria-label', 'Преимущества');
  });

  it('отображает все карточки преимуществ', () => {
    const { container } = render(<Features />);
    const articles = container.querySelectorAll('article');
    expect(articles.length).toBeGreaterThan(0);
  });

  it('применяет grid layout', () => {
    const { container } = render(<Features />);
    const section = container.querySelector('section');
    expect(section).toHaveClass('grid');
    expect(section).toHaveClass('md:grid-cols-3');
  });

  it('применяет анимацию fade-in к карточкам', () => {
    const { container } = render(<Features />);
    const animatedDivs = container.querySelectorAll('.animate-fade-in');
    expect(animatedDivs.length).toBeGreaterThan(0);
  });
});
