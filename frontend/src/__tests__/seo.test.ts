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

  it('должен содержать hreflang для RU, EN, BY, KZ, MD, RO, KG, UZ, TJ', () => {
    const html = readIndexHtml();
    expect(html).toContain('hreflang="ru"');
    expect(html).toContain('hreflang="en"');
    expect(html).toContain('hreflang="be"');
    expect(html).toContain('hreflang="kk"');
    expect(html).toContain('hreflang="ro"');
    expect(html).toContain('hreflang="ky"');
    expect(html).toContain('hreflang="uz"');
    expect(html).toContain('hreflang="tg"');
    expect(html).toContain('hreflang="x-default"');
  });

  it('должен содержать hreflang для стран диаспоры: US, GB, IL, DE, FR, LV, LT, EE, CA, AU, AR, BR, MX, NZ, UY', () => {
    const html = readIndexHtml();
    expect(html).toContain('hreflang="en-US"');
    expect(html).toContain('hreflang="en-GB"');
    expect(html).toContain('hreflang="he"');
    expect(html).toContain('hreflang="de"');
    expect(html).toContain('hreflang="fr"');
    expect(html).toContain('hreflang="lv"');
    expect(html).toContain('hreflang="lt"');
    expect(html).toContain('hreflang="et"');
    expect(html).toContain('hreflang="en-CA"');
    expect(html).toContain('hreflang="en-AU"');
    expect(html).toContain('hreflang="es-AR"');
    expect(html).toContain('hreflang="pt-BR"');
    expect(html).toContain('hreflang="es-MX"');
    expect(html).toContain('hreflang="en-NZ"');
    expect(html).toContain('hreflang="es-UY"');
  });

  it('НЕ должен содержать UA/Ukraine в SEO-разметке (hreflang, og:locale, geo)', () => {
    const html = readIndexHtml();
    const head = html.slice(0, html.indexOf('</head>'));
    expect(head).not.toMatch(/hreflang="uk"/i);
    expect(head).not.toMatch(/content="uk_UA"/i);
    expect(head).not.toContain('content="UA"');
    expect(html).not.toContain('Ukraine');
    expect(html).not.toContain('Украин');
  });

  it('должен содержать og:locale:alternate для BY, KZ, MD, RO, KG, UZ, TJ', () => {
    const html = readIndexHtml();
    expect(html).toContain('og:locale:alternate" content="be_BY"');
    expect(html).toContain('og:locale:alternate" content="kk_KZ"');
    expect(html).toContain('og:locale:alternate" content="ro_MD"');
    expect(html).toContain('og:locale:alternate" content="ro_RO"');
    expect(html).toContain('og:locale:alternate" content="ky_KG"');
    expect(html).toContain('og:locale:alternate" content="uz_UZ"');
    expect(html).toContain('og:locale:alternate" content="tg_TJ"');
  });

  it('должен содержать og:locale:alternate для диаспоры: GB, IL, DE, FR, LV, LT, EE, CA, AU, AR, BR, MX, NZ, UY', () => {
    const html = readIndexHtml();
    expect(html).toContain('og:locale:alternate" content="en_GB"');
    expect(html).toContain('og:locale:alternate" content="he_IL"');
    expect(html).toContain('og:locale:alternate" content="de_DE"');
    expect(html).toContain('og:locale:alternate" content="fr_FR"');
    expect(html).toContain('og:locale:alternate" content="lv_LV"');
    expect(html).toContain('og:locale:alternate" content="lt_LT"');
    expect(html).toContain('og:locale:alternate" content="et_EE"');
    expect(html).toContain('og:locale:alternate" content="en_CA"');
    expect(html).toContain('og:locale:alternate" content="en_AU"');
    expect(html).toContain('og:locale:alternate" content="es_AR"');
    expect(html).toContain('og:locale:alternate" content="pt_BR"');
    expect(html).toContain('og:locale:alternate" content="es_MX"');
    expect(html).toContain('og:locale:alternate" content="en_NZ"');
    expect(html).toContain('og:locale:alternate" content="es_UY"');
  });

  it('должен содержать geo для RU, BY, KZ, MD, RO, KG, UZ, TJ', () => {
    const html = readIndexHtml();
    expect(html).toContain('geo.country" content="RU"');
    expect(html).toContain('geo.country" content="BY"');
    expect(html).toContain('geo.country" content="KZ"');
    expect(html).toContain('geo.country" content="MD"');
    expect(html).toContain('geo.country" content="RO"');
    expect(html).toContain('geo.country" content="KG"');
    expect(html).toContain('geo.country" content="UZ"');
    expect(html).toContain('geo.country" content="TJ"');
    expect(html).toContain('geo.region" content="BY"');
    expect(html).toContain('geo.region" content="KZ"');
    expect(html).toContain('geo.region" content="MD"');
    expect(html).toContain('geo.region" content="RO"');
    expect(html).toContain('geo.region" content="KG"');
    expect(html).toContain('geo.region" content="UZ"');
    expect(html).toContain('geo.region" content="TJ"');
  });

  it('должен содержать geo для диаспоры: US, GB, IL, DE, FR, LV, LT, EE, CA, AU, AR, BR, MX, NZ, UY', () => {
    const html = readIndexHtml();
    expect(html).toContain('geo.country" content="US"');
    expect(html).toContain('geo.country" content="GB"');
    expect(html).toContain('geo.country" content="IL"');
    expect(html).toContain('geo.country" content="DE"');
    expect(html).toContain('geo.country" content="FR"');
    expect(html).toContain('geo.country" content="LV"');
    expect(html).toContain('geo.country" content="LT"');
    expect(html).toContain('geo.country" content="EE"');
    expect(html).toContain('geo.country" content="CA"');
    expect(html).toContain('geo.country" content="AU"');
    expect(html).toContain('geo.country" content="AR"');
    expect(html).toContain('geo.country" content="BR"');
    expect(html).toContain('geo.country" content="MX"');
    expect(html).toContain('geo.country" content="NZ"');
    expect(html).toContain('geo.country" content="UY"');
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
