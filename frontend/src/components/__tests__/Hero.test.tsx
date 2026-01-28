/**
 * Тесты для компонента Hero
 * Проверяем главную секцию сайта, CTA-кнопки и SEO
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Hero } from '../Hero';

describe('Hero Component', () => {
  it('должен отображать главный заголовок', () => {
    render(<Hero />);

    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveTextContent(/безопасный/i);
    expect(heading).toHaveTextContent(/ребенка/i);
  });

  it('должен отображать описание продукта', () => {
    render(<Hero />);

    const description = screen.getByText(/адаптивное.*игровое.*безопасное обучение/i);
    expect(description).toBeInTheDocument();
  });

  it('должен иметь две CTA-кнопки', () => {
    render(<Hero />);

    const primaryCta = screen.getByRole('link', { name: /начать использовать pandapal/i });
    const secondaryCta = screen.getByRole('link', { name: /узнать больше/i });

    expect(primaryCta).toBeInTheDocument();
    expect(secondaryCta).toBeInTheDocument();
  });

  it('основная CTA должна вести на Telegram бота', () => {
    render(<Hero />);

    const primaryCta = screen.getByRole('link', { name: /начать использовать pandapal/i });
    expect(primaryCta).toHaveAttribute('href', 'https://t.me/PandaPalBot');
    expect(primaryCta).toHaveAttribute('target', '_blank');
    expect(primaryCta).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('вторичная CTA должна вести на секцию #cta', () => {
    render(<Hero />);

    const secondaryCta = screen.getByRole('link', { name: /узнать больше/i });
    expect(secondaryCta).toHaveAttribute('href', '#cta');
  });

  it('CTA-кнопки должны иметь data-атрибуты для аналитики', () => {
    render(<Hero />);

    const primaryCta = screen.getByRole('link', { name: /начать использовать pandapal/i });
    const secondaryCta = screen.getByRole('link', { name: /узнать больше/i });

    expect(primaryCta).toHaveAttribute('data-cta-variant', 'primary');
    expect(secondaryCta).toHaveAttribute('data-cta-variant', 'secondary');
  });

  it('должен содержать Schema.org разметку для SEO', () => {
    const { container } = render(<Hero />);

    const schemaScript = container.querySelector('script[type="application/ld+json"]');
    expect(schemaScript).toBeInTheDocument();

    if (schemaScript) {
      const schemaData = JSON.parse(schemaScript.textContent || '{}');
      expect(schemaData['@type']).toBe('SoftwareApplication');
      expect(schemaData.name).toBe('PandaPal');
      expect(schemaData.applicationCategory).toBe('EducationalApplication');
    }
  });

  it('должен показывать кнопки CTA', () => {
    render(<Hero />);

    // Проверяем что есть кнопка "Начни"
    const primaryCta = screen.getByRole('link', { name: /начать использовать pandapal/i });
    expect(primaryCta).toHaveAttribute('href', 'https://t.me/PandaPalBot');

    // Проверяем что есть кнопка "Узнать больше"
    const secondaryCta = screen.getByRole('link', { name: /узнать больше/i });
    expect(secondaryCta).toHaveAttribute('href', '#cta');
  });
});
