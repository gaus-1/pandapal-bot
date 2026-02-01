/**
 * Тесты SEO: index.html и robots.txt.
 * Проверяем canonical, OG, отсутствие SearchAction и aggregateRating в Organization.
 */

import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { describe, it, expect } from 'vitest';

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(__dirname, '../..');

function readIndexHtml(): string {
  return readFileSync(join(frontendRoot, 'index.html'), 'utf-8');
}

function readRobotsTxt(): string {
  return readFileSync(join(frontendRoot, 'public', 'robots.txt'), 'utf-8');
}

describe('SEO: index.html', () => {
  it('должен содержать canonical URL', () => {
    const html = readIndexHtml();
    expect(html).toContain('rel="canonical"');
    expect(html).toContain('href="https://pandapal.ru/"');
  });

  it('должен содержать meta description', () => {
    const html = readIndexHtml();
    expect(html).toContain('name="description"');
    expect(html).toMatch(/content="[^"]*PandaPal[^"]*"/);
  });

  it('должен содержать Open Graph теги', () => {
    const html = readIndexHtml();
    expect(html).toContain('og:title');
    expect(html).toContain('og:description');
    expect(html).toContain('og:url');
    expect(html).toContain('og:image');
  });

  it('должен содержать hreflang для RU, EN, BY, KZ', () => {
    const html = readIndexHtml();
    expect(html).toContain('hreflang="ru"');
    expect(html).toContain('hreflang="en"');
    expect(html).toContain('hreflang="be"');
    expect(html).toContain('hreflang="kk"');
    expect(html).toContain('hreflang="x-default"');
  });

  it('должен содержать og:locale:alternate для be_BY и kk_KZ', () => {
    const html = readIndexHtml();
    expect(html).toContain('og:locale:alternate" content="be_BY"');
    expect(html).toContain('og:locale:alternate" content="kk_KZ"');
  });

  it('должен содержать geo для России, Беларуси, Казахстана', () => {
    const html = readIndexHtml();
    expect(html).toContain('geo.country" content="RU"');
    expect(html).toContain('geo.country" content="BY"');
    expect(html).toContain('geo.country" content="KZ"');
    expect(html).toContain('geo.region" content="BY"');
    expect(html).toContain('geo.region" content="KZ"');
  });

  it('Organization Schema не должен содержать aggregateRating', () => {
    const html = readIndexHtml();
    const orgBlock = html.includes('"@type": "Organization"')
      ? html.slice(html.indexOf('"@type": "Organization"'), html.indexOf('</script>', html.indexOf('"@type": "Organization"')))
      : '';
    expect(orgBlock).not.toContain('aggregateRating');
  });

  it('WebSite Schema не должен содержать SearchAction (поиск не реализован)', () => {
    const html = readIndexHtml();
    const webSiteBlock = html.includes('"@type": "WebSite"')
      ? html.slice(html.indexOf('"@type": "WebSite"'), html.indexOf('</script>', html.indexOf('"@type": "WebSite"')))
      : '';
    expect(webSiteBlock).not.toContain('SearchAction');
    expect(webSiteBlock).not.toContain('potentialAction');
  });
});

describe('SEO: robots.txt', () => {
  it('должен разрешать индексацию и указывать sitemap', () => {
    const robots = readRobotsTxt();
    expect(robots).toMatch(/Allow:\s*\//);
    expect(robots).toContain('Sitemap:');
    expect(robots).toContain('sitemap.xml');
  });

  it('не должен содержать Crawl-delay', () => {
    const robots = readRobotsTxt();
    expect(robots).not.toContain('Crawl-delay');
  });
});
