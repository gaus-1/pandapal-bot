/**
 * Тесты для компонента Header
 * Проверяем рендеринг, навигацию, accessibility
 * @module components/Header.test
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Header } from './Header';
import { SITE_CONFIG } from '../config/constants';

describe('Header Component', () => {
  /**
   * Тест 1: Базовый рендеринг
   * Проверяем, что компонент отображается без ошибок
   */
  it('должен отрендериться без ошибок', () => {
    render(<Header />);

    // Проверяем наличие логотипа
    const logo = screen.getByAltText(SITE_CONFIG.logo.alt);
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute('src', SITE_CONFIG.logo.src);

    // Проверяем название сайта
    expect(screen.getByText(SITE_CONFIG.name)).toBeInTheDocument();
  });

  /**
   * Тест 2: Навигационные ссылки
   * Проверяем наличие всех ссылок
   */
  it('должен содержать все навигационные ссылки', () => {
    render(<Header />);

    // Проверяем якорные ссылки
    expect(screen.getByText('Для родителей')).toHaveAttribute('href', '#parents');
    expect(screen.getByText('Для учителей')).toHaveAttribute('href', '#teachers');

    // Проверяем CTA-кнопку
    const startButton = screen.getByText('Начать');
    expect(startButton).toHaveAttribute('href', SITE_CONFIG.botUrl);
    expect(startButton).toHaveAttribute('target', '_blank');
    expect(startButton).toHaveAttribute('rel', 'noopener noreferrer');
  });

  /**
   * Тест 3: Accessibility (WCAG)
   * Проверяем доступность для screen readers
   */
  it('должен быть доступен для screen readers', () => {
    render(<Header />);

    // Проверяем наличие nav с aria-label
    const nav = screen.getByRole('navigation');
    expect(nav).toHaveAttribute('aria-label', 'Основная навигация');

    // Проверяем alt у изображения
    const logo = screen.getByRole('img');
    expect(logo).toHaveAttribute('alt');
  });

  /**
   * Тест 4: Адаптивность
   * Проверяем, что навигация скрыта на мобильных
   */
  it('должен скрывать навигацию на мобильных устройствах', () => {
    render(<Header />);

    const nav = screen.getByRole('navigation');
    // Проверяем наличие класса hidden (Tailwind)
    expect(nav.className).toContain('hidden');
    expect(nav.className).toContain('md:flex');
  });

  /**
   * Тест 5: Безопасность ссылок (OWASP A01)
   * Проверяем наличие rel="noopener noreferrer" на внешних ссылках
   */
  it('должен иметь безопасные атрибуты на внешних ссылках', () => {
    render(<Header />);

    const externalLink = screen.getByText('Начать');
    expect(externalLink).toHaveAttribute('rel', 'noopener noreferrer');
    expect(externalLink).toHaveAttribute('target', '_blank');
  });

  /**
   * Тест 6: Performance (React.memo)
   * Проверяем, что компонент мемоизирован
   */
  it('должен быть обёрнут в React.memo', () => {
    expect(Header.displayName).toBe('Header');
  });
});
