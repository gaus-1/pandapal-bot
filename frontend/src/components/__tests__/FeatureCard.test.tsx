/**
 * Тесты для компонента FeatureCard
 * Проверяем отображение карточки преимущества
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FeatureCard } from '../FeatureCard';
import type { Feature } from '../../types';

describe('FeatureCard Component', () => {
  const mockFeature: Feature = {
    id: 'test-feature',
    title: 'Тестовое преимущество',
    description: 'Описание тестового преимущества',
  };

  it('рендерится без ошибок', () => {
    const { container } = render(<FeatureCard feature={mockFeature} />);
    expect(container).toBeInTheDocument();
  });

  it('отображает заголовок преимущества', () => {
    render(<FeatureCard feature={mockFeature} />);
    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toHaveTextContent('Тестовое преимущество');
  });

  it('отображает описание преимущества', () => {
    render(<FeatureCard feature={mockFeature} />);
    expect(screen.getByText('Описание тестового преимущества')).toBeInTheDocument();
  });

  it('имеет правильную структуру article', () => {
    const { container } = render(<FeatureCard feature={mockFeature} />);
    const article = container.querySelector('article');
    expect(article).toBeInTheDocument();
  });

  it('применяет hover стили', () => {
    const { container } = render(<FeatureCard feature={mockFeature} />);
    const article = container.querySelector('article');
    expect(article).toHaveClass('hover:shadow-md');
  });

  it('корректно рендерит эмодзи в тексте', () => {
    const featureWithEmoji: Feature = {
      id: 'emoji-test',
      title: '🐼 Панда',
      description: '✨ Магия',
    };
    render(<FeatureCard feature={featureWithEmoji} />);
    expect(screen.getByText('🐼 Панда')).toBeInTheDocument();
    expect(screen.getByText('✨ Магия')).toBeInTheDocument();
  });

  it('корректно рендерит длинный текст', () => {
    const longFeature: Feature = {
      id: 'long-test',
      title: 'A'.repeat(100),
      description: 'B'.repeat(500),
    };
    render(<FeatureCard feature={longFeature} />);
    expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument();
  });
});
