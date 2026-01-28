/**
 * Тесты для компонента DarkModeToggle
 * Проверяем переключение темы и сохранение в localStorage
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DarkModeToggle } from '../DarkModeToggle';

describe('DarkModeToggle Component', () => {
  beforeEach(() => {
    // Очищаем localStorage перед каждым тестом
    localStorage.clear();
    // Удаляем класс dark
    document.documentElement.classList.remove('dark');
  });

  it('рендерится без ошибок', () => {
    render(<DarkModeToggle />);
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  it('имеет правильную aria-label', () => {
    render(<DarkModeToggle />);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label');
  });

  it('имеет правильный title', () => {
    render(<DarkModeToggle />);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('title');
  });

  it('отображает иконку луны по умолчанию (светлая тема)', () => {
    render(<DarkModeToggle />);
    const button = screen.getByRole('button');
    const svg = button.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('переключает тему при клике', () => {
    render(<DarkModeToggle />);
    const button = screen.getByRole('button');

    // Первый клик - включаем темную тему
    fireEvent.click(button);
    expect(document.documentElement.classList.contains('dark')).toBe(true);

    // Второй клик - выключаем темную тему
    fireEvent.click(button);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('сохраняет выбор темы в localStorage', () => {
    render(<DarkModeToggle />);
    const button = screen.getByRole('button');

    // Включаем темную тему
    fireEvent.click(button);
    expect(localStorage.getItem('theme')).toBe('dark');

    // Выключаем темную тему
    fireEvent.click(button);
    expect(localStorage.getItem('theme')).toBe('light');
  });

  it('загружает сохраненную тему из localStorage', () => {
    // Сохраняем темную тему в localStorage
    localStorage.setItem('theme', 'dark');

    render(<DarkModeToggle />);

    // Проверяем что темная тема применена
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('использует системные предпочтения если нет сохраненной темы', () => {
    // Mock window.matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation(query => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    render(<DarkModeToggle />);

    // Должна применится темная тема по системным предпочтениям
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });
});
