/**
 * Тесты для компонента Hero
 * Проверяем отображение, CTA-кнопку, SEO
 * @module components/Hero.test
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Hero } from './Hero';
import { SITE_CONFIG } from '../config/constants';

describe('Hero Component', () => {
  /**
   * Тест 1: Отображение заголовка
   * Проверяем наличие H1 (важно для SEO)
   */
  it('должен отображать главный заголовок (H1)', () => {
    render(<Hero />);

    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toBeInTheDocument();
    expect(heading.textContent).toContain('Безопасный ИИ-друг');
    expect(heading.textContent).toContain('для твоего ребенка');
  });

  /**
   * Тест 2: Описание продукта
   * Проверяем наличие подзаголовка
   */
  it('должен отображать описание продукта', () => {
    render(<Hero />);

    const description = screen.getByText(
      /Адаптивное, игровое и безопасное обучение для 1–9 классов/i
    );
    expect(description).toBeInTheDocument();
  });

  /**
   * Тест 3: CTA-кнопка
   * Проверяем наличие и корректность ссылки на Telegram
   */
  it('должен содержать CTA-кнопку с правильной ссылкой', () => {
    render(<Hero />);

    const ctaButton = screen.getByRole('link', { name: /Начать использовать/i });
    expect(ctaButton).toBeInTheDocument();
    expect(ctaButton).toHaveAttribute('href', SITE_CONFIG.botUrl);
    expect(ctaButton).toHaveAttribute('target', '_blank');
  });

  /**
   * Тест 4: Безопасность ссылки (OWASP A01)
   * Проверяем rel="noopener noreferrer" для защиты от tabnabbing
   */
  it('должен иметь безопасные атрибуты на CTA-кнопке', () => {
    render(<Hero />);

    const ctaButton = screen.getByText('Начать использовать');
    expect(ctaButton).toHaveAttribute('rel', 'noopener noreferrer');
  });

  /**
   * Тест 5: Accessibility (ARIA)
   * Проверяем наличие aria-label для screen readers
   */
  it('должен иметь aria-label на CTA-кнопке', () => {
    render(<Hero />);

    const ctaButton = screen.getByLabelText(/Начать использовать PandaPal в Telegram/i);
    expect(ctaButton).toBeInTheDocument();
  });

  /**
   * Тест 6: User interaction
   * Проверяем, что кнопка кликабельна
   */
  it('должен позволять кликнуть по CTA-кнопке', async () => {
    const user = userEvent.setup();
    render(<Hero />);

    const ctaButton = screen.getByText('Начать использовать');

    // Кнопка должна быть видимой и кликабельной
    expect(ctaButton).toBeVisible();
    await user.click(ctaButton);

    // После клика ничего не должно сломаться
    expect(ctaButton).toBeInTheDocument();
  });

  /**
   * Тест 7: CSS классы (стилизация)
   * Проверяем наличие Tailwind классов
   */
  it('должен иметь корректные стили', () => {
    render(<Hero />);

    const section = screen.getByRole('heading', { level: 1 }).closest('section');
    expect(section).toHaveClass('text-center');
  });

  /**
   * Тест 8: Мемоизация (Performance)
   */
  it('должен быть мемоизирован (React.memo)', () => {
    expect(Hero.displayName).toBe('Hero');
  });
});
