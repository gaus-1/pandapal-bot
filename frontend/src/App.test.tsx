/**
 * Тесты для главного компонента App
 * Проверяем композицию компонентов и структуру страницы
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App Component', () => {
  it('должен рендериться без ошибок', () => {
    const { container } = render(<App />);
    expect(container).toBeInTheDocument();
  });

  it('должен содержать Header', () => {
    render(<App />);

    // Проверяем наличие логотипа из Header
    const logo = screen.getByAltText(/pandapal/i);
    expect(logo).toBeInTheDocument();
  });

  it('должен содержать Hero секцию', () => {
    render(<App />);

    // Проверяем главный заголовок из Hero
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toBeInTheDocument();
  });

  it('должен содержать main элемент', () => {
    render(<App />);

    const main = screen.getByRole('main');
    expect(main).toBeInTheDocument();
  });

  it('должен иметь переключатель темной темы', () => {
    render(<App />);

    // DarkModeToggle должен быть в документе
    const darkModeToggle = screen.getByRole('button', { name: /theme/i }) ||
                          document.querySelector('[data-testid="dark-mode-toggle"]') ||
                          document.querySelector('button');
    expect(darkModeToggle).toBeInTheDocument();
  });

  it('должен иметь градиентный фон', () => {
    const { container } = render(<App />);

    const rootDiv = container.firstChild as HTMLElement;
    expect(rootDiv).toHaveClass('min-h-screen');
    expect(rootDiv.className).toMatch(/bg-gradient/);
  });

  it('должен содержать CTA кнопки', () => {
    render(<App />);

    const ctaButtons = screen.getAllByRole('link');
    expect(ctaButtons.length).toBeGreaterThan(0);
  });

  it('должен быть доступным (accessibility)', () => {
    render(<App />);

    // Проверяем наличие semantic HTML
    const main = screen.getByRole('main');
    const nav = screen.getByRole('navigation');
    const heading = screen.getByRole('heading', { level: 1 });

    expect(main).toBeInTheDocument();
    expect(nav).toBeInTheDocument();
    expect(heading).toBeInTheDocument();
  });
});
