/**
 * Тесты SEO/AEO для index.html, robots.txt, sitemap.xml и llms.txt.
 * Проверяем каноничность, соц.мета, schema-consistency и discoverability бота.
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

function readSitemapXml(): string {
  return readFileSync(join(frontendRoot, 'public', 'sitemap.xml'), 'utf-8');
}

function readLlmsTxt(): string {
  return readFileSync(join(frontendRoot, 'public', 'llms.txt'), 'utf-8');
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

  it('должен содержать Twitter Card теги', () => {
    const html = readIndexHtml();
    expect(html).toContain('name="twitter:card"');
    expect(html).toContain('name="twitter:title"');
    expect(html).toContain('name="twitter:description"');
    expect(html).toContain('name="twitter:image"');
  });

  it('должен содержать hreflang для RU/EN и x-default', () => {
    const html = readIndexHtml();
    expect(html).toContain('hreflang="ru"');
    expect(html).toContain('hreflang="en"');
    expect(html).toContain('hreflang="x-default"');
  });

  it('НЕ должен содержать скрытый AEO-блок #seo-content', () => {
    const html = readIndexHtml();
    expect(html).not.toContain('id="seo-content"');
  });

  it('должен содержать ссылки на Telegram бота в schema/контенте', () => {
    const html = readIndexHtml();
    expect(html).toContain('https://t.me/PandaPalBot');
    expect(html).toContain('@PandaPalBot');
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

  it('FAQ Schema: ответ про стоимость должен содержать «30» и «месяц»/«мес», не «в день»', () => {
    const html = readIndexHtml();
    const faqBlock = html.includes('"@type": "FAQPage"')
      ? html.slice(html.indexOf('"@type": "FAQPage"'), html.indexOf('</script>', html.indexOf('"@type": "FAQPage"')))
      : '';
    expect(faqBlock).toContain('30');
    expect(faqBlock).toMatch(/месяц|мес/);
    expect(faqBlock).not.toMatch(/30\s*запросов\s*в\s*день/);
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

describe('SEO: sitemap.xml', () => {
  it('должен содержать только канонический URL главной страницы', () => {
    const sitemap = readSitemapXml();
    expect(sitemap).toContain('<loc>https://pandapal.ru/</loc>');
    expect(sitemap).not.toContain('<loc>https://pandapal.ru/premium</loc>');
    expect(sitemap).not.toContain('<loc>https://pandapal.ru/privacy</loc>');
    expect(sitemap).not.toContain('<loc>https://pandapal.ru/offer</loc>');
  });
});

describe('AEO: llms.txt', () => {
  it('должен содержать официальный сайт и Telegram бота', () => {
    const llms = readLlmsTxt();
    expect(llms).toContain('Official website: https://pandapal.ru/');
    expect(llms).toContain('Official Telegram bot: https://t.me/PandaPalBot');
    expect(llms).toContain('Primary handle: @PandaPalBot');
  });
});
