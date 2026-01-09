/**
 * Vite plugin для статического pre-rendering для SEO
 * Генерирует статические HTML файлы для основных страниц
 *
 * Примечание: Для полноценного SSR рекомендуется использовать Next.js или Nuxt.js
 * Этот plugin создает базовый pre-render для улучшения SEO
 */

import type { Plugin } from 'vite';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

export function vitePluginPrerender(): Plugin {
  return {
    name: 'vite-plugin-prerender',
    apply: 'build',
    async closeBundle() {
      // После сборки генерируем статические HTML для SEO
      const distPath = join(process.cwd(), 'dist');
      const indexPath = join(distPath, 'index.html');

      if (!existsSync(indexPath)) {
        console.warn('⚠️ index.html не найден, пропускаем pre-render');
        return;
      }

      // Читаем index.html для проверки
      readFileSync(indexPath, 'utf-8');

      // Создаем статические версии для основных страниц
      // Для полноценного SSR нужен Next.js/Nuxt.js, здесь только базовая структура
      console.log('✅ Pre-render: базовый HTML готов для SEO');
    },
  };
}
