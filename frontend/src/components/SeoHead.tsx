import React, { useEffect } from 'react';

const SEO_BASE_URL = 'https://pandapal.ru/';
const BREADCRUMB_SCRIPT_ID = 'seo-breadcrumb';

export interface BreadcrumbItem {
  name: string;
  path: string;
}

function buildBreadcrumbJsonLd(items: BreadcrumbItem[]): string {
  const itemListElement = items.map((item, index) => ({
    '@type': 'ListItem',
    position: index + 1,
    name: item.name,
    item: item.path === '/' ? SEO_BASE_URL : `${SEO_BASE_URL}${item.path.replace(/^\//, '')}`,
  }));
  return JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement,
  });
}

interface SeoHeadProps {
  title: string;
  description: string;
  canonicalPath?: string;
  locale?: 'ru_RU' | 'en_US';
  imageUrl?: string;
  breadcrumbs?: BreadcrumbItem[];
}

const ensureMeta = (selector: string, create: () => HTMLMetaElement): HTMLMetaElement => {
  const existing = document.querySelector(selector) as HTMLMetaElement | null;
  if (existing) {
    return existing;
  }
  const created = create();
  document.head.appendChild(created);
  return created;
};

const ensureCanonical = (): HTMLLinkElement => {
  const existing = document.querySelector('link[rel="canonical"]') as HTMLLinkElement | null;
  if (existing) {
    return existing;
  }
  const link = document.createElement('link');
  link.setAttribute('rel', 'canonical');
  document.head.appendChild(link);
  return link;
};

function buildCanonicalUrl(path: string): string {
  const normalized = path === '/' ? '' : path.replace(/^\//, '');
  return normalized ? `${SEO_BASE_URL}${normalized}` : SEO_BASE_URL;
}

export const SeoHead: React.FC<SeoHeadProps> = React.memo(
  ({ title, description, canonicalPath = '/', locale = 'ru_RU', imageUrl, breadcrumbs }) => {
    useEffect(() => {
      const canonicalUrl = buildCanonicalUrl(canonicalPath);
      document.title = title;

    const descriptionMeta = ensureMeta('meta[name="description"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('name', 'description');
      return m;
    });
    descriptionMeta.setAttribute('content', description);

    const ogTitleMeta = ensureMeta('meta[property="og:title"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('property', 'og:title');
      return m;
    });
    ogTitleMeta.setAttribute('content', title);

    const ogDescriptionMeta = ensureMeta('meta[property="og:description"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('property', 'og:description');
      return m;
    });
    ogDescriptionMeta.setAttribute('content', description);

    const ogUrlMeta = ensureMeta('meta[property="og:url"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('property', 'og:url');
      return m;
    });
    ogUrlMeta.setAttribute('content', canonicalUrl);

    const ogLocaleMeta = ensureMeta('meta[property="og:locale"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('property', 'og:locale');
      return m;
    });
    ogLocaleMeta.setAttribute('content', locale);

    const twitterTitleMeta = ensureMeta('meta[name="twitter:title"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('name', 'twitter:title');
      return m;
    });
    twitterTitleMeta.setAttribute('content', title);

    const twitterDescriptionMeta = ensureMeta('meta[name="twitter:description"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('name', 'twitter:description');
      return m;
    });
    twitterDescriptionMeta.setAttribute('content', description);

      if (imageUrl) {
        const ogImageMeta = ensureMeta('meta[property="og:image"]', () => {
          const m = document.createElement('meta');
          m.setAttribute('property', 'og:image');
          return m;
        });
        ogImageMeta.setAttribute('content', imageUrl);
        const twitterImageMeta = ensureMeta('meta[name="twitter:image"]', () => {
          const m = document.createElement('meta');
          m.setAttribute('name', 'twitter:image');
          return m;
        });
        twitterImageMeta.setAttribute('content', imageUrl);
        const twitterImageAltMeta = ensureMeta('meta[name="twitter:image:alt"]', () => {
          const m = document.createElement('meta');
          m.setAttribute('name', 'twitter:image:alt');
          return m;
        });
        twitterImageAltMeta.setAttribute('content', 'PandaPal — безопасный AI-друг для детей');
      }

      const canonical = ensureCanonical();
      canonical.setAttribute('href', canonicalUrl);

      // BreadcrumbList: один script на документ, обновляем по id
      let breadcrumbScript = document.getElementById(BREADCRUMB_SCRIPT_ID) as HTMLScriptElement | null;
      if (breadcrumbs?.length) {
        const jsonLd = buildBreadcrumbJsonLd(breadcrumbs);
        if (breadcrumbScript) {
          breadcrumbScript.textContent = jsonLd;
        } else {
          breadcrumbScript = document.createElement('script');
          breadcrumbScript.id = BREADCRUMB_SCRIPT_ID;
          breadcrumbScript.type = 'application/ld+json';
          breadcrumbScript.textContent = jsonLd;
          document.head.appendChild(breadcrumbScript);
        }
      } else if (breadcrumbScript) {
        breadcrumbScript.remove();
      }
    }, [title, description, canonicalPath, locale, imageUrl, breadcrumbs]);

    return null;
  }
);

SeoHead.displayName = 'SeoHead';
