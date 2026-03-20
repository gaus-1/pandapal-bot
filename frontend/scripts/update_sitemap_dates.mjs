/**
 * Обновляет lastmod в frontend/public/sitemap.xml.
 *
 * По умолчанию обновляет ВСЕ URL до текущей даты (YYYY-MM-DD).
 * С флагом --diff обновляет только URL, чьи страницы реально изменились
 * (проверяет mtime файлов в src/, config/, components/ и features/).
 *
 * Использование:
 *   npm run update-sitemap-dates          # все URL = сегодня
 *   npm run update-sitemap-dates -- --diff  # по mtime файлов
 */
import { readFileSync, writeFileSync, statSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sitemapPath = join(__dirname, '../public/sitemap.xml');
const srcRoot = join(__dirname, '../src');
const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
const isDiff = process.argv.includes('--diff');

/**
 * Маппинг URL-слагов -> маска файлов/директорий, влияющих на контент страницы.
 * Если хоть один файл из списка новее текущего lastmod — обновляем дату.
 */
const PAGE_SOURCES = {
  '/': ['App.tsx', 'components/Hero.tsx', 'components/Features.tsx', 'components/CallToAction.tsx', 'config/constants.ts'],
  '/bezopasnyy-ai-dlya-detey': ['features/Discoverability'],
  '/pomoshch-s-domashkoy-v-telegram': ['features/Discoverability'],
  '/igra-moya-panda': ['features/Discoverability', 'config/seo-text.ts'],
  '/premium': ['features/Premium'],
  '/donation': ['features/Donation'],
  '/privacy': ['features/Legal'],
  '/personal-data': ['features/Legal'],
  '/offer': ['features/Legal'],
  '/help': ['features/Help', 'config/help-articles.ts'],
};

/** Получить максимальный mtime среди файлов внутри пути (рекурсивно). */
function getLatestMtime(basePath) {
  try {
    const stat = statSync(basePath);
    if (stat.isFile()) return stat.mtimeMs;
    if (stat.isDirectory()) {
      let max = 0;
      for (const entry of readdirSync(basePath, { withFileTypes: true })) {
        const child = join(basePath, entry.name);
        const t = getLatestMtime(child);
        if (t > max) max = t;
      }
      return max;
    }
  } catch {
    return 0;
  }
  return 0;
}

/** Определить дату lastmod для конкретного URL. */
function getLastmod(urlPath) {
  if (!isDiff) return today;

  const sources = PAGE_SOURCES[urlPath];
  if (!sources) return today; // для help-статей и прочих — ставим сегодня

  let maxMs = 0;
  for (const rel of sources) {
    const abs = join(srcRoot, rel);
    const t = getLatestMtime(abs);
    if (t > maxMs) maxMs = t;
  }

  return maxMs > 0 ? new Date(maxMs).toISOString().slice(0, 10) : today;
}

const xml = readFileSync(sitemapPath, 'utf-8');

// Обновляем lastmod для каждого <url>, вычисляя дату по маппингу
const updated = xml.replace(
  /<url>\s*<loc>([^<]+)<\/loc>\s*<lastmod>[^<]*<\/lastmod>/g,
  (match, loc) => {
    const urlPath = loc.replace('https://pandapal.ru', '').replace(/\/$/, '') || '/';
    const newDate = getLastmod(urlPath);
    return match.replace(/<lastmod>[^<]*<\/lastmod>/, `<lastmod>${newDate}</lastmod>`);
  }
);

writeFileSync(sitemapPath, updated, 'utf-8');
console.log(`sitemap.xml: lastmod updated${isDiff ? ' (diff mode)' : ` (all → ${today})`}`);
