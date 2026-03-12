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

  it('должен содержать hreflang для RU/EN и x-default (только языки с контентом)', () => {
    const html = readIndexHtml();
    expect(html).toContain('hreflang="ru"');
    expect(html).toContain('hreflang="en"');
    expect(html).toContain('hreflang="x-default"');
    // Не должно быть локалей без реального контента
    expect(html).not.toContain('hreflang="be"');
    expect(html).not.toContain('hreflang="kk"');
    expect(html).not.toContain('hreflang="de"');
    expect(html).not.toContain('hreflang="fr"');
    expect(html).not.toContain('hreflang="he"');
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

  it('SoftwareApplication Schema должен содержать installUrl на бота', () => {
    const html = readIndexHtml();
    expect(html).toContain('"installUrl": "https://t.me/PandaPalBot"');
  });

  it('Organization Schema должна содержать EducationalOrganization и не содержать aggregateRating', () => {
    const html = readIndexHtml();
    expect(html).toContain('"EducationalOrganization"');
    const orgBlock = html.includes('"EducationalOrganization"')
      ? html.slice(html.indexOf('"EducationalOrganization"'), html.indexOf('</script>', html.indexOf('"EducationalOrganization"')))
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
  it('должен содержать главную и ключевые канонические SEO-страницы', () => {
    const sitemap = readSitemapXml();
    expect(sitemap).toContain('<loc>https://pandapal.ru/</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/bezopasnyy-ai-dlya-detey</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/safe-ai-for-kids</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/pomoshch-s-domashkoy-v-telegram</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/homework-help-telegram-bot</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/premium</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/donation</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/privacy</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/personal-data</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/offer</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/igra-moya-panda</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/help</loc>');
    expect(sitemap).toContain('<loc>https://pandapal.ru/help/kak-nachat</loc>');
  });
});

describe('AEO: llms.txt', () => {
  it('должен содержать официальный сайт и Telegram бота', () => {
    const llms = readLlmsTxt();
    expect(llms).toContain('Official website: https://pandapal.ru/');
    expect(llms).toContain('Official Telegram bot: https://t.me/PandaPalBot');
    expect(llms).toContain('Primary handle: @PandaPalBot');
  });

  it('должен содержать упоминание Моя панда / tamagotchi / виртуальный питомец', () => {
    const llms = readLlmsTxt();
    const hasPandaMention =
      llms.includes('My Panda') ||
      llms.includes('Моя панда') ||
      llms.includes('tamagotchi') ||
      llms.includes('virtual pet') ||
      llms.includes('виртуальный питомец');
    expect(hasPandaMention).toBe(true);
  });

  it('должен содержать прямую ссылку на тамагочи (startapp=my_panda)', () => {
    const llms = readLlmsTxt();
    expect(llms).toContain('startapp=my_panda');
    expect(llms).toContain('t.me/PandaPalBot');
  });

  it('должен содержать FAQ-секцию с вопросами Q: и ответами A:', () => {
    const llms = readLlmsTxt();
    expect(llms).toContain('## FAQ');
    expect(llms).toContain('Q: ');
    expect(llms).toContain('A: ');
    // Должны быть RU и EN вопросы
    expect(llms).toContain('Q: Что такое PandaPal?');
    expect(llms).toContain('Q: What is PandaPal?');
  });
});

describe('SEO: noscript fallback', () => {
  it('должен содержать noscript блок с ключевым контентом', () => {
    const html = readIndexHtml();
    // Должен быть noscript с h1 и основным контентом
    expect(html).toContain('<h1>PandaPal');
    expect(html).toContain('Возможности');
    expect(html).toContain('Частые вопросы');
    expect(html).toContain('t.me/PandaPalBot');
  });
});
