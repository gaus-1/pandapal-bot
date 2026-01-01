/**
 * Тесты для компонента Section
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Section } from '../Section';
import type { Section as SectionType } from '../../types';

describe('Section Component', () => {
  const mockSection: SectionType = {
    id: 'test-section',
    title: 'Тестовая секция',
    description: 'Контент секции',
  };

  it('рендерится без ошибок', () => {
    const { container } = render(<Section section={mockSection} />);
    expect(container).toBeInTheDocument();
  });

  it('отображает заголовок секции', () => {
    render(<Section section={mockSection} />);
    expect(screen.getByText('Тестовая секция')).toBeInTheDocument();
  });

  it('отображает описание секции', () => {
    render(<Section section={mockSection} />);
    expect(screen.getByText('Контент секции')).toBeInTheDocument();
  });

  it('имеет правильную структуру section', () => {
    const { container } = render(<Section section={mockSection} />);
    const section = container.querySelector('section');
    expect(section).toBeInTheDocument();
    expect(section).toHaveAttribute('id', 'test-section');
  });

  it('корректно рендерит секцию с минимальными данными', () => {
    const minimalSection: SectionType = {
      id: 'minimal',
      title: 'Минимальная секция',
      description: 'Описание',
    };
    render(<Section section={minimalSection} />);
    expect(screen.getByText('Минимальная секция')).toBeInTheDocument();
  });
});
