/**
 * Тесты для компонента Header
 * Проверяем отображение логотипа, навигации и CTA-кнопки
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Header } from '../Header';

describe('Header Component', () => {
  it('должен отображать логотип PandaPal', () => {
    render(<Header />);

    const logo = screen.getByAlt(/pandapal/i);
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute('src');
  });

  it('должен отображать название сайта', () => {
    render(<Header />);

    const siteName = screen.getByText(/pandapal/i);
    expect(siteName).toBeInTheDocument();
  });

  it('должен содержать навигационные ссылки', () => {
    render(<Header />);

    const nav = screen.getByRole('navigation');
    expect(nav).toBeInTheDocument();
  });

  it('должен иметь CTA-кнопку "Начать"', () => {
    render(<Header />);

    const ctaButton = screen.getByRole('link', { name: /начать/i });
    expect(ctaButton).toBeInTheDocument();
    expect(ctaButton).toHaveAttribute('href');
    expect(ctaButton).toHaveAttribute('target', '_blank');
    expect(ctaButton).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('должен иметь правильную aria-label для навигации', () => {
    render(<Header />);

    const nav = screen.getByRole('navigation');
    expect(nav).toHaveAttribute('aria-label', 'Основная навигация');
  });

  it('логотип должен иметь правильные размеры', () => {
    render(<Header />);

    const logo = screen.getByAlt(/pandapal/i);
    expect(logo).toHaveAttribute('width', '48');
    expect(logo).toHaveAttribute('height', '48');
  });

  it('логотип должен загружаться с приоритетом', () => {
    render(<Header />);

    const logo = screen.getByAlt(/pandapal/i);
    expect(logo).toHaveAttribute('loading', 'eager');
  });
});
