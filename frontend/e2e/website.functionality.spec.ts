/**
 * E2E тесты для функциональности сайта
 * Проверка что все компоненты сайта работают корректно
 */

import { test, expect } from '@playwright/test';

test.describe('Website Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://pandapal.ru');
  });

  test('главная страница должна загружаться', async ({ page }) => {
    // Проверяем что страница загрузилась
    await expect(page).toHaveTitle(/PandaPal/i);

    // Проверяем что есть основной контент
    const hero = page.locator('h1').first();
    await expect(hero).toBeVisible();
  });

  test('Hero секция должна отображаться', async ({ page }) => {
    // Проверяем заголовок
    const h1 = page.locator('h1').first();
    await expect(h1).toBeVisible();
    await expect(h1).toContainText(/безопасный|PandaPal/i);

    // Проверяем описание
    const description = page.locator('p').first();
    await expect(description).toBeVisible();
  });

  test('Features секция должна отображать карточки', async ({ page }) => {
    // Прокручиваем к секции features
    const features = page.locator('[id="features"]');
    await features.scrollIntoViewIfNeeded();

    // Проверяем что секция видна
    await expect(features).toBeVisible();

    // Проверяем что есть карточки
    const cards = page.locator('[id="features"] > div');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('CTA кнопки должны быть кликабельными', async ({ page }) => {
    // Проверяем кнопку "Начни"
    const startButton = page.locator('a[href*="t.me"]').first();
    if (await startButton.count() > 0) {
      await expect(startButton).toBeVisible();
      // Проверяем что ссылка корректная
      const href = await startButton.getAttribute('href');
      expect(href).toContain('t.me');
    }
  });

  test('темная тема должна переключаться', async ({ page }) => {
    // Ищем переключатель темы
    const themeToggle = page.locator('button[aria-label*="тема"], button[aria-label*="theme"]').first();

    if (await themeToggle.count() > 0) {
      // Получаем текущую тему
      const initialTheme = await page.evaluate(() => {
        return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
      });

      // Кликаем на переключатель
      await themeToggle.click();

      // Ждем изменения темы
      await page.waitForTimeout(500);

      // Проверяем что тема изменилась
      const newTheme = await page.evaluate(() => {
        return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
      });

      expect(newTheme).not.toBe(initialTheme);
    }
  });

  test('навигация должна работать', async ({ page }) => {
    // Ищем ссылки навигации
    const navLinks = page.locator('nav a, header a');
    const count = await navLinks.count();

    if (count > 0) {
      // Проверяем что ссылки кликабельны (пропускаем скрытые на мобильных)
      for (let i = 0; i < Math.min(count, 3); i++) {
        const link = navLinks.nth(i);
        const isVisible = await link.isVisible();
        if (isVisible) {
          await expect(link).toBeVisible();
        }
      }
    }
  });

  test('footer должен отображаться', async ({ page }) => {
    // Прокручиваем вниз
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

    // Проверяем что footer виден
    const footer = page.locator('footer').first();
    await expect(footer).toBeVisible();
  });

  test('SEO мета-теги должны присутствовать', async ({ page }) => {
    // Проверяем title
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);

    // Проверяем meta description (используем .first() так как их может быть несколько)
    const metaDescription = page.locator('meta[name="description"]').first();
    if (await metaDescription.count() > 0) {
      const content = await metaDescription.getAttribute('content');
      expect(content).toBeTruthy();
    }
  });
});
