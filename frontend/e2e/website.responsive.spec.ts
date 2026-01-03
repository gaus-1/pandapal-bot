/**
 * E2E тесты для адаптивности сайта
 * Проверка что сайт корректно работает на разных размерах экрана
 */

import { test, expect } from '@playwright/test';

test.describe('Website Responsive Design', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://pandapal.ru');
  });

  test('должен корректно отображаться на мобильных устройствах', async ({ page }) => {
    // Устанавливаем размер мобильного устройства
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE

    // Проверяем что Hero секция видна
    const hero = page.locator('section').first();
    await expect(hero).toBeVisible();

    // Проверяем что текст не выходит за границы
    const heroText = page.locator('h1').first();
    const boundingBox = await heroText.boundingBox();
    expect(boundingBox?.width).toBeLessThanOrEqual(375);
  });

  test('должен корректно отображаться на планшетах', async ({ page }) => {
    // Устанавливаем размер планшета
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad

    // Проверяем что контент адаптируется
    const features = page.locator('[id="features"]');
    await expect(features).toBeVisible();

    // Проверяем что карточки в сетке
    const featureCards = page.locator('[id="features"] > div');
    const count = await featureCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('должен корректно отображаться на десктопе', async ({ page }) => {
    // Устанавливаем размер десктопа
    await page.setViewportSize({ width: 1920, height: 1080 });

    // Проверяем что все секции видны
    const hero = page.locator('section').first();
    await expect(hero).toBeVisible();

    const features = page.locator('[id="features"]');
    await expect(features).toBeVisible();
  });

  test('навигация должна работать на всех размерах экрана', async ({ page }) => {
    const viewports = [
      { width: 375, height: 667 }, // Mobile
      { width: 768, height: 1024 }, // Tablet
      { width: 1920, height: 1080 }, // Desktop
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);

      // Проверяем что кнопки кликабельны
      const ctaButton = page.locator('a[href*="t.me"]').first();
      if (await ctaButton.count() > 0) {
        await expect(ctaButton).toBeVisible();
      }
    }
  });

  test('текст должен быть читаемым на всех размерах', async ({ page }) => {
    const viewports = [
      { width: 375, height: 667 },
      { width: 768, height: 1024 },
      { width: 1920, height: 1080 },
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);

      // Проверяем что заголовок виден
      const h1 = page.locator('h1').first();
      await expect(h1).toBeVisible();

      // Проверяем что текст не слишком маленький
      const fontSize = await h1.evaluate((el) => {
        return window.getComputedStyle(el).fontSize;
      });
      const fontSizeNum = parseFloat(fontSize);
      expect(fontSizeNum).toBeGreaterThan(16); // Минимум 16px для читаемости
    }
  });
});
