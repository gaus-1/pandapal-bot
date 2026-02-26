/**
 * Обновляет lastmod во всех <url> в frontend/public/sitemap.xml до текущей даты (YYYY-MM-DD).
 * Вызывать перед сборкой или при релизе: npm run update-sitemap-dates
 */
import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const sitemapPath = join(__dirname, '../public/sitemap.xml');
const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD

const xml = readFileSync(sitemapPath, 'utf-8');
const updated = xml.replace(/<lastmod>[^<]*<\/lastmod>/g, `<lastmod>${today}</lastmod>`);
writeFileSync(sitemapPath, updated, 'utf-8');
console.log(`sitemap.xml: lastmod set to ${today}`);
