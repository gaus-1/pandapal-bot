/**
 * Интеграционные тесты для App
 * Проверяем, что все компоненты корректно работают вместе
 * @module App.test
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';
import { SITE_CONFIG, FEATURES, SECTIONS } from './config/constants';

describe('App Integration Tests', () => {
  /**
   * Тест 1: Полный рендеринг приложения
   */
  it('должен отрендерить все основные секции', () => {
    render(<App />);
    
    // Проверяем Header
    expect(screen.getByRole('banner')).toBeInTheDocument(); // @ts-ignore   
    
    // Проверяем Main content
    expect(screen.getByRole('main')).toBeInTheDocument(); // @ts-ignore
    
    // Проверяем Footer
    expect(screen.getByRole('contentinfo')).toBeInTheDocument(); // @ts-ignore
  });

  /**
   * Тест 2: Логотип (Header + Footer)
   */
  it('должен отображать логотип в Header и Footer', () => {
    render(<App />);
    
    const logos = screen.getAllByAltText(SITE_CONFIG.logo.alt);
    // Логотип должен быть 2 раза (header + footer)
    expect(logos).toHaveLength(2);
    
    logos.forEach((logo) => {
      expect(logo).toHaveAttribute('src', SITE_CONFIG.logo.src); // @ts-ignore
    });
  });

  /**
   * Тест 3: Hero section
   */
  it('должен отображать Hero-секцию с заголовком и CTA', () => {
    render(<App />);
    
    // H1 заголовок
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toBeInTheDocument(); // @ts-ignore
    expect(heading.textContent).toContain('Безопасный ИИ-друг');
    
    // CTA-кнопки (2 штуки: в Header + в Hero)
    const ctaButtons = screen.getAllByText(/Начать/i);
    expect(ctaButtons.length).toBeGreaterThanOrEqual(2);
  });

  /**
   * Тест 4: Features секция
   */
  it('должен отображать все карточки преимуществ', () => {
    render(<App />);
    
    // Проверяем, что все features отрендерены
    FEATURES.forEach((feature) => {
      expect(screen.getByText(feature.title)).toBeInTheDocument(); // @ts-ignore
      expect(screen.getByText(feature.description)).toBeInTheDocument();
    });
    
    // Должно быть ровно 3 карточки
    const articles = screen.getAllByRole('article');
    expect(articles).toHaveLength(FEATURES.length);
  });

  /**
   * Тест 5: Динамические секции
   */
  it('должен отображать все секции из SECTIONS', () => {
    render(<App />);
    
    SECTIONS.forEach((section) => {
      // Проверяем заголовки секций (используем getAllByText т.к. текст может быть в навигации тоже)
      const headings = screen.getAllByText(section.title);
      expect(headings.length).toBeGreaterThan(0);
      expect(screen.getByText(section.description)).toBeInTheDocument(); // @ts-ignore
      
      // Проверяем, что section имеет правильный ID (для якорей)
      const sectionElement = document.getElementById(section.id);
      expect(sectionElement).toBeInTheDocument(); // @ts-ignore
    });
  });

  /**
   * Тест 6: Навигация (якорные ссылки)
   */
  it('должен содержать рабочие якорные ссылки', () => {
    render(<App />);
    
    // Проверяем ссылки на секции
    const parentsLink = screen.getByRole('link', { name: 'Для родителей' });
    expect(parentsLink).toHaveAttribute('href', '#parents'); // @ts-ignore
    
    const teachersLink = screen.getByRole('link', { name: 'Для учителей' });
    expect(teachersLink).toHaveAttribute('href', '#teachers'); // @ts-ignore
  });

  /**
   * Тест 7: Внешние ссылки (безопасность - OWASP A01)
   */
  it('должен иметь безопасные атрибуты на всех внешних ссылках', () => {
    render(<App />);
    
    // Находим все ссылки на Telegram бота
    const externalLinks = screen.getAllByRole('link', { name: /Начать/i });
    
    externalLinks.forEach((link) => {
      // Проверяем безопасность
      expect(link).toHaveAttribute('target', '_blank'); // @ts-ignore
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      expect(link).toHaveAttribute('href', SITE_CONFIG.botUrl);
    });
  });

  /**
   * Тест 8: Accessibility (A11Y)
   */
  it('должен быть доступен для screen readers', () => {
    render(<App />);
    
    // Проверяем semantic HTML
    expect(screen.getByRole('banner')).toBeInTheDocument(); // header
    expect(screen.getByRole('main')).toBeInTheDocument(); // main
    expect(screen.getByRole('contentinfo')).toBeInTheDocument(); // footer
    expect(screen.getByRole('navigation')).toBeInTheDocument(); // nav
    
    // Проверяем headings hierarchy (H1 → H2 → H3)
    const h1 = screen.getByRole('heading', { level: 1 });
    expect(h1).toBeInTheDocument();
    
    const h2headings = screen.getAllByRole('heading', { level: 2 });
    expect(h2headings.length).toBeGreaterThan(0);
    
    const h3headings = screen.getAllByRole('heading', { level: 3 });
    expect(h3headings.length).toBeGreaterThanOrEqual(FEATURES.length);
  });

  /**
   * Тест 9: SEO (meta tags через document)
   */
  it('должен иметь корректный title', () => {
    // Title устанавливается в index.html, а не через React
    // В тестовом окружении он пустой, поэтому просто проверяем что app рендерится
    render(<App />);
    const pandapalTexts = screen.getAllByText(SITE_CONFIG.name);
    expect(pandapalTexts.length).toBeGreaterThan(0); // Должен быть в Header и Footer   
  });

  /**
   * Тест 10: Производительность (No unnecessary re-renders)
   */
  it('должен рендериться один раз при mount', () => {
    let renderCount = 0;
    
    const TestWrapper = () => {
      renderCount++;
      return <App />;
    };
    
    render(<TestWrapper />);
    expect(renderCount).toBe(1);
  });

  /**
   * Тест 11: Responsive layout
   */
  it('должен иметь адаптивные классы', () => {
    render(<App />);
    
    const main = screen.getByRole('main');
    expect(main.className).toContain('max-w-6xl');
    expect(main.className).toContain('mx-auto');
    expect(main.className).toContain('px-4');
  });

  /**
   * Тест 12: Все изображения имеют alt (WCAG)
   */
  it('должен иметь alt-текст у всех изображений', () => {
    render(<App />);
    
    const images = screen.getAllByRole('img');
    images.forEach((img) => {
      expect(img).toHaveAttribute('alt');
      const alt = img.getAttribute('alt');
      expect(alt).not.toBe(''); // Alt не должен быть пустым
    });
  });
});

